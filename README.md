# DeepMentor

[简体中文](README.md) | [English](README.en.md) | [参与共建 / Contributing](CONTRIBUTING.md)

**有据可查的人生导师，帮你把问题想深，把行动落地。**

DeepMentor 是一个基于公开证据、面向真实处境的人生导师知识库。它把人物公开发表过的经验、原话出处与核验记录接入你的 AI 助手，在面对创业经营、战略决策、学习迭代与人生选择时，帮你理清事实、推演边界、形成行动。当前收录 30 位导师，完整名单见[人物知识目录](docs/MENTORS.md)。

## 首屏核心说明

1. **真实处境出发**：用户带着具体的问题、目标、资源与现实约束前来咨询。
2. **灵活导师路由**：既可明确指定某位导师，也可在未指定时根据全库可引用的已核验证据自动匹配。
3. **严格证据支撑**：返回已复核材料、原始出处、具体定位和核验范围；AI 辅助检查、字幕对照与音频听辨按实际记录区分。
4. **行动验证闭环**：由调用方 AI 结合用户事实判断适用条件，形成下一步可执行行动与验证/停止指标。
5. **开放社区共建**：欢迎社区共同补充人生导师、一手来源、反例、观点演变与适用边界。

### 让“Deep”体现在分析质量

“Deep” 不依赖黑盒模型或虚构的通用语义理解，而体现在有据可查、层层推演的分析链条：

$$\text{用户处境} \longrightarrow \text{关键问题} \longrightarrow \text{证据与适用性} \longrightarrow \text{行动建议} \longrightarrow \text{验证和停止条件}$$

- **职责边界清晰**：DeepMentor 负责可信检索与证据把关（原文出处、定位、版本一致性与停用隔离），调用方 AI 负责深入推演与情境作答。
- **不夸大能力**：保持轻量的 SQLite FTS5/BM25 检索，无需生成模型或向量依赖。董事会返回带证据的多视角、交叉质询与权衡矩阵，由调用方 AI 推演，不冒充人物对话。

## 一起完善你的人生导师

DeepMentor 欢迎大家共同补充。你可以添加影响过自己的导师，完善已有人物的采访、文章和公开观点，也可以纠正错引、补充反例和适用条件。人物不需要按热度入选；先从一份能核对的一手材料、一条有边界的原则开始。

- **推荐导师或资料**：[提交导师线索](https://github.com/gdpu11/deepmentor/issues/new?template=add-mentor.md)，附公开来源和具体定位；不会写代码也能参与。
- **发现问题**：[提交证据纠错](https://github.com/gdpu11/deepmentor/issues/new?template=correct-evidence.md)，说明条目、原文与上下文。
- **贡献知识包或代码**：按[中英文贡献指南](CONTRIBUTING.md)提交 Pull Request。资料先核对，待核内容保持 `pending`；通过格式检查不等于观点获得证实。

## 当前能用什么

- **马斯克**：8 条原则，来自 Lex 原播客文字稿与本人 X 原帖，覆盖工程决策、实际用途和时间分配。
- **孙宇晨**：11 条原则。Alan 4:22:29 采访及 William 上下集均完成本地机器转写，并增加 7 条经原片字幕与上下文复核的证据；覆盖本地记录、选择、客户价值、方法学习和规则迭代。全文未逐句听辨，不当成已核验原话库。
- **纳瓦尔**：9 条原则，来自 `nav.al`、本人 X 和书籍官网，补充阅读习惯及创造/销售能力。
- **段永平**：8 条原则，来自浙江大学官方现场记录和澎湃原报道，补充商业模式与判断依据的重检。未填造 X 账号。
- **科比、周杰伦、景甜**：各 4 条原则，分别取自本人文章、原播客及原发布媒体的自采专访；影视人物观点不从他人谈论或歌词推断。
- **格雷厄姆**：22条，覆盖问题发现、首批用户、增长与现金、时间、合伙与授权，含2024年 Founder Mode。
- **巴菲特、芒格**：分别23、20条，覆盖能力边界、风险与配置、纠错、激励、多学科判断、学习及人生选择；本人署名与编者文字分开，保留2025年巴菲特致股东文字。
- **贝索斯**：23条，来自署名股东信及2023年原采访文字，覆盖客户、可逆决策、实验、标准、沟通、团队意见和专注。
- **James Clear**：20条，覆盖身份与习惯、环境、行动门槛、记录、中断恢复和真正交付。
- **雷军、张小龙**：各20条，取自机构原发、本人署名信或原发布讲话文字，覆盖创业准备、用户、效率、质量，以及产品、平台、表达与复杂度。雷军资料覆盖至2023年，张小龙至2021年，历史产品陈述不作为当前政策。
- **乔布斯、盖茨、奥特曼、西弗斯**：分别15、16、20、15条，覆盖设计与聚焦、问题与效果、选人与创业验证、行动与授权。
- **吴恩达、李飞飞、黄仁勋**：分别20、16、15条，覆盖职业与项目、数据和人本技术、技术市场、判断与团队条件。
- **纳德拉、张一鸣、任正非**：分别18、15、16条，覆盖学习与组织、基础与独立选择、需求、研究和供应依赖。历史公司自述保留时期，不当成当前事实。
- **费曼、摩根·豪泽尔、亚当·格兰特**：分别16、18、15条，覆盖求证与不确定性、金钱与风险边界、重新思考与协作。
- **德韦克、达克沃思、布琳·布朗**：分别16、15、18条，覆盖学习策略和支持条件、灵活坚持、信任与沟通；不从成长心态或毅力标签推断个人价值。
- **统一访问**：Python、CLI、HTTP JSON API、标准MCP stdio与本机Streamable HTTP。提供可生成的客户端配置和真实连通性自检，无需模型API Key就能检索；最终的情境分析由调用方AI完成。
- **来源更新**：检测已登记网页的文字变化，保存版本并暂停受影响引用；新来源需登记和复核。
- **视频工作流**：yt-dlp 采集、CPU 或 Apple Silicon GPU 转写、分块恢复、原片字幕 OCR 对照、术语异文记录。机器结果先保持 `pending`，知识证据另行逐片段核验。

当前有 **30 个人物包、130 个来源记录、465 条证据、460 条原则**。保留作者、原链接、短摘录、具体定位、核验范围与应用限制。可浏览[人物知识目录](docs/MENTORS.md)、[30位扩充审计](docs/EXPANSION-30-AUDIT.md)与[转写复核记录](docs/TRANSCRIPTS.md)。检索使用中英文词项匹配和 SQLite FTS5/BM25，没有向量检索、人物全量观点覆盖或自动联网回答。

## 深度咨询：从诊断到行动

P0、P1、P2 已有可运行入口，完整参数与边界见[咨询与行动指南](docs/CONSULTATION.md)。

| 功能 | 本地入口 | MCP 工具 |
| --- | --- | --- |
| 多导师董事会与权衡矩阵 | `board` / `ask --mode board` | `consult_board` |
| 三问诊断与决策备忘录依据 | `interview --interactive` | `diagnose` |
| 逆向压力测试 | `stress-test` / `roast` | `stress_test` |
| 私人行动账本与复查 | `action-add`、`actions`、`check-in`、`action-export` | `add_action`、`list_actions`、`check_in` |
| 待核导师包脚手架 | `scaffold mentor --interactive --output` | 本地贡献工具 |
| Raycast / Alfred / OpenClaw / 飞书 / Slack | [脚本及 Docker 接入](docs/INTEGRATIONS.md) | 支持 MCP 的宿主可直接连接 |

```bash
deepmentor board '要不要辞职做AI产品？如何验证需求并控制风险'
deepmentor interview '我想创业，先做什么' --interactive
deepmentor stress-test '还没访谈用户就准备全职做产品'
deepmentor check-in
```

董事会与压力测试保留证据ID、原链接和适用边界；CLI 展示资料和编辑问题，最终咨询由接入的 AI 结合你的事实推演。行动账本仅在明确调用保存时写入本机，不自动保存提问。

## 直接问 DeepMentor

在已接入 MCP 的 AI 中，可以说：

> 用 DeepMentor 帮我看看，怎么赚自己的第一个 100w？

也可以明确指定：

> 帮我用 DeepMentor 问问孙宇晨，怎么赚自己的第一个 100w？

AI 调用 `ask_mentor`。未指定导师时，从当前可引用的资料中自动匹配，并在回复开头说明采用了谁的公开资料及选择理由；明确指定导师时优先遵循你的选择。DeepMentor 返回依据、编辑整理的步骤和未知条件；最终情境回答由调用的 AI 按照「用户处境 → 关键问题 → 证据与适用性 → 行动建议 → 验证和停止条件」生成，不冒充孙宇晨本人。

本地也可以直接输入完整请求：

```bash
.venv/bin/deepmentor ask '用DeepMentor帮我看看，怎么赚自己的第一个100w'
# 指定人物，或取得给 AI 使用的 JSON 依据包
.venv/bin/deepmentor ask --person 孙宇晨 '怎么赚到第一桶金' --format json
.venv/bin/deepmentor ask '用DeepMentor问问芒格，怎样检查激励对判断的影响'
.venv/bin/deepmentor ask '用DeepMentor帮我看看，一个可以撤回的决定也要层层审批，怎么办'

# 旧命令 open-mentor 保持完全兼容：
.venv/bin/open-mentor ask '用OpenMentor帮我看看，怎么赚自己的第一个100w'
```

`ask` 默认显示带原始链接、时间戳和应用边界的资料；金额目标会先列出币种、收入/利润/净资产口径、期限和资源等待确认项。未指明人物时按证据匹配一位导师；明确请求多位导师或未收录的人物时会要求选择。“不要用孙宇晨，用纳瓦尔……”会尊重否定指定；明确请求未收录导师时，背景里提到已收录人物也不会导致静默换人。没有足够证据时不会随意指定导师。

提问解析同时识别新名称 `DeepMentor` 与旧名称 `OpenMentor`，前缀不影响意图识别、导师路由与检索排序。

## 带上背景和追问

通过 `situation` 提供本轮的目标、技能、时间和约束；该字段里的姓名不会被当成导师指定。主问题明确时按主问题检索，背景交给调用 AI 判断适用性；“那先做哪一步”等追问改用背景里的原问题检索。

```bash
.venv/bin/deepmentor ask '那我应该先做哪一步' \
  --situation '原问题是怎么赚第一个100w；我有后端开发经验，每周能投入10小时'
```

`ask`、`context`、对应 HTTP 接口及 MCP 工具都支持此字段。工具不保存聊天历史；AI 客户端应在追问时传入必要背景，需要沿用导师时同时传 `person`。没有原问题的常见追问返回 `needs_context`，不会靠“下一步”等词猜导师。请求和背景合计最多 10000 字符，背景与证据分开返回。

## 本地运行

Python 3.10+，SQLite 需支持 FTS5。新安装默认状态目录为 `.deepmentor`（源码检出位于仓库内，安装包位于 `~/.deepmentor/`）；若存在旧版 `.open-mentor` 数据，自动无缝复用，不丢失任何复核记录与停用状态。可用全局参数 `--state-dir` 指定独立目录。

```bash
git clone https://github.com/gdpu11/deepmentor.git
cd deepmentor
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[mcp]'
.venv/bin/deepmentor validate
.venv/bin/deepmentor people
.venv/bin/deepmentor search --person 纳瓦尔 '开源软件产品如何扩大规模'
.venv/bin/deepmentor context --person 纳瓦尔 '我有后端经验，想做一个开源工具，应该怎么选择产品方向？'
```

`context` 返回问题、匹配原则、待补充的信息和完整引用，类型为 `retrieved_guidance_context`。它是一份给 AI 使用的依据包；命令本身不伪装成已经生成了个性化回答。可以把 JSON 给当前 AI 分析，或通过 MCP 直接调用。

检索孙宇晨已复核的原片证据，或显式纳入二手资料：

```bash
.venv/bin/deepmentor search --person 孙宇晨 --include-pending 'AI 本地记录'
.venv/bin/deepmentor context --person 孙宇晨 --allow-secondary '换 AI 工具时，怎样保留历史记录？'
```

`--allow-secondary` 只允许已审阅的二手文字；待核、存在争议、撤回和版本变化未复核的证据仍然退出建议。

## 给 AI 接入 MCP

先安装可选依赖并检查接入：

```bash
.venv/bin/python -m pip install -e '.[mcp]'
.venv/bin/python -m deepmentor doctor --mcp
.venv/bin/python -m deepmentor mcp-config --format codex
# 使用mcpServers配置格式的客户端：
.venv/bin/python -m deepmentor mcp-config --format json
```

配置使用当前Python环境和绝对路径，从其他工作目录启动也能读取同一份资料与复核状态；命令只输出配置，不覆盖已有设置。默认启动命令为`python -m deepmentor mcp`。还可用`python -m deepmentor mcp --transport streamable-http --port 8766`启动本机`http://127.0.0.1:8766/mcp`。两种方式均已通过实际协议调用验证，接入步骤、旧配置迁移与返回格式见[MCP说明](docs/MCP.md)。

提供12个工具：`ask_mentor`、`list_people`、`search_knowledge`、`get_evidence`、`get_source`、`prepare_guidance`、`consult_board`、`stress_test`、`diagnose`、`list_actions`、`add_action`、`check_in`。

咨询及读取工具声明只读；`add_action` 与 `check_in` 明确声明写入且非幂等，仅在有保存意图时调用。各工具均返回结构化结果与兼容文本；原始参数严格校验，未知字段与字符串布尔值被拒绝。`search_knowledge`也支持明确允许二手资料的开关；待核或已停用证据继续隔离。

调用示例：

```json
{
  "tool": "ask_mentor",
  "arguments": {
    "request": "用DeepMentor帮我看看，怎么赚自己的第一个100w"
  }
}
```

推荐用户提示：

> 使用纳瓦尔知识库分析我的情况。先检索相关证据，说明哪些原则适用、哪些条件不成立，再按「用户处境 → 关键问题 → 证据与适用性 → 行动建议 → 验证和停止条件」给出可执行的下一步。区分原文、编辑归纳和你的推演，每个借用的观点附来源。

## HTTP API

```bash
.venv/bin/deepmentor serve --port 8765
curl 'http://127.0.0.1:8765/v1/search?person=naval&q=software'
curl -X POST http://127.0.0.1:8765/v1/ask \
  -H 'Content-Type: application/json' \
  -d '{"request":"帮我用DeepMentor问问孙宇晨，怎么赚自己的第一个100w"}'
```

支持 `POST /v1/ask` 解析完整请求、`POST /v1/context` 显式指定人物，两者均接受可选的 `situation` 字符串。另有 `GET /v1/people`、`GET /v1/evidence/<id>`、`GET /v1/sources/<id>`。另有董事会、压力测试、诊断与行动账本接口，见[完整指南](docs/CONSULTATION.md)。服务只监听本机回环地址；咨询不修改资料或执行抓取，行动接口仅按显式请求更新私人账本。

正常业务状态包括 `ready`（有相关可引用资料）、`insufficient_evidence`（资料不足）、`needs_person_selection`（需确认导师）、`needs_clarification`（诊断需补目标/资源/风险）和 `needs_context`（需补原问题）。本地 `state.json` 损坏时，涉及证据的 HTTP 请求返回 `503 review_state_unavailable`；CLI/MCP 同样报错并停止引用，不会将损坏状态重置成已接纳。

## 视频字幕与本地转写

```bash
.venv/bin/python -m pip install -e '.[media]'
.venv/bin/deepmentor fetch-subtitles sun-alan-video
# 没有字幕时，单独取得音频；不会偷偷切换到自动转写：
.venv/bin/deepmentor fetch-audio sun-alan-video
.venv/bin/python -m pip install -e '.[asr]'
.venv/bin/deepmentor transcribe sun-alan-video /path/to/audio.webm --model small --language zh
```

采集支持已登记来源的 URL 或 `origin_url`，保存到 `.deepmentor/media/`（或已有的 `.open-mentor/media/`），不读取浏览器 Cookie。yt-dlp 使用本机 Node 及其官方 JS 组件处理 YouTube；具体平台是否返回字幕需要实际检查，工具不能保证每个视频都有字幕。本地转写需要安装 FFmpeg，先统一解码为 16 kHz 单声道再交给模型。

VTT/SRT、YouTube json3 和 B 站字幕 JSON 会转换成带起止时间的段落。不会自动猜说话人，也不会将字幕提升为已核验知识。Whisper 首次运行会下载本地模型；转写只进入待核对区。转写按输入 SHA-256、模型、引擎、分块大小与原片偏移保存检查点，可续跑。使用截取音频时，用 `--source-offset` 指明原片秒数；未填写时会明确保留未知偏移，不声称覆盖完整原片。

Apple Silicon 可选 GPU 转写：

```bash
.venv/bin/python -m pip install -e '.[asr-mlx]'
.venv/bin/deepmentor transcribe sun-alan-video /path/to/audio.webm \
  --engine mlx --model mlx-community/whisper-large-v3-turbo \
  --chunk-seconds 600 --source-offset 0 --language zh
```

每个运行保存 `chunk-NNNN.json`、`progress.json`、最终 JSON/TXT/VTT。`input_coverage_complete` 只表示输入音频分块处理完成；机器稿不会自动修改知识包。原片画内字幕 OCR、异文修订与复核细节见[转写记录](docs/TRANSCRIPTS.md)，历史采集见[资料审计](docs/SEED-AUDIT.md)。

## 更新和贡献

```bash
.venv/bin/deepmentor check naval-specific
.venv/bin/deepmentor status
.venv/bin/deepmentor ingest sun-alan-video /path/to/authorized-subtitles.vtt
# 阅读保存的版本，核对摘录、说话人和上下文后，再显式接纳：
.venv/bin/deepmentor accept-revision naval-specific <sha256> --reviewer 'reviewer-name'
```

更新检查只比较已登记来源，不自动发现整个互联网的新内容，也不自动确认新观点。`accept-revision` 只确认资料版本，不会把 `pending` 证据变成已核验。新增或改变知识条目需修改 JSON 并经过内容复核。

## 旧版兼容与数据迁移

1. **命名与入口兼容**：
   - 新命令：`deepmentor` 和 `python -m deepmentor` 为主入口。
   - 旧命令：`open-mentor` 和 `python -m open_mentor` 保持完全兼容，复用同一套底层实现。
   - Python 代码中 `import open_mentor` 会发出一次 `DeprecationWarning`，原有接口继续正常可用。
2. **数据与复核保护**：
   - 状态目录优先级：**显式 `--state-dir` > 新目录 `.deepmentor` > 旧目录 `.open-mentor`**。
   - 若系统仅检测到旧版 `.open-mentor`，将无缝直接加载原有复核记录、停用状态和快照，已停用证据绝不会因改名被静默重置为可用。
   - 若用户同时存在 `.deepmentor` 与 `.open-mentor` 且两者均含有数据，系统直接抛出 `StateConflictError` 并中止，明确提示用户手动整合，杜绝静默合并、覆盖或数据丢失。
   - 继续使用旧目录即可保留全部状态。若选择改名，先停止写入进程、备份资料，并确认目标不存在；已有显式目录配置也需同步更新：
     ```bash
     test ! -e .deepmentor && mv .open-mentor .deepmentor # 源码检出目录内
     # 或
     test ! -e "$HOME/.deepmentor" && mv "$HOME/.open-mentor" "$HOME/.deepmentor" # 用户主目录下
     ```
3. **MCP 服务配置迁移**：
   - 默认生成名为 `deepmentor` 的服务配置。
   - 为避免重复注册导致工具冲突，请在客户端配置中将旧 `openmentor` 条目更新或替换为 `deepmentor`（详见 [MCP接入与自检](docs/MCP.md)）。

## 仓库地址迁移

项目已更名为 DeepMentor，仓库地址为 [gdpu11/deepmentor](https://github.com/gdpu11/deepmentor)。已有检出目录无需改名，只需更新远端：

```bash
git remote set-url origin https://github.com/gdpu11/deepmentor.git
```

## 测试与校验

```bash
.venv/bin/python -m unittest discover -s tests -v
```

代码和原创注释采用 MIT；第三方原文保留原权利，具体边界见 [DATA-LICENSE.md](DATA-LICENSE.md)。原始材料和私有导出保存在被 Git 忽略的 `.deepmentor/`（或历史 `.open-mentor/`），不随代码分发。
