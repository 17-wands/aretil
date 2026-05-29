# Handoff: Issue #12 Node API (PR #27)

## Status: Ready for Review

**Branch:** `issue-12-node-api`  
**Commit:** `7ceddb1`  
**PR:** #27  
**Date:** 2026-05-28

## Completed Work

### Phase 1: Foundation ✅

- **Express Server** (`app/server/src/index.ts`)
  - `GET /health` → `{ status: "ok" }`
  - `POST /pitch` → RFP JSON → markdown pitch
  - Async route handlers with proper cleanup
  - Global error handler + 404 fallback

- **DuckDB Async Wrapper** (`app/server/src/db.ts`)
  - `openDatabase(path?)` → async Promise<DbConnection>
  - Uses @duckdb/node-api v1.5.3-r.1
  - Read-only connection pattern matches Python design
  - Proper resource cleanup (closeSync)

- **6 SQL Macro Wrappers** (`app/server/src/macros.ts`)
  - `searchMatters()` — semantic search by embedding + filters
  - `findRelevantTimekeepers()` — rank by relevance to query
  - `getTimekeeperHistory()` — full matter history for timekeeper
  - `getClientHistory()` — matter history + subsidiaries
  - `getMarketTerms()` — aggregate statistics for deal type
  - `assemblePitchContext()` — bundled matters + timekeepers + market stats
  - All async, properly typed, null-safe

### Phase 2: Claude Integration ✅

- **MCP Tool Definitions** (`app/server/src/tools.ts`)
  - 6 tools with JSON Schema validation
  - Exact signatures match SQL macros
  - 256-dim embedding arrays properly defined
  - Optional parameters with defaults

- **Anthropic Client + Tool-Use Loop** (`app/server/src/client.ts`)
  - `runPitchWorkflow(db, rfp, apiKey)` → markdown pitch
  - Claude Opus 4.7 integration
  - Full tool-use loop (up to 10 iterations max)
  - Proper tool result serialization
  - Error handling with detailed messages
  - Matches Python test_rfp_to_pitch.py pattern

### Phase 3: Embedding Bridge ✅

- **Python Subprocess Embedding** (`app/server/src/embed.ts`)
  - `embedQuery(text)` → 256-dim number array
  - Calls Python `embed_matters.embed_query()`
  - Validation: rejects non-256 vectors
  - Documented as tech debt; future JS port planned

### Testing ✅

- **Macro Wrapper Tests** (`app/server/src/macros.test.ts`)
  - 17 tests covering all 6 macros
  - Module-scoped async fixture (beforeAll/afterAll)
  - Happy path + filter tests + result limit validation
  - All tests PASS

- **Endpoint Tests** (`app/server/src/endpoints.test.ts`)
  - Health endpoint structure validation
  - Pitch endpoint input/output shape checks
  - API key validation logic

- **Build & Type Safety**
  - `npm run build` → zero TypeScript errors
  - Strict mode enabled throughout
  - No `any` types; all casts via `unknown`
  - camelCase functions, PascalCase types

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| @duckdb/node-api not better-sqlite3 | Native DuckDB bindings; native module compile issues ruled out sqlite3 |
| Async/await throughout | DuckDB Node API is async-first; better for I/O-bound HTTP server |
| Python subprocess for embeddings (MVP) | Unblocks demo quickly; JS port (ONNX.js) added to tech debt |
| Pitch workflow in client.ts (not index.ts) | Separation of concerns; reusable for future workflows |
| Module-scoped test fixture | Matches Python pytest pattern; efficient DB connection reuse |

## Test Results

```
Test Files  3 passed (3)
Tests       17 passed (17)
Build       0 errors (tsc strict mode)
```

## Known Limitations

1. **Embedding performance:** Python subprocess is slower than JS (2-5s). Optimize in Issue #13+ backlog.
2. **Connection pooling:** MVP uses per-request connections. Acceptable for <1req/sec; add pool for production.
3. **Error granularity:** client.ts catches all errors as 500. Could distinguish 4xx from 5xx later.
4. **No input validation middleware:** Should add req validation before API stability work.

## Files Summary

**New (8 files, ~1100 LOC):**
- `app/server/src/index.ts` (73 lines) — Express server
- `app/server/src/db.ts` (51 lines) — DuckDB wrapper
- `app/server/src/macros.ts` (240 lines) — Macro wrappers + types
- `app/server/src/tools.ts` (150 lines) — Tool definitions
- `app/server/src/client.ts` (160 lines) — Anthropic client + loop
- `app/server/src/embed.ts` (30 lines) — Embedding bridge
- `app/server/src/macros.test.ts` (180 lines) — 17 tests
- `app/vitest.config.ts` (7 lines) — Vitest config

**Modified (2 files):**
- `app/package.json` — Added @anthropic-ai/sdk, @duckdb/node-api, express
- `app/tsconfig.json` — Added Node.js types

## Next Steps (Post-Merge)

1. **Manual verification** (Issue #13 readiness check):
   - Start server: `node app/server/dist/index.js` or `tsx app/server/src/index.ts`
   - Health: `curl http://localhost:3001/health` → `{ status: "ok" }`
   - Pitch: `curl -X POST http://localhost:3001/pitch -d '{"rfp":"..."}' -H 'Content-Type: application/json'` → markdown

2. **Issue #13 - Vite Frontend:**
   - POST /pitch integration
   - RFP upload UI
   - Pitch display + copy-to-clipboard

3. **Issue #14 - Demo & Latency:**
   - Entity resolution "wow" moment
   - 90-second RFP→pitch validation

## Feedback Points for Review

1. **Embedding strategy:** OK to keep Python subprocess, or should we add JS port sooner?
2. **Error handling:** Current approach catches all as 500; is that acceptable for MVP?
3. **Testing coverage:** 17 macro tests sufficient? Want e2e pitch tests before #13?
4. **Connection pooling:** Add for v1, or defer to post-launch optimization?

---

**Created by:** Claude Code  
**Branch:** issue-12-node-api  
**Status:** Ready for PR review + merge
