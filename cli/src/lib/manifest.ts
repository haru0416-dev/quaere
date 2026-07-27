import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

export interface Manifest {
  quaere_version: string
  skills: string[]
  /** Assembly profile the skills were installed with; absent means full. */
  profile?: string
}

export function readManifest(targetDir: string): Manifest | null {
  const p = join(targetDir, '.quaere', 'manifest.json')
  if (!existsSync(p)) return null
  try {
    return JSON.parse(readFileSync(p, 'utf-8')) as Manifest
  } catch {
    return null
  }
}

export function writeManifest(targetDir: string, manifest: Manifest): void {
  const dir = join(targetDir, '.quaere')
  mkdirSync(dir, { recursive: true })
  const p = join(dir, 'manifest.json')
  const tmp = `${p}.tmp`
  writeFileSync(tmp, JSON.stringify(manifest, null, 2) + '\n', 'utf-8')
  renameSync(tmp, p)
}

export function mergeManifest(
  existing: Manifest | null,
  version: string,
  newSkills: string[],
  profile?: string,
): Manifest {
  const skills = new Set([...(existing?.skills ?? []), ...newSkills])
  const merged: Manifest = { quaere_version: version, skills: [...skills].toSorted() }
  const effective = profile ?? existing?.profile
  if (effective && effective !== 'full') merged.profile = effective
  return merged
}
