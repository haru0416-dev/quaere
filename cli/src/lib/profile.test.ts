import { describe, expect, it } from 'vitest'
import { assembleProfile, hasProfileTags, ProfileTagError } from './profile.js'

const SOURCE = [
  '---',
  'name: x',
  '---',
  '# Title',
  '<!-- quaere:layer gate -->',
  'GATE',
  '<!-- /quaere:layer -->',
  '<!-- quaere:layer method -->',
  'METHOD',
  '<!-- /quaere:layer -->',
  '<!-- quaere:layer pedagogy -->',
  'PEDAGOGY',
  '<!-- /quaere:layer -->',
].join('\n')

describe('assembleProfile', () => {
  it('keeps every layer for full', () => {
    const out = assembleProfile(SOURCE, 'full')
    expect(out).toContain('GATE')
    expect(out).toContain('METHOD')
    expect(out).toContain('PEDAGOGY')
    expect(out).not.toContain('quaere:layer')
  })

  it('drops pedagogy for lean and everything but gate for contract', () => {
    const lean = assembleProfile(SOURCE, 'lean')
    expect(lean).toContain('METHOD')
    expect(lean).not.toContain('PEDAGOGY')
    const contract = assembleProfile(SOURCE, 'contract')
    expect(contract).toContain('GATE')
    expect(contract).not.toContain('METHOD')
  })

  it('always keeps untagged lines and collapses blank runs', () => {
    const contract = assembleProfile(SOURCE, 'contract')
    expect(contract).toContain('name: x')
    expect(contract).toContain('# Title')
    expect(contract).not.toMatch(/\n{3,}/)
  })

  it('rejects nesting, unknown layers, and unclosed blocks', () => {
    expect(() =>
      assembleProfile('<!-- quaere:layer gate -->\n<!-- quaere:layer method -->', 'full'),
    ).toThrow(ProfileTagError)
    expect(() => assembleProfile('<!-- quaere:layer bogus -->\nx\n<!-- /quaere:layer -->', 'full')).toThrow(
      /unknown layer/,
    )
    expect(() => assembleProfile('<!-- quaere:layer gate -->\nx', 'full')).toThrow(/unclosed/)
    expect(() => assembleProfile('<!-- /quaere:layer -->', 'full')).toThrow(/without an open/)
  })
})

describe('hasProfileTags', () => {
  it('detects tagged and untagged sources', () => {
    expect(hasProfileTags(SOURCE)).toBe(true)
    expect(hasProfileTags('# plain skill')).toBe(false)
  })
})
