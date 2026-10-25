# OpenMentor

[English](README.en.md) | [简体中文](README.md) | [Contributing](CONTRIBUTING.md)

**Your 24/7 AI mentor library.**

Bring the publicly shared ideas of Justin Sun, Elon Musk, Warren Buffett, Duan Yongping, Naval Ravikant and more into your AI assistant. Ask a concrete question, explore relevant principles, and follow the evidence back to its source.

OpenMentor is an open-source knowledge library built around **source quality, review history, updates and a shared retrieval interface**. Your AI assistant produces the situational advice using attributed public material. The featured people are not participating in the conversation or endorsing the project.

## Build your mentor library together

Who has helped you think more clearly, build something useful, or make a difficult decision? Help others learn from their publicly shared work.

- [Suggest a mentor or source](https://github.com/gdpu11/open-mentor/issues/new?template=add-mentor.md). A primary-source link and a specific passage are a useful contribution; coding is optional.
- [Correct an attribution or evidence record](https://github.com/gdpu11/open-mentor/issues/new?template=correct-evidence.md). Context, counterexamples and changes of mind matter.
- [Contribute a knowledge pack, translation or code](CONTRIBUTING.md). Start with a small, verifiable contribution. Unreviewed material remains pending.

Mentors are selected for useful, attributable material. You can propose someone beyond the current list; popularity alone is not a selection criterion. Use public or explicitly authorized material and keep private conversations out of public contributions.

## What is available

The current release contains **30 people, 130 source records, 465 evidence records and 460 principles**. These are selected materials, not a complete account of anyone's thinking or latest position. See the [mentor catalog](docs/MENTORS.md) for the full inventory.

The collection includes:

- Entrepreneurship and judgment: Justin Sun, Naval Ravikant, Duan Yongping, Paul Graham, Warren Buffett, Charlie Munger, Jeff Bezos, Sam Altman and Derek Sivers.
- Technology and organizations: Elon Musk, Steve Jobs, Bill Gates, Andrew Ng, Fei-Fei Li, Jensen Huang, Satya Nadella, Lei Jun, Allen Zhang, Zhang Yiming and Ren Zhengfei.
- Learning and personal choices: Richard Feynman, James Clear, Morgan Housel, Adam Grant, Carol Dweck, Angela Duckworth, Brené Brown, Kobe Bryant, Jay Chou and Jing Tian.

Each principle connects to a short excerpt, original URL, publication date when known, passage or timestamp, review record, and editorial application limits. A source establishes what was expressed; it does not establish that a claim is true or a method will work for everyone.

Access is available through **Python, CLI, REST, MCP stdio and local Streamable HTTP**. The core retrieves evidence and guidance context without a model API key. A connected AI assistant turns that context into an answer.

## Quick start

Requires Python 3.10+ and SQLite with FTS5 support. Run from a source checkout:

```bash
git clone https://github.com/gdpu11/open-mentor.git
cd open-mentor
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[mcp]'
.venv/bin/python -m open_mentor validate
.venv/bin/python -m open_mentor doctor --mcp
.venv/bin/python -m open_mentor people
```

On Windows, use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.

Ask for a mentor explicitly, or let the library match eligible evidence:

```bash
.venv/bin/python -m open_mentor ask --person naval 'software leverage'
.venv/bin/python -m open_mentor ask 'How can I earn my first million?' --format json
.venv/bin/python -m open_mentor ask '用OpenMentor帮我看看，怎么赚自己的第一个100w'
```

Many curated summaries, application steps and topic rules are currently in Chinese. English names and queries are supported through token matching and a limited set of explicit topic rules; the English README does not imply full English-language corpus coverage. Your AI can explain the retrieved material in your preferred language while retaining citations.

For money-related questions, the response identifies missing assumptions such as currency, time horizon, resources, and the distinction between revenue, profit, income and net worth. Retrieved principles do not guarantee financial results.

## Connect through MCP

Generate a configuration using the Python environment and absolute paths of your installation:

```bash
.venv/bin/python -m open_mentor mcp-config --format codex
# For clients using the mcpServers JSON format:
.venv/bin/python -m open_mentor mcp-config --format json
```

Add the generated entry to your client's MCP settings and reconnect. These commands print configuration; they do not overwrite client settings. `doctor --mcp` starts a real stdio client and checks initialization, tool discovery and a guidance request from outside the checkout directory.

The default server command is `python -m open_mentor mcp`. A local Streamable HTTP server is also available:

```bash
.venv/bin/python -m open_mentor mcp --transport streamable-http --port 8766
```

Connect to `http://127.0.0.1:8766/mcp`. The server binds to loopback; public hosting and account authentication are outside this release.

| Tool | Purpose |
| --- | --- |
| `ask_mentor` | Resolve a full request, select or match a mentor, and retrieve cited guidance context. |
| `list_people` | List people, aliases and usable evidence counts. |
| `search_knowledge` | Search a person's principles and evidence. |
| `get_evidence` | Read an excerpt, locator, source and verification state. |
| `get_source` | Read provenance, redistribution limits and update status. |
| `prepare_guidance` | Retrieve guidance context for an explicitly selected person. |

Tools are read-only and return structured results plus compatible text. The calling AI should name the selected mentor and selection reason, cite the returned evidence IDs and URLs, and distinguish quotations, editorial guidance and its own inference. See [MCP details](docs/MCP.md) for configuration and response examples.

For a follow-up, pass the original question and relevant facts in `situation`. Pass `person` as well when retaining a mentor. The library does not store chat history; a context-free follow-up returns `needs_context`.

## Evidence and updates

Default guidance uses reviewed evidence whose original expression has been checked and whose source is eligible. Pending, disputed, retracted, changed or unavailable material is excluded. Explicitly allowing reviewed secondary sources preserves their attribution and verification limits.

```bash
.venv/bin/python -m open_mentor check naval-specific
.venv/bin/python -m open_mentor status
# After inspecting the stored revision and its context:
.venv/bin/python -m open_mentor accept-revision naval-specific <sha256> --reviewer 'reviewer-name'
```

Change detection checks registered sources, stores local revisions and pauses affected citations. It does not discover every new interview or X post. Source acceptance does not promote pending evidence into reviewed knowledge. Corrupt review state fails closed.

The optional media workflow supports yt-dlp captions/audio, local transcription, resumable chunks and review aids. Machine transcripts remain pending. In particular, Justin Sun's long Alan interview and William interviews have local machine transcripts, but only specifically reviewed clips are admitted as original evidence; the complete transcripts have not been checked line by line. See [transcript scope](docs/TRANSCRIPTS.md).

Source checkouts use `.open-mentor/` for local state; installed packages use `~/.open-mentor/`. Global `--data-dir` and `--state-dir` options go before the subcommand. Raw media, full transcripts, source snapshots and local client configuration stay out of Git.

## Other interfaces and checks

```bash
.venv/bin/python -m open_mentor serve --port 8765
curl 'http://127.0.0.1:8765/v1/search?person=naval&q=software'
```

REST endpoints include `GET /v1/people`, `/v1/search`, `/v1/evidence/<id>`, `/v1/sources/<id>`, and `POST /v1/ask` and `/v1/context`. REST on port 8765 is separate from MCP on port 8766.

```python
from contextlib import closing
from open_mentor.library import Library

with closing(Library()) as library:
    context = library.ask("How can I earn my first million?")
    print(context["status"], context.get("person"))
```

Run the existing checks with the MCP extra installed:

```bash
.venv/bin/python -m open_mentor validate
.venv/bin/python -m open_mentor doctor --mcp
.venv/bin/python -m unittest discover -s tests -v
```

Retrieval uses Chinese/English tokens and SQLite FTS5/BM25 with explicit topic expansion. There are no embeddings, unrestricted semantic routing, automatic conflict adjudication or multi-user editing backend. `ready` means relevant eligible material was found, not that the user's goal is achievable. The fixed regression scenarios are documented in [usage cases](docs/AUTO-SELECTION-CASES.md).

## License

Code and original annotations use the [MIT License](LICENSE). Third-party excerpts and source materials retain their original rights; see [data licensing boundaries](DATA-LICENSE.md) and each source's `rights` record. Public availability does not grant full-text redistribution rights.
