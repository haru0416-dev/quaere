import { type Dirent, existsSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { getPackageSkillsDir } from './paths.js'

export type SkillKind = 'core' | 'extension'

export interface SkillEntry {
  name: string
  dir: string
  kind: SkillKind
}

function readSkillsFrom(dir: string, kind: SkillKind): SkillEntry[] {
  if (!existsSync(dir)) return []
  return readdirSync(dir, { withFileTypes: true })
    .filter((d: Dirent) => d.isDirectory() && d.name.startsWith('quaere-'))
    .map((d: Dirent) => ({ name: d.name, dir: join(dir, d.name), kind }))
    .toSorted((a: SkillEntry, b: SkillEntry) => a.name.localeCompare(b.name))
}

export function getCoreSkills(): SkillEntry[] {
  return readSkillsFrom(join(getPackageSkillsDir(), 'core'), 'core')
}

export function getExtensionSkills(): SkillEntry[] {
  return readSkillsFrom(join(getPackageSkillsDir(), 'extensions'), 'extension')
}

export function getAllSkills(): SkillEntry[] {
  return [...getCoreSkills(), ...getExtensionSkills()]
}

/**
 * Resolve the set of skills to install.
 *
 * - core only (default)
 * - core + every extension (includeExtensions)
 * - core + named extensions (selectExtensions)
 */
export function resolveSkillSelection(options: {
  includeExtensions?: boolean
  selectExtensions?: string[]
}): { selected: SkillEntry[]; unknownExtensions: string[] } {
  const core = getCoreSkills()
  const extensions = getExtensionSkills()

  if (options.includeExtensions) {
    return { selected: [...core, ...extensions], unknownExtensions: [] }
  }

  const requested = options.selectExtensions ?? []
  if (requested.length === 0) {
    return { selected: core, unknownExtensions: [] }
  }

  const byName = new Map(extensions.map((s) => [s.name, s]))
  // accept both "quaere-audit" and "audit"
  const resolve = (name: string): SkillEntry | undefined =>
    byName.get(name) ?? byName.get(`quaere-${name}`)

  const picked: SkillEntry[] = []
  const unknown: string[] = []
  for (const name of requested) {
    const entry = resolve(name)
    if (entry) picked.push(entry)
    else unknown.push(name)
  }

  return { selected: [...core, ...picked], unknownExtensions: unknown }
}
