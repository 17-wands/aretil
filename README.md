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
model2vec, anthropic) and the dev tools (pytest, ruff).

### TypeScript app layer

```bash
cd app
npm install
```

## Usage

### Build the demo database

```bash
# Build the demo database: schema, fixtures, entity resolution, embeddings
.venv/bin/python scripts/build_db.py

# Regenerate the demo fixtures from SEC EDGAR (optional — fixtures are committed)
.venv/bin/python scripts/generate_data.py
```

### Demo Surface 1: Claude Desktop with MCP (Primary)

1. Ensure the database is built:
   ```bash
   .venv/bin/python scripts/build_db.py
   ```

2. Copy `mcp/mcp_config.json` to your Claude Desktop config directory:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

3. In the JSON, update the `cwd` path to your aretil project directory:
   ```json
   "cwd": "/Users/YOUR_USERNAME/Projects/aretil"
   ```

4. Restart Claude Desktop. The `aretil` MCP server will connect and expose six tools:
   - `search_matters` — semantic search over matter descriptions
   - `find_relevant_timekeepers` — find timekeepers by matter or text query
   - `get_client_history` — all matters for a client (including subsidiaries)
   - `get_market_terms` — aggregate statistics by deal type
   - `get_timekeeper_history` — a timekeeper's matter history
   - `assemble_pitch_context` — one-call pitch data (matters + timekeepers + terms)

5. Paste an RFP and ask Claude to draft a pitch.

### Demo Surface 2: TypeScript Web App (Backup)

**Terminal 1: Start the Node API server**
```bash
cd app
npm install  # if not done already
npm run build
node dist/server/src/index.js
```
The API server runs on `http://localhost:3001`.

**Terminal 2: Start the Vite dev server**
```bash
cd app
npm run dev
```
The web app runs on `http://localhost:5173`.

**In your browser:**
1. Open `http://localhost:5173`
2. Paste an RFP (sample below) into the "RFP" panel
3. Click "Generate pitch"
4. View the drafted pitch in the "Pitch" panel
5. Click "Copy to clipboard" to copy the pitch

**Sample RFP:**
```
We are seeking a law firm to advise on a healthcare M&A transaction.
The target is a mid-sized medical devices company specializing in
surgical instruments. The deal is expected to close in Q4 2026.
We need a firm with significant healthcare M&A experience, regulatory
expertise, and a strong track record representing targets in similar
transactions. Timeline is tight — response due by EOW.
```

### Demo Workflows

See [DEMO.md](DEMO.md) for detailed walkthroughs of:
- RFP-to-Pitch (main workflow)
- Timekeeper Bio/CV (secondary workflow)
- Entity-Resolution "wow" moment (data layer validation)

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
