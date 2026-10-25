"""Client configuration and a local MCP protocol check; no client settings are edited."""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from contextlib import closing
from importlib.metadata import version
from pathlib import Path

from jsonschema.exceptions import ValidationError

from .library import DATA_DIR, Library, default_state_dir, load_state

TOOLS = {"ask_mentor", "list_people", "search_knowledge", "get_evidence", "get_source", "prepare_guidance"}


def require_mcp():
    try:
        from mcp.server.fastmcp import FastMCP  # noqa: F401
    except ImportError as exc:
        raise ValueError("MCP dependencies are unavailable. Install with: python -m pip install 'open-mentor-core[mcp]' "
                         "(source checkout: python -m pip install -e '.[mcp]')") from exc


def server_config(data_dir=None, state_dir=None) -> dict:
    # Do not resolve the Python symlink: that would leave its virtual environment.
    return {"command": str(Path(sys.executable).absolute()),
            "args": ["-m", "open_mentor", "--data-dir", str(Path(data_dir or DATA_DIR).expanduser().resolve()),
                     "--state-dir", str(Path(state_dir or default_state_dir()).expanduser().resolve()), "mcp"],
            "env": {"PYTHONPATH": str(Path(__file__).resolve().parent.parent)}}


def render_config(format="json", data_dir=None, state_dir=None) -> str:
    config = server_config(data_dir, state_dir)
    if format == "json":
        return json.dumps({"mcpServers": {"openmentor": config}}, ensure_ascii=False, indent=2)
    if format == "codex":
        quote = lambda value: json.dumps(value, ensure_ascii=False)
        return ("[mcp_servers.openmentor]\n" + f"command = {quote(config['command'])}\n"
                + f"args = {quote(config['args'])}\n\n[mcp_servers.openmentor.env]\n"
                + f"PYTHONPATH = {quote(config['env']['PYTHONPATH'])}\n")
    raise ValueError("format must be json or codex")


async def _probe(config, person, question):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    # Exercise exactly the exported configuration, from outside the checkout.
    with tempfile.TemporaryDirectory(prefix="openmentor-mcp-probe-") as cwd:
        params = StdioServerParameters(**config, cwd=cwd)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                initialization = await session.initialize()
                definitions = await session.list_tools()
                if {t.name for t in definitions.tools} != TOOLS:
                    raise ValueError("MCP tools do not match the OpenMentor interface")
                people = await session.call_tool("list_people", {})
                if people.isError or not people.structuredContent:
                    raise ValueError("MCP list_people failed or returned no structured content")
                people = people.structuredContent["result"]
                response = await session.call_tool("ask_mentor", {"request": question, "person": person, "limit": 1})
                if response.isError or not response.structuredContent:
                    raise ValueError("MCP ask_mentor failed or returned no structured content")
                payload = response.structuredContent
                if payload.get("status") not in {"ready", "insufficient_evidence"} or payload.get("person", {}).get("id") != person:
                    raise ValueError("MCP returned an unexpected guidance response")
                return {"status": "ok", "sdk_version": version("mcp"), "protocol_version": initialization.protocolVersion,
                        "tools": sorted(TOOLS), "people": len(people), "probe_status": payload["status"],
                        "structured_output": True, "working_directory_independent": True}


def doctor(data_dir=None, state_dir=None, *, mcp=False) -> dict:
    checks = {}
    try:
        with closing(Library(data_dir, state_dir)) as library:
            load_state(library.state_dir)
            checks["knowledge"] = {"status": "ok", "people": len(library.people), "sources": len(library.sources),
                                   "evidence": len(library.evidence), "principles": len(library.principles)}
            checks["review_state"] = {"status": "ok", "directory": str(library.state_dir.absolute())}
            profiles = library.list_people()
            eligible = sum(p["eligible_evidence_count"] for p in profiles)
            checks["evidence"] = {"status": "ok" if eligible else "error", "eligible": eligible,
                                  "overdue_sources": sum(library.source(s)["check_overdue"] for s in library.sources)}
            if not eligible:
                checks["evidence"]["detail"] = "No evidence is currently eligible for guidance; inspect review and source status."
            first = next(iter(library.principles.values()), None)
            person = first["person_id"] if first else next(iter(library.people))
            question = first["title"] if first else "当前收录的资料范围"
    except (ValueError, OSError, ValidationError) as exc:
        return {"status": "error", "checks": {**checks, "knowledge_or_state": {"status": "error", "detail": str(exc)}}}
    if mcp:
        try:
            require_mcp()
            checks["mcp"] = asyncio.run(asyncio.wait_for(_probe(server_config(data_dir, state_dir), person, question), timeout=20))
        except Exception as exc:
            checks["mcp"] = {"status": "error", "detail": str(exc)}
    return {"status": "ok" if all(c["status"] == "ok" for c in checks.values()) else "error", "checks": checks}
