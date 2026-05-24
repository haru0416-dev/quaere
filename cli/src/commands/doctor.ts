import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { parseFrontmatter } from '../lib/frontmatter.js'
import { readManifest } from '../lib/manifest.js'
import { getClaudeSkillsDir, getCodexSkillsDir } from '../lib/paths.js'

const MAX_LINES = 500
const KEBAB_RE = /^[a-z][a-z0-9]*(-[a-z0-9]+)*$/

interface Issue {
  skill: string
  message: string
}

interface TargetResult {
  label: string
  dir: string
  issues: Issue[]
  ok: string[]
  orphans: string[]
}

function checkSkill(skillDir: string, name: string): string[] {
  const issues: string[] = []
  const skillMd = join(skillDir, 'SKILL.md')

  if (!existsSync(skillMd)) {
    issues.push('SKILL.md not found')
    return issues
  }

  const content = readFileSync(skillMd, 'utf-8')
  const lineCount = content.split('\n').length

  if (lineCount > MAX_LINES) {
    issues.push(`SKILL.md exceeds ${MAX_LINES} lines (${lineCount} lines)`)
  }

  const fm = parseFrontmatter(content)
  if (!fm) {
    issues.push('SKILL.md missing or malformed frontmatter')
    return issues
  }

  if (!fm.name) {
    issues.push('frontmatter missing required field: name')
  } else {
    if (fm.name !== name) {
      issues.push(`name mismatch: frontmatter says "${fm.name}", directory is "${name}"`)
    }
    if (!KEBAB_RE.test(fm.name)) {
      issues.push(`name "${fm.name}" is not valid kebab-case`)
    }
  }

  if (!fm.description) {
    issues.push('frontmatter missing required field: description')
  } else {
    const desc = fm.description.trimStart()
    if (desc.length < 80) {
      issues.push(`description is too short (${desc.length} chars, minimum 80)`)
    }
  }

  if (!fm.compatibility) {
    issues.push('frontmatter missing required field: compatibility')
  }

  if (!fm.license) {
    issues.push('frontmatter missing required field: license')
  } else if (fm.license.toUpperCase() !== 'MIT') {
    issues.push(`license must be MIT, got "${fm.license}"`)
  }

  return issues
}

function checkTarget(label: string, dir: string): TargetResult {
  const result: TargetResult = { label, dir, issues: [], ok: [], orphans: [] }

  const manifest = readManifest(dir)
  if (!manifest) {
    // No manifest is not itself an error — maybe not yet installed
    return result
  }

  const manifestedSet = new Set(manifest.skills)

  // Check every skill recorded in the manifest
  for (const name of manifest.skills) {
    const skillDir = join(dir, name)
    if (!existsSync(skillDir)) {
      result.issues.push({ skill: name, message: 'recorded in manifest but not found on disk' })
      continue
    }
    const problems = checkSkill(skillDir, name)
    if (problems.length > 0) {
      for (const msg of problems) result.issues.push({ skill: name, message: msg })
    } else {
      result.ok.push(name)
    }
  }

  // Detect orphan quaere-* directories not in manifest
  if (existsSync(dir)) {
    const entries = readdirSync(dir, { withFileTypes: true })
    for (const entry of entries) {
      if (entry.isDirectory() && entry.name.startsWith('quaere-') && !manifestedSet.has(entry.name)) {
        result.orphans.push(entry.name)
      }
    }
  }

  return result
}

export function runDoctor(): void {
  const targets = [
    { label: 'Claude Code', dir: getClaudeSkillsDir() },
    { label: 'Codex CLI', dir: getCodexSkillsDir() },
  ]

  let totalIssues = 0

  for (const { label, dir } of targets) {
    const result = checkTarget(label, dir)

    const manifest = readManifest(dir)
    if (!manifest) continue // not installed here, skip silently

    console.log(`\n${label}  (${dir})`)

    for (const name of result.ok) {
      console.log(`  ✓ ${name}`)
    }

    for (const { skill, message } of result.issues) {
      console.log(`  ✗ ${skill}: ${message}`)
      totalIssues++
    }

    for (const name of result.orphans) {
      console.log(`  ? ${name}: orphan directory (not in manifest) — run install to adopt or remove manually`)
      totalIssues++
    }
  }

  if (totalIssues === 0) {
    const checked = targets.filter(({ dir }) => readManifest(dir) !== null).length
    if (checked === 0) {
      console.log('No Quaere skills installed. Run: npx quaere-cli install')
    } else {
      console.log('\nAll checks passed.')
    }
  } else {
    console.log(`\n${totalIssues} issue${totalIssues === 1 ? '' : 's'} found.`)
    process.exit(1)
  }
}
