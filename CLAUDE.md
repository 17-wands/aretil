# aretil — Claude Code guide

`aretil` is a prototype: a legal experience-management data layer exposed as an
MCP server, with Claude as the front end. It demonstrates the
"firm-data-as-an-MCP-server" thesis. See PRD.md and ARCHITECTURE.md for the full
scope and design.

> **Proof of concept.** `aretil` is an unaffiliated PoC built from publicly
> available information — not production software, and not affiliated with or
> endorsed by any company named here. Full disclaimer in PRD.md.

## Project docs

Read the relevant doc before non-trivial work, and keep it current when behavior
changes (see the `update-docs` step in `workflows/feature-development.md`).

- **PRD.md** — scope, workflows, success criteria, non-goals.
- **ARCHITECTURE.md** — components, data model, MCP tool catalog, data flows.
- **DESIGN.md** — design system. Not yet defined.
- **WORKFLOW.md** — workflow manifest (see "Workflow context" below).

## Stack

The prototype is a hybrid:

- **Python data/ML core** — the DuckDB substrate, Splink entity resolution, local
  embeddings, the SQL-macro tool layer, and the DuckDB MCP server.
- **TypeScript/Node app layer** — the web UI and surrounding app tooling.

Use Python for the data/ML/MCP core and TypeScript for the app/UI layer. The
`npm` commands below target the TypeScript layer; the Python core uses `pytest`
and `ruff`.

## Skills

Before relying on your training data you MUST evaluate and apply ALL APPLICABLE
SKILLS to your problem space. IF AND ONLY IF you do not find a skill that applies
are you allowed to fall back to your training data.

Project skills are installed in `.claude/skills/`:

| Skill | Use when |
|---|---|
| `flowz` | Creating or updating `WORKFLOW.md` and `workflows/*.md` files. |
| `humanizer` | Editing user-facing prose or Markdown docs — strip AI-writing patterns before finalizing. |
| `accelint-ts-best-practices` | Writing or reviewing TypeScript/JavaScript. |
| `accelint-ts-testing` | Writing Vitest tests for the TypeScript layer. |
| `accelint-ts-documentation` | Adding JSDoc or code comments to TypeScript. |
| `accelint-ts-performance` | Optimizing slow TypeScript/JavaScript hot paths. |
| `accelint-ts-audit-all` | Running a full multi-skill audit of TypeScript code. |

The `accelint-ts-*` skills apply to the TypeScript layer only. The Python core
follows the conventions in ARCHITECTURE.md and standard Python tooling.

## Workflow context

A `WORKFLOW.md` file exists at the project root. It is the manifest for this
team's product workflow. When starting any work session:

1. Read `WORKFLOW.md` to understand what workflow files exist.
2. Identify which workflow(s) are relevant to the current task based on
   descriptions and tags.
3. Read only those workflow files from the `workflows/` directory.
4. Only perform steps where `actor` is `agent` or `either`. Steps marked
   `actor: human` require a person and must not be executed autonomously.
5. Before starting a step, verify its inputs exist. A step's outputs become the
   required inputs for downstream steps — do not skip producing them.
6. Follow enforcement levels: complete `required` steps, use judgment on
   `recommended`, skip `optional` unless specifically helpful.
7. Prefer the listed `ai:` and `tools:` entries unless there is a documented
   reason to deviate.

## Development workflow

GitHub Issues in the remote repo are the ordered backlog. Work issues in priority
order; do not skip ahead unless the human reprioritizes. The full step contract
is in `workflows/feature-development.md`.

Per issue: read the goal, tasks, and acceptance criteria → inspect code and docs
before editing → make the smallest coherent change → add or update tests when
behavior changes → update docs when product, architecture, or workflow changes →
run the required checks → open a PR.

Branches use `issue-XX-short-description`. A PR links its issue and states what
changed, why, tests run, docs updated, and known risks or follow-ups; include
screenshots for UI changes. After a PR merges:

```
git checkout main
git pull --ff-only
```

Then take the next open issue.

### Checks

TypeScript layer (wired up as the project matures):

```
npm run jobs:validate
npm test
npm run test:e2e
npm run build
```

Python core: `pytest` and `ruff`.

If a required command does not exist yet, implement it as part of the current
issue or explain why it is unavailable. As of 2026-05-18 there is no
`package.json` and no test suite, so these commands are not yet runnable.

## Conventions

- Make the smallest coherent change that satisfies the issue. No speculative
  abstractions, no scope creep.
- Update PRD.md, ARCHITECTURE.md, or WORKFLOW.md when a change affects product
  behavior, architecture, or workflow.
- Run `humanizer` over Markdown docs and user-facing copy before finalizing.
