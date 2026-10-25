import json
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from open_mentor.cli import main
from open_mentor.library import Library, default_state_dir
from open_mentor.rendering import render_guidance
from open_mentor.retrieval import analyze_query

REQUEST = "帮我用OpenMentor问问孙宇晨，怎么赚自己的第一个100w"


class AskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.library = Library(state_dir=Path(self.temp.name))
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.library.close)

    def test_money_paraphrases_retrieve_business_value_and_small_experiments(self):
        for question in [REQUEST, "怎么赚自己的第一个100W", "怎么挣自己的第一个100w", "如何赚到100万", "怎么赚到第一笔钱", "靠自己挣到第一桶金", "how to make my first million", "how can I earn a million", "帮我用OpenMentor的孙宇晨知识库来分析一下，怎么赚自己的第一个100w"]:
            with self.subTest(question=question):
                result = self.library.guidance_context("孙宇晨", question)
                self.assertEqual(result["status"], "ready")
                self.assertEqual(result["answer_scope"], "related_principles")
                ids = {p["id"] for p in result["principles"]}
                self.assertIn("sun-p-customer-value", ids)
                self.assertIn("sun-p-small-experiments", ids)
                self.assertNotIn("sun-p-select-methods", ids)
                self.assertNotIn("sun-p-capital-context", ids)  # financing is not personal income
                self.assertTrue(all(e["eligible"] and e["verification"]["origin_verified"] for e in result["citations"].values()))
                self.assertTrue(all(e["person_id"] == "justin-sun" for e in result["citations"].values()))
                self.assertTrue(any("币种" in q and "净利润" in q for q in result["questions_to_resolve"]))

    def test_filler_words_do_not_make_unrelated_question_answerable(self):
        for question in ["你觉得我自己的第一个问题怎么处理", "量子纠缠光子自旋", "帮我用孙宇晨知识库解释量子纠缠光子自旋", "使用OpenMentor孙宇晨的知识库，分析量子纠缠光子自旋", "我想用孙宇晨的知识库来解释一下量子纠缠光子自旋"]:
            result = self.library.guidance_context("孙宇晨", question)
            self.assertEqual(result["status"], "insufficient_evidence")
            self.assertFalse(result["citations"])
        self.assertFalse(analyze_query("我不想赚钱，只想学习摄影")["intents"])

    def test_invocation_is_not_retrieval_evidence(self):
        result = self.library.ask(REQUEST)
        self.assertEqual(result["query_analysis"]["retrieval_query"], "怎么赚自己的第一个100w")
        self.assertEqual(result["question"], REQUEST)
        for name in [p["name"] for p in self.library.people.values()]:
            result = self.library.ask(f"帮我用{name}的知识库解释量子纠缠光子自旋")
            self.assertEqual(result["status"], "insufficient_evidence", name)

    def test_natural_request_resolves_one_mentor_without_cross_person_evidence(self):
        result = self.library.ask(REQUEST)
        self.assertEqual(result["person"]["id"], "justin-sun")
        self.assertEqual(result["request_resolution"]["method"], "single_person_mentioned")
        english = self.library.ask("Please use Justin Sun: how can I earn my first million?")
        self.assertEqual(english["person"]["id"], "justin-sun")
        self.assertEqual(english["status"], "ready")
        explicit = self.library.ask("比较孙宇晨和马斯克对客户价值的看法", person="孙宇晨")
        self.assertEqual(explicit["person"]["id"], "justin-sun")

    def test_ambiguous_or_unavailable_mentor_requires_selection(self):
        for request in ["用孙宇晨和纳瓦尔的知识分析赚钱", "ask Jaywalking about software", "请用爱因斯坦的知识库分析投资"]:
            result = self.library.ask(request)
            self.assertEqual(result["status"], "needs_person_selection")
            self.assertFalse(result["citations"])
        for kwargs in [{"request": None}, {"request": ""}, {"request": REQUEST, "limit": True}, {"request": REQUEST, "person": 42}, {"request": REQUEST, "allow_secondary": "false"}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.library.ask(**kwargs)

    def test_topic_expansion_cannot_bypass_verification_or_changed_sources(self):
        state = {"sun-alan-video": {"status": "changed"}}
        (self.library.state_dir / "state.json").write_text(json.dumps(state))
        result = self.library.ask(REQUEST)
        self.assertNotIn("sun-e-customer-value-video", result["citations"])
        for e in self.library.evidence.values():
            if e["person_id"] == "justin-sun":
                e["verification"]["status"] = "pending"
        result = self.library.ask(REQUEST, allow_secondary=True)
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertFalse(result["citations"])

    def test_default_review_state_is_independent_of_working_directory(self):
        expected = default_state_dir()
        with patch("pathlib.Path.cwd", return_value=Path(self.temp.name)):
            self.assertEqual(default_state_dir(), expected)
            with patch("open_mentor.library.default_state_dir", return_value=Path(self.temp.name)), closing(Library()) as library:
                self.assertEqual(library.state_dir, Path(self.temp.name))
        # CLI must delegate the default to Library too, rather than supplying cwd/.open-mentor.
        state = {s["id"]: {"status": "changed"} for s in self.library.sources.values() if s["person_id"] == "justin-sun"}
        (Path(self.temp.name) / "state.json").write_text(json.dumps(state))
        with patch("open_mentor.library.default_state_dir", return_value=Path(self.temp.name)), redirect_stdout(io.StringIO()) as output:
            main(["ask", REQUEST, "--format", "json"])
        self.assertEqual(json.loads(output.getvalue())["status"], "insufficient_evidence")

    def test_cli_outputs_cited_readable_material_and_machine_context(self):
        command = [sys.executable, "-m", "open_mentor", "--state-dir", self.temp.name, "ask", REQUEST]
        result = subprocess.run(command + ["--format", "json"], capture_output=True, text=True, check=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ready")
        self.assertIn("sun-e-customer-value-video", payload["citations"])
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        self.assertIn("编辑整理", result.stdout)
        self.assertIn("sun-e-small-experiments", result.stdout)
        self.assertIn("youtube.com/watch?v=0Z-vhBvBmUY&t=2132", result.stdout)
        self.assertIn("净利润", result.stdout)
        self.assertNotIn("sun-e-models-william", result.stdout)
        blocked = self.library.ask("帮我用孙宇晨知识库解释量子纠缠光子自旋")
        self.assertIn("没有足够", render_guidance(blocked))
