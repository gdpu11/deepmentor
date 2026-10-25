"""Check coverage and compare sampled publisher captions; never approve evidence.

Usage: python scripts/audit_transcript.py path/to/transcript.json path/to/captions.ocr.jsonl
Outputs a review-audit.json next to the transcript. OCR is a second machine reading,
not a ground-truth transcript or a claim of human/audio verification.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import unicodedata
from bisect import bisect_left, bisect_right
from difflib import SequenceMatcher
from pathlib import Path


def comparable(text):
    return "".join(c for c in unicodedata.normalize("NFKC", text).lower() if c.isalnum())


def audit(transcript_path: Path, ocr_path: Path):
    data = json.loads(transcript_path.read_text())
    rows = data["segments"]
    duration, offset = data["input_duration_seconds"], data["source_offset_seconds"] or 0
    coverage_issues, timing_issues = [], []
    cursor = 0
    decoded = 0
    for expected in data["chunks"]:
        checkpoint = json.loads((transcript_path.parent / expected["path"]).read_text())
        if checkpoint["input_start"] != cursor:
            coverage_issues.append({"path": expected["path"], "reason": "noncontiguous_chunk"})
        cursor = checkpoint["input_end"]
        decoded += checkpoint["decoded_seconds"]
    if abs(cursor - duration) > .05 or abs(decoded - duration) > len(data["chunks"]) * .1:
        coverage_issues.append({"reason": "duration_mismatch", "last_chunk_end": cursor, "decoded_seconds": decoded})
    for i, row in enumerate(rows):
        a, b = row["start"], row["end"]
        if not (math.isfinite(a) and math.isfinite(b) and offset <= a <= b <= offset + duration + .1):
            timing_issues.append({"segment": i, "reason": "invalid_timestamp"})
        if i and a < rows[i - 1]["start"]:
            timing_issues.append({"segment": i, "reason": "timestamp_regression"})
    # Input is a resumable append-only OCR log. Use the latest result for each frame.
    frames = {}
    for line in ocr_path.read_text().splitlines():
        row = json.loads(line)
        frames[row["file"]] = row
    starts = [s["start"] for s in rows]
    comparisons = []
    for name, frame in sorted(frames.items()):
        if frame.get("error"):
            comparisons.append({"file": name, "error": frame["error"]})
            continue
        match = re.search(r"frame-(\d+)\.jpg$", name)
        if not match:
            raise ValueError("Expected fps=1/2 frame-NNNNNN.jpg files")
        # fps-filter output samples represent nominal two-second bins, not exact frame timestamps.
        t = (int(match[1]) - 1) * 2 + 1 + offset
        captions = [line["text"] for line in frame.get("lines", [])
                    if re.search(r"[\u3400-\u9fff]", line["text"]) and line["box"][2] >= .10
                    and line["box"][0] + line["box"][2] > .27]  # exclude left-corner programme/sponsor logos
        text = " ".join(captions)
        needle = comparable(text)
        if not needle:
            comparisons.append({"file": name, "nominal_seconds": t, "status": "no_chinese_caption"})
            continue
        lo, hi = max(0, bisect_left(starts, t - 7) - 1), bisect_right(starts, t + 7)
        nearby = comparable("".join(s["text"] for s in rows[lo:hi]))
        exact = needle in nearby
        score = sum(m.size for m in SequenceMatcher(None, needle, nearby, autojunk=False).get_matching_blocks()) / len(needle)
        comparisons.append({"file": name, "nominal_seconds": t, "publisher_caption_ocr": text,
                            "status": "exact_substring" if exact else "needs_text_review",
                            "matched_character_fraction": round(score, 3), "nearby_segments": [lo, hi]})
    flags = [{"segment": i, "start": row["start"], "end": row["end"], "flags": row["review_flags"]}
             for i, row in enumerate(rows) if row.get("review_flags")]
    result = {
        "source_id": data["source_id"], "status": "machine_checks_complete_pending_review",
        "transcript_sha256": hashlib.sha256(transcript_path.read_bytes()).hexdigest(),
        "ocr_sha256": hashlib.sha256(ocr_path.read_bytes()).hexdigest(),
        "input_sha256": data["input_sha256"], "model": data["model"], "engine": data["engine"],
        "input_duration_seconds": duration, "decoded_seconds": decoded, "chunks": len(data["chunks"]),
        "segments": len(rows), "characters": sum(len(r["text"]) for r in rows),
        "coverage_issues": coverage_issues, "timing_issues": timing_issues, "asr_flagged_segments": flags,
        "ocr_sampling": {"method": "fps=1/2 whole-frame sampling, Vision bottom 29%", "interval_seconds": 2,
                         "frames_expected": round(duration / 2), "frames_processed": len(frames),
                         "errors": sum("error" in row for row in frames.values()),
                         "exact_substrings": sum(c.get("status") == "exact_substring" for c in comparisons),
                         "needs_text_review": sum(c.get("status") == "needs_text_review" for c in comparisons),
                         "no_chinese_caption": sum(c.get("status") == "no_chinese_caption" for c in comparisons)},
        "comparisons": comparisons,
        "verification": "pending", "human_audio_review_complete": False,
        "limitations": ["OCR 采样不是全量字幕，原发布字幕也可能有误；未逐句听辨原音。",
                        "文字相似只用于排查漏段与异文，不证明说话人、事实或引用已核验。",
                        "跨分块边界、数字、人名和不同转写必须回看；知识条目另有片段级核验记录。"],
    }
    if len(frames) != round(duration / 2):
        result["coverage_issues"].append({"reason": "ocr_frame_count_mismatch"})
    output = transcript_path.parent / "review-audit.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"comparisons", "asr_flagged_segments"}}, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    audit(Path(sys.argv[1]), Path(sys.argv[2]))
