from __future__ import annotations

import json
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

from .library import Library, StateError


def make_server(host: str, port: int, data_dir=None, state_dir=None) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def parse_request(self):
            if not super().parse_request():
                return False
            allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            if self.headers.get("Host", "").lower() not in allowed:
                self.send_json(403, {"error": "invalid_host"})
                return False
            return True

        def send_json(self, status, payload):
            data = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = urlsplit(self.path)
            params = {k: v[-1] for k, v in parse_qs(url.query).items()}
            try:
                with closing(Library(data_dir, state_dir)) as library:
                    if url.path == "/v1/people":
                        result = library.list_people()
                    elif url.path == "/v1/actions":
                        from .ledger import Ledger
                        result = Ledger(library).list(params.get("status"))
                    elif url.path == "/v1/search":
                        result = library.search(params.get("person", ""), params.get("q", ""), int(params.get("limit", "5")))
                    elif url.path.startswith("/v1/evidence/"):
                        result = library.get_evidence(unquote(url.path.removeprefix("/v1/evidence/")))
                    elif url.path.startswith("/v1/sources/"):
                        result = library.source(unquote(url.path.removeprefix("/v1/sources/")))
                    else:
                        return self.send_json(404, {"error": "not_found"})
                self.send_json(200, result)
            except StateError as exc:
                self.send_json(503, {"error": "review_state_unavailable", "detail": str(exc)})
            except ValueError as exc:
                self.send_json(400, {"error": str(exc)})

        def do_POST(self):
            if self.path not in {"/v1/context", "/v1/ask", "/v1/board", "/v1/stress-test", "/v1/diagnose", "/v1/actions", "/v1/check-in"}:
                return self.send_json(404, {"error": "not_found"})
            if self.headers.get("Origin"):
                return self.send_json(403, {"error": "browser_origin_not_allowed"})
            if self.headers.get_content_type() != "application/json":
                return self.send_json(415, {"error": "Expected application/json"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 65536:
                    return self.send_json(413, {"error": "Request body must contain 1-65536 bytes"})
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict):
                    raise ValueError("Expected a JSON object")
                with closing(Library(data_dir, state_dir)) as library:
                    if self.path in {"/v1/board", "/v1/stress-test", "/v1/diagnose"}:
                        common = {"question", "situation", "allow_secondary"}
                        extra = {"people", "limit"} if self.path == "/v1/board" else (
                            {"person", "limit"} if self.path == "/v1/stress-test" else {"person", "answers"})
                        if set(body) - common - extra:
                            raise ValueError("Unknown consultation fields")
                        if "question" not in body:
                            raise ValueError("question is required")
                        method = {"/v1/board": library.consult_board, "/v1/stress-test": library.stress_test,
                                  "/v1/diagnose": library.diagnose}[self.path]
                        result = method(**body)
                    elif self.path == "/v1/actions":
                        from .ledger import Ledger
                        if set(body) - {"hypothesis", "probe", "success_criteria", "stop_criteria", "due_date", "evidence_ids"}:
                            raise ValueError("Unknown action fields")
                        if not {"hypothesis", "probe", "success_criteria", "stop_criteria", "due_date"} <= body.keys():
                            raise ValueError("Missing action fields")
                        result = Ledger(library).add(**body)
                    elif self.path == "/v1/check-in":
                        from .ledger import Ledger
                        if set(body) - {"action_id", "observation", "status"} or not {"action_id", "observation"} <= body.keys():
                            raise ValueError("Expected action_id, observation and optional status")
                        result = Ledger(library).check_in(**body)
                    elif self.path == "/v1/ask":
                        result = library.ask(body.get("request", ""), body.get("person"), body.get("limit", 5), body.get("allow_secondary", False), body.get("situation"))
                    else:
                        result = library.guidance_context(body.get("person", ""), body.get("question", ""), body.get("limit", 5), body.get("allow_secondary", False), body.get("situation"))
                self.send_json(200, result)
            except StateError as exc:
                self.send_json(503, {"error": "review_state_unavailable", "detail": str(exc)})
            except (ValueError, UnicodeError) as exc:
                self.send_json(400, {"error": str(exc)})

        def log_message(self, format, *args):
            # Questions and response bodies are intentionally absent from access logs.
            pass

    return ThreadingHTTPServer((host, port), Handler)
