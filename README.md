# aretil

A legal experience-management data layer, exposed as an MCP server, that lets
Claude answer business-development questions against a law firm's matter,
client, and timekeeper data.

> **Proof of concept.** `aretil` is an unaffiliated PoC built from publicly
> available information — not production software, and not affiliated with or
> endorsed by any company named in this repository. See [PRD.md](PRD.md) for the
> full disclaimer.

**Status:** early prototype, built issue by issue. Work is tracked in
[GitHub issues](https://github.com/17-wands/aretil/issues); the process is in
[WORKFLOW.md](WORKFLOW.md).

## Documentation

| File | Purpose |
|---|---|
| [PRD.md](PRD.md) | Product scope, workflows, success criteria. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Components, data model, MCP tool catalog. |
| [DESIGN.md](DESIGN.md) | The design system. |
| [WORKFLOW.md](WORKFLOW.md) | The issue-driven development workflow. |
| [CLAUDE.md](CLAUDE.md) | Guide for working in this repo with Claude Code. |

## Stack

A hybrid prototype:

- **Python data/ML core** — DuckDB substrate, Splink entity resolution, local
  embeddings, the SQL-macro tool layer, and the DuckDB MCP server.
- **TypeScript/Node app layer** — the web UI and its supporting API.

## Prerequisites

- **Node.js 20+** — for the TypeScript app layer.
- **[uv](https://docs.astral.sh/uv/)** — provisions Python 3.12, which the
  data/ML core requires (DuckDB 1.5.x needs Python ≥ 3.10).

Install uv, then make sure it is on your `PATH` (the installer prints how):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

### Python data/ML core

```bash
uv python install 3.12
"$(uv python find 3.12)" -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

This installs the data/ML core dependencies (duckdb, splink,
sentence-transformers, anthropic) and the dev tools (pytest, ruff).

### TypeScript app layer

```bash
cd app
npm install
```

## Usage

The project is built issue by issue. What runs today:

```bash
# Create the DuckDB database and apply the schema
.venv/bin/python scripts/init_db.py
```

Synthetic data, the MCP server, and the web app arrive in later issues.

## Checks

Python data/ML core:

```bash
.venv/bin/ruff check .
.venv/bin/pytest
```

TypeScript app layer (run from `app/`):

```bash
npm run build
npm test
npm run test:e2e
npm run jobs:validate
```

## Notes for contributors

- DuckDB files that store `VARIANT` columns must be created with
  `storage_compatibility_version = v1.5.0` — `scripts/init_db.py` does this.
  Reading an existing file needs no special configuration.
- Work follows [WORKFLOW.md](WORKFLOW.md): one branch and one PR per issue,
  worked in backlog order.
