# flowz-skill

A Claude Code skill that guides you through building a `WORKFLOW.md` for your project — conversationally, without the visual editor.

## Install

```bash
npx flowz-skill
```

This copies the skill files into `.agents/skills/flowz/` in your current project:

```
.agents/skills/flowz/
  SKILL.md       # skill definition (read by Claude Code)
  README.md      # this file
  examples/
    discovery.md   # example workflow file
    full-stack.md  # example full-stack workspace manifest
```

## Use

In a Claude Code session, invoke the skill:

```
/flowz
```

Claude will:
1. Inspect your project for existing workflow files and tech stack context
2. Walk you through defining workflows, steps, AI, and tools
3. Write `WORKFLOW.md` (the manifest) and `workflows/*.md` (workflow files) to your project root

## What gets created

```
your-project/
  WORKFLOW.md              ← manifest index (~200 tokens)
  workflows/
    discovery.md           ← one file per workflow
    development.md
    delivery.md
```

## Format spec

See [`../docs/workflow-md.md`](../docs/workflow-md.md) or [lets-flowz.vercel.app/workflow_md](https://lets-flowz.vercel.app/workflow_md) for the full format specification, field reference, and token budget methodology.

## Visual editor

To edit workflows visually, open [lets-flowz.vercel.app/canvas](https://lets-flowz.vercel.app/canvas) and import your `WORKFLOW.md` or the workspace `.json` file.

## Contributing

The skill source lives in `skill/` in the [Flowz repository](https://github.com/17-wands/flowz). PRs welcome.

## License

Apache 2.0
