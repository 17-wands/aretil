# PRD — `aretil` Prototype

> A legal experience-management data layer, exposed as an MCP server, that lets
> Claude answer real business-development questions against a law firm's matter,
> client, and timekeeper data.

**Status:** Prototype / demo artifact — not a shippable product.
**Owner:** TBD. **Last updated:** 2026-05-18.

> **Disclaimer — proof of concept.** `aretil` is an unaffiliated proof of concept
> built for product exploration. It is not production software, and is not
> affiliated with, authorized by, or endorsed by Litera or any other company named
> in these documents. It uses synthetic data only — no real firm, client, or
> personal data — and is built entirely from publicly available information, with
> no confidential or insider knowledge. Competitive references reflect public
> information at a point in time and may be incomplete or out of date. Provided
> as-is, without warranty.

---

## 1. Context & Background

This prototype supports a candidacy for a product role at Litera, running the
**Foundations** experience-management product line. The strategy work behind it
reached one conclusion: the highest-leverage thing to bring into the partnership
conversation is not a deck — it is a **working prototype** that makes the
strategic thesis tangible.

Two facts frame the prototype:

- **Claude for Legal launched May 12, 2026.** Anthropic shipped 20+ MCP connectors
  (iManage, NetDocuments, Westlaw, Harvey, DocuSign, Relativity, and more) and 12
  practice-area plugins. Legal is now Anthropic's most-engaged knowledge-work
  vertical. Notably, **Litera/Foundation is not on the connector list.**
- **Foundation ships no API.** Every serious competitor (Intapp DealCloud, others)
  exposes its data programmatically; Foundation does not. That is an architectural
  admission, and it is the gap this prototype is built to dramatize.

The prototype's job is to show — concretely, on a laptop — what the next legal-tech
category looks like: **firm experience data as an MCP server**, queryable by Claude.

## 2. Problem Statement

A law firm's most valuable business-development asset is its own history — the
matters it has worked, the clients it has served, the deals its lawyers have led.
That history is trapped:

- **It is locked in legacy architecture.** Foundation stores it in a relational,
  UI-centric schema with no API. No AI agent can reach it without going through a
  human and a screen.
- **The workflows on top of it are slow and manual.** Drafting a pitch in response
  to an inbound RFP, or assembling a tailored lawyer bio, is hours of analyst work
  spent finding and summarizing relevant past matters.
- **AI alone does not solve it.** Claude is excellent at synthesis and drafting, but
  it cannot answer "show me our healthcare M&A deals over $100M where we repped the
  target" unless something has first *structured and entity-resolved* that data.
  That something is the missing layer.

## 3. Prototype Goal & Positioning

**Goal:** a thinking artifact that makes the "firm-data-as-an-MCP-server" thesis
real enough to point at and argue about — built in roughly a weekend, deliberately
narrow, demonstrably working.

**Positioning:** the prototype is the **legal-experience data layer that Claude
queries**, not another AI assistant. It is explicitly *complementary* to Claude for
Legal:

- Anthropic provides the AI substrate and the orchestration surface.
- `aretil` provides the structured, entity-resolved firm-data layer that makes that
  substrate useful for experience management and BD.

The demo should look like a **new product category**, not a faster Foundation. The
data model, the access pattern (MCP), and the surfaces should feel different.

**Non-positioning:** this is not pitched as a Claude wrapper, and not as a feature.
Two distinct workflows running on one shared data layer are what make it read as a
*platform*.

## 4. Target User

A **business-development professional or partner at a mid-market US law firm**
(roughly sub-AmLaw 200). This segment is real and underserved:

- Foundation targets and prices for the AmLaw 100.
- DealCloud is enterprise-only.
- Ikaun markets to global firms.
- No competitor offers a credible experience-management product priced and scoped
  for a 150–500 lawyer firm.

The mid-market is also where the thesis is *tractable*: structuring and
entity-resolving ~8,000 matters is a days-long job; 800,000 is not.

## 5. Demo Scenario

A walkthrough the audience can follow in one sitting:

1. An **inbound RFP** arrives — a healthcare company shopping for M&A counsel.
2. In Claude (Desktop, connected to the `aretil` MCP server), the user asks Claude
   to draft a pitch in response.
3. Claude calls the data layer: it retrieves the firm's most relevant past matters
   (semantic + structured filtering), surfaces the timekeepers with the deepest
   relevant experience, and pulls supporting context.
4. Claude returns a **drafted pitch in ~90 seconds** — relevant matter list,
   highlighted timekeepers, and 2–3 paragraphs of pitch language.
5. Follow-up: the user asks for a **tailored bio** for one of those timekeepers,
   scoped to this opportunity. The same data layer answers — demonstrating a
   *platform*, not a one-off.
6. The "wow" moment: the user asks something only an entity-resolved layer can
   answer — *"deals where Latham was opposing counsel and we represented the
   target"* — and it returns in seconds because the data layer has reconciled
   "Latham", "Latham & Watkins", and "L&W" into one entity.

The same flow is available in a thin TypeScript web app (paste an RFP, get a pitch)
as a backup surface if live MCP setup fails.

## 6. In-Scope Workflows & Functional Requirements

### Workflow 1 — RFP-to-Pitch (flagship)

| # | Requirement |
|---|-------------|
| 1.1 | Accept an inbound RFP as free text (pasted into Claude or the web app). |
| 1.2 | Parse the RFP into a structured query intent (practice area, industry, deal type, jurisdiction, deal-size band). |
| 1.3 | Retrieve relevant past matters using semantic search over matter descriptions **and** structured filters. |
| 1.4 | Identify and rank the timekeepers with the most relevant experience for the retrieved matters. |
| 1.5 | Draft a pitch: a relevant-matter list with brief descriptions, highlighted timekeepers, and 2–3 paragraphs of pitch language styled to the RFP. |
| 1.6 | Output as markdown. |
| 1.7 | Target end-to-end latency: ~90 seconds. |

### Workflow 2 — Timekeeper Bio / CV

| # | Requirement |
|---|-------------|
| 2.1 | Accept a timekeeper identifier plus an optional target context (e.g., "for the healthcare M&A pitch above"). |
| 2.2 | Pull that timekeeper's full matter history from the data layer. |
| 2.3 | Filter and rank that history for relevance to the target context. |
| 2.4 | Produce a tailored CV: role, practice group, experience summary, and a curated list of representative matters. |
| 2.5 | Output as markdown. |

### Cross-cutting

| # | Requirement |
|---|-------------|
| X.1 | Both workflows run against the **same** shared data layer and the **same** tool set. |
| X.2 | Tool logic is defined once (as SQL macros) and reused by both the MCP server and the TypeScript web app. |
| X.3 | The SQL a tool runs is inspectable — the system is not a black box. |
| X.4 | The whole prototype runs locally on a laptop with no external infrastructure beyond the Claude API. |

## 7. Synthetic Dataset Requirements

| # | Requirement |
|---|-------------|
| D.1 | One fictional mid-market US firm (fake name, plausible office footprint, e.g. NY + Chicago). |
| D.2 | 50–100 plausible matters — name, client, practice area, deal type, jurisdiction, deal value, year, role, brief description. |
| D.3 | Supporting `clients`, `timekeepers`, and `parties` records, related to matters. |
| D.4 | A tag vocabulary — industry codes, deal subtypes, governing law, regulatory dimensions. |
| D.5 | Data shaped so a lawyer would recognize it as realistic; concentrated in 2–3 practice areas (e.g. healthcare and financial-services M&A) so retrieval has depth. |
| D.6 | **Deliberate name variants** for at least a few parties/counsel (e.g. "Latham" / "Latham & Watkins" / "L&W") so the entity-resolution demo has something to resolve. |
| D.7 | Fully synthetic — no real firm, client, or person. |

## 8. Success Criteria

The demo "lands" when all of the following are observably true:

- A drafted pitch is produced from an inbound RFP in roughly 90 seconds.
- The entity-resolution moment works: a query phrased with a short/variant name
  returns matters recorded under the formal name.
- Two visibly different workflows (pitch, bio) run on one shared data layer.
- The SQL behind each tool call is inspectable — the audience can see *how* an
  answer was produced.
- The differentiator reads as **the data layer**, not the AI. A viewer should come
  away thinking "the structuring is the hard part, and they did it," not "nice
  Claude wrapper."

## 9. Non-Goals / Out of Scope

Explicitly **not** in the prototype. These belong to a later "path to production":

- Real source-system connectors (Elite 3E, Aderant, iManage, NetDocuments, Intapp).
- Adopting Twenty CRM or OpenContracts as the product backbone.
- Production authentication, multi-tenancy, RBAC, audit logging.
- Real customer data of any kind.
- A polished or production-grade UI — the TypeScript web app is intentionally
  minimal and framework-light.
- Ingesting or parsing real documents (PDFs, deal docs, court filings).
- Scale beyond ~100 matters.
- Fine-tuned or self-hosted reasoning models — Claude via API is the only
  drafting/reasoning layer. (A small local embedding model is used at build time
  for semantic search; see ARCHITECTURE §3.3.)

## 10. Risks & Open Questions

| Risk / Question | Note |
|---|---|
| DuckDB MCP extension maturity | The architecture leans on a relatively new community extension. Mitigation: the thin TypeScript web app is a fully working backup surface that does not depend on it. |
| Crowded pitch-generation category | Harvey, Ikaun, and Pitchly all touch pitch/RFP work. The demo must make the *firm-specific, entity-resolved data layer* the visible differentiator — not the drafting. |
| Synthetic data realism | If the data looks fake, the demo loses credibility. Data generation must produce shapes a practicing lawyer recognizes. |
| Product name | `aretil` is the working repo name; the product name is not yet decided. |
| Scope creep in the meeting | If asked to add features live, the answer is "good test — I'll show a v2 next time," not on-the-spot coding. |
