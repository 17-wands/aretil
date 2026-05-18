# WORKFLOW.md Format Reference

## Two-tier structure

```
your-project/
  WORKFLOW.md              ← manifest index (~200 tokens)
  workflows/
    discovery.md           ← one file per workflow (~400-800 tokens each)
    development.md
    delivery.md
```

Agents read the manifest first, then load only the workflow files relevant to the current task.

---

## `WORKFLOW.md` — Manifest

```markdown
---
name: {workspace name}
version: 1.0.0
team: {team name}
exported: {ISO timestamp}
---

# Workflow Manifest: {workspace name}

## Load Instructions

This file is the workspace index. When starting a session, read this manifest first.
Load only the workflow files relevant to your current task.
Match your task to the workflow descriptions and tags below.

```yaml
workspace:
  name: {workspace name}
  version: 1.0.0
  workflows:
    - id: {id}
      name: {name}
      file: workflows/{slug}.md
      description: {one line}
      tags: [{tag1}, {tag2}]
      depends_on: [{other-workflow-id}]
      tokens: {estimate}
``

## Workflow Index

- **[{name}](workflows/{slug}.md)** — {description} *(≈{tokens} tokens)*
  Tags: {tag1}, {tag2}
```

---

## `workflows/{slug}.md` — Workflow file

```markdown
---
name: {workflow name}
version: 1.0.0
description: {description}
tags: [{tags}]
exported: {ISO timestamp}
---

# Workflow: {workflow name}

{one paragraph description}
See `WORKFLOW.md` in the project root for the full workspace manifest.

## Conventions

- `actor: human` — must be performed by a person
- `actor: agent` — can be fully delegated to an AI agent
- `actor: either` — human or agent, at the team's discretion
- `enforcement: required` — this step must be completed before proceeding
- `enforcement: recommended` — skip only with documented justification
- `enforcement: optional` — use at team discretion
- `alternatives` — acceptable substitutes when the primary tool is unavailable

---

## Steps

```yaml
workflow:
  id: {workflow-id}
  name: {workflow name}
  steps:
    - id: {step-id}
      name: {step name}
      description: {description ≤200 chars}
      inputs: ["{artifact 1}", "{artifact 2}"]
      outputs: ["{artifact 1}", "{artifact 2}"]
      ai:
        - name: {agent name}
          model: {model id}
          skills: [{skill1}, {skill2}]
          harness: {harness}
      tools:
        - name: {tool name}
          type: {saas|ai-tool|cli|sdk|ide|local-config}
          required: {true|false}
          alternatives: [{alt1}, {alt2}]
      actor: {human|agent|either}
      enforcement: {required|recommended|optional}
      notes: {optional, ≤300 chars}
``
```

---

## Field limits

| Field | Limit |
|-------|-------|
| `description` | ≤ 200 chars |
| `notes` | ≤ 300 chars |
| Tool/AI names | ≤ 60 chars |
| Inputs/outputs per step | ≤ 8 items, ≤ 80 chars each |
| Tool alternatives | ≤ 4 |

## Token estimation

`ceil(total_chars / 3.8)` — empirical cl100k ratio for mixed YAML+English, ±8%.

Thresholds: green < 4,000 · amber 4,000–8,000 · red > 8,000 per workflow file.
