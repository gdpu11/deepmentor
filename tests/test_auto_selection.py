import json
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path

from deepmentor.library import Library
from deepmentor.rendering import render_guidance

SCENARIOS = Path(__file__).parent / "fixtures" / "mentor_scenarios.json"


class AutoSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.library = Library(state_dir=Path(self.temp.name))
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.library.close)

    def test_scenarios_match_useful_sources_or_refuse_without_guessing(self):
        cases = json.loads(SCENARIOS.read_text())
        self.assertGreaterEqual(len(cases), 80)
        for case in cases:
            with self.subTest(case=case["id"]):
                r = self.library.ask(case["request"], person=case.get("explicit_person"), situation=case.get("situation"))
                self.assertEqual(r["status"], case.get("status", "ready"))
                if "excluded_intent" in case:
                    self.assertNotIn(case["excluded_intent"], r.get("query_analysis", {}).get("intents", []))
                if "person" in case:
                    self.assertEqual(r["person"]["id"], case["person"])
                    self.assertEqual(r["request_resolution"]["method"], case.get("method", "automatic_evidence_match"))
                if r["status"] == "ready":
                    self.assertIn(case["principle"], {p["id"] for p in r["principles"]})
                    self.assertTrue(r["request_resolution"]["reason"])
                    self.assertTrue(r["citations"])
                    self.assertTrue(all(e["person_id"] == r["person"]["id"] and e["eligible"]
                                        and e["verification"]["status"] == "reviewed" and e["verification"]["origin_verified"]
                                        for e in r["citations"].values()))
                    rendered = render_guidance(r)
                    self.assertIn("本次采用的导师资料", rendered)
                    self.assertIn(r["person"]["name"], rendered)
                    if r["request_resolution"]["method"] == "automatic_evidence_match":
                        self.assertIn("自动匹配", rendered)
                        self.assertIn("选择理由", rendered)
                else:
                    self.assertFalse(r["citations"])
                    if r["status"] == "needs_context":
                        self.assertIn("缺少原问题", render_guidance(r))
                    elif r.get("person") is None and r["status"] != "needs_person_selection":
                        self.assertIn("没有足够", render_guidance(r))

    def test_ranking_is_stable_independent_of_output_limit(self):
        request = "用OpenMentor帮我看看，怎么赚自己的第一个100w"
        choices = [self.library.ask(request, limit=n) for n in [1, 3, 5, 20]]
        self.assertEqual({r["person"]["id"] for r in choices}, {"justin-sun"})
        rankings = [r["request_resolution"]["candidates"] for r in choices]
        self.assertTrue(all(r == rankings[0] for r in rankings))
        for r in choices:
            self.assertTrue(set(r["request_resolution"]["supporting_principle_ids"]) <= {p["id"] for p in r["principles"]})

    def test_unusable_sources_are_excluded_before_selecting_a_person(self):
        state = {s["id"]: {"status": "changed"} for s in self.library.sources.values() if s["person_id"] == "justin-sun"}
        (self.library.state_dir / "state.json").write_text(json.dumps(state))
        r = self.library.ask("怎么赚自己的第一个100w")
        self.assertEqual(r["status"], "ready")
        self.assertNotEqual(r["person"]["id"], "justin-sun")
        self.assertNotIn("justin-sun", {p["person_id"] for p in r["request_resolution"]["candidates"]})
        self.assertTrue(all(e["person_id"] != "justin-sun" for e in r["citations"].values()))
        explicit = self.library.ask("怎么赚自己的第一个100w", person="孙宇晨")
        self.assertEqual(explicit["status"], "insufficient_evidence")
        self.assertEqual(explicit["person"]["id"], "justin-sun")
        state = {s["id"]: {"status": "changed"} for s in self.library.sources.values()}
        (self.library.state_dir / "state.json").write_text(json.dumps(state))
        self.assertEqual(self.library.ask("怎么赚自己的第一个100w")["status"], "insufficient_evidence")

    def test_pending_disputed_and_retracted_material_cannot_select_a_mentor(self):
        for status in ["pending", "disputed", "retracted"]:
            for e in self.library.evidence.values():
                e["verification"]["status"] = status
            for allow_secondary in [False, True]:
                with self.subTest(status=status, allow_secondary=allow_secondary):
                    r = self.library.ask("怎么赚自己的第一个100w", allow_secondary=allow_secondary)
                    self.assertEqual(r["status"], "insufficient_evidence")
                    self.assertIsNone(r["person"])
                    self.assertFalse(r["citations"])

    def test_cli_identifies_automatically_selected_mentor_and_reason(self):
        for mod in ["deepmentor", "open_mentor"]:
            command = [sys.executable, "-m", mod, "--state-dir", self.temp.name, "ask", "用DeepMentor帮我看看，怎么赚自己的第一个100w"]
            r = json.loads(subprocess.run(command + ["--format", "json"], capture_output=True, text=True, check=True).stdout)
            self.assertEqual(r["person"]["id"], "justin-sun")
            self.assertEqual(r["request_resolution"]["method"], "automatic_evidence_match")
            text = subprocess.run(command, capture_output=True, text=True, check=True).stdout
            self.assertIn("**孙宇晨**（自动匹配）", text)
            self.assertIn("选择理由", text)
            self.assertIn("sun-e-customer-value-video", text)
