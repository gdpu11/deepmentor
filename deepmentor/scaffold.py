"""Generate a schema-valid pending mentor draft without inventing verification."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .library import DATA_DIR
from .ledger import text


def scaffold(person_id, name, source_url, source_title, publisher, excerpt, locator, summary, output):
    if not isinstance(person_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,49}", person_id):
        raise ValueError("person_id must be 2-50 lowercase letters, digits or hyphens")
    for key, value in locals().copy().items():
        if key not in {"output", "person_id"}:
            text(value, key)
    sid, eid, pid = (person_id + suffix for suffix in ("-source-01", "-e-01", "-p-01"))
    pack = {"schema_version": 1, "person": {"id": person_id, "name": name, "aliases": [],
        "description": "社区草稿；待核验公开来源。"},
        "sources": [{"id": sid, "title": source_title, "url": source_url, "publisher": publisher,
            "kind": "essay", "authority": "secondary", "published_at": None, "language": "und",
            "rights": {"license": "待核对", "redistribution": "metadata_and_short_excerpts", "note": "仅保存用户提供的短摘录；须核对授权与来源。"},
            "review": {"status": "pending", "checked_at": date.today().isoformat(), "reviewer": "unreviewed-draft",
                       "method": "scaffold_only", "note": "仅创建草稿，未核实归属、文字或上下文。"},
            "content_sha256": None, "refresh": {"mode": "manual", "interval_days": 90}}],
        "evidence": [{"id": eid, "source_id": sid, "speaker": name, "excerpt": excerpt, "summary": summary,
            "locator": {"type": "heading", "value": locator}, "verification": {"status": "pending",
            "origin_verified": False, "checked_at": None, "reviewer": None, "note": "用户提供的待核草稿，不可用于建议。"},
            "tags": ["待核对"], "context": "待补充原始语境与归属核验。"}],
        "principles": [{"id": pid, "title": source_title, "summary": summary, "topics": ["待整理"],
            "evidence_ids": [eid], "application": {"questions": [], "steps": [], "limits": ["未完成核验，不可用于建议。"]}}]}
    schema = json.loads((DATA_DIR / "pack.schema.json").read_text())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(pack)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as file:
        json.dump(pack, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return {"status": "pending_draft", "path": str(path), "person_id": person_id,
            "next": "核对原文、说话人、上下文、来源类型与权利后再提交复核；格式通过不等于内容已核验。"}
