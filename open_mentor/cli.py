from __future__ import annotations

import argparse
import json
import sys
from contextlib import closing
from pathlib import Path

from jsonschema.exceptions import ValidationError

from .library import Library
from .updates import Updates


def main(argv=None):
    parser = argparse.ArgumentParser(description="OpenMentor: evidence-backed public knowledge")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--state-dir", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("people")
    sub.add_parser("validate")
    sub.add_parser("status")
    command = sub.add_parser("mcp-config", help="Print an absolute-path MCP client configuration")
    command.add_argument("--format", choices=["json", "codex"], default="json")
    command = sub.add_parser("doctor", help="Check knowledge, review state and optionally the real MCP connection")
    command.add_argument("--mcp", action="store_true")
    command = sub.add_parser("ask")
    command.add_argument("request")
    command.add_argument("--person")
    command.add_argument("--situation", help="本轮背景；追问时应包含原问题，不保存会话历史")
    command.add_argument("--limit", type=int, default=5)
    command.add_argument("--allow-secondary", action="store_true")
    command.add_argument("--format", choices=["markdown", "json"], default="markdown")
    for name in ("search", "context"):
        command = sub.add_parser(name)
        command.add_argument("query")
        command.add_argument("--person", required=True)
        command.add_argument("--limit", type=int, default=5)
        command.add_argument("--allow-secondary", action="store_true")
        if name == "search":
            command.add_argument("--include-pending", action="store_true")
        else:
            command.add_argument("--situation", help="本轮背景或追问对应的原问题")
    for name in ("evidence", "source", "check"):
        command = sub.add_parser(name)
        command.add_argument("id", nargs="?" if name == "check" else None)
    command = sub.add_parser("ingest")
    command.add_argument("source_id")
    command.add_argument("file", type=Path)
    command = sub.add_parser("accept-revision")
    command.add_argument("source_id")
    command.add_argument("revision")
    command.add_argument("--reviewer", required=True)
    command = sub.add_parser("import-x")
    command.add_argument("file", type=Path)
    command.add_argument("--person", required=True)
    command = sub.add_parser("serve")
    command.add_argument("--port", type=int, default=8765)
    for name in ("fetch-subtitles", "fetch-audio"):
        command = sub.add_parser(name)
        command.add_argument("source_id")
        command.add_argument("--url")
    command = sub.add_parser("transcribe")
    command.add_argument("source_id")
    command.add_argument("file", type=Path)
    command.add_argument("--model", default="small")
    command.add_argument("--language", default="zh")
    command.add_argument("--engine", choices=["faster-whisper", "mlx"], default="faster-whisper")
    command.add_argument("--chunk-seconds", type=int, default=600)
    command.add_argument("--source-offset", type=float)
    command = sub.add_parser("mcp")
    command.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    command.add_argument("--port", type=int, default=8766, help="Loopback port for Streamable HTTP (default: 8766)")
    args = parser.parse_args(argv)
    try:
        if args.command == "mcp":
            from .integration import require_mcp
            require_mcp()
            from .mcp_server import create_server
            if not 1 <= args.port <= 65535:
                raise ValueError("port must be between 1 and 65535")
            create_server(args.data_dir, args.state_dir, port=args.port).run(transport=args.transport)
            return
        if args.command == "mcp-config":
            from .integration import render_config
            print(render_config(args.format, args.data_dir, args.state_dir))
            return
        if args.command == "doctor":
            from .integration import doctor
            result = doctor(args.data_dir, args.state_dir, mcp=args.mcp)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if result["status"] != "ok":
                raise SystemExit(1)
            return
        if args.command == "serve":
            from .api import make_server
            server = make_server("127.0.0.1", args.port, args.data_dir, args.state_dir)
            print(f"OpenMentor HTTP API: http://127.0.0.1:{server.server_port}/v1/people", file=sys.stderr)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
            return
        with closing(Library(args.data_dir, args.state_dir)) as library:
            updates = Updates(library)
            if args.command == "people":
                result = library.list_people()
            elif args.command == "validate":
                result = {"status": "valid", "people": len(library.people), "sources": len(library.sources), "evidence": len(library.evidence), "principles": len(library.principles)}
            elif args.command == "search":
                result = library.search(args.person, args.query, args.limit, args.include_pending, args.allow_secondary)
            elif args.command == "context":
                result = library.guidance_context(args.person, args.query, args.limit, args.allow_secondary, args.situation)
            elif args.command == "ask":
                result = library.ask(args.request, args.person, args.limit, args.allow_secondary, args.situation)
            elif args.command == "evidence":
                result = library.get_evidence(args.id)
            elif args.command == "source":
                result = library.source(args.id)
            elif args.command == "status":
                result = [{"source_id": s["id"], "review": s["review"], "runtime": library.source(s["id"])["runtime"],
                           "check_overdue": library.source(s["id"])["check_overdue"]} for s in library.sources.values()]
            elif args.command == "check":
                result = [updates.check(source_id) for source_id in ([args.id] if args.id else library.sources)]
            elif args.command == "ingest":
                result = updates.ingest(args.source_id, args.file)
            elif args.command == "accept-revision":
                result = updates.accept(args.source_id, args.revision, args.reviewer)
            elif args.command == "import-x":
                result = updates.import_x(args.person, args.file)
            elif args.command in {"fetch-subtitles", "fetch-audio", "transcribe"}:
                from .media import Media
                media = Media(library)
                if args.command == "fetch-subtitles":
                    result = media.fetch_subtitles(args.source_id, args.url)
                elif args.command == "fetch-audio":
                    result = media.fetch_audio(args.source_id, args.url)
                else:
                    result = media.transcribe(args.source_id, args.file, args.model, args.language,
                                              args.engine, args.chunk_seconds, args.source_offset)
        if args.command == "ask" and args.format == "markdown":
            from .rendering import render_guidance
            print(render_guidance(result))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, ValidationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
