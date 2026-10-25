# 转写与片段复核记录

截至 2026-10-24，已实际下载并转写下列三个公开版本。**机器全文保持待核；已复核入库的是单独列出的 7 条片段证据。没有完成整场逐句人工听辨，也没有独立验证采访中的全部主张。**

| 原发布版本 | 平台时长 | 输入音频实测时长 | 完成分块 | 转写段数 | OCR 采样画面 | 术语修订记录 |
| --- | --- | --- | --- | --- | --- | --- |
| [Alan × 孙宇晨](https://www.youtube.com/watch?v=0Z-vhBvBmUY)，2026-10-09 | 4:22:29 | 15749.361 秒 | 27/27 | 7335 | 7875/7875 | 166 |
| [William 上集：AI 黄金时代，普通人如何下注？](https://www.youtube.com/watch?v=o9Jn__LGGI4)，2026-10-16 | 47:08 | 2828.401 秒 | 5/5 | 1209 | 1414/1414 | 4 |
| [William 下集：争议之外，我认为最好的进化方式](https://www.youtube.com/watch?v=lFnc_92IeEI)，2026-10-22 | 36:39 | 2198.721 秒 | 4/4 | 956 | 1099/1099 | 32 |

合计 9500 段、89799 个字符（含中文、英文与数字）。William 简介中的 3.5 小时是录制时长，不能当成当前已取得的公开剪辑时长。Alan 的 B 站版于 10 月 10 日发布、元数据为 15750 秒；分别保留两平台日期和时长。

## 实际检查范围

1. yt-dlp 核对原频道、视频 ID、发布日期与时长；三个版本都没有可下载的平台字幕。
2. 完整音轨以 FFmpeg 解码为 16 kHz 单声道，MLX Whisper large-v3-turbo 在本机离线转写。模型版本为 `mlx-community/whisper-large-v3-turbo`，缓存提交 `a4aaeec0636e6fef84abdcbe3544cb2bf7e9f6fb`；mlx-whisper 0.4.3、mlx 0.32.4。输入 SHA-256、偏移、引擎和分块配置均保存。
3. 36 个分块的解码时长、连续性与全文段落时码均通过结构检查。这个结果只说明音轨被完整处理，不说明没有听错字或漏识别语句。
4. 原片每两秒采样，macOS Vision 识别底部画内字幕，保留 10388 份结果。比对排除角落节目/赞助标识。它是第二次机器读取，不能当作标准答案或准确率评测。
5. 对 Claude、薄肌、Lean 等少量已确认词形，仅在附近原片字幕也支持目标词时生成工作稿修订。202 处修订均保留 ASR 原文、修订文字、时码及字幕画面；原始 ASR 不覆盖，全文依旧 `pending`。
6. 入库引用另外检查了原片画面、发言归属和前后问答；没有把访谈主持人的话归给孙宇晨。`reviewed` 来源状态只覆盖知识包使用的片段，不代表机器全文已经审定。

## 本次入库的原片证据

| 证据 ID | 原片位置 | 支持的编辑归纳 |
| --- | --- | --- |
| `sun-e-portable-video` | Alan 00:07:28–00:07:51 | 把持续记录保存成可迁移的本地文档 |
| `sun-e-map-video` | Alan 00:43:13–00:45:18 | 决定前先调查资源、条件和选项 |
| `sun-e-interest-focus-video` | Alan 00:19:37–00:20:28 | 结合兴趣选择一个方向继续钻研 |
| `sun-e-customer-value-video` | Alan 00:35:32–00:36:52 | 用具体客户价值检验商业机会 |
| `sun-e-iterate-william` | William 上集 00:29:57–00:30:26 | 新规则需要反馈与迭代 |
| `sun-e-brand-william` | William 上集 00:45:20–00:46:42 | 调查价格之外的信任、习惯和差异化 |
| `sun-e-models-william` | William 下集 00:04:24–00:07:14 | 按具体问题拆开学习参照方法 |

两条既有 TechFlow 整理稿证据继续保留二手属性；本地文档与探图原则现在也有原片片段支持。所有应用步骤仍标为编辑推演，不冒充孙宇晨对当前用户的建议。

## 仍待复核的范围

原始机器稿与画内字幕的表达并不总一致。原始 ASR 的逐字子串匹配为 Alan 3754 个采样、William 上集 550 个、下集 402 个；另外分别有 3296、742、532 个含中文字幕的采样未完全匹配。**这些不是错误数量**：字幕可能经过编辑，OCR 也会认错字，短句可能跨转写段。差异列表已保存用于后续逐句回看。

没有把量子计算时点、投资收益、医疗/体重效果、私人关系叙述及数学阈值直接升级成指导事实。片段核对确认的是公开表达，事实正确性和对用户的适用性仍须分别判断。

## 本地文件与复现

原始音视频、完整机器全文、采样画面和修订日志都在被 Git 忽略的 `.open-mentor/media/<source-id>/`。不随开源知识包或 wheel 分发。每个源含：

- `audio-acquisition.json`、`video-acquisition.json`：采集记录与原片校验和。
- `asr-mlx-*/transcript.json`、`.txt`、`.vtt`：原始机器稿；`chunk-NNNN.json` 与 `progress.json` 支持恢复。
- `captions.ocr.jsonl`：逐画面 OCR；`asr-mlx-*/review-audit.json` 保存结构与异文检查。
- `asr-mlx-*/transcript.normalized.*`、`term-corrections.json`：保留待核状态的工作稿及逐处术语修改。
- `evidence-review.json`：已入库片段的来源区间、截图 SHA-256、复核方法与边界。

本地入口为 `.open-mentor/review/README.md`。复现脚本：

```bash
# 转写；同输入、模型和配置会恢复已有分块
.venv/bin/open-mentor transcribe sun-alan-video /path/to/audio.webm \
  --engine mlx --model mlx-community/whisper-large-v3-turbo \
  --chunk-seconds 600 --source-offset 0 --language zh

# 原片画面采样，按源分别存放
ffmpeg -i /path/to/video.mp4 -vf fps=1/2 -q:v 4 /path/to/frames/frame-%06d.jpg
# frame-paths.txt 每行一个绝对画面路径；Vision 仅适用于 macOS
swiftc scripts/ocr_frames.swift -o /tmp/openmentor-ocr
/tmp/openmentor-ocr frame-paths.txt captions.ocr.jsonl

.venv/bin/python scripts/audit_transcript.py /path/to/transcript.json captions.ocr.jsonl
.venv/bin/python scripts/normalize_asr_terms.py /path/to/transcript.json captions.ocr.jsonl
```

机器稿、OCR 和修订脚本均不会自动给知识证据设置 `reviewed` 或填说话人。短摘录、来源和编辑归纳在公开 JSON 包中，仍须经过独立的片段复核。
