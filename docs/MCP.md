# MCP接入与自检

DeepMentor提供标准MCP服务。默认使用stdio，由客户端启动本地进程；也可在本机启动Streamable HTTP。所有工具只读，返回可引用的资料，由调用方AI结合用户情况深入分析并引导行动落地。无需模型API Key。

## 安装与检查

在项目虚拟环境中安装：

```bash
python -m pip install -e '.[mcp]'
python -m deepmentor doctor --mcp
```

当前使用官方Python SDK `mcp>=1.30,<2`。`doctor`先检查知识包、引用关系、来源状态、可引用证据和逾期来源数；`--mcp`再从另一个临时目录启动实际stdio进程，执行初始化、工具发现、人物列表和一次资料调用。它检查接入与当前可用性，不验证人物观点的事实正确性，也不会自动抓取或接纳来源。全部资料停用或状态损坏时不会报告指导已就绪。失败时输出JSON并返回非零退出码。

## 生成本机配置

```bash
# 使用mcpServers配置格式的客户端
python -m deepmentor mcp-config --format json
# Codex的TOML配置块
python -m deepmentor mcp-config --format codex
```

命令使用当前Python环境，输出绝对路径、知识目录、状态目录和模块查找路径。Python的虚拟环境路径不会被解析成系统Python，路径中空格、中文和引号按配置格式编码；从其他工作目录启动也能找到同一份资料与来源状态。配置只打印，不覆盖客户端已有设置。

若需自定义数据与复核目录，全局参数放在子命令前：

```bash
python -m deepmentor --data-dir /absolute/path/data --state-dir /absolute/path/state mcp-config --format codex
```

Codex使用`[mcp_servers.deepmentor]`配置块，可合并到用户级`~/.codex/config.toml`或受信任项目的`.codex/config.toml`。也可用`codex mcp add deepmentor --env PYTHONPATH=/absolute/path/deepmentor -- /absolute/path/deepmentor/.venv/bin/python -m deepmentor mcp`登记stdio命令；这里不强制指定新状态目录，服务会按规则复用旧目录。优先采用生成器输出的实际路径，已有自定义目录则保留原有`--state-dir`。登记后重启对应MCP连接以加载服务。配置格式和连接方式依据[OpenAI Docs](https://learn.chatgpt.com/docs/extend/mcp)。

可以用`codex mcp get deepmentor --json`核对登记。配置存在和协议自检通过，不等于当前正在运行的AI会话已刷新工具列表。

## 从旧版 OpenMentor 迁移 MCP 配置

若你此前已在 Codex、Claude Desktop、Cursor 等客户端中登记过 `openmentor`：
1. **避免双重登记**：不要同时保留 `openmentor` 和 `deepmentor` 两个服务条目，以免六个同名工具在客户端中重复或产生冲突。
2. **Codex TOML 迁移**：
   在 `~/.codex/config.toml` 中，将 `[mcp_servers.openmentor]` 重命名为 `[mcp_servers.deepmentor]`，并将命令行参数 `-m open_mentor` 更新为 `-m deepmentor`。
   保留原有的显式`--state-dir`，并核对`--data-dir`已指向新的`deepmentor/data`。不要直接把旧状态路径替换成不存在的新空目录。
   若使用 CLI 注册，先生成并核对新配置，再替换旧条目：
   ```bash
   python -m deepmentor mcp-config --format codex
   # 使用输出的实际路径登记 deepmentor 并核对连通性后，再移除旧条目
   codex mcp remove openmentor
   ```
3. **Claude / Cursor JSON 迁移**：
   将 `mcpServers` 下的 `"openmentor"` 键更名为 `"deepmentor"`，并将 args 中的 `"open_mentor"` 更新为 `"deepmentor"`；显式`--data-dir`更新为新知识包路径，`--state-dir`继续指向原有复核数据。
4. **工具稳定性**：六个工具的名称、参数、类型与返回结构保持 100% 稳定，下游 AI prompt 和工作流无需做参数重构。

## 六个工具

| 工具 | 用途与主要参数 |
| --- | --- |
| `ask_mentor` | 统一入口。`request`必填；可选`person`、`situation`、`limit`、`allow_secondary`。未指定导师时自动匹配并返回理由。 |
| `list_people` | 列出姓名、别名、资料范围、证据数与当前可引用数量。 |
| `search_knowledge` | 指定`person`和`query`检索；可选`limit`、`include_pending`、`allow_secondary`。待核线索不能用于指导。 |
| `get_evidence` | 用`evidence_id`读取短摘录、原始链接、定位、日期与核验状态。 |
| `get_source` | 用`source_id`读取来源、版权范围、更新状态与下次检查日期。 |
| `prepare_guidance` | 指定`person`和`question`取得依据包；支持`situation`、`limit`、`allow_secondary`。 |

`limit`必须是1—20的整数；布尔选项必须传JSON布尔值。`"true"`、`"false"`、数字代替布尔值以及未知参数都会被拒绝。字符串`"null"`保持字符串含义，只有JSON的`null`才表示空值。请求与背景的总长度最多10000字符。调用方明确允许二手资料时才设置`allow_secondary=true`，仍保留归属和原始表达未核对的标记。

六个工具均提供输出Schema、`structuredContent`及兼容的文本内容。字典结果直接返回对象；人物和搜索列表的结构化内容位于`result`数组，原有逐项文本块也保留。这符合[MCP工具结果规范](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)。

正常业务结果包括`ready`、`insufficient_evidence`、`needs_person_selection`和`needs_context`。参数错误、未知ID或状态损坏通过`isError=true`报告；修复后可以继续使用同一连接。不得把失败结果当空证据成功回答。

## 实际提问

```json
{
  "request": "用DeepMentor帮我看看，怎么赚自己的第一个100w",
  "limit": 3
}
```

```json
{
  "request": "那我应该先做哪一步",
  "person": "吴恩达",
  "situation": "原问题是AI项目怎么同时设置技术和业务里程碑；我负责一个小团队"
}
```

调用`ask_mentor`后，AI先说明所用导师和选择理由，再引用实际返回的证据ID与`citation_url`分析适用条件。分析按「用户处境 → 关键问题 → 证据与适用性 → 行动建议 → 验证和停止条件」展开，区分原始表达、编辑应用和当前推演；不编造用户经历，不承诺收入，不冒充名人本人。`ready`只是当前有相关资料。

## Streamable HTTP

```bash
python -m deepmentor mcp --transport streamable-http --port 8766
```

MCP地址为`http://127.0.0.1:8766/mcp`，只监听本机回环地址；使用SDK的来源与Host校验。支持Streamable HTTP的客户端连接该地址。Codex可使用如下配置，选择它时不必同时登记stdio实例：

```toml
[mcp_servers.deepmentor]
url = "http://127.0.0.1:8766/mcp"
```

该地址提供MCP协议；已有`deepmentor serve`仍提供`127.0.0.1:8765/v1/...` REST API。两种HTTP入口的协议和端点不同。这里只提供本机服务，不包含公网托管或账户认证部署。

## 内容范围

服务当前读取30个人物包。原始来源、待核机器稿、已核证据和编辑应用的范围见[人物目录](MENTORS.md)、[资料规范](SOURCES.md)与[转写记录](TRANSCRIPTS.md)。MCP接通不会提升证据级别；来源变更、不可用、待核、争议或撤回的资料继续受原有规则限制。
