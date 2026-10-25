import json
import gzip
import tempfile
import unittest
import zlib
from copy import deepcopy
from email.message import Message
from io import BytesIO
from http.client import IncompleteRead
from pathlib import Path
from unittest.mock import patch

import brotli

from open_mentor.library import Library, StateError
from open_mentor.updates import Updates, fetch_text, normalize, sha256, visible_text


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.library = Library(state_dir=self.root / "state")
        self.updates = Updates(self.library)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.library.close)

    def test_visible_text_excludes_scripts_and_navigation(self):
        text = visible_text('<nav>noise</nav><script>ignore()</script><p>Hello &amp; world</p>')
        self.assertEqual(text, "Hello & world")
        self.assertEqual(normalize("Ａ\n  B"), "A B")

    def response(self, data, content_type="text/html", encoding=None):
        response = BytesIO(data)
        response.url = "https://example.org/original"
        response.headers = Message()
        response.headers["Content-Type"] = content_type
        if encoding:
            response.headers["Content-Encoding"] = encoding
        return response

    def test_compressed_original_pages_have_the_same_normalized_text(self):
        html = '<nav>site</nav><p>用户 &amp; creator’s value</p>'.encode()
        for encoding, data in [("identity", html), ("gzip", gzip.compress(html)),
                               ("br", brotli.compress(html)), ("deflate", zlib.compress(html))]:
            with self.subTest(encoding=encoding), patch("open_mentor.updates.urlopen", return_value=self.response(data, encoding=encoding)):
                self.assertEqual(fetch_text("https://example.org/original"), "用户 & creator’s value")

    def test_legacy_and_declared_html_charsets_remain_readable(self):
        cases = [("<p>creator’s value</p>".encode("cp1252"), "text/html", "creator’s value"),
                 ('<meta charset="gbk"><p>用户价值</p>'.encode("gbk"), "text/html", "用户价值"),
                 ("café".encode("latin-1"), "text/plain; charset=iso-8859-1", "café")]
        for data, content_type, expected in cases:
            with self.subTest(content_type=content_type), patch("open_mentor.updates.urlopen", return_value=self.response(data, content_type)):
                self.assertEqual(fetch_text("https://example.org/original"), expected)
        # A declared charset is a contract, not a reason to silently reinterpret corrupt text.
        with patch("open_mentor.updates.urlopen", return_value=self.response(b"\xff", "text/html; charset=utf-8")):
            with self.assertRaises(UnicodeDecodeError):
                fetch_text("https://example.org/original")

    def test_invalid_or_oversized_decoded_source_is_not_accepted(self):
        for data, encoding in [(b"broken", "br"), (b"broken", "deflate"), (b"raw", "unsupported"),
                               (gzip.compress(b"x" * (4 * 1024 * 1024 + 1)), "gzip")]:
            with self.subTest(encoding=encoding), patch("open_mentor.updates.urlopen", return_value=self.response(data, encoding=encoding)):
                with self.assertRaises(ValueError):
                    fetch_text("https://example.org/original")

    def test_truncated_gzip_marks_source_unavailable_instead_of_leaving_it_accepted(self):
        data = gzip.compress(b"incomplete source response")[:-3]
        with patch("open_mentor.updates.urlopen", return_value=self.response(data, encoding="gzip")):
            result = self.updates.check("naval-specific")
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("Invalid gzip", result["error"])
        self.assertFalse(self.library.get_evidence("naval-e-specific")["eligible"])

    def test_interrupted_http_body_also_marks_source_unavailable(self):
        response = self.response(b"partial")
        with patch.object(response, "read", side_effect=IncompleteRead(b"partial", 12)):
            with patch("open_mentor.updates.urlopen", return_value=response):
                result = self.updates.check("naval-specific")
        self.assertEqual(result["status"], "unavailable")
        self.assertFalse(self.library.get_evidence("naval-e-specific")["eligible"])

    def test_eligibility_and_source_metadata_use_the_same_observed_revision(self):
        accepted = self.library.source("naval-specific")
        changed = {**deepcopy(accepted), "runtime": {"status": "changed"}}
        with patch.object(self.library, "source", side_effect=[accepted, changed]):
            result = self.library.get_evidence("naval-e-specific")
        self.assertEqual(result["eligible"], result["source"]["runtime"].get("status", "accepted") == "accepted")

    def test_corrupt_review_state_fails_closed_without_overwriting_it(self):
        self.library.state_dir.mkdir()
        path = self.library.state_dir / "state.json"
        values = ["{invalid", "[]", "null", '{"naval-specific": []}', '{"naval-specific": {}}',
                  '{"naval-specific": {"status": []}}', '{"naval-specific": {"status": "unknown"}}',
                  '{"naval-specific": {"status": "accepted", "last_checked_at": "bad date"}}',
                  '{"naval-specific": {"status": "accepted", "last_checked_at": 7}}',
                  '{"naval-specific": {"status": "accepted", "accepted_sha256": "bad hash"}}']
        for text in values:
            with self.subTest(state=text):
                path.write_text(text)
                with self.assertRaises(StateError):
                    self.library.ask("怎么赚第一个100w")
                with self.assertRaises(StateError):
                    self.library.get_evidence("naval-e-specific")
                self.assertEqual(path.read_text(), text)
        path.write_text("{}")
        self.assertEqual(self.library.ask("怎么赚第一个100w")["status"], "ready")

    def test_unchanged_source_remains_usable(self):
        text = self.library.evidence["naval-e-specific"]["excerpt"]
        self.library.sources["naval-specific"]["content_sha256"] = sha256(text)
        with patch("open_mentor.updates.fetch_text", return_value=text):
            result = self.updates.check("naval-specific")
        self.assertEqual(result["status"], "accepted")
        self.assertTrue(self.library.search("naval", "专长"))

    def test_drift_requires_explicit_acceptance_even_if_quote_survives(self):
        text = "New context. " + self.library.evidence["naval-e-specific"]["excerpt"]
        with patch("open_mentor.updates.fetch_text", return_value=text):
            result = self.updates.check("naval-specific")
        self.assertEqual(result["status"], "changed")
        self.assertEqual(self.library.search("naval", "专长"), [])
        accepted = self.updates.accept("naval-specific", result["latest_sha256"], "test reviewer")
        self.assertEqual(accepted["status"], "accepted")
        self.assertTrue(self.library.search("naval", "专长"))

    def test_acceptance_rejects_missing_excerpt(self):
        with patch("open_mentor.updates.fetch_text", return_value="The old excerpt was removed."):
            result = self.updates.check("naval-specific")
        self.assertIn("naval-e-specific", result["missing_excerpts"])
        with self.assertRaisesRegex(ValueError, "absent"):
            self.updates.accept("naval-specific", result["latest_sha256"], "test reviewer")

    def test_fetch_failure_preserves_last_accepted_version_but_blocks_guidance(self):
        text = self.library.evidence["naval-e-specific"]["excerpt"]
        self.library.sources["naval-specific"]["content_sha256"] = sha256(text)
        with patch("open_mentor.updates.fetch_text", return_value=text):
            self.updates.check("naval-specific")
        with patch("open_mentor.updates.fetch_text", side_effect=OSError("offline")):
            result = self.updates.check("naval-specific")
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["accepted_sha256"], sha256(text))
        self.assertEqual(self.library.search("naval", "专长"), [])

    def test_importing_caption_does_not_verify_original(self):
        # A future unreviewed revision; the curated source may already have reviewed clips.
        self.library.sources["sun-alan-video"]["review"]["status"] = "pending"
        for e in self.library.evidence.values():
            if e["source_id"] == "sun-alan-video":
                e["verification"].update(status="pending", origin_verified=False)
        path = self.root / "subtitles.vtt"
        path.write_text("WEBVTT\n00:00:01.000 --> 00:00:03.000\nTest caption fixture")
        result = self.updates.ingest("sun-alan-video", path)
        self.updates.accept("sun-alan-video", result["revision"], "test reviewer")
        self.assertEqual(self.library.source("sun-alan-video")["review"]["status"], "pending")
        self.assertFalse(self.library.get_evidence("sun-e-portable-video")["eligible"])

    def test_x_import_only_enters_review_inbox(self):
        path = self.root / "posts.json"
        post = {"url": "https://x.com/test_fixture/status/123", "author": "test_fixture", "published_at": "2026-10-24T00:00:00Z", "text": "Test fixture; not a real quotation"}
        path.write_text(json.dumps({"posts": [post]}))
        evidence_count = len(self.library.evidence)
        result = self.updates.import_x("naval", path)
        self.assertEqual(result["status"], "pending_review")
        draft = json.loads(Path(result["path"]).read_text())
        self.assertEqual(draft["posts"][0]["status"], "pending")
        self.assertFalse(draft["posts"][0]["origin_verified"])
        self.assertEqual(len(self.library.evidence), evidence_count)
        post["author"] = "different_author"
        path.write_text(json.dumps({"posts": [post]}))
        with self.assertRaisesRegex(ValueError, "author"):
            self.updates.import_x("naval", path)
