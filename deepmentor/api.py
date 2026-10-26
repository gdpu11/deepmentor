from __future__ import annotations

import json
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

from .library import Library, StateError


def make_server(host: str, port: int, data_dir=None, state_dir=None) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
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
            if self.path not in {"/v1/context", "/v1/ask"}:
                return self.send_json(404, {"error": "not_found"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 65536:
                    return self.send_json(413, {"error": "Request body must contain 1-65536 bytes"})
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict):
                    raise ValueError("Expected a JSON object")
                with closing(Library(data_dir, state_dir)) as library:
                    if self.path == "/v1/ask":
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
