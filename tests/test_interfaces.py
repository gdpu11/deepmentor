import asyncio
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from open_mentor.api import make_server

EXPANSION_REQUESTS = [
    ("用保罗·格雷厄姆的知识库，怎样招募第一批用户", "paul-graham", "pg-e-manual-recruiting"),
    ("用巴菲特的知识库分析，看不懂的生意能买吗", "warren-buffett", "buffett-e-circle-of-competence"),
    ("用查理·芒格的知识库分析激励如何影响判断", "charlie-munger", "munger-e-incentive-bias"),
    ("用贝索斯的知识库分析可逆决策太慢怎么办", "jeff-bezos", "bezos-e-reversible-decisions"),
    ("用James Clear的知识库，怎样从两分钟习惯开始", "james-clear", "clear-e-two-minute-start"),
    ("用雷军的知识库分析产品质量和交付跟不上增长", "lei-jun", "lei-e-growth-foundations"),
    ("用张小龙的知识库分析订阅内容的用户控制", "allen-zhang", "zhang-e-subscription-control"),
    ("用吴恩达的知识库，AI教程零散，怎样建立连贯基础", "andrew-ng", "ng-e-coherent-learning"),
    ("用奥特曼的知识库，通过实际协作样本补充面试判断", "sam-altman", "altman-e-bounded-work-sample"),
    ("用布琳·布朗的知识库，分配任务没给权限和资源怎么办", "brene-brown", "brown-e-task-authority-resources"),
    ("用德韦克的知识库，学习卡住不能只说更努力，怎么办", "carol-dweck", "dweck-e-effort-with-support"),
    ("用达克沃思的知识库，重要目标继续坚持，具体路径能换吗", "angela-duckworth", "duckworth-e-flexible-perseverance"),
    ("用费曼的知识库，不支持假设的实验结果也要报告吗", "richard-feynman", "feynman-e-report-all-outcomes"),
    ("用摩根·豪泽尔的知识库，别人的买卖目标和时间尺度不同怎么办", "morgan-housel", "housel-e-different-games"),
    ("用西弗斯的知识库，过度依赖一个大客户怎么办", "derek-sivers", "sivers-e-customer-concentration"),
    ("用李飞飞的知识库，AI数据覆盖不全，怎样考虑代表性", "fei-fei-li", "fei-e-representative-data"),
    ("用黄仁勋的知识库，经理靠垄断信息维持权力", "jensen-huang", "huang-e-information-not-status"),
    ("用亚当·格兰特的知识库，如何理解志愿者参与的动机", "adam-grant", "grant-e-participation-motives"),
    ("用纳德拉的知识库，不必要的组织层级阻碍决策", "satya-nadella", "nadella-e-reduce-unnecessary-layers"),
    ("用张一鸣的知识库，只考虑下一轮融资，长期能力怎么办", "zhang-yiming", "yiming-e-beyond-funding-window"),
    ("用乔布斯的知识库，产品线太乱，客户分不清型号", "steve-jobs", "jobs-e-coherent-product-line"),
    ("用盖茨的知识库，评价老师除了分数还有哪些来源的反馈", "bill-gates", "gates-e-multiple-feedback-sources"),
    ("用任正非的知识库，关键部件只有一个供应商，怎样准备备份", "ren-zhengfei", "ren-e-supplier-backups"),
]


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = make_server("127.0.0.1", 0, state_dir=Path(self.temp.name))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def test_http_search_and_context_have_real_citations(self):
        with urlopen(self.base + "/v1/search?person=naval&q=software", timeout=5) as response:
            self.assertTrue(json.load(response))
        request = Request(self.base + "/v1/context", json.dumps({"person": "naval", "question": "software leverage"}).encode(), {"Content-Type": "application/json"})
        with urlopen(request, timeout=5) as response:
            result = json.load(response)
        self.assertEqual(result["status"], "ready")
        self.assertIn("naval-e-leverage", result["citations"])

    def test_http_rejects_bad_body_and_limits(self):
        for body in ([], {"person": "naval", "question": "software", "limit": True}):
            request = Request(self.base + "/v1/context", json.dumps(body).encode(), {"Content-Type": "application/json"})
            with self.assertRaises(HTTPError) as error:
                urlopen(request, timeout=5)
            self.assertEqual(error.exception.code, 400)

    def test_http_natural_mentor_request(self):
        body = {"request": "帮我用OpenMentor问问孙宇晨，怎么赚自己的第一个100w"}
        request = Request(self.base + "/v1/ask", json.dumps(body).encode(), {"Content-Type": "application/json"})
        with urlopen(request, timeout=5) as response:
            result = json.load(response)
        self.assertEqual(result["person"]["id"], "justin-sun")
        self.assertEqual(result["answer_scope"], "related_principles")
        self.assertIn("sun-e-customer-value-video", result["citations"])
        self.assertIn("sun-e-small-experiments", result["citations"])
        self.assertEqual(result["citations"]["sun-e-customer-value-video"]["citation_url"], "https://www.youtube.com/watch?v=0Z-vhBvBmUY&t=2132")
        for body in ({"request": []}, {"request": "怎么赚钱", "limit": True}):
            request = Request(self.base + "/v1/ask", json.dumps(body).encode(), {"Content-Type": "application/json"})
            with self.assertRaises(HTTPError) as error:
                urlopen(request, timeout=5)
            self.assertEqual(error.exception.code, 400)

    def test_http_exposes_all_new_packs_with_their_own_evidence(self):
        with urlopen(self.base + "/v1/people", timeout=5) as response:
            people = json.load(response)
        self.assertTrue({person for _, person, _ in EXPANSION_REQUESTS} <= {p['id'] for p in people})
        for text, person, eid in EXPANSION_REQUESTS:
            with self.subTest(person=person):
                request = Request(self.base + "/v1/ask", json.dumps({"request": text}).encode(), {"Content-Type": "application/json"})
                with urlopen(request, timeout=5) as response:
                    result = json.load(response)
                self.assertEqual(result["person"]["id"], person)
                self.assertIn(eid, result["citations"])
                self.assertTrue(all(e["person_id"] == person and e["eligible"] for e in result["citations"].values()))

    def test_http_automatic_selection_matches_local_library(self):
        from contextlib import closing
        from open_mentor.library import Library
        for text in ["用OpenMentor帮我看看，怎么赚自己的第一个100w", "我做的流程很乱，要不要直接自动化", "如何养成阅读习惯", "用OpenMentor帮我看看", "阅读时突然胸痛，应该吃什么药"]:
            with self.subTest(request=text):
                request = Request(self.base + "/v1/ask", json.dumps({"request": text}).encode(), {"Content-Type": "application/json"})
                with urlopen(request, timeout=5) as response:
                    actual = json.load(response)
                with closing(Library(state_dir=Path(self.temp.name))) as library:
                    expected = library.ask(text)
                self.assertEqual(actual, expected)

    def test_http_situation_and_followup_match_library_on_both_endpoints(self):
        from contextlib import closing
        from open_mentor.library import Library
        situation = "原问题是怎么赚第一个100w，我会Python，每周有10小时"
        for endpoint, body in [("ask", {"request": "那我应该先做哪一步", "situation": situation}),
                               ("context", {"person": "naval", "question": "那我应该先做哪一步", "situation": situation})]:
            request = Request(self.base + "/v1/" + endpoint, json.dumps(body).encode(), {"Content-Type": "application/json"})
            with urlopen(request, timeout=5) as response:
                actual = json.load(response)
            with closing(Library(state_dir=Path(self.temp.name))) as library:
                expected = library.ask(**body) if endpoint == "ask" else library.guidance_context(**body)
            self.assertEqual(actual, expected)
            self.assertEqual(actual["status"], "ready")
        body = {"request": "那我应该先做哪一步", "situation": []}
        request = Request(self.base + "/v1/ask", json.dumps(body).encode(), {"Content-Type": "application/json"})
        with self.assertRaises(HTTPError) as error:
            urlopen(request, timeout=5)
        self.assertEqual(error.exception.code, 400)

    def test_http_invalid_review_state_returns_503_and_recovers_after_repair(self):
        path = Path(self.temp.name) / "state.json"
        request = Request(self.base + "/v1/ask", json.dumps({"request": "怎么赚第一个100w"}).encode(), {"Content-Type": "application/json"})
        for raw in ["{invalid", "[]", "null", '{"naval-specific": {"status": "accepted", "last_checked_at": false}}']:
            path.write_text(raw)
            for target in [request, self.base + "/v1/people"]:
                with self.subTest(state=raw, method="POST" if target is request else "GET"):
                    with self.assertRaises(HTTPError) as error:
                        urlopen(target, timeout=5)
                    self.assertEqual(error.exception.code, 503)
                    self.assertEqual(json.load(error.exception)["error"], "review_state_unavailable")
                    self.assertEqual(path.read_text(), raw)
        path.write_text("{}")
        with urlopen(request, timeout=5) as response:
            self.assertEqual(json.load(response)["status"], "ready")


class MCPTests(unittest.TestCase):
    def test_official_sdk_stdio_client_calls_real_server(self):
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            self.skipTest("Install .[mcp] to run the protocol integration test")

        async def exercise(root):
            server = StdioServerParameters(command=sys.executable, args=["-m", "open_mentor", "--state-dir", root, "mcp"])
            async with stdio_client(server) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    self.assertEqual({t.name for t in tools.tools}, {"list_people", "search_knowledge", "get_evidence", "get_source", "prepare_guidance", "ask_mentor"})
                    self.assertIn("situation", next(t for t in tools.tools if t.name == "ask_mentor").inputSchema["properties"])
                    people = await session.call_tool("list_people", {})
                    self.assertTrue({person for _, person, _ in EXPANSION_REQUESTS} <=
                                    {json.loads(c.text)['id'] for c in people.content})
                    for text, person, eid in EXPANSION_REQUESTS:
                        result = await session.call_tool("ask_mentor", {"request": text})
                        self.assertFalse(result.isError)
                        payload = json.loads(result.content[0].text)
                        self.assertEqual(payload["person"]["id"], person)
                        self.assertIn(eid, payload["citations"])
                        self.assertTrue(all(e["person_id"] == person and e["eligible"] for e in payload["citations"].values()))
                    result = await session.call_tool("prepare_guidance", {"person": "纳瓦尔", "question": "软件开源产品"})
                    self.assertFalse(result.isError)
                    payload = json.loads(result.content[0].text)
                    self.assertEqual(payload["status"], "ready")
                    self.assertIn("naval-e-leverage", payload["citations"])
                    result = await session.call_tool("ask_mentor", {"request": "帮我用OpenMentor问问孙宇晨，怎么赚自己的第一个100w"})
                    self.assertFalse(result.isError)
                    payload = json.loads(result.content[0].text)
                    self.assertEqual(payload["person"]["id"], "justin-sun")
                    self.assertIn("sun-e-customer-value-video", payload["citations"])
                    self.assertIn("sun-e-small-experiments", payload["citations"])
                    self.assertTrue(payload["citations"]["sun-e-customer-value-video"]["citation_url"].endswith("&t=2132"))
                    self.assertTrue(all(e["eligible"] and e["verification"]["origin_verified"] for e in payload["citations"].values()))
                    from contextlib import closing
                    from open_mentor.library import Library
                    for text in ["用OpenMentor帮我看看，怎么赚自己的第一个100w", "流程稳定前该不该自动化", "如何养成阅读习惯", "用OpenMentor帮我看看", "我的作品被人抄袭了，要怎么起诉维权"]:
                        result = await session.call_tool("ask_mentor", {"request": text})
                        self.assertFalse(result.isError)
                        actual = json.loads(result.content[0].text)
                        with closing(Library(state_dir=Path(root))) as library:
                            expected = library.ask(text)
                        self.assertEqual(actual, expected)

                    situation = "原问题是怎么赚第一个100w，我会Python，每周有10小时"
                    for tool, body in [("ask_mentor", {"request": "那我应该先做哪一步", "situation": situation}),
                                       ("prepare_guidance", {"person": "naval", "question": "那我应该先做哪一步", "situation": situation})]:
                        result = await session.call_tool(tool, body)
                        self.assertFalse(result.isError)
                        actual = json.loads(result.content[0].text)
                        with closing(Library(state_dir=Path(root))) as library:
                            expected = library.ask(**body) if tool == "ask_mentor" else library.guidance_context(**body)
                        self.assertEqual(actual, expected)
                        self.assertEqual(actual["status"], "ready")
                    result = await session.call_tool("ask_mentor", {"request": "那我应该先做哪一步"})
                    self.assertFalse(result.isError)
                    self.assertEqual(json.loads(result.content[0].text)["status"], "needs_context")
                    state = Path(root) / "state.json"
                    state.write_text("[]")
                    result = await session.call_tool("ask_mentor", {"request": "怎么赚第一个100w"})
                    self.assertTrue(result.isError)
                    self.assertIn("review state", result.content[0].text)
                    state.write_text("{}")
                    result = await session.call_tool("ask_mentor", {"request": "怎么赚第一个100w"})
                    self.assertFalse(result.isError)

        with tempfile.TemporaryDirectory() as root:
            asyncio.run(asyncio.wait_for(exercise(root), timeout=20))
