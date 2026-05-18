# Architecture — `aretil` Prototype

Companion to [PRD.md](PRD.md). This document describes *how* the prototype is
built. Scope is the prototype only; a forward-looking production architecture is
sketched in §10 and is explicitly out of scope for the build.

> **Disclaimer — proof of concept.** `aretil` is an unaffiliated proof of concept
> built for product exploration. It is not production software, and is not
> affiliated with, authorized by, or endorsed by Litera or any other company named
> in these documents. It uses synthetic data only — no real firm, client, or
> personal data — and is built entirely from publicly available information, with
> no confidential or insider knowledge. Competitive references reflect public
> information at a point in time and may be incomplete or out of date. Provided
> as-is, without warranty.

---

## 1. System Overview

```
                          ┌─────────────────────────────┐
  scripts/generate_data ─▶ │   Synthetic fixtures        │
  (Claude-assisted)        │   matters / clients /       │
                           │   timekeepers / parties     │
                           └──────────────┬──────────────┘
                                          │  scripts/build_db
                                          ▼
                  ┌──────────────────────────────────────────────┐
                  │            DuckDB substrate                   │
                  │  • relational tables (+ VARIANT fields)        │
                  │  • Lance dataset — matter-description vectors  │
                  │  • resolved_parties — Splink entity resolution │
                  │  • SQL macros  ◀── the one canonical tool layer│
                  └───────────┬───────────────────────┬──────────┘
                              │                       │
              DuckDB MCP extension          TypeScript web app — a
              exposes macros as             thin Node API opens the
              MCP tools                     DuckDB file, runs macros
                              │                       │
                              ▼                       ▼
                     ┌─────────────────┐      ┌─────────────────┐
                     │  Claude Desktop │      │  TypeScript SPA │
                     │  (primary demo) │      │ (backup surface)│
                     └────────┬────────┘      └────────┬────────┘
                              │                        │
                              └────────┬───────────────┘
                                       ▼
                              Claude API — drafts the
                              pitch / bio from tool results
```

The two surfaces share **one** tool layer: parameterized SQL macros in DuckDB.
Claude Desktop reaches them through the DuckDB MCP extension; the TypeScript web
app's Node API opens the same DuckDB file and calls the identical macros. There is
no second implementation of tool logic to keep in sync.

## 2. Design Principles

- **DuckDB is the entire data substrate.** Relational tables, vector search, and
  the entity-resolution backend all live in one DuckDB file — no separate vector
  DB or data service. The only other process is a thin Node API for the web app.
- **SQL macros are the single source of truth for tools.** A tool is a named,
  parameterized SQL macro. The MCP server and the web UI both invoke the same
  macros — tool behavior cannot drift between surfaces.
- **MCP-native.** The data layer is designed to be queried by an AI agent over MCP
  from day one — the access pattern the broader market is converging on.
- **Local and lightweight.** The whole prototype runs on a laptop. The only
  external dependency at demo time is the Claude API for drafting.
- **Inspectable, not black-box.** Every tool call resolves to visible SQL — a
  deliberate contrast to opaque legal-AI products.

## 3. Components

### 3.1 Data layer — DuckDB

- **DuckDB 1.5.x** for the prototype, to use the native `VARIANT` type for
  semi-structured matter fields. **DuckDB 1.4 LTS** is the stated production target
  (supported through Sept 2026); the prototype notes but does not depend on this.
- `VARIANT` holds deal-type-specific fields so a single `matters` table cleanly
  carries both an M&A matter (buyer / seller / deal value) and a litigation matter
  (venue / causes of action) without a wall of nullable columns.

### 3.2 Entity resolution — Splink

- **Splink** (MIT; probabilistic record linkage that runs *on* DuckDB) reconciles
  party and counsel name variants — "Latham", "Latham & Watkins", "L&W" → one
  canonical entity.
- Output is a `resolved_parties` table plus an alias→canonical map, materialized at
  build time. `search_matters` joins through it so a query phrased with any variant
  matches matters recorded under any other.

### 3.3 Semantic search — Lance

- Matter descriptions are embedded and stored as a **Lance** dataset, queried from
  within DuckDB via the Lance extension. Vector, structured, and full-text
  filtering happen in one SQL dialect.
- Embeddings are produced by a local `sentence-transformers` model (no API
  dependency at build time). DuckDB's `vss` extension is the fallback if the Lance
  extension is unavailable.

### 3.4 Tool layer — SQL macros

The canonical tools, defined once in `macros/tools.sql`. See §5 for signatures.

### 3.5 MCP server — DuckDB MCP extension

The DuckDB MCP extension exposes the SQL macros as MCP tools. Claude Desktop is
configured to launch it against the built `aretil.duckdb` file. This is the primary
demo surface and the strategically on-message one ("firm data as an MCP server").

### 3.6 Web app — TypeScript

A simple TypeScript web app: paste an RFP, get a pitch. It has two parts — a Vite
single-page frontend (`app/web/`) and a thin Node API (`app/server/`). The Node API
opens `data/aretil.duckdb` via DuckDB's Node bindings, exposes each SQL macro as a
tool, and runs the Claude API tool-use loop. The frontend is kept minimal and
framework-light on purpose, to keep room to evolve the UI. This is the backup
surface if live MCP setup fails in the meeting.

### 3.7 AI layer — Claude API

Drafting (pitch language, bio prose) and RFP intent parsing use the Claude API —
`claude-opus-4-7` for quality, `claude-sonnet-4-6` where latency matters. Claude
does no data retrieval itself; it only calls tools and synthesizes their results.

### 3.8 Synthetic data generator

`scripts/generate_data.py` uses the Claude API to generate the fixtures described
in PRD §7 — a fictional firm, 50–100 matters, related records, and deliberate name
variants for the entity-resolution demo.

## 4. Data Model

Relational core, with `VARIANT` for type-specific matter detail.

| Table | Key columns |
|---|---|
| `clients` | `client_id`, `name`, `industry`, `parent_client_id` (self-ref for parent/subsidiary) |
| `matters` | `matter_id`, `name`, `client_id`→`clients`, `practice_area`, `deal_type`, `jurisdiction`, `deal_value`, `year`, `firm_role` (lead counsel / co-counsel / advisor), `description`, `attributes` (`VARIANT`) |
| `timekeepers` | `timekeeper_id`, `name`, `title`, `practice_group`, `years_experience` |
| `matter_timekeepers` | `matter_id`→`matters`, `timekeeper_id`→`timekeepers`, `role_on_matter` |
| `parties` | `party_id`, `matter_id`→`matters`, `raw_name`, `party_type` (counterparty / opposing_counsel / advisor), `side` |
| `resolved_parties` | `canonical_party_id`, `canonical_name` — produced by Splink |
| `party_resolution` | `party_id`→`parties`, `canonical_party_id`→`resolved_parties` |
| `tags` | `tag_id`, `tag_type` (industry_code / deal_subtype / governing_law / regulatory), `value` |
| `matter_tags` | `matter_id`→`matters`, `tag_id`→`tags` |
| `matter_embeddings` | `matter_id`→`matters`, `embedding` (Lance dataset) |

## 5. MCP Tool Catalog

Each tool is a SQL macro. Names are stable across the MCP server and the web UI.

| Tool | Parameters | Returns |
|---|---|---|
| `search_matters` | `query_text`, `practice_area?`, `industry?`, `deal_type?`, `jurisdiction?`, `min_value?`, `max_value?` | Ranked matters — semantic similarity over descriptions combined with structured filters; joins through `party_resolution` so party-name variants match. |
| `find_relevant_timekeepers` | `matter_ids[]` *or* `query_text` | Timekeepers ranked by depth of relevant matter experience, with their role on each. |
| `get_client_history` | `client_name` | All matters for a client, including subsidiaries via `parent_client_id`. |
| `get_market_terms` | `deal_type`, `practice_area?`, `jurisdiction?` | Aggregate "what's market" stats over comparable matters (deal-value distribution, common terms). |
| `get_timekeeper_history` | `timekeeper_id` *or* `name` | A timekeeper's full matter history with roles and matter detail. |
| `assemble_pitch_context` | RFP intent params (practice area, industry, deal type, jurisdiction, value band) | One bundle — relevant matters + ranked timekeepers + market terms — for one-call pitch drafting. |

RFP parsing (free text → structured intent) is a Claude reasoning step, not a tool.

## 6. Data Flow

### 6.1 RFP-to-Pitch

1. User pastes an inbound RFP into Claude Desktop (or the web UI).
2. Claude parses the RFP into structured query intent (practice area, industry,
   deal type, jurisdiction, value band).
3. Claude calls `assemble_pitch_context` (or `search_matters` +
   `find_relevant_timekeepers` + `get_market_terms` individually).
4. The macro(s) run against DuckDB — semantic search via Lance, structured
   filters, party joins through `party_resolution`.
5. Claude drafts the pitch from the returned context: relevant-matter list,
   highlighted timekeepers, 2–3 paragraphs of pitch language. Output: markdown.

### 6.2 Timekeeper Bio / CV

1. User asks for a bio of timekeeper *X*, optionally scoped to a target context.
2. Claude calls `get_timekeeper_history(X)`.
3. Claude ranks that history for relevance to the target context (reasoning step;
   may call `search_matters` to scope the context).
4. Claude drafts a tailored CV — role, practice group, experience summary, curated
   representative matters. Output: markdown.

## 7. Tech Stack & Versions

| Component | Choice | Version |
|---|---|---|
| Data/ML core language | Python | 3.11+ |
| App-layer language | TypeScript / Node | Node 20+ |
| Data substrate | DuckDB | 1.5.x (prototype); 1.4 LTS = production target |
| Entity resolution | Splink | 4.x |
| Vector search | DuckDB Lance extension (`vss` extension as fallback) | current |
| Embeddings | `sentence-transformers` (local) | current |
| AI layer | `anthropic` SDK (Python core + Node app) — `claude-opus-4-7`, `claude-sonnet-4-6` | current |
| MCP | DuckDB MCP extension | current |
| Web frontend | Vite + TypeScript SPA | current |
| Web API | Node + TypeScript (thin); DuckDB Node bindings (`@duckdb/node-api`) | current |

Versions are pinned in `pyproject.toml` (Python core) and `app/package.json`
(TypeScript app) at build time.

## 8. Proposed Repo Layout

```
aretil/
  data/
    fixtures/          # generated synthetic records (JSON/CSV)
    aretil.duckdb      # built database — gitignored
  schema/
    schema.sql         # table DDL
  macros/
    tools.sql          # canonical SQL macros = the tool layer
  mcp/
    mcp_config.json    # DuckDB MCP extension / Claude Desktop config
  app/                 # TypeScript web app
    web/               # Vite + TypeScript SPA — the frontend
    server/            # thin Node API — opens DuckDB, runs macros + Claude loop
    package.json
  prompts/
    pitch.md           # pitch-drafting prompt
    bio.md             # bio-drafting prompt
  scripts/
    generate_data.py   # Claude-assisted synthetic data generation
    build_db.py        # load fixtures, embed, run Splink, install macros
  pyproject.toml
  README.md
```

## 9. Running the Prototype

1. `python scripts/generate_data.py` — generate synthetic fixtures into
   `data/fixtures/`.
2. `python scripts/build_db.py` — load fixtures into DuckDB, build matter
   embeddings (Lance), run Splink to populate `resolved_parties`, install the SQL
   macros. Produces `data/aretil.duckdb`.
3. **Primary surface:** configure Claude Desktop to launch the DuckDB MCP server
   against `data/aretil.duckdb` (per `mcp/mcp_config.json`).
4. **Backup surface:** `cd app && npm install && npm run dev` — starts the Node
   API and the Vite frontend.
5. `ANTHROPIC_API_KEY` must be set for drafting.

## 10. Path to Production (out of prototype scope)

The prototype proves the wedge; the production system would replace the
weekend-grade pieces with durable infrastructure:

- **Twenty CRM** as the CRM / entity backbone — modern, MCP-native, custom objects
  for matters/timekeepers/parties. *AGPL-3.0; see §11.*
- **OpenContracts** (MIT) as the document/matter knowledge layer for ingesting and
  annotating real deal documents.
- A real **data-engineering pipeline** — Splink + spaCy + LexNLP — for ingesting,
  normalizing, and tagging firm data from source systems.
- **Real source-system connectors** — Elite 3E, Aderant, iManage, NetDocuments,
  Intapp — none of which exist in the prototype.
- **DuckLake** lakehouse (v1.0, Apr 2026) for scaling the data substrate from a
  single file to a production lakehouse without a rewrite.

## 11. Licensing Notes

| Component | License | Note |
|---|---|---|
| DuckDB | MIT | Permissive. |
| Splink | MIT | Permissive. |
| Lance | Apache-2.0 | Permissive. |
| Vite | MIT | Permissive. |
| `anthropic` SDK | MIT | Permissive. |
| `sentence-transformers` | Apache-2.0 | Permissive. |
| Twenty CRM | **AGPL-3.0** | Production phase only. Offering an AGPL fork as a service triggers source-disclosure; mitigate via a commercial dual-license with Twenty, or build atop their app/extension framework. Not a prototype concern. |
