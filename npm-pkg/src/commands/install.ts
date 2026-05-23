import { cpSync, existsSync, mkdirSync, renameSync, rmSync } from 'fs'
import { join } from 'path'
import { mergeManifest, readManifest, writeManifest } from '../lib/manifest.js'
import { Agent, resolveTargetDirs } from '../lib/paths.js'
import { getBundledSkills } from '../lib/skills.js'

declare const __VERSION__: string

export interface InstallOptions {
  force?: boolean
}

export async function runInstall(agent: Agent, opts: InstallOptions = {}): Promise<void> {
  const skills = getBundledSkills()
  if (skills.length === 0) {
    console.error('error: no bundled skills found — package may be corrupted')
    process.exit(1)
  }

  const targets = resolveTargetDirs(agent)

  for (const targetDir of targets) {
    mkdirSync(targetDir, { recursive: true })

    const installed: string[] = []
    const skipped: string[] = []

    for (const skill of skills) {
      const dest = join(targetDir, skill.name)
      const staging = join(targetDir, `.${skill.name}.staging`)
      const backup = join(targetDir, `.${skill.name}.backup`)

      // Check version match to skip unnecessary work (unless --force)
      if (!opts.force && existsSync(dest)) {
        const existing = readManifest(targetDir)
        if (existing?.quaere_version === __VERSION__ && existing.skills.includes(skill.name)) {
          skipped.push(skill.name)
          continue
        }
      }

      // Clean up any leftover staging directory
      rmSync(staging, { recursive: true, force: true })

      // Stage into a temporary directory first
      cpSync(skill.dir, staging, { recursive: true })

      // Back up the current install (if any) before promoting staging
      if (existsSync(dest)) {
        rmSync(backup, { recursive: true, force: true })
        renameSync(dest, backup)
      }

      // Atomic promotion: staging → dest
      renameSync(staging, dest)

      // Clean up backup now that the new version is live
      rmSync(backup, { recursive: true, force: true })

      installed.push(skill.name)
    }

    if (installed.length === 0 && skipped.length > 0) {
      console.log(`\n${targetDir}`)
      console.log(`  Already up to date (${skipped.length} skill${skipped.length === 1 ? '' : 's'}, v${__VERSION__})`)
      console.log('  Use --force to reinstall anyway.')
      continue
    }

    // Update manifest (additive — preserves skills installed by other tools)
    const existing = readManifest(targetDir)
    writeManifest(targetDir, mergeManifest(existing, __VERSION__, installed))

    console.log(`\nInstalled to ${targetDir}:`)
    for (const name of installed) {
      console.log(`  ✓ ${name}`)
    }
    if (skipped.length > 0) {
      console.log(`  (skipped ${skipped.length} already up-to-date)`)
    }
    console.log()
    console.log('Commands:')
    for (const { name } of skills) {
      console.log(`  /${name}`)
    }
  }
}
