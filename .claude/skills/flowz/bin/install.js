#!/usr/bin/env node

const fs = require('fs')
const path = require('path')

const TARGET_DIR = path.join(process.cwd(), '.agents', 'skills', 'flowz')
const SKILL_DIR = path.join(__dirname, '..')

const FILES = [
  'SKILL.md',
  'README.md',
  'CHANGELOG.md',
  'examples/discovery.md',
  'examples/full-stack.md',
  'references/format.md',
]

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
}

function main() {
  const projectName = path.basename(process.cwd())

  console.log('\n  Flowz skill installer\n')
  console.log(`  Project: ${projectName}`)
  console.log(`  Target:  .agents/skills/flowz/\n`)

  for (const file of FILES) {
    const src = path.join(SKILL_DIR, file)
    const dest = path.join(TARGET_DIR, file)
    if (fs.existsSync(src)) {
      ensureDir(path.dirname(dest))
      fs.copyFileSync(src, dest)
      console.log(`  + ${file}`)
    }
  }

  console.log(`
  Skill installed at .agents/skills/flowz/

  Invoke in Claude Code:
    /flowz

  Claude will guide you through building WORKFLOW.md for this project.

  Format spec:
    https://lets-flowz.vercel.app/workflow_md
`)
}

main()
