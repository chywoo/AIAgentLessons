# AGENTS.md

This file is for coding agents (Codex/Claude/Cursor/etc.). Keep it strict and actionable.

## Overview

<!-- AGENTSGEN:START section=overview -->
- **Project:** AIAgentStudy
- **Stack:** Python 3.12+, OpenAI SDK
- **Purpose:** Educational study project demonstrating a simple AI agent with tool calling
- Keep changes small and verifiable.
<!-- AGENTSGEN:END section=overview -->

<!-- AGENTSGEN:START section=repo_context -->
### Repo context

- Project: AIAgentStudy
- Stack: Python 3.12+, OpenAI SDK
- Root: `.`
- Start with:
  - `README.md`
- CI: `.github/workflows/`
- Key directories:
  - `00.simple-agent/` — agent implementation (tools, config, runner, test)
  - `prompt/` — agent execution specification (execspec.md)
<!-- AGENTSGEN:END section=repo_context -->

<!-- AGENTSGEN:START section=guardrails -->
### Guardrails

- Work only within the requested scope and preserve local conventions.
- Prefer focused changes; use 300 changed lines as a review signal, not a hard limit.
- Never discard user files, handwritten content, migrations, or data.
- Never hardcode tokens/keys. Never print secrets; document required environment-variable names.
- Run side-effecting or destructive operations only with existing authorization.
- Before changing these areas, confirm intent unless the current task already authorizes it:
  - schema changes
  - auth/payments/crypto
  - deletions or large refactors
  - new build tooling/CI changes
  - new major dependencies
- A change is complete when behavior, relevant tests, and affected docs agree.
<!-- AGENTSGEN:END section=guardrails -->

<!-- AGENTSGEN:START section=workflow -->
### Workflow

1. Read the nearest instructions and reproduce the current behavior.
2. Implement the smallest coherent change and keep generated output reviewable.
3. Run the narrowest useful check, then the full project checks before finalizing.
4. Update docs and contracts when behavior changes.
5. Report changed behavior, verification, and any material limitation.
<!-- AGENTSGEN:END section=workflow -->

<!-- AGENTSGEN:START section=verification -->
### Verification

- Run the repository's full test suite or the closest documented equivalent.
- If a check cannot run, state why and name the remaining command.
<!-- AGENTSGEN:END section=verification -->

<!-- AGENTSGEN:START section=stack -->
## Stack

- **Language:** Python 3.12+
- **Runtime:** CPython 3.12+
- **Dependencies:** `openai>=3.17.0`
- **Tooling:** `uv` (lockfile: `uv.lock`)
- **Entry points:** `main.py`, `00.simple-agent/main.py`
<!-- AGENTSGEN:END section=stack -->

<!-- AGENTSGEN:START section=style -->
### Style (static)

- Match existing naming, formatting, and module boundaries.
- Prefer direct code and explicit errors over new abstractions.
- Validate external input at system boundaries.
- Keep logs free of secrets and personal data.
- Add types or comments where they clarify a public or non-obvious contract.
- Reuse current dependencies unless a new one materially reduces complexity.
<!-- AGENTSGEN:END section=style -->

## Rules Of Engagement

<!-- AGENTSGEN:START section=rules -->
**DO**
- Prefer small diffs.
- Add or update tests when behavior changes.
- Run repo checks before finishing.

**DON'T**
- Do not rewrite unrelated code.
- Do not refactor without confirming intent.
- Do not commit secrets or local env files.

**If uncertain**
- Ask a short clarifying question before making big changes.

**Warnings**
- (none)
<!-- AGENTSGEN:END section=rules -->

## Commands

<!-- AGENTSGEN:START section=commands -->
## Commands

- **Install:** `pip install -e .` or `uv sync`
- **Run agent demo:** `python 00.simple-agent/main.py`
- **Run tests:** `python 00.simple-agent/test.py`
- **Lint:** (not configured)
- **Build:** (not configured)
<!-- AGENTSGEN:END section=commands -->

<!-- AGENTSGEN:START section=repo_structure -->
## Repo Structure

```
.
├── AGENTS.md                 # Agent contract and guidelines
├── README.md                 # Project overview and getting started
├── RUNBOOK.md                # Operational runbook
├── main.py                   # Root entry point (hello world)
├── pyproject.toml            # Project metadata and dependencies
├── uv.lock                   # Dependency lockfile
├── .gitignore                # Ignored files
├── .venv                     # Virtual environment
├── .idea                     # IDE configuration
├── 00.simple-agent/          # Simple agent implementation
│   ├── agent.py              # Agent runner with tool calling loop
│   ├── config.py             # Agent configuration
│   ├── tools.py              # Tool definitions (calculator, time)
│   ├── main.py               # Agent demo script
│   └── test.py               # Test script
└── prompt/
    └── execspec.md           # Agent execution specification
```
<!-- AGENTSGEN:END section=repo_structure -->

## Output Protocol

<!-- AGENTSGEN:START section=output_protocol -->
When you finish work, include:
- Summary (1-3 bullets)
- Files changed (list paths)
- Verification (exact commands to run)
<!-- AGENTSGEN:END section=output_protocol -->

<!-- graft:start -->
## Graft — repo context graph

This repo is indexed in `graft/`: small linked markdown nodes that explain each
system and carry exact file:line spans, kept in sync with the code through git.

For ANY task here — understanding how something works, finding where code lives,
or scoping a change — get context from the graph before grepping or opening
source files. Re-ask freely (it's cheap) and reuse literal identifiers you
already have (symbol, error string, file name) as the query. New to this repo?
Run `graft map` first — a token-budgeted orientation (dir clusters, hubs,
hotspots), no LLM, no key.

- Run `graft ask "<your question>" --source` → ranked nodes with the relevant
  code spans inlined (each hit's ≤8-line crux by default; `--full` for whole
  definitions when the crux isn't enough). Match the tool to the task shape:
  for understanding or editing, the top node IS the answer — cite its
  `covers:` file:line spans and edit straight from `--source`. For
  exhaustive tasks ("every occurrence / every caller of this pattern"), ranked
  results are top-N, not complete — run `graft grep "<literal>"` instead
  (exhaustive over indexed files, grouped by enclosing symbol), falling back
  to raw `grep -rn` only for unindexed files.
- `graft skeleton <file>` → every definition's signature + span, ~10× cheaper
  than reading the file; use it to skim an API surface.
- `graft callers <symbol>` gives precomputed, exact edges — who calls this.
  Add `--direction out` for what it calls, or `--depth N` to walk
  transitively for the full blast radius. For structural questions, skip
  ranking and use this directly.
- Or browse: `graft/INDEX.md` lists every node; follow the links.
- Monorepos and folders of multiple repos rank fairly across sub-projects —
  hits carry `[scope/]` labels naming which one they're from. Narrow with
  `graft ask "<task>" --in <scope>/` once you know where you're working.

If a returned span is truncated ("+N more lines"), open the file at that exact
range before finalizing. Only open source files when a node genuinely lacks a
needed detail, and then at the exact file:line the node points to — never
re-read whole files.

After big code changes, refresh the graph with `graft build` (deterministic,
no API key, $0).
<!-- graft:end -->
