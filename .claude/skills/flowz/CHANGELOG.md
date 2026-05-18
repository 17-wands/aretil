# Changelog

## [1.1] - 2026-05-08

### Added
- Frontmatter with `name`, `description`, `license`, `metadata.version`, `metadata.author` — skill was previously invisible to automatic activation because no trigger description existed
- `NEVER Do` section with six concrete anti-patterns; omitting this meant agents had no guard against producing phase-based output (wrong format) or skipping the `actor` field (breaks the contract)
- `references/format.md` with complete output format templates and field limits — moved out of SKILL.md to reduce activation context by ~800 tokens

### Changed
- Output format updated from phase-based (`## Phase: {name}` + per-phase YAML) to flat workflow → steps structure, matching the data model change made in v1.1 of the Flowz app
- "When to invoke" section removed from body — trigger conditions belong only in the frontmatter `description` field; having them in the body wastes tokens after activation
- Step 3 (build workflow) simplified — removed nested phase loop, steps are now direct children of a workflow
- Field limit and token estimation tables moved to `references/format.md`

### Version
- 1.0 → 1.1 (minor: new sections, structural improvements, format correction)
