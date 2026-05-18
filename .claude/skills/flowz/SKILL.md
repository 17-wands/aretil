---
name: flowz
description: Use when creating or updating WORKFLOW.md files for a project — when users say "create a WORKFLOW.md", "document our workflow", "set up workflow files", "add workflow context", "write our team's workflow", "what's our workflow", or when a project has no WORKFLOW.md and needs one. Also use when a user wants to extend, update, or audit existing workflow files.
license: Apache-2.0
metadata:
  author: flowz
  version: "1.1"
---

# Flowz Workflow Builder

## NEVER Do

- **NEVER use phases** — the format is flat: workspace → workflows → steps. There is no intermediate phase layer. If you produce phase-based output, it will fail to import.
- **NEVER skip the `actor` field** — every step must declare `actor: human | agent | either`. This is the core contract; omitting it defeats the purpose of the format.
- **NEVER create a single monolithic `WORKFLOW.md`** — always use the two-tier structure: a root manifest plus `workflows/*.md` files. A single file doesn't allow selective loading.
- **NEVER produce placeholder outputs** — each step's `outputs` must name real artifacts (e.g. `"EDA notebook"`, `"Feature branch"`) that downstream steps can reference as inputs. Vague entries like `"results"` break the contract.
- **NEVER describe what a step does in `notes`** — `description` carries the what; `notes` carries constraints, gotchas, or reasons a human must own the step.
- **NEVER overwrite existing workflow files** — read them first and extend, not replace.

---

## Procedure

### Step 1 — Assess existing state

Read any existing workflow files before proceeding:

```
Read: WORKFLOW.md (if exists)
Read: workflows/*.md (if exists)
```

If files exist, extend rather than replace. Note what workflows are already defined.

### Step 2 — Discover context

Infer what you can from the codebase first (README, package.json, .claude/, .cursor/, .github/), then ask only for what's missing:

1. **Workspace name** — e.g. "Acme Engineering"
2. **Team name** (optional)
3. **Workflows** — what distinct areas of work exist? Each becomes a separate `workflows/*.md` file.
   Good starting point: discovery, development, delivery — but tailor to the actual team.
4. **Tech stack** — tools, IDEs, AI models (infer from project files; confirm before assuming)

Do not ask all at once. Gather what you can, then ask only for gaps.

### Step 3 — Build each workflow

For each workflow, walk through steps interactively:

```
For each step:
  - Name (required)
  - Description (≤ 200 chars — what does this step produce or decide?)
  - Actor: human / agent / either (who is eligible to perform this step?)
  - Inputs: what artifacts must exist before this step starts?
  - Outputs: what artifacts must this step produce for downstream steps?
  - AI: which models, harnesses, or skills are involved?
  - Tools: SaaS, CLI, IDE, SDK — required vs. optional? Any alternatives?
  - Enforcement: required / recommended / optional
```

Inference rule: if the tech stack is visible, pre-fill the `ai:` and `tools:` fields and ask for confirmation rather than starting from scratch.

### Step 4 — Write files

Load [references/format.md](references/format.md) for the exact file format and field limits before writing.

Write in this order:
1. Each `workflows/{slug}.md` file
2. The root `WORKFLOW.md` manifest

### Step 5 — Confirm and summarize

After writing:
- List files created with their token estimates (`ceil(chars / 3.8)`)
- Suggest adding the CLAUDE.md snippet below to the project's `CLAUDE.md`
- Offer to open the visual editor: `lets-flowz.vercel.app/canvas` (supports import of generated files)

---

## CLAUDE.md snippet to suggest

```markdown
## Workflow context

A `WORKFLOW.md` file exists at the project root. It is the manifest for this team's
product workflow. When starting any work session:

1. Read `WORKFLOW.md` to understand what workflow files exist.
2. Identify which workflow(s) are relevant to the current task based on descriptions and tags.
3. Read only those workflow files from the `workflows/` directory.
4. Only perform steps where `actor` is `agent` or `either`. Steps marked `actor: human`
   require a person and must not be executed autonomously.
5. Before starting a step, verify its inputs exist. A step's outputs become the required
   inputs for downstream steps — do not skip producing them.
6. Follow enforcement levels: complete `required` steps, use judgment on `recommended`,
   skip `optional` unless specifically helpful.
7. Prefer the listed `ai:` and `tools:` entries unless there is a documented reason to deviate.
```

---

## Examples

See [`examples/`](./examples/) for sample output files.
