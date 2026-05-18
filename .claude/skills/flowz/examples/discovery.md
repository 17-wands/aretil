---
name: Discovery & Requirements
version: 1.0.0
description: User research, design direction, and PRD drafting.
tags: [discovery, ux, requirements, research]
exported: 2026-05-08T10:00:00Z
---

# Workflow: Discovery & Requirements

This workflow covers user research synthesis through PRD sign-off.
Load this file when working on discovery tasks, design decisions, or requirements writing.
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
  id: discovery-requirements
  name: Discovery & Requirements
  steps:
    - id: research-synthesis
      name: User Research Synthesis
      description: Synthesize user interviews and analytics into insights.
      inputs:
        - "Interview recordings"
        - "Analytics exports"
        - "Support ticket themes"
      outputs:
        - "Insight brief"
        - "User journey map"
      ai:
        - name: Claude Sonnet
          model: claude-sonnet-4-6
          skills: [summarize, extract-themes, cluster-insights]
          harness: claude-code
      tools:
        - name: Notion
          type: saas
          required: true
          alternatives: [Confluence, Miro]
        - name: Dovetail
          type: saas
          required: false
          alternatives: [Maze, UserTesting]
      actor: either
      enforcement: required

    - id: design-direction
      name: Design Direction
      description: Define UX flows and visual direction from insights.
      inputs:
        - "Insight brief"
        - "Brand guidelines"
      outputs:
        - "Wireframes"
        - "Design spec"
      ai: []
      tools:
        - name: Figma
          type: saas
          required: true
          alternatives: [Sketch, Penpot]
      actor: human
      enforcement: recommended

    - id: prd-drafting
      name: PRD Drafting
      description: Draft product requirements document with Claude assistance.
      inputs:
        - "Opportunity brief"
        - "Design spec"
        - "User journey map"
      outputs:
        - "PRD"
        - "Acceptance criteria"
      ai:
        - name: Claude Sonnet
          model: claude-sonnet-4-6
          skills: [write, structure, critique, generate-acceptance-criteria]
          harness: claude-code
      tools:
        - name: Linear
          type: saas
          required: true
          alternatives: [Jira, "GitHub Issues"]
      actor: agent
      enforcement: required

    - id: prd-review
      name: PRD Review
      description: Stakeholder review and sign-off on requirements.
      inputs:
        - "PRD"
        - "Acceptance criteria"
      outputs:
        - "Approved PRD"
      ai:
        - name: Claude Sonnet
          model: claude-sonnet-4-6
          skills: [critique, suggest-gaps]
          harness: claude-code
      tools:
        - name: Linear
          type: saas
          required: true
          alternatives: []
      actor: human
      enforcement: required
      notes: "Get explicit sign-off before development begins."
```
