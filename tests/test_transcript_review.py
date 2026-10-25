import copy
import unittest

from scripts.normalize_asr_terms import normalize_terms


class TranscriptReviewTests(unittest.TestCase):
    def test_term_changes_need_local_caption_support_and_never_approve_raw_text(self):
        raw = {"verification": "pending", "source_offset_seconds": 0, "segments": [
            {"start": 100, "end": 102, "text": "都丢给Cloud", "speaker": None, "verification": "pending"},
            {"start": 200, "end": 202, "text": "Cloud", "speaker": None, "verification": "pending"},
        ]}
        original = copy.deepcopy(raw)
        frames = [
            {"file": "frame-000051.jpg", "lines": [{"text": "都丢给Claude", "box": [.3, .4, .4, .2]}]},
            # A corner logo is not evidence for changing the second utterance.
            {"file": "frame-000101.jpg", "lines": [{"text": "Claude", "box": [.05, .4, .15, .2]}]},
        ]
        normalized, changes = normalize_terms(raw, frames)
        self.assertEqual(normalized["segments"][0]["text"], "都丢给Claude")
        self.assertEqual(normalized["segments"][1]["text"], "Cloud")
        self.assertEqual(len(changes), 1)
        self.assertEqual(raw, original)
        self.assertEqual(normalized["verification"], "pending")
        self.assertTrue(all(r["speaker"] is None and r["verification"] == "pending" for r in normalized["segments"]))
