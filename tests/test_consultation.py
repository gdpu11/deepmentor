import asyncio
import io
import json
import os
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from deepmentor.cli import main
from deepmentor.library import Library, StateError
from deepmentor.ledger import Ledger, render_action
from deepmentor.scaffold import scaffold


class ConsultationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.library = Library(state_dir=self.root)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.library.close)

    def test_board_has_cited_perspectives_matrix_and_editorial_cross_examination(self):
        result = self.library.consult_board('创业如何验证用户需求与控制风险')
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(len(result['perspectives']), 3)
        self.assertTrue(result['cross_examination'])
        for row in result['tradeoff_matrix'] + result['cross_examination']:
            self.assertTrue(row['evidence_ids'])
            self.assertTrue(set(row['evidence_ids']) <= result['citations'].keys())
        self.assertEqual(len({c['person']['id'] for c in result['perspectives']}), 3)

    def test_automatic_board_reports_selection_method_in_markdown(self):
        from deepmentor.rendering import render_consultation
        result = self.library.consult_board('创业如何验证用户需求与控制风险')
        rendered = render_consultation(result)
        self.assertIn('自动匹配', rendered)
        self.assertIn('选择理由', rendered)
        self.assertNotIn('按请求指定', rendered)
        explicit = self.library.consult_board('software leverage', ['naval', 'kobe-bryant'])
        self.assertEqual(explicit['perspectives'][0]['request_resolution']['method'], 'explicit_board')

    def test_explicit_board_does_not_replace_missing_mentor_evidence(self):
        result = self.library.consult_board('software leverage', ['naval', 'kobe-bryant'])
        self.assertEqual(result['status'], 'insufficient_evidence')
        self.assertIn('kobe-bryant', result['unavailable_people'])
        self.assertEqual([c['person']['id'] for c in result['perspectives']], ['naval'])
        for people in (['naval', '呐瓦尔'], ['naval'], 'naval', ['unknown', 'naval']):
            with self.assertRaises(ValueError):
                self.library.consult_board('software', people)

    def test_board_respects_negation_and_unknown_requested_names(self):
        result = self.library.consult_board('不要用纳瓦尔，创业如何验证需求')
        self.assertNotIn('naval', [c['person']['id'] for c in result['perspectives']])
        result = self.library.consult_board('用孔子的知识库分析创业')
        self.assertEqual(result['status'], 'needs_person_selection')
        self.assertFalse(result['citations'])

    def test_no_context_or_no_evidence_does_not_create_debate(self):
        for question, status in [('那先做哪一步', 'needs_context'), ('量子纠缠光子自旋', 'insufficient_evidence')]:
            result = self.library.consult_board(question)
            self.assertEqual(result['status'], status)
            self.assertFalse(result['citations'])

    def test_changed_sources_are_removed_from_board_and_stress_test(self):
        initial = self.library.consult_board('软件开源产品如何扩大规模')
        blocked = {e['source_id']: {'status': 'changed'} for e in self.library.evidence.values()}
        (self.root / 'state.json').write_text(json.dumps(blocked))
        self.assertTrue(initial['citations'])
        for result in (self.library.consult_board('软件开源产品如何扩大规模'),
                       self.library.stress_test('软件开源产品如何扩大规模')):
            self.assertEqual(result['status'], 'insufficient_evidence')
            self.assertFalse(result['citations'])

    def test_stress_test_uses_real_limits_and_citations(self):
        result = self.library.stress_test('software leverage', 'naval')
        self.assertEqual(result['status'], 'ready')
        self.assertTrue(result['failure_modes'])
        for mode in result['failure_modes']:
            self.assertTrue(set(mode['evidence_ids']) <= result['citations'].keys())
            self.assertEqual(mode['kind'], 'editorial_stress_question')

    def test_diagnosis_waits_for_all_answers_and_does_not_save(self):
        result = self.library.diagnose('如何验证创业需求', {'goal': '本月验证付费需求'})
        self.assertEqual(result['status'], 'needs_clarification')
        self.assertEqual([q['id'] for q in result['questions']], ['resources', 'downside'])
        answers = {'goal': '本月验证付费需求', 'resources': '每周10小时', 'downside': '预算1000元，未获得有效反馈就停止'}
        result = self.library.diagnose('如何验证创业需求', answers)
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['artifact_type'], 'decision_memo_context')
        self.assertIn('每周10小时', result['user_situation'])
        self.assertFalse(list(self.root.iterdir()))
        for bad in ([], {'goall': 'x'}, {'goal': True}, {'goal': ''}):
            with self.assertRaises(ValueError):
                self.library.diagnose('如何创业', bad)

    def test_scaffold_is_pending_and_never_overwrites(self):
        path = self.root / 'data' / 'people' / 'test-person.json'
        args = ('test-person', 'Test Person', 'https://example.com/article', 'An article', 'Example', 'User supplied short text', 'Section 1', '待核摘要', path)
        scaffold(*args)
        with LibraryContext(path.parent.parent, self.root / 'draft-state') as draft:
            self.assertEqual(draft.search('test-person', '待核摘要'), [])
            e = draft.get_evidence('test-person-e-01')
            self.assertFalse(e['eligible'])
            self.assertIsNone(e['source']['content_sha256'])
        with self.assertRaises(FileExistsError):
            scaffold(*args)

    def test_cli_interview_board_alias_and_ledger_export(self):
        for argv in (['ask', '如何验证创业用户需求', '--mode', 'board'],
                     ['roast', 'software leverage', '--person', 'naval'],
                     ['interview', '如何创业']):
            with redirect_stdout(io.StringIO()) as out:
                main(['--state-dir', str(self.root), *argv])
            self.assertIn('DeepMentor', out.getvalue())
        action = self.add_action()
        with redirect_stdout(io.StringIO()) as out:
            main(['--state-dir', str(self.root), 'action-export', action['id']])
        self.assertIn('ACTION-PLAN', out.getvalue())
        self.assertIn('停止条件', out.getvalue())

    def add_action(self):
        return Ledger(self.library).add('用户愿意为工具付费', '72小时访谈5人', '至少2人愿意试用', '无人愿意试用就停止', '2026-11-01', ['naval-e-leverage'])

    def test_ledger_persists_checkins_and_rechecks_changed_sources(self):
        action = self.add_action()
        ledger = Ledger(self.library)
        row = ledger.check_in(action['id'], '访谈5人，2人愿意试用', 'completed')
        self.assertEqual(row['status'], 'completed')
        self.assertEqual(len(row['checkins']), 1)
        self.assertEqual(ledger.list('active'), [])
        self.assertIn('访谈5人', render_action(row))
        eid = row['evidence_ids'][0]
        source = self.library.evidence[eid]['source_id']
        (self.root / 'state.json').write_text(json.dumps({source: {'status': 'changed'}}))
        self.assertFalse(ledger.get(row['id'])['evidence_status'][0]['eligible'])
        with self.assertRaises(ValueError):
            self.add_action()
        (self.root / 'state.json').write_text('{broken')
        with self.assertRaises(StateError):
            ledger.get(row['id'])

    def test_ledger_concurrent_checkins_preserve_every_observation(self):
        action = self.add_action()
        def update(n):
            # Each process/connection has its own library, as CLI/HTTP/MCP do.
            with LibraryContext(state_dir=self.root) as lib:
                Ledger(lib).check_in(action['id'], f'observation {n}')
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(update, range(12)))
        self.assertEqual(len(Ledger(self.library).get(action['id'])['checkins']), 12)

    def test_corrupt_ledger_fails_without_resetting_user_data(self):
        path = self.root / 'ledger.sqlite3'
        path.write_text('corrupt-user-data')
        with self.assertRaisesRegex(ValueError, 'repair or restore'):
            Ledger(self.library).list()
        self.assertEqual(path.read_text(), 'corrupt-user-data')

    def test_invalid_status_types_are_rejected_before_mutating_ledger(self):
        ledger = Ledger(self.library)
        action = self.add_action()
        for status in ([], {}, True, 1):
            with self.subTest(status=status):
                with self.assertRaises(ValueError):
                    ledger.list(status)
                with self.assertRaises(ValueError):
                    ledger.check_in(action['id'], 'invalid status', status)
        row = ledger.get(action['id'])
        self.assertEqual(row['status'], 'active')
        self.assertEqual(row['checkins'], [])

    def test_ledger_invalid_input_does_not_create_state(self):
        ledger = Ledger(self.library)
        self.assertEqual(ledger.list(), [])
        with self.assertRaises(ValueError):
            ledger.add('hypothesis', 'probe', 'success', 'stop', 'tomorrow')
        with self.assertRaises(ValueError):
            ledger.add('hypothesis', 'probe', 'success', 'stop', '2026-11-01', 'naval-e-leverage')
        self.assertFalse(ledger.path.exists())


class LibraryContext:
    def __init__(self, data_dir=None, state_dir=None):
        self.library = Library(data_dir, state_dir)
    def __enter__(self):
        return self.library
    def __exit__(self, *args):
        self.library.close()
