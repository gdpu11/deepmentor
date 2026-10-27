import asyncio
import hashlib
import hmac
import importlib.util
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from deepmentor.api import make_server
from deepmentor.bot import make_bot_server, verify_slack


class NewHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = make_server('127.0.0.1', 0, state_dir=Path(self.temp.name))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def post(self, path, body, headers=None):
        req = Request(self.base + path, json.dumps(body).encode(), headers or {'Content-Type': 'application/json'})
        with urlopen(req, timeout=10) as response:
            return json.load(response)

    def test_consultations_and_explicit_ledger_writes(self):
        board = self.post('/v1/board', {'question': '如何验证创业需求与控制风险'})
        self.assertEqual(board['status'], 'ready')
        self.assertTrue(board['tradeoff_matrix'])
        stress = self.post('/v1/stress-test', {'question': 'software leverage', 'person': 'naval'})
        self.assertTrue(stress['failure_modes'])
        diagnosis = self.post('/v1/diagnose', {'question': '如何创业'})
        self.assertEqual(diagnosis['status'], 'needs_clarification')
        row = self.post('/v1/actions', {'hypothesis': '有人愿意使用', 'probe': '采访5人', 'success_criteria': '2人愿意试用',
            'stop_criteria': '无人试用', 'due_date': '2026-11-01'})
        result = self.post('/v1/check-in', {'action_id': row['id'], 'observation': '访谈完成', 'status': 'completed'})
        self.assertEqual(result['status'], 'completed')
        with urlopen(self.base + '/v1/actions?status=completed') as response:
            self.assertEqual(json.load(response)[0]['id'], row['id'])

    def test_invalid_fields_and_cross_site_writes_are_rejected(self):
        invalid = [('/v1/board', {'question': 'software', 'limit': True}),
                   ('/v1/board', {'question': 'software', 'people': 'naval'}),
                   ('/v1/diagnose', {'question': 'software', 'answers': {'goal': True}}),
                   ('/v1/diagnose', {'question': 'software', 'unsafe': True}),
                   ('/v1/actions', {}), ('/v1/check-in', {}),
                   ('/v1/check-in', {'action_id': 'unknown', 'observation': 'test', 'status': []}),
                   ('/v1/check-in', {'action_id': 'unknown', 'observation': 'test', 'status': {}})]
        for path, body in invalid:
            with self.assertRaises(HTTPError) as error:
                self.post(path, body)
            self.assertEqual(error.exception.code, 400)
        with self.assertRaises(HTTPError) as error:
            self.post('/v1/actions', {}, {'Origin': 'https://untrusted.example', 'Content-Type': 'application/json'})
        self.assertEqual(error.exception.code, 403)
        with self.assertRaises(HTTPError) as error:
            self.post('/v1/actions', {}, {'Content-Type': 'text/plain'})
        self.assertEqual(error.exception.code, 415)
        req = Request(self.base + '/v1/actions', headers={'Host': 'untrusted.example'})
        with self.assertRaises(HTTPError) as error:
            urlopen(req, timeout=5)
        self.assertEqual(error.exception.code, 403)


class SlackTests(unittest.TestCase):
    def test_signature_and_replay_window(self):
        body, timestamp, secret = b'text=software', '1234', 'test-secret'
        digest = 'v0=' + hmac.new(secret.encode(), b'v0:1234:' + body, hashlib.sha256).hexdigest()
        self.assertTrue(verify_slack(secret, timestamp, digest, body, 1234))
        self.assertFalse(verify_slack(secret, timestamp, digest, body, 1535))
        self.assertFalse(verify_slack(secret, timestamp, digest, body + b'x', 1234))
        self.assertFalse(verify_slack(secret, None, digest, body, 1234))

    def test_signed_workspace_scoped_ephemeral_reply(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, SLACK_SIGNING_SECRET='secret', SLACK_TEAM_ID='T-test'):
            server = make_bot_server('127.0.0.1', 0, state_dir=Path(root))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                def request(team, signature=True):
                    body = urlencode({'team_id': team, 'command': '/deepmentor', 'text': 'software leverage'}).encode()
                    timestamp = str(int(time.time()))
                    digest = 'v0=' + hmac.new(b'secret', b'v0:' + timestamp.encode() + b':' + body, hashlib.sha256).hexdigest()
                    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'X-Slack-Request-Timestamp': timestamp,
                               'X-Slack-Signature': digest if signature else 'invalid'}
                    return urlopen(Request(f'http://127.0.0.1:{server.server_port}/slack/commands', body, headers), timeout=5)
                with request('T-test') as response:
                    payload = json.load(response)
                self.assertEqual(payload['response_type'], 'ephemeral')
                self.assertFalse(payload['mrkdwn'])
                self.assertIn('https://', payload['text'])
                for team, signature, status in [('T-other', True, 403), ('T-test', False, 401)]:
                    with self.assertRaises(HTTPError) as error:
                        request(team, signature)
                    self.assertEqual(error.exception.code, status)
                self.assertFalse(list(Path(root).iterdir()))
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


@unittest.skipUnless(importlib.util.find_spec('lark_oapi'), 'Install .[bots] for Feishu SDK checks')
class FeishuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)

    @classmethod
    def tearDownClass(cls):
        cls.loop.close()
        asyncio.set_event_loop(None)

    def test_allowed_chat_mention_gate_dedup_and_stable_reply_uuid(self):
        from deepmentor.feishu_bot import message_handler
        from lark_oapi.api.im.v1 import P2ImMessageReceiveV1
        with tempfile.TemporaryDirectory() as root:
            client = MagicMock()
            client.im.v1.message.reply.return_value.success.return_value = True
            handler = message_handler(client, {'allowed'}, 'ou-bot', state_dir=Path(root))
            def event(chat='allowed', mention=True, sender='user'):
                return P2ImMessageReceiveV1({'event': {'sender': {'sender_type': sender}, 'message': {
                    'message_id': 'om-1', 'chat_id': chat, 'chat_type': 'group', 'message_type': 'text',
                    'create_time': str(int(time.time() * 1000)), 'content': json.dumps({'text': '@_user_1 software leverage'}),
                    'mentions': [{'key': '@_user_1', 'id': {'open_id': 'ou-bot'}}] if mention else []}}})
            handler(event(chat='other'))
            handler(event(mention=False))
            handler(event(sender='app'))
            self.assertFalse(client.im.v1.message.reply.called)
            handler(event())
            handler(event())
            self.assertEqual(client.im.v1.message.reply.call_count, 1)
            request = client.im.v1.message.reply.call_args.args[0]
            self.assertIn('https://', json.loads(request.request_body.content)['text'])
            second = message_handler(client, {'allowed'}, 'ou-bot', state_dir=Path(root))
            second(event())
            self.assertEqual(request.request_body.uuid, client.im.v1.message.reply.call_args.args[0].request_body.uuid)


@unittest.skipUnless(importlib.util.find_spec('mcp'), 'Install .[mcp] for protocol checks')
class NewMCPTests(unittest.TestCase):
    def test_new_protocols_and_ledger_annotations_over_stdio(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from deepmentor.integration import server_config
        async def exercise(root):
            async with stdio_client(StdioServerParameters(**server_config(state_dir=root))) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = {t.name: t for t in (await session.list_tools()).tools}
                    self.assertFalse(tools['add_action'].annotations.readOnlyHint)
                    self.assertFalse(tools['check_in'].annotations.idempotentHint)
                    result = await session.call_tool('consult_board', {'question': '创业如何验证用户需求'})
                    self.assertFalse(result.isError)
                    self.assertEqual(result.structuredContent['status'], 'ready')
                    result = await session.call_tool('stress_test', {'question': 'software leverage', 'person': 'naval'})
                    self.assertTrue(result.structuredContent['failure_modes'])
                    result = await session.call_tool('diagnose', {'question': '如何创业'})
                    self.assertEqual(result.structuredContent['status'], 'needs_clarification')
                    result = await session.call_tool('add_action', {'hypothesis': '有人需要工具', 'probe': '采访5人',
                        'success_criteria': '2人试用', 'stop_criteria': '无人试用', 'due_date': '2026-11-01'})
                    identifier = result.structuredContent['id']
                    result = await session.call_tool('check_in', {'action_id': identifier, 'observation': '访谈完成', 'status': 'stopped'})
                    self.assertEqual(result.structuredContent['status'], 'stopped')
                    result = await session.call_tool('list_actions', {'status': 'stopped'})
                    self.assertEqual(result.structuredContent['result'][0]['id'], identifier)
                    for tool, args in [('consult_board', {'question': '创业', 'limit': True}),
                        ('diagnose', {'question': '创业', 'answers': {'goal': True}}),
                        ('add_action', {'hypothesis': 'x', 'probe': 'y', 'success_criteria': 'z', 'stop_criteria': 's', 'due_date': 5})]:
                        result = await session.call_tool(tool, args)
                        self.assertTrue(result.isError)
        with tempfile.TemporaryDirectory() as root:
            asyncio.run(asyncio.wait_for(exercise(root), timeout=30))
