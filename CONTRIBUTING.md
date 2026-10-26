# Contributing to DeepMentor / 一起完善你的人生导师

[English](#english) | [简体中文](#简体中文) | [README](README.md)

## English

Help build a mentor library people can inspect, question and improve. A useful contribution can be one original interview passage, an attribution correction, a missing limitation, a better retrieval example, a translation or a code fix. You do not need to add a large collection to get started.

### Suggest a mentor without writing code

Open a [mentor/source issue](https://github.com/gdpu11/deepmentor/issues/new?template=add-mentor.md) with the person's name, a practical topic, original public URLs and a precise passage, page or timestamp. Explain who is speaking and why the passage is useful. Mark anything you have not checked. Proposing a source does not make it eligible for guidance.

To report a wrong quote, speaker, date or application, use the [evidence correction issue](https://github.com/gdpu11/deepmentor/issues/new?template=correct-evidence.md). Include existing evidence/principle IDs where possible. Preserve changes of mind and conflicting contexts rather than silently blending them.

### Contribute a knowledge pack

1. Fork the repository, install `.[mcp]`, and create a branch. Check the [catalog](docs/MENTORS.md) and open issues for an existing pack or contribution.
2. Add or edit `deepmentor/data/people/<person-id>.json`. Use an existing pack for structure and [pack.schema.json](deepmentor/data/pack.schema.json) for required fields. Start with one source and one bounded principle; the current large packs are not a minimum contribution quota.
3. Keep the chain `person → principle → evidence → source` intact. IDs must be globally unique, and references must remain within the same person. Provide names/aliases, source provenance and rights, a short excerpt, the actual speaker, a precise locator and context.
4. Check attribution and surrounding context in the original publication or recording. Fill the actual review date, reviewer, method and scope; disclose AI assistance and transcript limitations. `origin_verified=true` requires checking the original expression. A publisher's machine transcript alone does not establish audio accuracy.
5. Use `pending` and `origin_verified=false` for unchecked evidence, and describe what is missing. A draft PR or issue is suitable for work awaiting review. Never change a status just to make tests pass. `reviewed` records exactly what was checked, not a person's complete body of work or the truth of every claim.
6. Separate the person's expression from editorial interpretation. In `application`, include useful questions, reversible steps and explicit limits. Do not invent quotes, personal traits, income promises or endorsement.
7. Add focused retrieval cases in `tests/fixtures/mentor_scenarios.json` for ready-to-use material. Include a useful match and a related question the evidence cannot answer; verify changed/pending evidence stays excluded. Extend relevant interface tests and update the catalog/current counts when corpus coverage changes. Existing fixed counts should be reconciled, not used to reject new mentors or weaken evidence gates.
8. Run the checks below and open a PR with source links, review scope, changes and results. Passing schema/tests checks structure and behavior; it does not replace content review before merge.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[mcp]'
.venv/bin/python -m deepmentor validate
.venv/bin/python -m deepmentor doctor --mcp
.venv/bin/python -m unittest discover -s tests -v
```

For a draft whose sources are all pending, `doctor` may report no eligible evidence. Report that honestly and keep it out of the usable corpus until reviewed. Use a separate `--data-dir` / `--state-dir` before the subcommand when testing a private draft.

### Sources, privacy and rights

- Prefer the person's own writing, original interviews, official transcripts and attributable publisher editions. Distinguish the speaker from the interviewer, editor, translator and reader comments.
- Keep original URLs, dates or explicit unknowns, and page/timestamp/heading locators. Describe whether you checked text, captions, audio or a selected excerpt.
- Public contributions contain metadata, short excerpts and original annotations. Keep books, long transcripts, raw media, private exports, cookies, tokens, local client configuration and personal paths out of commits. Use `.deepmentor/` (or legacy `.open-mentor/`) for private review material.
- A readable webpage or downloadable book does not establish redistribution permission. Fill `rights` honestly and follow [DATA-LICENSE.md](DATA-LICENSE.md). Do not upload private conversations or identifying personal information as mentor material.
- Mark contested material `disputed` and explain the issue. Do not erase an earlier position or remove evidence safeguards to improve retrieval results.

The [source review guide](docs/SOURCES.md) has more detail (currently Chinese). Code changes should remain focused and include proportionate tests. Translations should preserve qualifications, citations and the distinction between original text and editorial application. Do not add dependencies or generated files unrelated to your change.

## 简体中文

欢迎把影响过你的人生导师补进来，也欢迎完善已有导师。一条能核对的观点、一次错引纠正、一个适用边界，都是有价值的贡献；不需要一次整理整本书或整场采访。

### 不写代码也能参与

用[导师／资料推荐](https://github.com/gdpu11/deepmentor/issues/new?template=add-mentor.md)提供人物、实际问题、一手公开链接和具体页码、段落或时间戳。说明谁在说话、你核对了什么、还有什么不确定。提交线索不会自动进入可引用知识。

发现错引、说话人混淆、日期错误或过度推论时，用[证据纠错](https://github.com/gdpu11/deepmentor/issues/new?template=correct-evidence.md)，尽量附上条目 ID、原文定位和上下文。观点变化应保留时间与语境。

### 提交知识包

1. Fork 仓库、安装 `.[mcp]` 并建分支。先查[人物目录](docs/MENTORS.md)和现有 Issue，避免重复。
2. 在 `deepmentor/data/people/<person-id>.json` 新建或补充人物包。参考现有包的结构，并遵循 [Schema](deepmentor/data/pack.schema.json)。可以先做一份来源、一条原则，不要求凑够大包的数量。
3. 保持 `人物 → 原则 → 证据 → 来源` 的完整引用。ID 全库唯一，不跨人物引用。填写来源与权利、真实说话人、短摘录、准确定位和上下文。
4. 回到原发布文字或原片核对归属、原话和前后文。写明实际核对日期、复核者、方式和范围；AI 辅助、机器转写、只看字幕等情况如实记录。只有实际核对原始表达，才设置 `origin_verified=true`。
5. 未核对的证据保持 `pending`、`origin_verified=false`，写清缺项，先提交 Draft PR 或资料 Issue。不要为了测试通过而改成 `reviewed`。已核验只代表记录中的具体范围，不等于全量思想或事实真实性已验证。
6. `application` 是编辑整理，写清适用问题、可逆步骤和限制；不编原话、恒定人格、收益承诺或人物背书。
7. 为可用材料补充 `tests/fixtures/mentor_scenarios.json` 中的有效提问及缺证据场景，检查来源停用和待核状态仍能隔离；按影响补充接口用例、人物目录与当前数量。已有测试中的固定数量要随语料变化核对，不能成为拒绝新增导师或削弱门槛的理由。
8. 运行上面的 `validate`、`doctor --mcp` 和测试命令，再提交 PR，说明来源、核对范围、改动和结果。格式和测试通过不代替合并前的内容复核。

如果单独测试的草稿全部待核，`doctor` 可能提示没有可用证据；如实记录，完成复核后再纳入可用语料。可在子命令前用 `--data-dir`、`--state-dir` 指定隔离目录。

### 保留证据，也保留边界

优先本人文章、原始采访、机构原稿及可归属作者的出版版本；采访者、编者、译者、评论区与本人表达分别处理。日期未知就保留未知，字幕核对不要写成逐句听辨。

公开提交只包含元数据、短摘录与原创归纳。完整书籍、长转写、原始音视频、私有导出和本机配置留在 `.deepmentor/`（或历史 `.open-mentor/`）；凭据、Cookie、私人对话和本机个人路径不要入库。网页能读不等于允许全文再分发，授权填写见 [DATA-LICENSE.md](DATA-LICENSE.md)。

有争议的条目标为 `disputed` 并记录原因；不能静默抹去旧观点或关闭证据隔离。更多规则见[资料规范与复核](docs/SOURCES.md)。代码修复保持聚焦，翻译保留引用、限定条件和原文／编辑应用的区别。
