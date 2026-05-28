import { existsSync } from 'node:fs'
import { readManifest } from '../lib/manifest.js'
import { getClaudeSkillsDir, getCodexSkillsDir } from '../lib/paths.js'
import { getCoreSkills, getExtensionSkills } from '../lib/skills.js'

interface TargetInfo {
  label: string
  dir: string
}

const TARGETS: TargetInfo[] = [
  { label: 'Claude Code', dir: getClaudeSkillsDir() },
  { label: 'Codex CLI', dir: getCodexSkillsDir() },
]

export function runList(): void {
  const coreNames = new Set(getCoreSkills().map((s) => s.name))
  const extensionNames = new Set(getExtensionSkills().map((s) => s.name))
  const kindOf = (name: string): string => {
    if (coreNames.has(name)) return 'core'
    if (extensionNames.has(name)) return 'extension'
    return 'other'
  }

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
      console.log(`  ${marker} ${name}  (${kindOf(name)})${note}`)
    }

    const installed = new Set(manifest.skills)
    const availableExtensions = [...extensionNames].filter((n) => !installed.has(n))
    if (availableExtensions.length > 0) {
      console.log('  available extensions (not installed):')
      for (const name of availableExtensions) {
        console.log(`    · ${name}  — install with: quaere install --skill ${name.replace(/^quaere-/, '')}`)
      }
    }
  }

  if (!found) {
    console.log('No Quaere skills installed.')
    console.log('Run: npx quaere-cli install')
  }
}
