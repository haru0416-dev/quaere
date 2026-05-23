import { existsSync } from 'node:fs'
import { readManifest } from '../lib/manifest.js'
import { getClaudeSkillsDir, getCodexSkillsDir } from '../lib/paths.js'

interface TargetInfo {
  label: string
  dir: string
}

const TARGETS: TargetInfo[] = [
  { label: 'Claude Code', dir: getClaudeSkillsDir() },
  { label: 'Codex CLI', dir: getCodexSkillsDir() },
]

export function runList(): void {
  let found = false

  for (const { label, dir } of TARGETS) {
    const manifest = readManifest(dir)
    if (!manifest) continue

    found = true
    console.log(`\n${label}  (${dir})`)
    console.log(`  version  ${manifest.quaere_version}`)

    if (manifest.skills.length === 0) {
      console.log('  (no skills recorded)')
      continue
    }

    for (const name of manifest.skills) {
      const onDisk = existsSync(dir + '/' + name)
      const marker = onDisk ? '✓' : '✗'
      const note = onDisk ? '' : '  [missing on disk]'
      console.log(`  ${marker} ${name}${note}`)
    }
  }

  if (!found) {
    console.log('No Quaere skills installed.')
    console.log('Run: npx quaere-cli install')
  }
}
