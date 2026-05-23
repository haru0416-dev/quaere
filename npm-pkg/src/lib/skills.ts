import { type Dirent, readdirSync } from 'fs'
import { join } from 'path'
import { getPackageSkillsDir } from './paths.js'

export interface SkillEntry {
  name: string
  dir: string
}

export function getBundledSkills(): SkillEntry[] {
  const skillsDir = getPackageSkillsDir()
  return readdirSync(skillsDir, { withFileTypes: true })
    .filter((d: Dirent) => d.isDirectory() && /^quaere-/.test(d.name))
    .map((d: Dirent) => ({ name: d.name, dir: join(skillsDir, d.name) }))
    .sort((a: SkillEntry, b: SkillEntry) => a.name.localeCompare(b.name))
}
