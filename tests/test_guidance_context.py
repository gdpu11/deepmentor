import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from open_mentor.library import Library
from open_mentor.rendering import render_guidance


class GuidanceContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.library = Library(state_dir=self.root)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.library.close)

    def test_followup_requires_actual_context_even_with_a_named_mentor(self):
        for question in ["那我应该先做哪一步", "OpenMentor，接下来怎么办？", "What should I do next?", "用纳瓦尔的知识库分析一下，接下来怎么办", "接下来呢", "那我下一步该干啥"]:
            with self.subTest(question=question):
                result = self.library.ask(question)
                self.assertEqual(result["status"], "needs_context")
                self.assertFalse(result["citations"])
                self.assertFalse(result["principles"])
                self.assertIn("缺少原问题", render_guidance(result))
        explicit = self.library.ask("用孙宇晨的知识库分析，接下来怎么办", person="naval")
        self.assertEqual(explicit["status"], "needs_context")
        self.assertEqual(explicit["person"]["id"], "naval")

    def test_excluded_mentor_invocations_do_not_pollute_retrieval(self):
        for request in ["不要用孙宇晨，怎么赚第一个100w", "不要用孙宇晨和纳瓦尔的知识库，怎么赚第一个100w"]:
            result = self.library.ask(request)
            self.assertEqual(result["query_analysis"]["retrieval_query"], "怎么赚第一个100w")
            excluded = set(result["request_resolution"]["excluded_person_ids"])
            self.assertNotIn(result["person"]["id"], excluded)
            self.assertTrue(all(e["person_id"] not in excluded for e in result["citations"].values()))

    def test_followup_uses_supplied_problem_and_does_not_persist_user_facts(self):
        situation = "原问题是怎么赚第一个100w；我会Python，每周能投入10小时"
        result = self.library.ask("那我应该先做哪一步", situation=situation)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["person"]["id"], "justin-sun")
        self.assertEqual(result["user_situation"], situation)
        self.assertEqual(result["query_analysis"]["retrieval_basis"], "situation")
        self.assertIn("sun-e-customer-value-video", result["citations"])
        self.assertIn(situation, render_guidance(result))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_background_names_do_not_choose_the_mentor_or_change_the_main_problem(self):
        situation = "我是马斯克粉丝，也读纳瓦尔的书；每周有10小时"
        baseline = self.library.ask("怎么赚第一个100w")
        result = self.library.ask("怎么赚第一个100w", situation=situation)
        self.assertEqual(result["person"], baseline["person"])
        self.assertEqual(result["citations"], baseline["citations"])
        self.assertEqual(result["query_analysis"]["retrieval_basis"], "request")
        explicit = self.library.ask("怎么赚第一个100w", person="naval", situation=situation)
        self.assertEqual(explicit["person"]["id"], "naval")
        self.assertTrue(all(e["person_id"] == "naval" for e in explicit["citations"].values()))

    def test_context_cannot_bypass_source_gates_and_medical_task_requirements(self):
        state = {s["id"]: {"status": "changed"} for s in self.library.sources.values()}
        (self.root / "state.json").write_text(json.dumps(state))
        result = self.library.ask("那我应该先做哪一步", situation="原问题是怎么赚第一个100w")
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertFalse(result["citations"])
        (self.root / "state.json").unlink()
        result = self.library.ask("那我应该先做哪一步", situation="阅读时突然胸痛，应该吃什么药")
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertFalse(result["citations"])

    def test_invalid_background_and_options_rejected_on_both_guidance_entrypoints(self):
        for situation in ["", " ", [], 7, "背" * 10000]:
            with self.subTest(situation_type=type(situation).__name__), self.assertRaises(ValueError):
                self.library.ask("怎么赚钱", situation=situation)
            with self.assertRaises(ValueError):
                self.library.guidance_context("naval", "怎么赚钱", situation=situation)
        for kwargs in [{"limit": True}, {"limit": 0}, {"allow_secondary": "false"}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.library.guidance_context("naval", "那我应该先做哪一步", **kwargs)

    def test_financial_scope_notice_only_appears_for_an_income_question(self):
        for question in ["如何养成阅读习惯", "合作伙伴失信怎么办", "我想转行，如何选择职业方向"]:
            result = self.library.ask(question)
            self.assertEqual(result["status"], "ready")
            self.assertNotIn("目标金额或达成期限", render_guidance(result))
        self.assertIn("目标金额或达成期限", render_guidance(self.library.ask("怎么赚第一个100w")))

    def test_cli_supports_contextual_followup_and_preserves_explicit_mentor(self):
        command = [sys.executable, "-m", "open_mentor", "--state-dir", self.temp.name]
        situation = "原问题是怎么赚第一个100w，我有后端开发经验"
        result = subprocess.run(command + ["ask", "那我应该先做哪一步", "--situation", situation, "--format", "json"], capture_output=True, text=True, check=True)
        payload = json.loads(result.stdout)
        expected = self.library.ask("那我应该先做哪一步", situation=situation)
        self.assertEqual(payload["person"], expected["person"])
        self.assertEqual(payload["citations"], expected["citations"])
        self.assertEqual(payload["user_situation"], situation)
        result = subprocess.run(command + ["context", "那我应该先做哪一步", "--person", "naval", "--situation", situation], capture_output=True, text=True, check=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["person"]["id"], "naval")
        self.assertEqual(payload["status"], "ready")
