# DeepMentor

[English](README.en.md) | [简体中文](README.md) | [Contributing](CONTRIBUTING.md)

**Evidence-backed mentors for thoughtful decisions and practical action.**

DeepMentor is an open-source knowledge library designed to bring verified public expressions, original citations, and review history into your AI assistant. When navigating business strategy, leadership, career transitions, learning, and life choices, it helps you clarify constraints, examine evidence boundaries, and take practical action. Currently features 30 mentors; see the full inventory in the [mentor catalog](docs/MENTORS.md).

## Core Principles

1. **Grounded in Reality**: Users consult with real problems, concrete goals, and practical constraints.
2. **Flexible Routing**: Explicitly choose a mentor, or let the library automatically match one based on eligible, reviewed evidence across the entire corpus.
3. **Traceable Citations**: Returns reviewed statements, original publication links, precise locators (passages, timestamps), and review scopes.
4. **Actionable Feedback Loop**: The calling AI assistant analyzes situational fit and outlines reversible next steps with stopping/validation criteria.
5. **Community-Driven**: Everyone can contribute mentors, primary sources, counterexamples, shifts in thinking, and applicability boundaries.

### Quality of Analysis Defines "Deep"

"Deep" does not mean ungrounded generative hallucinations or opaque embeddings. It is defined by a rigorous, step-by-step reasoning chain:

$$\text{User Situation} \longrightarrow \text{Critical Question} \longrightarrow \text{Evidence \& Applicability} \longrightarrow \text{Actionable Advice} \longrightarrow \text{Validation \& Stopping Criteria}$$

- **Clear Division of Roles**: DeepMentor strictly handles knowledge retrieval and evidence integrity (provenance, locators, version consistency, exclusion of unverified/changed sources). The calling AI assistant performs situational reasoning and answers the user.
- **Honest Scoping**: No unneeded model dependencies, and no false promises of unverified real-time scraping or multi-agent debate.

## Build Your Mentor Library Together

Who has helped you think more clearly, build something useful, or make a difficult decision? Help others learn from their publicly shared work.

- [Suggest a mentor or source](https://github.com/gdpu11/deepmentor/issues/new?template=add-mentor.md). A primary-source link and a specific passage are a useful contribution; coding is optional.
- [Correct an attribution or evidence record](https://github.com/gdpu11/deepmentor/issues/new?template=correct-evidence.md). Context, counterexamples and changes of mind matter.
- [Contribute a knowledge pack, translation or code](CONTRIBUTING.md). Start with a small, verifiable contribution. Unreviewed material remains pending.

## What is Available

The collection currently contains **30 people, 130 source records, 465 evidence records, and 460 principles**.

- Entrepreneurship and judgment: Justin Sun, Naval Ravikant, Duan Yongping, Paul Graham, Warren Buffett, Charlie Munger, Jeff Bezos, Sam Altman, and Derek Sivers.
- Technology and organizations: Elon Musk, Steve Jobs, Bill Gates, Andrew Ng, Fei-Fei Li, Jensen Huang, Satya Nadella, Lei Jun, Allen Zhang, Zhang Yiming, and Ren Zhengfei.
- Learning and personal choices: Richard Feynman, James Clear, Morgan Housel, Adam Grant, Carol Dweck, Angela Duckworth, Brené Brown, Kobe Bryant, Jay Chou, and Jing Tian.

Each principle connects to a short excerpt, original URL, publication date when known, locator/timestamp, review record, and editorial application limits. See the [mentor catalog](docs/MENTORS.md), [30-mentor audit](docs/EXPANSION-30-AUDIT.md), and [transcript review log](docs/TRANSCRIPTS.md).

## Quick Start

Requires Python 3.10+ and SQLite with FTS5 support. Run from a source checkout:

```bash
git clone https://github.com/gdpu11/deepmentor.git
cd deepmentor
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[mcp]'
.venv/bin/deepmentor validate
.venv/bin/deepmentor doctor --mcp
.venv/bin/deepmentor people
```

On Windows, use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.

Ask for a mentor explicitly, or let the library match eligible evidence:

```bash
.venv/bin/deepmentor ask --person naval 'software leverage'
.venv/bin/deepmentor ask 'How can I earn my first million?' --format json
.venv/bin/deepmentor ask '用DeepMentor帮我看看，怎么赚自己的第一个100w'

# Legacy open-mentor command remains fully supported:
.venv/bin/open-mentor ask '用OpenMentor帮我看看，怎么赚自己的第一个100w'
```

Natural query parsing seamlessly handles both `DeepMentor` and `OpenMentor` prefixes without biasing candidate selection or ranking.

## Connect Through MCP

Generate an MCP client configuration using the active environment and absolute paths:

```bash
.venv/bin/python -m deepmentor mcp-config --format codex
# For clients using the mcpServers JSON format:
.venv/bin/python -m deepmentor mcp-config --format json
```

The default server command is `python -m deepmentor mcp`. A local Streamable HTTP server is also available:

```bash
.venv/bin/python -m deepmentor mcp --transport streamable-http --port 8766
```

Connect to `http://127.0.0.1:8766/mcp`. See [MCP documentation](docs/MCP.md) for full configuration, legacy migration, and tool definitions.

| Tool | Purpose |
| --- | --- |
| `ask_mentor` | Resolve a full request, select or match a mentor, and retrieve cited guidance context. |
| `list_people` | List people, aliases, corpus size, and usable evidence counts. |
| `search_knowledge` | Search a person's principles and evidence. |
| `get_evidence` | Read an excerpt, locator, source, and verification state. |
| `get_source` | Read provenance, redistribution limits, and update status. |
| `prepare_guidance` | Retrieve guidance context for an explicitly selected person. |

Tools are read-only and return structured results plus compatible text. The calling AI evaluates the user's situation, follows the reasoning framework (`Situation → Question → Evidence → Action → Verification`), and cites specific evidence IDs and URLs.

## Backward Compatibility & Migration

1. **Command and Import Compatibility**:
   - New commands: `deepmentor` and `python -m deepmentor`.
   - Legacy commands: `open-mentor` and `python -m open_mentor` remain fully functional and share the exact same implementation.
   - Python code importing `open_mentor` issues a `DeprecationWarning` and forwards to `deepmentor`.
2. **Review State and Deactivation Protection**:
   - State directory priority: **Explicit `--state-dir` > New `.deepmentor` > Legacy `.open-mentor`**.
   - If only `.open-mentor` exists, it is loaded automatically. Deactivated sources and review statuses are strictly preserved.
   - If both `.deepmentor` and `.open-mentor` exist with data, DeepMentor raises a `StateConflictError` rather than silently merging or overwriting state.
   - Keeping the legacy directory is fully supported. If renaming it, stop writers, back up the data, ensure the target does not exist, and update any explicitly configured paths:
     ```bash
     test ! -e .deepmentor && mv .open-mentor .deepmentor # inside repository checkout
     # or
     test ! -e "$HOME/.deepmentor" && mv "$HOME/.open-mentor" "$HOME/.deepmentor" # in home directory
     ```
3. **MCP Registration Migration**:
   - Update your client's entry key from `openmentor` to `deepmentor` to avoid duplicate tool registrations.

## Repository Address Migration

The project is now DeepMentor at [gdpu11/deepmentor](https://github.com/gdpu11/deepmentor). Existing checkout directories can keep their names; update the remote URL:

```bash
git remote set-url origin https://github.com/gdpu11/deepmentor.git
```

## Running Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## License

Code and original annotations use the [MIT License](LICENSE). Third-party excerpts and source materials retain their original rights; see [data licensing boundaries](DATA-LICENSE.md) and each source's `rights` record.
