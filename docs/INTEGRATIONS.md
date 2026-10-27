# 桌面、Agent 与聊天机器人

各入口复用同一证据筛选逻辑。桌面脚本和 Bot 给出紧凑的资料与来源；在需要完整个性化分析时，使用支持工具调用的 AI，按咨询协议综合作答。咨询不自动写行动账本。

## Raycast Script Command

1. 本地安装 DeepMentor。设置环境变量 `DEEPMENTOR_PYTHON` 为安装它的 Python 绝对路径，例如检出目录下的 `.venv/bin/python`。
2. 将 [`integrations/desktop/deepmentor.sh`](../integrations/desktop/deepmentor.sh) 所在目录添加到 Raycast 的 Script Commands。若 GUI 不继承终端环境，在自己的脚本副本中设置该变量。
3. 输入问题，或使用 `board 问题`、`stress-test 问题`、`interview 问题`。结果在 Raycast fullOutput 中显示，附原始出处。

脚本将输入当作参数传递，不使用 `eval`。`interview` 显示定界问题；下一轮可通过 AI 或 CLI `interview --answers` 补齐回答。

## Alfred

创建 Script Filter，输入作为 **argv**，使用以下脚本（将占位路径改为你的路径）：

```bash
exec "$DEEPMENTOR_PYTHON" "/absolute/path/deepmentor/integrations/desktop/alfred.py" "$1"
```

设置 Workflow 环境变量 `DEEPMENTOR_PYTHON`，将结果连接到 Copy to Clipboard。回车复制带出处的完整结果，支持与 Raycast 相同的前缀。标准输出只含 Alfred JSON。

## OpenClaw 与其他可运行本地命令的 Agent

可把以下命令作为本地工具接入，或直接让 Agent 调用 CLI。问题通过独立 argv 传入，不拼进 shell 程序：

```bash
deepmentor ask '具体问题' --format json
deepmentor board '具体决策' --format json
deepmentor stress-test '计划与假设' --format json
deepmentor interview '具体目标' --answers answers.json --format json
```

让 Agent 遵循返回的 `instructions`，通过原始证据ID/链接作答，再按用户明确意图调用 `action-add` 和 `check-in`。支持 MCP 的宿主可使用 `deepmentor mcp-config --format json` 生成配置；实际安装路径与工具配置方式由宿主决定，不假设 OpenClaw 的任意版本内置 MCP 支持。

## Slack：Docker slash command

创建 Slack 应用并注册 `/deepmentor`，Request URL 指向你的 HTTPS 反向代理 `/slack/commands`。在宿主环境配置该应用的签名密钥和允许的 workspace ID：

```bash
export SLACK_SIGNING_SECRET='从应用配置读取，勿提交到仓库'
export SLACK_TEAM_ID='T...'
docker compose up --build -d
```

容器端口仅映射到宿主回环 `127.0.0.1:8767`，需由自己的 HTTPS 反向代理转发。`GET /health` 是健康检查；该端口不暴露普通 HTTP API 或账本。

示例：`/deepmentor board 创业如何验证客户需求`，也支持普通问题、`stress-test` 和 `interview`。响应为当前用户可见的 ephemeral 消息，不向群公开问题。实现依据 [Slack 签名校验规则](https://docs.slack.dev/authentication/verifying-requests-from-slack/)，验证 HMAC-SHA256、五分钟时间窗口、workspace 与命令名称。凭据只从环境读取，不记录请求正文。

同步网关使用 BM25 和少量原则。实际处理速度取决于机器和语料大小；若语料明显扩大，应改为异步应答。尚未配置的生成模型不会被隐式调用，Bot 返回带出处的资料与编辑问题。

无需 Docker 也可运行：

```bash
deepmentor bot --platform slack --port 8767
```

`bot` 监听 `0.0.0.0`，仅用于经过签名校验的 Slack 网关；普通 `serve` 仍只监听本机。

## 飞书：官方 SDK 长连接

启用自建应用机器人、`im.message.receive_v1` 事件及收发消息所需权限，在开发者后台选择长连接。参考[飞书官方长连接文档](https://open.feishu.cn/document/ukTMukTMukTM/uYDNxYjL2QTM24iN0EjN/event-subscription-configure-)和[官方 Python SDK](https://github.com/larksuite/oapi-sdk-python)。从应用配置获得凭据和机器人 open_id，并显式允许目标 chat_id：

```bash
pip install -e '.[bots]'
export FEISHU_APP_ID='cli_...'
export FEISHU_APP_SECRET='从应用配置读取，勿提交到仓库'
export FEISHU_BOT_OPEN_ID='ou_...'
export FEISHU_ALLOWED_CHAT_IDS='oc_...'
deepmentor bot --platform feishu
# 或使用不开放入站端口的 Docker 配置
docker compose -f compose.feishu.yaml up --build -d
```

仅处理允许会话中的用户文本；群聊还要求 @当前机器人。私聊的 chat_id 也需加入允许列表。示例：`@机器人 stress-test 还没客户就辞职开发产品`。回复在同一聊天中可见，问题和回答不要包含不应对群成员公开的内容。

SDK 负责长连接认证，不开公网回调端口。处理器过滤机器人消息和超过10分钟的事件，使用短期内存去重及确定性发送 UUID 降低重投重复回复；不是持久化的消息队列或跨集群 exactly-once 保证。该 Bot 只咨询，不保存聊天或自动写账本。工作区凭据、真实聊天发送与远端配置需要你在部署环境接入，本地测试使用模拟客户端。

Docker 镜像使用非 root 用户、独立 `/state` 卷及白名单构建上下文，避免把本机状态、账本、环境文件或转写资料打进镜像。
