# 深度咨询与行动闭环

DeepMentor 返回经过证据门槛筛选的咨询依据与交互协议。接入 MCP 的 AI 负责追问、交叉质询和最终决策备忘录；CLI 直接展示带出处的原则、编辑问题与行动候选。整个流程不需要在 DeepMentor 中配置生成模型 API Key。

## P0：私人董事会

```bash
deepmentor board '要不要辞职做AI产品？如何验证需求与控制风险'
deepmentor ask '创业怎样验证用户需求' --mode board
# 明确指定2-3位导师；有任何一位缺少相关证据，返回 insufficient_evidence，不换人
deepmentor board '创业如何验证用户需求与控制风险' --people 纳瓦尔 巴菲特 保罗·格雷厄姆 --format json
```

`consult_board` MCP 工具与 `POST /v1/board` 接受 `question`、可选 `people`（2-3个不重复的名字/ID）、`limit`（每人1-5条，默认3）、`situation`、`allow_secondary`。未指定时，先找有相关且可引用原则的导师，再按相关性与匹配主题差异选最多3位；仅有一位有证据时不会凑成董事会。自然语言中的否定指定会被排除；明确未收录人物时要求重新选择。

返回 `perspectives`、`tradeoff_matrix`、`cross_examination`、统一 `citations`。每行权衡和交叉问题带证据ID。主题差异不等于对立立场，不能把人物标签写成事实。交叉问题是编辑提示，AI 需要基于实际出处检验是否存在冲突，保留不能消解的分歧，并说明用户需要收集哪些事实来选择。

推荐调用方提示：

> 用 consult_board 分析我的决定。先分别还原每个视角最强的论据，再各找一个对其他视角的关键反问；不能编造人物对话。把真正的证据分歧与我的处境造成的权衡分开。输出选项矩阵、决定性未知、72小时实验和停止条件。每个借用观点附证据ID及原链接。

## P0：先访谈再出决策备忘录

```bash
deepmentor interview '我想创业，应该先做什么'
deepmentor interview '我想创业，应该先做什么' --interactive
# 非交互客户端把回答作为 JSON 文件传入
deepmentor interview '我想创业，应该先做什么' --answers answers.json --format json
```

`answers.json` 示例：

```json
{
  "goal": "本月决定是否继续开发，先验证真实需求",
  "resources": "后端经验，每周10小时，实验预算1000元",
  "downside": "不辞职；最多投入一个月，拿不到试用反馈就停止"
}
```

MCP `diagnose` / `POST /v1/diagnose` 使用 `question`、可选 `answers`、`person`、`situation`、`allow_secondary`。三项回答不全时返回 `needs_clarification` 及剩余问题，调用方逐次收集后重调。全部提供后返回 `decision_memo_context`：用户事实、证据与备忘录章节。回答只是用户自述，不能当作已核事实。CLI 的 `ask --mode interview` 可先取得三问，后续使用 `interview --answers`。访谈本身不保存聊天历史。

## P1：逆向压力测试

```bash
deepmentor stress-test '我要辞职开发产品，但还没访谈过用户'
deepmentor roast '融资后再考虑客户收入' --person 保罗·格雷厄姆
```

MCP `stress_test` / `POST /v1/stress-test` 接受 `question`、可选 `person`、`limit`、`situation`、`allow_secondary`。`failure_modes` 从已匹配原则的应用问题与边界构造失败预演、待证伪假设、实验候选和停止指标提示。它们是编辑诊断素材，不是已经证实的失败原因。最终的“三个致命假设”应由调用方AI结合用户事实提炼；批评计划，不给用户贴人格标签。

## P1：行动账本

```bash
deepmentor action-add \
  --hypothesis '目标用户愿意为减少重复排查付费' \
  --probe '72小时内访谈5位潜在用户，演示现有原型' \
  --success-criteria '至少2位愿意试用并约定下一次反馈' \
  --stop-criteria '5人均无明确需求，停止继续开发并重选问题' \
  --due-date 2026-11-01 --evidence pg-e-manual-recruiting

deepmentor actions --status active
deepmentor check-in
deepmentor check-in ACTION_ID --observation '访谈5人，2人愿意试用' --status completed
deepmentor check-in ACTION_ID --observation '没有发现明确需求' --status stopped
deepmentor action-export ACTION_ID --output ACTION-PLAN.md
```

以上人数、日期和预算都是示例，按你的实际约束替换。截止日期使用 `YYYY-MM-DD`。`action-export` 默认向终端输出；指定文件时拒绝覆盖已有文件。

账本位于已解析的状态目录 `ledger.sqlite3`，复用 `--state-dir` 和旧目录迁移规则。SQLite 事务保证同时运行的 CLI/HTTP/MCP 不会互相覆盖复查记录。保存的是用户明确提交的假设、实验、成功/停止条件、日期与可选证据ID；不自动保存咨询。历史记录读取时重新检查证据状态，停用或删除的证据不会继续标成可用。复查由用户运行或调用AI显式发起，没有后台定时提醒。

MCP `list_actions` 只读；`add_action` 与 `check_in` 的注解明确为写入且非幂等，调用方须在用户有保存意图时使用。HTTP 提供 `GET /v1/actions?status=active`、`POST /v1/actions` 和 `POST /v1/check-in`，字段与MCP对应。普通 HTTP 服务只监听回环地址；请求限制回环 Host，POST 要求 JSON 并拒绝带浏览器 Origin 的请求，防止网页触发本地账本写入。

## 轻量检索

保持 SQLite FTS5/BM25 与中英文词项扩展，不引入 Embedding、向量索引或模型服务。检索和导师路由不需要模型下载、API Key 或外部进程；证据状态筛选继续执行。

## P2：导师贡献脚手架

```bash
deepmentor scaffold mentor --interactive --output .deepmentor/drafts/people/new-mentor.json
# 或全部提供参数以便脚本使用
deepmentor scaffold mentor --id new-mentor --name '导师姓名' \
  --url 'https://example.com/original' --title '来源标题' --publisher '发布方' \
  --excerpt '用户提供的短摘录' --locator '章节或段落' --summary '待核摘要' \
  --output .deepmentor/drafts/people/new-mentor.json
```

生成符合当前 Schema 的最小人物包，含完整引用链。来源和证据均 `pending`，`origin_verified=false`，内容哈希保持 `null`，来源类型暂按未核二手资料处理。脚手架不会联网核验或生成原话，也不会伪造复核者、发布日期与哈希。先核对原出处、归属、语境、权利及来源类型，补齐应用问题/步骤/边界后再按[贡献指南](../CONTRIBUTING.md)提交。输出文件已有时拒绝覆盖；草稿默认留在隔离目录，避免混入发布语料。

桌面和聊天入口见[集成指南](INTEGRATIONS.md)。
