---
name: AI-Native Full Stack
version: 1.0.0
team: Example Engineering
description: Standard product lifecycle manifest for an AI-native engineering team.
exported: 2026-05-08T10:00:00Z
---

# Workflow Manifest: AI-Native Full Stack

This team uses Claude Code, Cursor, GitHub Actions, and Vercel across the product lifecycle.
Three focused workflow files cover discovery/requirements, development, and delivery.

## Load Instructions

This file is the workspace index. When starting a session, read this manifest first.
Load only the workflow files relevant to your current task.
Match your task to the workflow descriptions and tags below.

```yaml
workspace:
  name: AI-Native Full Stack
  version: 1.0.0
  team: Example Engineering
  workflows:
    - id: discovery-requirements
      name: Discovery & Requirements
      file: workflows/discovery-requirements.md
      description: User research, design direction, and PRD drafting
      tags: [discovery, ux, requirements]
      tokens: 1420

    - id: development
      name: Development
      file: workflows/development.md
      description: AI-assisted feature development, code review, and testing
      tags: [dev, claude-code, cursor, testing, github]
      depends_on: [discovery-requirements]
      tokens: 2180

    - id: delivery
      name: Delivery
      file: workflows/delivery.md
      description: Deployment, CI/CD pipelines, and production monitoring
      tags: [deployment, ci-cd, vercel, monitoring]
      depends_on: [development]
      tokens: 980
```

## Workflow Index

- **[Discovery & Requirements](workflows/discovery-requirements.md)** — User research, design direction, and PRD drafting *(≈1,420 tokens)*
  Tags: discovery, ux, requirements

- **[Development](workflows/development.md)** — AI-assisted feature development, code review, and testing *(≈2,180 tokens)*
  Tags: dev, claude-code, cursor, testing, github
  Depends on: discovery-requirements

- **[Delivery](workflows/delivery.md)** — Deployment, CI/CD pipelines, and production monitoring *(≈980 tokens)*
  Tags: deployment, ci-cd, vercel, monitoring
  Depends on: development
