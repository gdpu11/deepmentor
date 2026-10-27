"""Slack slash-command gateway. Signed, workspace-scoped, ephemeral evidence replies."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from .library import Library


def verify_slack(secret, timestamp, signature, body, current_time=None):
    try:
        if not secret or abs((time.time() if current_time is None else current_time) - int(timestamp)) > 300:
            return False
        digest = hmac.new(secret.encode(), b"v0:" + timestamp.encode() + b":" + body, hashlib.sha256).hexdigest()
        return hmac.compare_digest("v0=" + digest, signature)
    except (TypeError, ValueError, AttributeError):
        return False


def consult(library, request):
    if not isinstance(request, str) or not request.strip():
        raise ValueError("请输入问题；可使用 board / stress-test / interview 前缀。")
    mode, _, question = request.partition(" ")
    if mode == "board":
        return library.consult_board(question, limit=1)
    if mode in {"stress-test", "roast"}:
        return library.stress_test(question, limit=2)
    if mode == "interview":
        return library.diagnose(question)
    return library.ask(request, limit=2)


def compact_reply(result):
    """Plain text with complete source URLs, suitable for chat and desktop surfaces."""
    lines = ["DeepMentor · " + result["status"], "公开资料与编辑建议；请结合你的处境验证。"]
    if result["artifact_type"] == "board_context":
        contexts = result["perspectives"]
    else:
        contexts = [result]
    for context in contexts:
        if context.get("person"):
            lines += ["\n采用资料：" + context["person"]["name"]]
        for p in context.get("principles", []):
            lines += [p["title"], p["summary"][:240]]
            if p["application"]["limits"]:
                lines += ["边界：" + p["application"]["limits"][0][:160]]
            if p["evidence"]:
                e = p["evidence"][0]
                lines += [e["id"] + " " + e["citation_url"]]
    for row in result.get("cross_examination", [])[:2]:
        lines += ["交叉质询（编辑提示）：" + row["prompt"]]
    for row in result.get("failure_modes", [])[:2]:
        lines += ["压力测试：" + row["pre_mortem"]]
    lines += [q["question"] for q in result.get("questions", [])]
    if result["status"] != "ready":
        lines += result.get("questions_to_resolve", [])[:3]
    return "\n".join(lines)


def make_bot_server(host="0.0.0.0", port=8767, data_dir=None, state_dir=None):
    secret, team = os.environ.get("SLACK_SIGNING_SECRET"), os.environ.get("SLACK_TEAM_ID")
    if not secret or not team:
        raise ValueError("Set SLACK_SIGNING_SECRET and SLACK_TEAM_ID before starting the Slack bot")

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def send_json(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self.send_json(200 if self.path == "/health" else 404, {"status": "ok" if self.path == "/health" else "not_found"})

        def do_POST(self):
            if self.path != "/slack/commands":
                return self.send_json(404, {"error": "not_found"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 65536:
                    return self.send_json(413, {"error": "invalid_body_size"})
                body = self.rfile.read(size)
                if not verify_slack(secret, self.headers.get("X-Slack-Request-Timestamp"),
                                    self.headers.get("X-Slack-Signature"), body):
                    return self.send_json(401, {"error": "invalid_signature"})
                params = parse_qs(body.decode("utf-8"))
                if params.get("team_id") != [team] or params.get("command") != ["/deepmentor"]:
                    return self.send_json(403, {"error": "workspace_or_command_not_allowed"})
                request = params.get("text", [""])[0]
                with closing(Library(data_dir, state_dir)) as library:
                    reply = compact_reply(consult(library, request))
                # Disable mrkdwn to avoid mentions or formatting from user/corpus text.
                self.send_json(200, {"response_type": "ephemeral", "text": reply, "mrkdwn": False})
            except (ValueError, OSError):
                self.send_json(200, {"response_type": "ephemeral", "text": "无法取得可引用资料。请检查问题、复核状态及本机配置。", "mrkdwn": False})

        def log_message(self, *args):
            pass

    return ThreadingHTTPServer((host, port), Handler)
