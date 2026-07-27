import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { assembleProfile } from './profile.js'

// Guards the pilot skill's tagging: every profile assembles, the layer
// boundaries land where the design says, and each assembly stays inside its
// length budget (a house discipline — the historical Codex read cap that
// first motivated it was fixed upstream in openai/codex#16479).
describe('quaere-evidence assembly', () => {
  const src = readFileSync(join(__dirname, '../../../skills/core/quaere-evidence/SKILL.md'), 'utf-8')

  it('assembles all three profiles with the right layers', () => {
    const full = assembleProfile(src, 'full')
    const lean = assembleProfile(src, 'lean')
    const contract = assembleProfile(src, 'contract')
    for (const out of [full, lean, contract]) {
      expect(out).toContain('Iron Law')
      expect(out).toContain('name: quaere-evidence')
      expect(out).not.toContain('quaere:layer')
    }
    expect(lean).toContain('Probe budget')
    expect(lean).not.toContain('10-field')
    expect(contract).not.toContain('Probe budget')
    expect(full).toContain('10-field')
  })

  it('keeps each assembly inside its length budget', () => {
    expect(assembleProfile(src, 'lean').split('\n').length).toBeLessThanOrEqual(200)
    expect(assembleProfile(src, 'contract').split('\n').length).toBeLessThanOrEqual(60)
  })
})
