import json
import tempfile
import unittest
import shutil
import wave
from pathlib import Path
from unittest.mock import patch

from deepmentor.library import Library
from deepmentor.media import Media, parse_captions
from deepmentor.updates import fetch_text


class MediaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.library = Library(state_dir=self.root)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.library.close)

    def test_vtt_keeps_timestamps_and_does_not_invent_speakers(self):
        path = self.root / "fixture.vtt"
        path.write_text("WEBVTT\n\n00:01.250 --> 00:03.500\n<c>测试字幕</c>\n\n00:03.500 --> 00:04.000\n测试字幕\n\n00:04.000 --> 00:05.500\n下一句\n")
        segments = parse_captions(path)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]["start"], 1.25)
        self.assertEqual(segments[1]["end"], 5.5)
        self.assertTrue(all(s["speaker"] is None and s["verification"] == "pending" for s in segments))

    def test_platform_json_formats_and_invalid_time_range(self):
        path = self.root / "fixture.json"
        path.write_text(json.dumps({"body": [{"from": 1, "to": 2, "content": "测试"}]}))
        self.assertEqual(parse_captions(path)[0]["text"], "测试")
        path.write_text(json.dumps({"events": [{"tStartMs": 1000, "dDurationMs": 500, "segs": [{"utf8": "hello"}]}]}))
        self.assertEqual(parse_captions(path)[0]["end"], 1.5)
        path.write_text(json.dumps({"body": [{"from": 2, "to": 1, "content": "测试"}]}))
        with self.assertRaisesRegex(ValueError, "time range"):
            parse_captions(path)

    def test_downloaded_automatic_caption_stays_pending(self):
        self.library.sources["sun-alan-video"]["review"]["status"] = "pending"
        root = self.root / "media" / "sun-alan-video"
        root.mkdir(parents=True)
        caption = root / "fixture.zh.vtt"
        caption.write_text("WEBVTT\n\n00:01.000 --> 00:02.000\n测试字幕\n")
        info = {"id": "fixture", "title": "Test fixture", "requested_subtitles": {"zh": {"filepath": str(caption)}}, "subtitles": {}}
        with patch("deepmentor.media._yt_dlp") as cls:
            cls.return_value.return_value.__enter__.return_value.extract_info.return_value = info
            result = Media(self.library).fetch_subtitles("sun-alan-video")
        self.assertEqual(result["status"], "downloaded_pending_review")
        self.assertEqual(result["transcripts"][0]["kind"], "platform_automatic_caption")
        document = json.loads(Path(result["transcripts"][0]["path"]).read_text())
        self.assertEqual(document["verification"], "pending")
        self.assertEqual(self.library.source("sun-alan-video")["review"]["status"], "pending")

    def test_empty_subtitles_is_reported_as_empty(self):
        with patch("deepmentor.media._yt_dlp") as cls:
            cls.return_value.return_value.__enter__.return_value.extract_info.return_value = {"id": "fixture"}
            result = Media(self.library).fetch_subtitles("sun-alan-video")
        self.assertEqual(result["status"], "no_subtitles")

    def test_only_registered_source_urls_can_be_downloaded(self):
        with self.assertRaisesRegex(ValueError, "Register"):
            Media(self.library).fetch_subtitles("sun-alan-video", "https://example.org/unrelated")

    def test_unsupported_or_empty_captions_are_not_reported_as_success(self):
        path = self.root / "unsupported.ttml"
        path.write_text("<tt>fixture</tt>")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            parse_captions(path)
        root = self.root / "media" / "sun-alan-video"
        root.mkdir(parents=True)
        empty = root / "empty.vtt"
        empty.write_text("WEBVTT\n")
        with patch("deepmentor.media._yt_dlp") as cls:
            cls.return_value.return_value.__enter__.return_value.extract_info.return_value = {"id": "fixture", "requested_subtitles": {"en": {"filepath": str(empty)}}}
            with self.assertRaisesRegex(ValueError, "no timed text"):
                Media(self.library).fetch_subtitles("sun-alan-video")

    def test_x_embed_response_requires_matching_post_and_author(self):
        response = {"id_str": "123", "user": {"screen_name": "naval"}, "text": "test fixture"}
        with patch("deepmentor.updates.urlopen") as opening:
            opening.return_value.__enter__.return_value.read.side_effect = [json.dumps(response).encode(), json.dumps({**response, "user": {"screen_name": "different"}}).encode()]
            self.assertEqual(fetch_text("https://x.com/naval/status/123"), "test fixture")
            with self.assertRaisesRegex(ValueError, "expected author"):
                fetch_text("https://x.com/naval/status/123")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is optional")
    def test_transcription_resume_offsets_and_pending_review(self):
        self.library.sources["sun-alan-video"]["review"]["status"] = "pending"
        try:
            import numpy  # optional ASR dependency
        except ImportError:
            self.skipTest("ASR dependencies are optional")
        audio = self.root / "fixture.wav"
        with wave.open(str(audio), "wb") as output:
            output.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            output.writeframes(b"\0\0" * (16000 * 61))
        def fake_recognize(data, language):
            return [{"start": 0, "end": len(data) / 16000, "text": "fixture"}]
        with patch("deepmentor.media._recognizer", return_value=fake_recognize) as model:
            result = Media(self.library).transcribe("sun-alan-video", audio, chunk_seconds=30, source_offset=42)
            document = json.loads(Path(result["path"]).read_text())
            self.assertEqual(len(document["chunks"]), 3)
            self.assertTrue(document["input_coverage_complete"])
            self.assertFalse(document["source_complete_verified"])
            self.assertEqual(document["segments"][0]["start"], 42)
            self.assertEqual(document["segments"][-1]["end"], 103)
            self.assertTrue(all(s["verification"] == "pending" and s["speaker"] is None for s in document["segments"]))
            model.assert_called_once()
        with patch("deepmentor.media._recognizer", side_effect=AssertionError("must resume completed chunks")):
            resumed = Media(self.library).transcribe("sun-alan-video", audio, chunk_seconds=30, source_offset=42)
            self.assertEqual(result["path"], resumed["path"])
        self.assertEqual(self.library.source("sun-alan-video")["review"]["status"], "pending")
        with patch("deepmentor.media._audio_duration", return_value=90), patch("deepmentor.media._recognizer", return_value=fake_recognize):
            with self.assertRaisesRegex(ValueError, "duration differs"):
                Media(self.library).transcribe("sun-alan-video", audio, chunk_seconds=60)
