import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema.exceptions import ValidationError

from deepmentor.library import DATA_DIR, Library, StateConflictError, StateError, default_state_dir, resolve_state_dir


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        shutil.copytree(DATA_DIR, self.data)
        self.library = Library(self.data, self.root / "state")
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.library.close)

    def change_pack(self, name, mutate):
        path = self.data / "people" / (name + ".json")
        pack = json.loads(path.read_text())
        mutate(pack)
        path.write_text(json.dumps(pack))

    def test_chinese_alias_and_evidence_backed_retrieval(self):
        result = self.library.guidance_context("呐瓦尔", "软件开源产品如何扩大规模")
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["person"]["id"], "naval")
        self.assertIn("naval-e-leverage", result["citations"])
        self.assertNotIn("naval-e-book-leverage", result["citations"])
        for evidence in result["citations"].values():
            self.assertTrue(evidence["verification"]["origin_verified"])
            self.assertTrue(evidence["source"]["url"].startswith("https://"))

    def test_latest_interview_is_not_falsely_verified(self):
        self.library.evidence["sun-e-portable-video"]["verification"].update(status="pending", origin_verified=False)
        self.assertFalse(self.library.get_evidence("sun-e-portable-video")["eligible"])
        result = self.library.guidance_context("孙宇晨", "本地记录与模型迁移")
        self.assertNotIn("sun-e-portable-video", result["citations"])

    def test_explicit_secondary_policy_preserves_attribution(self):
        result = self.library.guidance_context("孙宇晨", "AI 本地记录与模型迁移", allow_secondary=True)
        self.assertEqual(result["status"], "ready")
        secondary = [e for e in result["citations"].values() if e["source"]["authority"] == "secondary"]
        self.assertTrue(secondary)
        for evidence in secondary:
            self.assertFalse(evidence["verification"]["origin_verified"])
            self.assertIn("TechFlow", evidence["speaker"])
            self.assertTrue(evidence["eligible"])

    def test_unrelated_question_does_not_receive_generic_wisdom(self):
        result = self.library.guidance_context("naval", "量子纠缠光子自旋")
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(result["citations"], {})

    def test_disputed_and_retracted_evidence_never_supports_advice(self):
        for status in ("pending", "disputed", "retracted"):
            with self.subTest(status=status):
                self.library.evidence["naval-e-specific"]["verification"]["status"] = status
                self.assertEqual(self.library.search("naval", "专长"), [])

    def test_changed_source_blocks_evidence(self):
        self.library.state_dir.mkdir()
        (self.library.state_dir / "state.json").write_text(json.dumps({"naval-specific": {"status": "changed"}}))
        self.assertEqual(self.library.search("naval", "专长"), [])

    def test_missing_provenance_rejected(self):
        self.change_pack("naval", lambda p: p["sources"][0].pop("rights"))
        with self.assertRaises(ValidationError):
            Library(self.data, self.library.state_dir)

    def test_broken_evidence_reference_rejected(self):
        self.change_pack("naval", lambda p: p["principles"][0].update(evidence_ids=["missing-evidence"]))
        with self.assertRaisesRegex(ValueError, "Invalid evidence reference"):
            Library(self.data, self.library.state_dir)

    def test_identifiers_must_be_unique_across_entity_types(self):
        self.change_pack("naval", lambda p: p["principles"][0].update(id=p["sources"][0]["id"]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            Library(self.data, self.library.state_dir)

    def test_book_cannot_be_declared_original_by_flag(self):
        self.change_pack("naval", lambda p: next(e for e in p["evidence"] if e["id"] == "naval-e-book-leverage")["verification"].update(origin_verified=True))
        with self.assertRaisesRegex(ValueError, "cannot verify the original"):
            Library(self.data, self.library.state_dir)

    def test_all_mentors_retrieve_applicable_reviewed_material(self):
        examples = [
            ("马斯克", "流程一直变化，要怎样做自动化", "musk-p-automation"),
            ("孙宇晨", "创业怎样降低试错成本", "sun-p-small-experiments"),
            ("呐瓦尔", "团队合作职责和责任不清", "naval-p-accountability"),
            ("段永平", "错误决策怎样纠错并避免沉没成本", "duan-p-correct-errors"),
            ("科比", "失败之后怎样复盘和练习基本功", "kobe-p-failure-fuel"),
            ("周杰伦", "作品被拒绝如何分析反馈与受众适配", "jay-p-feedback-fit"),
            ("景甜", "怎样区分反馈和单纯评价", "jing-p-feedback-filter"),
        ]
        for person, question, expected in examples:
            with self.subTest(person=person):
                result = self.library.guidance_context(person, question)
                self.assertEqual(result["status"], "ready")
                self.assertIn(expected, {p["id"] for p in result["principles"]})
                self.assertTrue(result["citations"])

    def test_invalid_query_inputs_rejected(self):
        for kwargs in ({"query": ""}, {"query": "code", "limit": True}, {"query": "code", "limit": 21}, {"query": "code", "allow_secondary": "true"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.library.search("naval", **kwargs)
        with self.assertRaisesRegex(ValueError, "Unknown person"):
            self.library.person("unknown-person")

    def test_state_dir_resolution_priorities_and_conflict_detection(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            explicit_dir = temp_path / "explicit"
            new_dir = temp_path / ".deepmentor"
            old_dir = temp_path / ".open-mentor"

            # 1. Explicit directory always wins
            self.assertEqual(resolve_state_dir(explicit_dir, base_dir=temp_path), explicit_dir)

            # 2. Neither exists -> returns new_dir (.deepmentor)
            self.assertEqual(resolve_state_dir(None, base_dir=temp_path), new_dir)

            # 3. Old exists with content, new does not -> returns old_dir (protects legacy data!)
            old_dir.mkdir()
            (old_dir / "state.json").write_text('{"naval-specific": {"status": "changed"}}')
            self.assertEqual(resolve_state_dir(None, base_dir=temp_path), old_dir)

            # 4. Migrated: new exists with content, old is removed -> returns new_dir
            new_dir.mkdir()
            (new_dir / "state.json").write_text('{"naval-specific": {"status": "changed"}}')
            shutil.rmtree(old_dir)
            self.assertEqual(resolve_state_dir(None, base_dir=temp_path), new_dir)

            # 5. Conflict: both exist with files -> raises StateConflictError!
            old_dir.mkdir()
            (old_dir / "state.json").write_text('{"naval-specific": {"status": "accepted"}}')
            with self.assertRaises(StateConflictError) as ctx:
                resolve_state_dir(None, base_dir=temp_path)
            self.assertIn("State directory conflict", str(ctx.exception))
            self.assertIn("DeepMentor will not silently merge", str(ctx.exception))

            # 6. If both exist but new is empty, falls back to legacy
            shutil.rmtree(new_dir)
            new_dir.mkdir()
            self.assertEqual(resolve_state_dir(None, base_dir=temp_path), old_dir)

    def test_legacy_open_mentor_compatibility_module(self):
        import warnings
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            import open_mentor
            from open_mentor.library import Library as LegacyLibrary
            from open_mentor.cli import main as legacy_cli
            self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in recorded))
            self.assertEqual(open_mentor.__version__, "0.1.0")
            self.assertIs(LegacyLibrary, Library)
            self.assertTrue(callable(legacy_cli))
