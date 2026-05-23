import { existsSync } from 'fs'
import { homedir } from 'os'
import { dirname, join } from 'path'
import { fileURLToPath } from 'url'

// Resolve the package root from the compiled dist/cli.js location
const distDir = dirname(fileURLToPath(import.meta.url))

export function getPackageSkillsDir(): string {
  return join(distDir, '..', 'skills')
}

export function getClaudeSkillsDir(): string {
  return join(homedir(), '.claude', 'skills')
}

export function getCodexSkillsDir(): string {
  return join(homedir(), '.agents', 'skills')
}

export type Agent = 'claude' | 'codex' | 'all' | 'auto'

export function resolveTargetDirs(agent: Agent): string[] {
  if (agent === 'claude') return [getClaudeSkillsDir()]
  if (agent === 'codex') return [getCodexSkillsDir()]
  if (agent === 'all') return [getClaudeSkillsDir(), getCodexSkillsDir()]

  // auto: detect which agent directories already exist
  const hasClaude = existsSync(join(homedir(), '.claude'))
  const hasCodex = existsSync(join(homedir(), '.agents'))

  if (hasClaude && hasCodex) return [getClaudeSkillsDir(), getCodexSkillsDir()]
  if (hasCodex) return [getCodexSkillsDir()]
  return [getClaudeSkillsDir()] // default to Claude
}
