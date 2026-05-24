import { type Dirent, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { getPackageSkillsDir } from './paths.js'

export interface SkillEntry {
  name: string
  dir: string
}

export function getBundledSkills(): SkillEntry[] {
  const skillsDir = getPackageSkillsDir()
  return readdirSync(skillsDir, { withFileTypes: true })
    .filter((d: Dirent) => d.isDirectory() && d.name.startsWith('quaere-'))
    .map((d: Dirent) => ({ name: d.name, dir: join(skillsDir, d.name) }))
    .toSorted((a: SkillEntry, b: SkillEntry) => a.name.localeCompare(b.name))
}
