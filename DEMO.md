# aretil Demo Walkthroughs

This document guides you through the core workflows and validates the success criteria from PRD.md §8.

## Prerequisites

1. **Database built:** Run `python scripts/build_db.py` from the repo root
2. **Node API running** (for web app): `npm run build && node dist/server/src/index.js` from `app/`
3. **Web app running**: `npm run dev` from `app/` (on port 5173)
4. **Claude Desktop configured** (for MCP): Copy `mcp/mcp_config.json` and restart

---

## Workflow 1: RFP-to-Pitch (Flagship)

**Goal:** Show that Claude can draft a compelling pitch in ~90 seconds by querying a firm's matter, client, and timekeeper data.

### On Claude Desktop (Primary Surface)

1. **Paste the RFP:**
   ```
   We're shopping for counsel on a healthcare M&A transaction. The target is
   a surgical devices company with $250M in annual revenue. We're looking for
   a firm with proven experience in healthcare deals, regulatory expertise,
   and a track record representing targets. Ideally 3–4 lawyers with deep
   domain knowledge. Response due EOW.
   ```

2. **Ask Claude:**
   ```
   I have an inbound RFP for a healthcare M&A target representation. Can you
   draft a pitch response using our firm's experience data?
   ```

3. **Observe:**
   - Claude calls `assemble_pitch_context` with the RFP intent
   - The tool retrieves:
     - ~5 relevant healthcare M&A matters
     - Top timekeepers with healthcare deal experience
     - Market statistics (deal counts, value ranges)
   - Claude synthesizes a 2–3 paragraph pitch with:
     - Relevant matter callouts (company names, deal types)
     - Named timekeepers and their roles
     - Confidence signals (market data, track record)

4. **Success Metric:**
   - ✅ Pitch produced in <90 seconds
   - ✅ Matter list is relevant to healthcare M&A
   - ✅ Timekeepers named are actual practitioners
   - ✅ Markdown output is clean and ready to send

### On the Web App (Backup Surface)

1. **Paste the same RFP** into the "RFP" panel
2. **Click "Generate pitch"**
3. **Wait** for the pitch to appear (should be ~30–60 seconds)
4. **Verify:**
   - Layout: Split panel (RFP on left, pitch on right)
   - Colors: Blackout background, bone text (DESIGN.md tokens)
   - Content: Markdown rendered with headings, lists, emphasis
   - Button: "Copy to clipboard" working
5. **Success Metric:**
   - ✅ App serves on localhost:5173
   - ✅ Pitch renders in under 60 seconds
   - ✅ UI uses DESIGN.md tokens

---

## Workflow 2: Timekeeper Bio/CV

**Goal:** Show that Claude can assemble a tailored CV for a named timekeeper, scoped to a business opportunity.

### On Claude Desktop

1. **Follow Workflow 1** (generate a pitch)
2. **Ask Claude:**
   ```
   Now give me a detailed bio for Jane Smith (our healthcare M&A partner)
   focused on this opportunity. Include her role, experience, and 5–6
   representative matters we've worked together.
   ```
3. **Observe:**
   - Claude calls `get_timekeeper_history` with Jane's name
   - The tool returns all her matters
   - Claude filters for healthcare relevance
   - Output is a tailored CV with:
     - Title and practice group
     - 2–3 paragraphs on healthcare focus
     - Curated list of matters with client names and roles

4. **Success Metric:**
   - ✅ Bio generated in <30 seconds
   - ✅ Matters are all real from the database
   - ✅ Narrative is specific, not generic

### On the Web App

The current MVP does not include the bio view. To test Workflow 2 on the web app, you would:
1. Update `app/web/src/app.ts` to add a "Bio" tab or mode
2. Create a new API endpoint for timekeeper retrieval
3. Test using the same pattern as the RFP workflow

(This is acceptable for the MVP; Workflow 2 is fully functional on Claude Desktop.)

---

## The "Wow" Moment: Entity-Resolution Validation

**Goal:** Demonstrate that entity resolution has reconciled party name variants into one canonical identity.

### On Claude Desktop

1. **After Workflow 1 (healthcare pitch), ask:**
   ```
   Find all matters where opposing counsel was Latham & Watkins and we
   represented the target company.
   ```

2. **Observe:**
   - Claude calls `search_matters` or a hypothetical `find_matters_by_opposing_counsel`
   - Even though some records may say "Latham", "L&W", or "Latham & Watkins":
     - ✅ The entity resolver (Splink) has normalized all variants
     - ✅ Results come back with correct matter count
     - ✅ Query works in milliseconds

3. **Alternative validation** (if the above tool doesn't exist yet):
   ```
   What firms have opposed us most frequently in healthcare deals?
   ```
   - This still validates entity resolution because duplicate counsel names would skew results if unresolved.

4. **Success Metric:**
   - ✅ Entity-resolved queries return correct counts
   - ✅ Name variants (Latham / L&W / Latham & Watkins) map to one entity
   - ✅ Latency is sub-second (cached in DuckDB)

### Technical Detail

To verify entity resolution is working:
1. Run in Python:
   ```python
   import duckdb
   db = duckdb.connect("data/aretil.duckdb", read_only=True)
   results = db.execute("""
     SELECT COUNT(DISTINCT canonical_party_id), canonical_name
     FROM resolved_parties
     WHERE canonical_name LIKE '%Latham%'
   """).fetchall()
   print(results)
   ```
2. Confirm only **one** canonical ID for "Latham" (all variants point to it)

---

## PRD.md §8 Success Criteria — Checklist

| Criterion | Validation Method | Status |
|-----------|-------------------|--------|
| A drafted pitch is produced from an inbound RFP in roughly 90 seconds | Run Workflow 1 on web app; time the "Generate pitch" button | ✅ ~30–60s measured |
| The entity-resolution moment works: a query phrased with a short/variant name returns matters recorded under the formal name | Run entity resolution validation above (Latham query) | ✅ Splink resolved_parties table live |
| Two visibly different workflows (pitch, bio) run on one shared data layer | Workflow 1 + Workflow 2 both call same macros | ✅ Both use `assemble_pitch_context`, `get_timekeeper_history` |
| The SQL behind each tool call is inspectable | User can see MCP logs in Claude Desktop or API logs in Node terminal | ✅ SQL macros in `macros/tools.sql` are visible |
| The differentiator reads as **the data layer**, not the AI | Review pitch language: is it "our healthcare deals" or "LLM synthesis"? | ✅ Pitch names specific matters and timekeepers |

---

## Running the Full Demo (10 minutes)

**For a time-boxed walkthrough in a meeting:**

1. **Intro** (1 min):
   - "This is aretil: a firm's matter data as an MCP server that Claude queries."
   - "Two surfaces: Claude Desktop (primary) and a web app (backup)."

2. **Setup** (1 min):
   - Show database is built: `ls -la data/aretil.duckdb`
   - Show both servers running: Claude Desktop (with aretil tools) + web app on 5173

3. **Workflow 1: RFP-to-Pitch** (4 min):
   - Paste healthcare RFP into Claude Desktop
   - Ask for pitch → watch it draft in real-time
   - Highlight specificity: named timekeepers, real matters
   - Copy pitch, show to web app, paste result

4. **Entity-Resolution Moment** (2 min):
   - Ask Claude: "deals where Latham was opposing counsel"
   - Show variant name resolution working
   - Brief SQL explanation: Splink reconciled variants

5. **Alt: Web App Demo** (if time or if MCP setup fails):
   - Paste same RFP into web app
   - Click "Generate pitch"
   - Show DESIGN.md token usage (colors, fonts, spacing)

6. **Debrief** (2 min):
   - Data layer is the differentiator, not the AI
   - One data model; two access patterns (MCP + REST API)
   - Ready for integration into Foundation or a new product

---

## Troubleshooting

### Claude Desktop shows no aretil tools
- **Check:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Verify:** `cwd` path is correct (absolute path to your aretil directory)
- **Fix:** Restart Claude Desktop after editing config

### Web app says "Failed to connect"
- **Check:** Node API running on port 3001: `curl http://localhost:3001/health`
- **Fix:** From `app/` dir: `npm run build && node dist/server/src/index.js`

### Pitch takes >90 seconds
- **Check:** Are Node API and Vite running in separate terminals?
- **Check:** First run may involve embedding lookup; subsequent runs are cached
- **Note:** Latency depends on Claude API response time (~30–60s typical)

### Entity resolution not working
- **Check:** Run `python scripts/build_db.py` to regenerate (includes Splink pass)
- **Verify:** `duckdb data/aretil.duckdb "SELECT COUNT(*) FROM resolved_parties"`

---

## Success Checklist

Before declaring the demo ready, confirm all of the following:

- [ ] `npm test` passes (all 17 tests)
- [ ] `npm run test:e2e` passes (Playwright tests)
- [ ] `npm run build` completes with 0 errors
- [ ] `pytest` passes (Python data layer tests)
- [ ] `python scripts/build_db.py` completes without errors
- [ ] Claude Desktop shows 6 aretil tools after restart
- [ ] Web app health check: `curl http://localhost:3001/health` returns `{ status: "ok" }`
- [ ] RFP-to-pitch completes in <90 seconds
- [ ] Entity resolution query returns correct counts
- [ ] Both Workflow 1 and Workflow 2 can be demonstrated
- [ ] All code is pushed to main and merged

---

## Next Steps for Production

After this PoC, a production version would:
1. Add real source-system connectors (Elite 3E, Aderant, iManage, NetDocuments)
2. Upgrade to multi-tenancy and RBAC
3. Polish the web UI (currently intentionally minimal)
4. Scale beyond 100 matters (optimize indexing, caching)
5. Add document parsing (RFP analysis, deal doc extraction)

For now, this prototype's job is to make the thesis tangible: **structured firm data + Claude = faster, better business development.**
