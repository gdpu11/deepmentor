"""Normalize a small checked vocabulary only with nearby publisher-caption support.

Raw ASR stays immutable; the normalized working copy and every change stay pending
full audio review. This script does not approve knowledge or infer speakers.
Usage: python scripts/normalize_asr_terms.py transcript.json captions.ocr.jsonl
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from bisect import bisect_left, bisect_right
from pathlib import Path

from deepmentor.media import _cue_time

PAIRS = [("Cloud", "Claude"), ("搏击", "薄肌"), ("波长", "波场"), ("冰大", "宾大"),
         ("盲格", "芒格"), ("LIN", "Lean"), ("新鲜代谢", "新陈代谢")]


def normalize_terms(data, frames):
    result = copy.deepcopy(data)
    timed = []
    for frame in frames:
        match = re.search(r"frame-(\d+)\.jpg$", frame["file"])
        if match and not frame.get("error"):
            caption = " ".join(line["text"] for line in frame.get("lines", [])
                               if line["box"][2] >= .10 and line["box"][0] + line["box"][2] > .27)
            timed.append(((int(match[1]) - 1) * 2 + 1 + (data.get("source_offset_seconds") or 0), frame["file"], caption))
    timed.sort()
    times = [f[0] for f in timed]
    changes = []
    for index, row in enumerate(result["segments"]):
        for old, new in PAIRS:
            if old not in row["text"]:
                continue
            nearby = timed[bisect_left(times, row["start"] - 3):bisect_right(times, row["end"] + 3)]
            support = [f for f in nearby if new.casefold() in f[2].casefold()]
            if not support:
                continue
            frame = min(support, key=lambda f: abs(f[0] - (row["start"] + row["end"]) / 2))
            before = row["text"]
            row["text"] = before.replace(old, new)
            changes.append({"segment": index, "start": row["start"], "end": row["end"], "before": before,
                            "after": row["text"], "old": old, "new": new, "caption_frame": frame[1],
                            "caption_ocr": frame[2], "method": "nearby_publisher_caption_supported_term_normalization",
                            "verification": "pending_full_audio_review"})
    result["normalization"] = {"scope": "checked_terms_with_nearby_caption_support", "changes": len(changes),
                               "verification": "pending_full_audio_review"}
    # Never promote the working copy as a fully verified transcript.
    result["verification"] = "pending"
    return result, changes


def main(transcript: Path, ocr: Path):
    raw = transcript.read_bytes()
    data = json.loads(raw)
    frames = [json.loads(line) for line in ocr.read_text().splitlines()]
    result, changes = normalize_terms(data, frames)
    result["original_transcript_sha256"] = hashlib.sha256(raw).hexdigest()
    root = transcript.parent
    (root / "transcript.normalized.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (root / "term-corrections.json").write_text(json.dumps({"source_id": data["source_id"],
        "raw_transcript_sha256": result["original_transcript_sha256"], "ocr_sha256": hashlib.sha256(ocr.read_bytes()).hexdigest(),
        "changes": changes, "verification": "pending_full_audio_review"}, ensure_ascii=False, indent=2) + "\n")
    (root / "transcript.normalized.txt").write_text("\n".join(
        f"[{_cue_time(s['start'])}–{_cue_time(s['end'])}] {s['text']}" for s in result["segments"]) + "\n")
    (root / "transcript.normalized.vtt").write_text("WEBVTT\n\n" + "\n\n".join(
        f"{_cue_time(s['start'])} --> {_cue_time(s['end'])}\n{s['text']}" for s in result["segments"]) + "\n")
    print(json.dumps({"source_id": data["source_id"], "term_changes": len(changes), "verification": "pending_full_audio_review"}))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
