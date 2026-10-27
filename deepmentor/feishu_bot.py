"""Opt-in Feishu WebSocket bot, limited to configured chats and explicit mentions."""
from __future__ import annotations

import asyncio
import json
import os
import threading
import time
import uuid
from contextlib import closing

from .bot import compact_reply, consult
from .library import Library


def message_handler(client, allowed_chats, bot_open_id, data_dir=None, state_dir=None):
    from lark_oapi.api.im.v1 import ReplyMessageRequest, ReplyMessageRequestBody

    seen, lock = {}, threading.Lock()

    def handle(data):
        event = data.event
        message = event.message
        if event.sender.sender_type != "user" or message.message_type != "text" or message.chat_id not in allowed_chats:
            return
        mentions = message.mentions or []
        own = [m for m in mentions if m.id and m.id.open_id == bot_open_id]
        if message.chat_type != "p2p" and not own:
            return
        try:
            request = json.loads(message.content).get("text", "")
            if not isinstance(request, str):
                return
            for mention in own:
                request = request.replace(mention.key, "")
            request = request.strip()
            if not request:
                return
            if abs(time.time() - int(message.create_time) / 1000) > 600:
                return
        except (TypeError, ValueError, AttributeError):
            return
        with lock:
            current = time.monotonic()
            for key in list(seen):
                if seen[key] < current - 600:
                    del seen[key]
            if message.message_id in seen:
                return
            seen[message.message_id] = current
        try:
            with closing(Library(data_dir, state_dir)) as library:
                reply = compact_reply(consult(library, request))
        except (ValueError, OSError):
            reply = "无法取得可引用资料。请检查问题、复核状态及本机配置。"
        # Stable UUID also deduplicates a retried send across process restarts/replicas.
        body = (ReplyMessageRequestBody.builder().msg_type("text")
                .content(json.dumps({"text": reply}, ensure_ascii=False))
                .uuid(str(uuid.uuid5(uuid.NAMESPACE_URL, "deepmentor:" + message.message_id))).build())
        try:
            response = client.im.v1.message.reply(ReplyMessageRequest.builder()
                        .message_id(message.message_id).request_body(body).build())
            if not response.success():
                raise ValueError("Feishu reply failed; check app permissions and chat access")
        except Exception:
            with lock:
                seen.pop(message.message_id, None)
            raise

    return handle


def run_feishu(data_dir=None, state_dir=None):
    # The official SDK obtains the current event loop during import.
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    try:
        import lark_oapi as lark
    except ImportError as exc:
        raise ValueError("Install Feishu bot dependencies: pip install 'deepmentor-core[bots]' (checkout: pip install -e '.[bots]')") from exc
    app_id, secret = os.environ.get("FEISHU_APP_ID"), os.environ.get("FEISHU_APP_SECRET")
    bot_id = os.environ.get("FEISHU_BOT_OPEN_ID")
    chats = {c.strip() for c in os.environ.get("FEISHU_ALLOWED_CHAT_IDS", "").split(",") if c.strip()}
    if not app_id or not secret or not bot_id or not chats:
        raise ValueError("Set FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_BOT_OPEN_ID and FEISHU_ALLOWED_CHAT_IDS")
    client = lark.Client.builder().app_id(app_id).app_secret(secret).timeout(10).log_level(lark.LogLevel.ERROR).build()
    handler = (lark.EventDispatcherHandler.builder("", "")
               .register_p2_im_message_receive_v1(message_handler(client, chats, bot_id, data_dir, state_dir)).build())
    lark.ws.Client(app_id, secret, event_handler=handler, log_level=lark.LogLevel.ERROR).start()
