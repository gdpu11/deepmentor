"""Private, opt-in action ledger with transactional multi-process updates."""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import closing, contextmanager
from datetime import date, datetime, timezone
from pathlib import Path


def text(value, name, maximum=10000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} must contain 1-{maximum} characters")
    return value.strip()


def now():
    return datetime.now(timezone.utc).isoformat()


class Ledger:
    def __init__(self, library):
        self.library = library
        self.path = library.state_dir / "ledger.sqlite3"

    @contextmanager
    def _database(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with closing(sqlite3.connect(self.path, timeout=10)) as db:
                self.path.chmod(0o600)
                db.row_factory = sqlite3.Row
                db.execute("PRAGMA foreign_keys=ON")
                db.executescript("""
                    CREATE TABLE IF NOT EXISTS actions (id TEXT PRIMARY KEY, hypothesis TEXT NOT NULL,
                        probe TEXT NOT NULL, success_criteria TEXT NOT NULL, stop_criteria TEXT NOT NULL,
                        due_date TEXT NOT NULL, evidence_ids TEXT NOT NULL, status TEXT NOT NULL,
                        created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
                    CREATE TABLE IF NOT EXISTS checkins (id INTEGER PRIMARY KEY, action_id TEXT NOT NULL REFERENCES actions(id),
                        observation TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);
                """)
                with db:
                    yield db
        except sqlite3.Error as exc:
            raise ValueError(f"Cannot access action ledger {self.path}; repair or restore it before continuing: {exc}") from exc

    def add(self, hypothesis, probe, success_criteria, stop_criteria, due_date, evidence_ids=None):
        values = [text(v, k) for k, v in (("hypothesis", hypothesis), ("probe", probe),
                  ("success_criteria", success_criteria), ("stop_criteria", stop_criteria))]
        if not isinstance(due_date, str) or date.fromisoformat(due_date).isoformat() != due_date:
            raise ValueError("due_date must be YYYY-MM-DD")
        if evidence_ids is None:
            evidence_ids = []
        if not isinstance(evidence_ids, list) or len(evidence_ids) > 50 or any(not isinstance(e, str) for e in evidence_ids):
            raise ValueError("evidence_ids must be a list of at most 50 evidence IDs")
        evidence_ids = list(dict.fromkeys(evidence_ids))
        for eid in evidence_ids:
            if not self.library.get_evidence(eid)["eligible"]:
                raise ValueError(f"Evidence is not eligible: {eid}")
        identifier, timestamp = uuid.uuid4().hex, now()
        with self._database() as db:
            db.execute("INSERT INTO actions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       [identifier, *values, due_date, json.dumps(evidence_ids), "active", timestamp, timestamp])
        return self.get(identifier)

    def get(self, action_id):
        text(action_id, "action_id", 80)
        if not self.path.exists():
            raise ValueError(f"Unknown action: {action_id}")
        with self._database() as db:
            row = db.execute("SELECT * FROM actions WHERE id=?", (action_id,)).fetchone()
            if row is None:
                raise ValueError(f"Unknown action: {action_id}")
            result = dict(row)
            result["checkins"] = [dict(r) for r in db.execute("SELECT * FROM checkins WHERE action_id=? ORDER BY id", (action_id,))]
        result["evidence_ids"] = json.loads(result["evidence_ids"])
        # Historical plans remain visible; current source status is always rechecked.
        result["evidence_status"] = []
        for eid in result["evidence_ids"]:
            try:
                e = self.library.get_evidence(eid)
                result["evidence_status"].append({"id": eid, "eligible": e["eligible"],
                    "reason": e["eligibility_reason"], "citation_url": e["citation_url"]})
            except ValueError as exc:
                from .library import StateError
                if isinstance(exc, StateError):
                    raise
                result["evidence_status"].append({"id": eid, "eligible": False, "reason": "removed_from_corpus"})
        result["overdue"] = result["status"] == "active" and result["due_date"] < date.today().isoformat()
        return result

    def list(self, status=None):
        if status is not None and (not isinstance(status, str) or status not in {"active", "completed", "stopped"}):
            raise ValueError("status must be active, completed or stopped")
        if not self.path.exists():
            return []
        with self._database() as db:
            rows = db.execute("SELECT id FROM actions WHERE (? IS NULL OR status=?) ORDER BY due_date, created_at", (status, status)).fetchall()
        return [self.get(r["id"]) for r in rows]

    def check_in(self, action_id, observation, status="active"):
        text(action_id, "action_id", 80)
        observation = text(observation, "observation")
        if not isinstance(status, str) or status not in {"active", "completed", "stopped"}:
            raise ValueError("status must be active, completed or stopped")
        if not self.path.exists():
            raise ValueError(f"Unknown action: {action_id}")
        with self._database() as db:
            timestamp = now()
            cursor = db.execute("UPDATE actions SET status=?, updated_at=? WHERE id=?", (status, timestamp, action_id))
            if cursor.rowcount != 1:
                raise ValueError(f"Unknown action: {action_id}")
            db.execute("INSERT INTO checkins(action_id, observation, status, created_at) VALUES (?, ?, ?, ?)",
                       (action_id, observation, status, timestamp))
        return self.get(action_id)


def render_action(action):
    lines = ["# ACTION-PLAN", "", f"ID：{action['id']}", f"状态：{action['status']} · 复查日期：{action['due_date']}", ""]
    for key, title in (("hypothesis", "待验证假设"), ("probe", "72小时低成本实验"),
                       ("success_criteria", "成功指标"), ("stop_criteria", "停止条件")):
        lines += [f"## {title}", "", action[key], ""]
    lines += ["## 证据当前状态", ""]
    for e in action["evidence_status"]:
        lines += [f"- [{e['id']}]({e.get('citation_url', '')})：{e['reason']}"]
    lines += ["", "## 复查记录", ""]
    for c in action["checkins"]:
        lines += [f"- {c['created_at']} · {c['status']}：{c['observation']}"]
    return "\n".join(lines)
