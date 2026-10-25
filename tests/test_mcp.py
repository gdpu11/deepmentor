import asyncio
import builtins
import importlib.util
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from open_mentor.cli import main
from open_mentor.integration import TOOLS, doctor, render_config, server_config
from open_mentor.library import DATA_DIR

HAS_MCP = importlib.util.find_spec("mcp") is not None


class ConfigurationTests(unittest.TestCase):
    def test_config_keeps_venv_python_and_makes_paths_absolute(self):
        with tempfile.TemporaryDirectory(prefix="openmentor 路径 ") as directory:
            state = Path(directory) / "state with spaces"
            data = Path(directory) / "data 资料"
            config = json.loads(render_config("json", data, state))["mcpServers"]["openmentor"]
            self.assertEqual(config["command"], os.path.abspath(sys.executable))
            self.assertEqual(config["args"], ["-m", "open_mentor", "--data-dir", str(data.resolve()), "--state-dir", str(state.resolve()), "mcp"])
            self.assertTrue(Path(config["env"]["PYTHONPATH"]).is_absolute())
            self.assertFalse(state.exists())

    @unittest.skipIf(sys.version_info < (3, 11), "tomllib is available on Python 3.11+")
    def test_codex_toml_has_the_same_process_configuration(self):
        import tomllib
        with tempfile.TemporaryDirectory(prefix='openmentor 路径 " ') as root:
            expected = server_config(DATA_DIR, Path(root))
            actual = tomllib.loads(render_config("codex", DATA_DIR, Path(root)))
            self.assertEqual(actual["mcp_servers"]["openmentor"], expected)

    def test_missing_mcp_has_actionable_cli_error_and_no_traceback(self):
        original = builtins.__import__

        def without_mcp(name, *args, **kwargs):
            if name.startswith("mcp"):
                raise ModuleNotFoundError("No module named 'mcp'")
            return original(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=without_mcp), redirect_stderr(io.StringIO()) as err:
            with self.assertRaises(SystemExit) as exit:
                main(["mcp"])
        self.assertEqual(exit.exception.code, 2)
        self.assertIn(".[mcp]", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())

    def test_doctor_fails_closed_and_returns_nonzero_without_overwriting_state(self):
        with tempfile.TemporaryDirectory() as root:
            state = Path(root) / "state.json"
            state.write_text("{broken")
            with redirect_stdout(io.StringIO()) as out, self.assertRaises(SystemExit) as exit:
                main(["--state-dir", root, "doctor"])
            self.assertEqual(exit.exception.code, 1)
            result = json.loads(out.getvalue())
            self.assertEqual(result["status"], "error")
            self.assertIn("review state", result["checks"]["knowledge_or_state"]["detail"])
            self.assertEqual(state.read_text(), "{broken")

    def test_doctor_does_not_claim_guidance_is_ready_when_all_sources_are_stopped(self):
        with tempfile.TemporaryDirectory() as root:
            state = {}
            for path in (DATA_DIR / "people").glob("*.json"):
                state.update({s["id"]: {"status": "changed"} for s in json.loads(path.read_text())["sources"]})
            (Path(root) / "state.json").write_text(json.dumps(state))
            result = doctor(state_dir=root)
            self.assertEqual(result["status"], "error")
            self.assertEqual(result["checks"]["evidence"]["eligible"], 0)
            self.assertIn("No evidence", result["checks"]["evidence"]["detail"])

    @unittest.skipUnless(HAS_MCP, "Install .[mcp] for protocol checks")
    def test_doctor_uses_exported_configuration_outside_checkout(self):
        with tempfile.TemporaryDirectory(prefix="openmentor 资料 ") as root:
            root = Path(root)
            data, state = root / "data with spaces", root / "状态"
            shutil.copytree(DATA_DIR, data)
            result = doctor(data, state, mcp=True)
            self.assertEqual(result["status"], "ok", result)
            self.assertEqual(result["checks"]["mcp"]["people"], 30)
            self.assertTrue(result["checks"]["mcp"]["working_directory_independent"])
            self.assertTrue(result["checks"]["mcp"]["structured_output"])
            self.assertFalse(state.exists())


@unittest.skipUnless(HAS_MCP, "Install .[mcp] for protocol checks")
class ProtocolTests(unittest.TestCase):
    def test_stdio_rejects_coercion_unknown_fields_and_preserves_literal_strings(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def exercise(root):
            async with stdio_client(StdioServerParameters(**server_config(state_dir=root))) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = (await session.list_tools()).tools
                    self.assertEqual({t.name for t in tools}, TOOLS)
                    for t in tools:
                        self.assertTrue(t.annotations.readOnlyHint)
                        self.assertFalse(t.annotations.openWorldHint)
                        self.assertTrue(t.outputSchema)
                        self.assertFalse(t.inputSchema["additionalProperties"])
                    invalid = [
                        ("ask_mentor", {"request": "怎么赚钱", "limit": n}) for n in [True, 1.0, "3", 0, 21]
                    ] + [
                        ("ask_mentor", {"request": "怎么赚钱", "allow_secondary": "true"}),
                        ("ask_mentor", {"request": "怎么赚钱", "allow_secondary": 1}),
                        ("ask_mentor", {"request": "怎么赚钱", "persson": "naval"}),
                        ("ask_mentor", {"request": "怎么赚钱", "person": "null"}),
                        ("ask_mentor", {"request": "a" * 10001}),
                        ("search_knowledge", {"person": "naval", "query": "software", "include_pending": "false"}),
                        ("search_knowledge", {"person": "naval", "query": "software", "allow_secondary": "true"}),
                        ("prepare_guidance", {"person": "naval", "question": "software", "situation": []}),
                        ("list_people", {"ignored": True}),
                    ]
                    for tool, args in invalid:
                        with self.subTest(tool=tool, arguments=args):
                            result = await session.call_tool(tool, args)
                            self.assertTrue(result.isError)
                    result = await session.call_tool("ask_mentor", {"request": "怎么赚第一个100w", "situation": "null"})
                    self.assertFalse(result.isError)
                    self.assertEqual(result.structuredContent["user_situation"], "null")
                    self.assertEqual(json.loads(result.content[0].text), result.structuredContent)
                    people = await session.call_tool("list_people", {})
                    self.assertEqual([json.loads(c.text) for c in people.content], people.structuredContent["result"])
                    search = await session.call_tool("search_knowledge", {"person": "孙宇晨", "query": "本地记录", "allow_secondary": True})
                    self.assertFalse(search.isError)
                    evidence = [e for p in search.structuredContent["result"] for e in p["evidence"]]
                    self.assertTrue(any(not e["verification"]["origin_verified"] for e in evidence))

        with tempfile.TemporaryDirectory() as root:
            asyncio.run(asyncio.wait_for(exercise(root), timeout=25))

    def test_streamable_http_runs_real_cli_with_evidence_and_state_gates(self):
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client
        import httpx

        async def exercise(root, port, process):
            for _ in range(100):
                if process.poll() is not None:
                    self.fail("MCP HTTP server exited before initialization")
                try:
                    reader, writer = await asyncio.open_connection("127.0.0.1", port)
                    writer.close()
                    await writer.wait_closed()
                    break
                except OSError:
                    await asyncio.sleep(.05)
            else:
                self.fail("MCP HTTP server startup timed out")
            url = f"http://127.0.0.1:{port}/mcp"
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers={"Origin": "https://untrusted.example"}, json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
                self.assertEqual(response.status_code, 403)
            async with streamable_http_client(url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.assertEqual({t.name for t in (await session.list_tools()).tools}, TOOLS)
                    result = await session.call_tool("ask_mentor", {"request": "用OpenMentor帮我看看，怎么赚第一个100w"})
                    self.assertFalse(result.isError)
                    payload = result.structuredContent
                    self.assertEqual(payload["person"]["id"], "justin-sun")
                    eid = "sun-e-customer-value-video"
                    self.assertIn(eid, payload["citations"])
                    evidence = await session.call_tool("get_evidence", {"evidence_id": eid})
                    self.assertEqual(evidence.structuredContent, payload["citations"][eid])
                    source = await session.call_tool("get_source", {"source_id": evidence.structuredContent["source_id"]})
                    self.assertEqual(source.structuredContent["id"], "sun-alan-video")
                    people = await session.call_tool("list_people", {})
                    self.assertEqual(len(people.structuredContent["result"]), 30)
                    result = await session.call_tool("prepare_guidance", {"person": "naval", "question": "software leverage"})
                    self.assertIn("naval-e-leverage", result.structuredContent["citations"])
                    result = await session.call_tool("search_knowledge", {"person": "naval", "query": "software"})
                    self.assertTrue(result.structuredContent["result"])
                    result = await session.call_tool("ask_mentor", {"request": "怎么赚钱", "allow_secondary": "true"})
                    self.assertTrue(result.isError)
                    state = Path(root) / "state.json"
                    state.write_text(json.dumps({s["source_id"]: {"status": "changed"} for s in payload["citations"].values()}))
                    result = await session.call_tool("ask_mentor", {"request": "怎么赚第一个100w", "person": "孙宇晨"})
                    self.assertNotIn(eid, result.structuredContent["citations"])
                    state.write_text("{broken")
                    result = await session.call_tool("ask_mentor", {"request": "怎么赚钱"})
                    self.assertTrue(result.isError)
                    state.write_text("{}")
                    result = await session.call_tool("ask_mentor", {"request": "怎么赚钱"})
                    self.assertFalse(result.isError)

        with tempfile.TemporaryDirectory() as root, socket.socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            port = reserved.getsockname()[1]
            reserved.close()
            config = server_config(state_dir=root)
            with tempfile.TemporaryFile(mode="w+") as errors:
                process = subprocess.Popen([config["command"], *config["args"], "--transport", "streamable-http", "--port", str(port)],
                                           env={**os.environ, **config["env"]}, cwd=root, stdout=subprocess.DEVNULL, stderr=errors)
                try:
                    asyncio.run(asyncio.wait_for(exercise(root, port, process), timeout=25))
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
