import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from deepmentor.library import Library


NEW_PEOPLE = {'paul-graham', 'warren-buffett', 'charlie-munger', 'jeff-bezos',
              'james-clear', 'lei-jun', 'allen-zhang',
              'steve-jobs', 'bill-gates', 'sam-altman', 'andrew-ng', 'fei-fei-li',
              'jensen-huang', 'satya-nadella', 'zhang-yiming', 'ren-zhengfei',
              'richard-feynman', 'derek-sivers', 'morgan-housel', 'adam-grant',
              'carol-dweck', 'angela-duckworth', 'brene-brown'}
CASES = json.loads((Path(__file__).parent / 'fixtures' / 'mentor_scenarios.json').read_text())
AUTO_CASES = [c for c in CASES if c['id'].startswith(('expansion-auto-', 'thirty-auto-'))]


class ExpansionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.library = Library(state_dir=self.root)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.library.close)

    def test_each_requested_pack_has_substantial_traceable_coverage(self):
        self.assertTrue(NEW_PEOPLE <= self.library.people.keys())
        self.assertEqual({c['person'] for c in AUTO_CASES}, NEW_PEOPLE)
        for person in NEW_PEOPLE:
            principles = [p for p in self.library.principles.values() if p['person_id'] == person]
            self.assertGreaterEqual(len(principles), 15)
            # Volume is only a structural check; the reviewed scenario set covers different tasks.
            named = [c for c in CASES if c.get('person') == person and c.get('method') == 'single_person_mentioned']
            self.assertGreaterEqual(len({c.get('principle') for c in named if c.get('principle')}), 6)
            for p in principles:
                for eid in p['evidence_ids']:
                    e = self.library.get_evidence(eid)
                    self.assertTrue(e['eligible'], eid)
                    self.assertEqual(e['person_id'], person)
                    self.assertTrue(e['locator']['value'])
                    self.assertTrue(e['context'])
                    self.assertTrue(p['application']['limits'])

    def test_changed_and_unavailable_new_sources_block_explicit_and_automatic_use(self):
        for status in ['changed', 'unavailable']:
            state = {s['id']: {'status': status} for s in self.library.sources.values() if s['person_id'] in NEW_PEOPLE}
            (self.root / 'state.json').write_text(json.dumps(state))
            for case in AUTO_CASES:
                with self.subTest(status=status, person=case['person']):
                    explicit = self.library.ask(case['request'], person=case['person'], allow_secondary=True)
                    self.assertEqual(explicit['status'], 'insufficient_evidence')
                    self.assertFalse(explicit['citations'])
                    automatic = self.library.ask(case['request'])
                    if automatic.get('person'):
                        self.assertNotIn(automatic['person']['id'], NEW_PEOPLE)
                    self.assertTrue(all(e['person_id'] not in NEW_PEOPLE for e in automatic['citations'].values()))

    def test_new_material_does_not_bypass_review_status_or_original_verification(self):
        original = deepcopy(self.library.evidence)
        for status in ['pending', 'disputed', 'retracted', 'original_not_verified']:
            self.library.evidence = deepcopy(original)
            for e in self.library.evidence.values():
                if e['person_id'] not in NEW_PEOPLE:
                    continue
                if status == 'original_not_verified':
                    e['verification']['origin_verified'] = False
                else:
                    e['verification']['status'] = status
            for case in AUTO_CASES:
                with self.subTest(status=status, person=case['person']):
                    result = self.library.ask(case['request'], person=case['person'])
                    self.assertEqual(result['status'], 'insufficient_evidence')
                    self.assertFalse(result['citations'])

    def test_each_new_pack_is_usable_from_real_cli(self):
        for case in AUTO_CASES:
            with self.subTest(person=case['person']):
                result = subprocess.run([sys.executable, '-m', 'deepmentor', '--state-dir', self.temp.name,
                                         'ask', case['request'], '--person', case['person'], '--format', 'json'],
                                        capture_output=True, text=True, check=True)
                payload = json.loads(result.stdout)
                self.assertEqual(payload['person']['id'], case['person'])
                self.assertIn(case['principle'], {p['id'] for p in payload['principles']})
                self.assertTrue(all(e['eligible'] and e['person_id'] == case['person'] for e in payload['citations'].values()))

    def test_all_aliases_resolve_and_unreviewed_sources_stay_unusable(self):
        for person in NEW_PEOPLE:
            profile = self.library.people[person]
            for alias in [profile['name'], *profile['aliases']]:
                self.assertEqual(self.library.person(alias)['id'], person)
        for s in self.library.sources.values():
            if s['person_id'] in NEW_PEOPLE:
                s['review']['status'] = 'pending'
        for c in AUTO_CASES:
            with self.subTest(person=c['person']):
                result = self.library.ask(c['request'], person=c['person'])
                self.assertEqual(result['status'], 'insufficient_evidence')
                self.assertFalse(result['citations'])

    def test_mentor_frameworks_do_not_supply_specialist_answers(self):
        for person in NEW_PEOPLE:
            for question in ['胸口痛应该吃什么药', '股票明天一定涨吗',
                             '我的合同应该怎么起诉维权', '求解这个积分有什么结果']:
                with self.subTest(person=person, question=question):
                    result = self.library.ask(question, person=person)
                    self.assertEqual(result['status'], 'insufficient_evidence')
                    self.assertFalse(result['citations'])
