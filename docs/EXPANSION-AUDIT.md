# 七位导师扩充审计

本页保留从7位扩充到14位时的验收记录；下文统计与分发包检查均属于该阶段。当前30位的范围与验收见[30位扩充审计](EXPANSION-30-AUDIT.md)。

2026-10-25。本轮七位全部入库，新增 **55 个来源记录（54 个不同 URL）、148 条证据和148条原则**。全库为 **14 人、82 个来源记录、201 条证据、196 条原则**。同一份伯克希尔2014年度文件含巴菲特和芒格各自署名文章，分开登记作者范围，不算两份独立事实验证。

“比较完整”指覆盖每位主要方法主题，并附应用问题、步骤及限制；不表示收集全部公开历史、全部 X 帖子、完整书籍或截至今天的所有立场。雷军本轮资料覆盖至2023年，张小龙至2021年；不会声称这些是2026年的全部现行政策或最新观点。

## 主题覆盖与实际知识包

| 导师 | 来源记录 / 原则 | 本轮资料范围 | 主题 |
| --- | --- | --- | --- |
| [保罗·格雷厄姆](../deepmentor/data/people/paul-graham.json) | 12 / 22 | 经典随笔及2024年9月 Founder Mode | 问题发现、早期用户、迭代与自动化、增长与现金、工作时间、合伙协作、学习、授权边界 |
| [沃伦·巴菲特](../deepmentor/data/people/warren-buffett.json) | 10 / 23 | 1996—2024年度信选段及2025-11-10本人致股东文字 | 能力圈、竞争优势、资本配置、负债与流动性、管理激励、沟通、纠错、榜样与尊重 |
| [查理·芒格](../deepmentor/data/people/charlie-munger.json) | 6 / 20 | 2005作者修订文字、2007 USC现场引语、Wesco三封信、2014独立署名文章 | 逆向思考、激励、认知偏差、学习与多学科、职业信任、授权与资本分工、估计与资金、经验复制边界 |
| [杰夫·贝索斯](../deepmentor/data/people/jeff-bezos.json) | 6 / 23 | 1997、2016、2017、2018、2020年度信及2023 Lex采访原发布文字稿 | 客户、长期投入、实验、可逆决策、流程与标准、书面沟通、团队意见、专注 |
| [詹姆斯·克利尔](../deepmentor/data/people/james-clear.json) | 12 / 20 | 作者官网文章、书籍选段及作者习惯手册 | 身份与习惯、系统、环境与提示、行动门槛、渐进难度、记录与反馈、中断恢复、真正交付 |
| [雷军](../deepmentor/data/people/lei-jun.json) | 5 / 20 | 2015/2017/2023武汉大学原发、2018亲署公开信、2020演讲实录 | 目标与创业准备、商业经验、用户、成本效率、质量与交付、团队、技术与跨域学习、回馈 |
| [张小龙](../deepmentor/data/people/allen-zhang.json) | 4 / 20 | 2016公开课的发布者同步稿及2018/2019/2021原发布讲话文字 | 用户价值、工具任务、平台、订阅控制、增长验证、推荐与冷启动、身份与表达、复杂度 |

每位至少六个不同任务主题。下面给出代表性原则 ID，完整条目、定位和应用边界见[人物目录](MENTORS.md)及对应 JSON。

- 保罗·格雷厄姆：`pg-p-own-problem`、`pg-p-manual-recruiting`、`pg-p-manual-before-automation`、`pg-p-default-alive`、`pg-p-maker-time`、`pg-p-cofounder-relationship`、`pg-p-aptitude-interest`、`pg-p-delegation-boundaries`。
- 沃伦·巴菲特：`buffett-p-circle-of-competence`、`buffett-p-durable-economics`、`buffett-p-price-discipline`、`buffett-p-funding-independence`、`buffett-p-owner-aligned-incentives`、`buffett-p-owner-communication`、`buffett-p-learn-and-move-on`、`buffett-p-choose-role-models`。
- 查理·芒格：`munger-p-invert-failure`、`munger-p-incentive-bias`、`munger-p-availability-checklist`、`munger-p-multidisciplinary-models`、`munger-p-deserve-trust`、`munger-p-central-capital-role`、`munger-p-estimate-uncertainty`、`munger-p-success-replicability`。
- 杰夫·贝索斯：`bezos-p-customer-focus`、`bezos-p-long-term-thesis`、`bezos-p-failure-scale`、`bezos-p-reversible-decisions`、`bezos-p-teachable-standards`、`bezos-p-written-reasoning`、`bezos-p-senior-speaks-later`、`bezos-p-long-attention-practice`。
- 詹姆斯·克利尔：`clear-p-identity-direction`、`clear-p-systems-over-wishes`、`clear-p-habit-stacking`、`clear-p-environment-steps`、`clear-p-two-minute-start`、`clear-p-habit-record`、`clear-p-resume-after-miss`、`clear-p-action-produces-output`。
- 雷军：`lei-p-startup-motivation`、`lei-p-commercial-experience`、`lei-p-user-participation`、`lei-p-whole-chain-efficiency`、`lei-p-growth-foundations`、`lei-p-complementary-team`、`lei-p-learn-new-domain`、`lei-p-give-within-means`。
- 张小龙：`zhang-p-user-value-first`、`zhang-p-complete-and-leave`、`zhang-p-platform-capabilities`、`zhang-p-subscription-control`、`zhang-p-validate-pull-before-scale`、`zhang-p-method-fits-stage`、`zhang-p-public-private-identity`、`zhang-p-unnecessary-complexity`。

## 核验方法与归属边界

- 逐条读取本人文章、署名信或原发布者文字，核对作者/说话人、前后文、条件与定位。148条短摘录的本地定位和基线哈希检查通过；43处 PDF 摘录另与所填文件页序比对。核验者明确标为 Codex 辅助，未冒充独立人工审稿。
- 芒格 Stripe Press 文件为本人2005年修订、增补的书面作品；封面说明合并的版本从未整场讲过。已查看封面，不称其为某场录音逐字稿或整本书。USC记录只取明确归于芒格的引语。
- 伯克希尔2014文件中的两位作者分开定位。2025年 Thanksgiving Message 明确归于巴菲特；Greg Abel署名的后续年度信没有归入巴菲特。
- 雷军2018招股书仅使用 PDF 文件第6—10页的董事长公开信，已渲染检查信首与末页署名；不把其后整本招股书叙述归于个人。武汉大学讲话的录音整理、记者归纳与他人发言区分记录。2020原发实录注明略有删节，未采用疑似错字。
- 张小龙2018报道只用“附上张小龙演讲全文”后的本人讲话；导语与正文不逐字一致。2016同步页区分本页2018刊载日和2016讲话；发布账号腾讯大讲堂的[认证资料](https://cloud.tencent.cn/developer/user/1054460)另作归属核对。未把AI医疗预测作为指导，隐私陈述仍注明为历史自述。
- 格雷厄姆只给月/年的随笔不虚构完整发布日期。James Clear网页可能后续增补书籍选段，早期页面元数据不证明每句话当时已经存在。贝索斯原采访文字稿明确提示可能有误，所用段落已定位但未宣称整场逐句听辨。
- 来源只能证明公开表达；公司历史数据、成功原因、人格或技术预测不自动成为独立事实。编辑步骤与人物原话分开。相似观点保留不同适用条件，例如手工招募用户不等于未验证产品就做大规模投放。

## 功能与内容验证

- `open-mentor validate`：14人物包的格式、唯一ID和引用关系通过。
- `python -m unittest discover -s tests -v`：**65项测试通过**，其中固定场景 **154个**；本轮新增74个输入。覆盖七位各八个具体任务、英文姓名别名、七种自动选择及原有七位回归。
- 七位均经实际 CLI 子进程、本机 HTTP 和官方 MCP SDK stdio 调用；检查导师归属、预期证据与可引用状态。新增来源变更、读取失败、待核、争议、撤回和原始表达未核对均有停用检查。
- 扩充语料后修复：泛词/虚词碎片误命中、价格材料误用于预测、多条弱结果累加压过直接证据。自动选择现按每位最强合格证据比较，limit只影响展示。扩展仍是公开有限规则，不保证任意自然语言语义理解。
- 原站 Brotli/gzip/deflate 解码、旧HTML编码及超长/损坏响应有回归。实际重读 `pg-startupideas`、`pg-makersschedule`、`buffett-1996`，三份规范化文本哈希均与基线相同、摘录无缺失。
- 原始网页、PDF、媒体、完整转写和逐条上下文账本保留在忽略目录；知识包仅包含元数据、有限短摘录和原创归纳。

Wheel与sdist均已构建并核对：包含14个人物包，代码/数据与当前文件一致，未包含私人目录、完整网页/PDF、音视频或长字幕。另在独立目录解包wheel，确认实际导入来自解包目录，七种自动选择、带背景追问、来源停用、损坏状态拒绝和格式校验均通过。该检查使用现有依赖环境，不声称在新虚拟环境完成了安装。

## 基线复查

本轮本地快照审计：55来源记录、54不同URL、148摘录全部通过规范化文本SHA-256、摘录存在性与逐URL短摘录数量检查。短摘录合并同URL计数；完整原文不随代码分发。此脚本不判断作者、上下文、事实或方法有效性，不能代替内容复核。

```bash
.venv/bin/python scripts/audit_sources.py \
  --people paul-graham warren-buffett charlie-munger jeff-bezos james-clear lei-jun allen-zhang \
  --snapshots .open-mentor/revisions
```

需要与登记哈希对应的本地原文快照；从原站重新读取时页面更新可能使哈希变化。PDF按来源记录手动导入和复核，不伪装成已支持自动解析更新。

| 来源 ID / 原始页面 | 发布日期 | 规范化文本 SHA-256 | 摘录数 |
| --- | --- | --- | --- |
| [`zhang-2016-tencent`](https://developer.cloud.tencent.com/article/1042628) | 2018-02-12 | `ec06ad02b2eb3567e343d1b40569b73dba4e15adc767593ee56c6e3fa56a25e8` | 5 |
| [`zhang-2018-geekpark`](https://www.geekpark.net/news/226011) | 2018-01-15 | `629f8678ed350e7e7e7660f2ad94bee9a232b8520e10977b5a5f28a30d43eae6` | 3 |
| [`zhang-2019-geekpark`](https://www.geekpark.net/news/237288) | 2019-01-10 | `4d5db3d109d7e0841162bcf3f0e838c8f535ed0d85990fcee1d4336491c20df9` | 6 |
| [`zhang-2021-geekpark`](https://www.geekpark.net/news/272872) | 2021-01-19 | `0239f4b328845aa64731ce1a07425fc9661566b57f0b5c133ad28bc514306897` | 6 |
| [`munger-stripe-zine`](https://assets.stripeassets.com/fzn2n1nzq965/0RUnI35jpt78x10nvlO2Y/b66a46dba182182a2a0082213eafc634/SP_PCA-ZINE_2023_11_27.pdf) | 未确认完整日期，见知识包 | `47747ad86d8a33b38a0a5efe553e40c9a88a4440b5d72e8b79c6fcc1f0eb658c` | 10 |
| [`munger-usc-2007`](https://gould.usc.edu/news/300-graduate-from-usc-law/) | 未确认完整日期，见知识包 | `77047b1346eaaeb556af1ae8d29f63e732ae637cca3832ca6ae45e2c80756bcd` | 3 |
| [`munger-berkshire-2014`](https://www.berkshirehathaway.com/letters/2014ltr.pdf) | 未确认完整日期，见知识包 | `ffae760ec53d6fa239bb60ff43de6859384e36548372ee0dce8397554c83904b` | 3 |
| [`munger-wesco-2004`](https://berkshirehathaway.com/wesco/cm2004.pdf) | 2005-03-09 | `c0acab3cf917d3398ea4f063b1d02be28c05d7bc1bd029d2c7454f7d1e81fc31` | 1 |
| [`munger-wesco-2008`](https://berkshirehathaway.com/wesco/cm2008.pdf) | 2009-02-25 | `bc95bf4cf33b066ee2c8e0d2bbcb66ea6590c8edf0c2c8bbe116feaddb142c03` | 1 |
| [`munger-wesco-2009`](https://berkshirehathaway.com/wesco/cm2009.pdf) | 2010-02-26 | `3ffbef1f5015d909905a4192a13fe2f5c73c446f4d451035dc705e9314ffdec5` | 2 |
| [`clear-identity-based-habits`](https://jamesclear.com/identity-based-habits) | 2012-12-31 | `db551b9cb4371b890986d6edacdb30521f463f7c9344dced0762482bc538aff8` | 2 |
| [`clear-goals-systems`](https://jamesclear.com/goals-systems) | 2013-10-28 | `13785d9c9f7b20e4ea441f9a8b3cbb937f218c3cbd79f216d9f8fc18a496cf00` | 2 |
| [`clear-habit-guide`](https://jamesclear.com/habit-guide) | 2014-07-18 | `b886888cbc610a07385a3968157a6d8944b8c63dbf8e8fcb7d8789b9cacf0590` | 2 |
| [`clear-habit-stacking`](https://jamesclear.com/habit-stacking) | 2014-08-01 | `24a51a2fe4f465983abe3110d659cb02669832a24f33e0bee9e91e957648f269` | 1 |
| [`clear-environment-design`](https://jamesclear.com/environment-design) | 2013-07-11 | `2220f359bf0600b189cb2d1e9e57d25717c887c360966acbef5fdab4d55029f5` | 1 |
| [`clear-goldilocks-rule`](https://jamesclear.com/goldilocks-rule) | 2016-06-28 | `88edc58f3fc2c3cab28fad805848967180466ac151694f6c59ca57ea64b2574e` | 2 |
| [`clear-habit-tracker`](https://jamesclear.com/habit-tracker) | 2019-01-14 | `e34de6df22094e8f3212060de2de5b2fe74b600f7aa536f619e53b157aa3b3f2` | 2 |
| [`clear-procrastinating`](https://jamesclear.com/how-to-stop-procrastinating) | 2013-05-27 | `0b0be3fc263ee2cd545cc5eb87e9010ed54fe03e2d015769b28af80c5d37d4e5` | 2 |
| [`clear-action`](https://jamesclear.com/taking-action) | 2013-06-27 | `1659d2b9b091f5ff4234d261bb2ef0bc3759fce9be90d0688a2e383e086fe581` | 2 |
| [`clear-recovery`](https://jamesclear.com/get-back-on-track) | 2013-03-21 | `3b763888995fc22d1ee290fe3b6e79214bb98b8b2affeb94789708e4cf80588d` | 2 |
| [`clear-bundling`](https://jamesclear.com/temptation-bundling) | 2015-06-25 | `cac0868d06276942eb8012dbe9891ad8185529d48f6b3ad1ccfc4406d9d6dbb0` | 1 |
| [`clear-habits-booklet`](https://jamesclear.com/wp-content/uploads/2013/09/habits-v2.pdf) | 未确认完整日期，见知识包 | `a30934a5543090056f9ee71d0e6392567147f54afa1c2cbbdfd85ed88e50105d` | 1 |
| [`bezos-1997`](https://www.aboutamazon.com/news/company-news/amazons-original-1997-letter-to-shareholders) | 1998-03-21 | `3d464c23f3ebb24fd536de5775574a8189f51f54bc4b690d5dd73d7ad2dbf4ff` | 3 |
| [`bezos-2016`](https://www.aboutamazon.com/news/company-news/2016-letter-to-shareholders) | 2017-04-17 | `b9b7f171ae1b55afa9a218028dfd684beaab31ce8570ef875cc59e0362177d65` | 6 |
| [`bezos-2017`](https://www.aboutamazon.com/news/company-news/2017-letter-to-shareholders) | 2018-04-18 | `adb25e213a55dbcdb5aa3ae9074b53767f0597048364bee3f74c9f79b192f267` | 4 |
| [`bezos-2018`](https://www.aboutamazon.com/news/company-news/2018-letter-to-shareholders) | 2019-04-11 | `fe1b705681235eadbdc19a4a8512709403db9bf2152c7ed73ec5c514f8a0eaf1` | 4 |
| [`bezos-2020`](https://www.aboutamazon.com/news/company-news/2020-letter-to-shareholders) | 2021-04-15 | `5f20de852bb4470bf27984779fef6210d50f8e43153b35638abf99f92ef8479f` | 3 |
| [`bezos-lex-2023`](https://lexfridman.com/jeff-bezos-transcript/) | 2023-12-14 | `ba178f48f49583f0da01ea09e26c8511de3a46d627193505e8794081a32b5e50` | 3 |
| [`lei-whu-2015-original`](https://news.whu.edu.cn/info/1002/43786.htm) | 2015-06-27 | `676ddffec6081b6c54772142a98c514b40e055de590b9bdc184f6cdc38397c16` | 3 |
| [`lei-whu-2017-original`](https://news.whu.edu.cn/info/1002/48413.htm) | 2017-04-10 | `bbd9c258ff6ef15b86993758fd3206175d794b9d955e218da493603daa7e88fc` | 3 |
| [`lei-prospectus-2018`](https://www.hkexnews.hk/listedco/listconews/sehk/2018/0625/LTN20180625034_C.pdf) | 2018-06-25 | `28f35e2d4b3f2308c163a727978d6a0231737c99c58087f41b1f9e601d3bbed3` | 5 |
| [`lei-2020-geekpark`](https://www.geekpark.net/news/264145) | 2020-08-11 | `43a155f901e329e839b818289f42667671199b87ec270975938c49cca8544e0b` | 4 |
| [`lei-whu-2023`](https://news.whu.edu.cn/info/1002/447457.htm) | 2023-11-30 | `d7577669288e5f762c54d40108b8e3f6f560152668cb9a72a3092902397eec6e` | 5 |
| [`pg-startupideas`](https://www.paulgraham.com/startupideas.html) | 未确认完整日期，见知识包 | `1b856320f04db1bcb04270048a9de106a3931d23b4720223d490ff9762778722` | 3 |
| [`pg-ds`](https://www.paulgraham.com/ds.html) | 未确认完整日期，见知识包 | `759346846c917390994557a68d3d24c2dfc27740a445158162717742a89c9658` | 3 |
| [`pg-growth`](https://www.paulgraham.com/growth.html) | 未确认完整日期，见知识包 | `fd4ef8e82146efd962f38b88c22e8c51a2e883a4861c205022df17db3e27547b` | 2 |
| [`pg-makersschedule`](https://www.paulgraham.com/makersschedule.html) | 未确认完整日期，见知识包 | `eaeda0923801c6a51fa64b6ca404135e52eebd83d3ebd8cd08717ef3f5d0058e` | 2 |
| [`pg-relres`](https://www.paulgraham.com/relres.html) | 未确认完整日期，见知识包 | `648dbb5ef127cd620fdff5e5938844c5ca30a9f7a97c07a7d6ecf615ca538c3b` | 1 |
| [`pg-founders`](https://www.paulgraham.com/founders.html) | 未确认完整日期，见知识包 | `438dd10628b0acd995d416592e434ed5b7f2ab1364f28c9ee6162580cd9c5ae8` | 1 |
| [`pg-schlep`](https://www.paulgraham.com/schlep.html) | 未确认完整日期，见知识包 | `eea2dea849fa226096fc7919ba738ac0d86646fc7b98c9ebae403de7cffc7e25` | 1 |
| [`pg-mean`](https://www.paulgraham.com/mean.html) | 未确认完整日期，见知识包 | `3b86bbe9c8e767d697df51ec921e71b814dd3b1715fc9eae0590d4f2ecdd661c` | 1 |
| [`pg-greatwork`](https://www.paulgraham.com/greatwork.html) | 未确认完整日期，见知识包 | `86c814f71dd585a86298a4d97f130cb8ba70044deb857e085958355b573bd0c9` | 3 |
| [`pg-determination`](https://www.paulgraham.com/determination.html) | 未确认完整日期，见知识包 | `28dc6100dc115dab7d603a81b16df0eae576bbc54d20217ce7239224753c5ff8` | 2 |
| [`pg-aord`](https://www.paulgraham.com/aord.html) | 未确认完整日期，见知识包 | `0e0d9e9fa5ddb4b604c46224264e6ccc796e0868b1a3d87592639df357dd9ca2` | 1 |
| [`pg-founder-mode`](https://www.paulgraham.com/foundermode.html) | 未确认完整日期，见知识包 | `a1f3a2fdf9418561ef42849b29ed44b345f520fdaf2155fc5a4f75558f13a339` | 2 |
| [`buffett-1996`](https://www.berkshirehathaway.com/letters/1996.html) | 1997-02-28 | `6df0e8290624d26a5fda6a7b82d98045f9bd56bb013e4e742f4a7bac05f35569` | 2 |
| [`buffett-1999`](https://www.berkshirehathaway.com/letters/1999htm.html) | 2000-03-01 | `a58988fc41ff66fcf5f651c361344ce6003f4ea4c5da86ba82c060b409bd6d09` | 1 |
| [`buffett-2001`](https://www.berkshirehathaway.com/letters/2001pdf.pdf) | 2002-02-28 | `4f4f00170ea35b9fe51682bf98110471852c39f6a2646aad4a0dcb575af090d3` | 3 |
| [`buffett-2004`](https://www.berkshirehathaway.com/letters/2004ltr.pdf) | 2005-02-28 | `9b92d8ac664db91a1042b5ea92a4fb91ea74aa63f05bf17c7207e33b14c607b1` | 2 |
| [`buffett-2011`](https://www.berkshirehathaway.com/letters/2011ltr.pdf) | 2012-02-25 | `03b52a83fc53a20ef3dfa0128346171b3bbed7e3d1b1c0ac60f2e9699f08996d` | 3 |
| [`buffett-2013`](https://www.berkshirehathaway.com/letters/2013ltr.pdf) | 2014-02-28 | `9aa3ca1175f768e89c0dfca67334cf12deebb6ad7ddfa84c007c5efa21f2d8c8` | 2 |
| [`buffett-2014`](https://www.berkshirehathaway.com/letters/2014ltr.pdf) | 2015-02-27 | `ffae760ec53d6fa239bb60ff43de6859384e36548372ee0dce8397554c83904b` | 1 |
| [`buffett-2017`](https://www.berkshirehathaway.com/letters/2017ltr.pdf) | 2018-02-24 | `e77b68776e70fbd33d81cf035383ea42814bca6de2c57df95589f0be18d1ee71` | 3 |
| [`buffett-2024`](https://www.berkshirehathaway.com/letters/2024ltr.pdf) | 2025-02-22 | `ea98c5e9ce353981ca7fbc7e403d93094868062dd164e034a682b2aa8ed55730` | 3 |
| [`buffett-thanksgiving-2025`](https://berkshirehathaway.com/news/nov1025.pdf) | 2025-11-10 | `7968bbfae80a1ce7866c30d044f9415d80472933595a8cfbbe20ef9e225cd84b` | 3 |
