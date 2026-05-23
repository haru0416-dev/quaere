import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'fs'
import { join } from 'path'

export interface Manifest {
  quaere_version: string
  skills: string[]
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
): Manifest {
  const skills = new Set([...(existing?.skills ?? []), ...newSkills])
  return { quaere_version: version, skills: [...skills].sort() }
}
