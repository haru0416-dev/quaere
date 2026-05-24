import { describe, expect, it } from 'vitest'
import { parseFrontmatter } from './frontmatter.js'

describe('parseFrontmatter', () => {
  it('returns null when content lacks a leading delimiter', () => {
    expect(parseFrontmatter('no frontmatter here')).toBeNull()
  })

  it('returns null when the closing delimiter is missing', () => {
    expect(parseFrontmatter('---\nname: foo\nno closer')).toBeNull()
  })

  it('parses plain scalar values', () => {
    const fm = parseFrontmatter('---\nname: quaere-audit\nlicense: MIT\n---\nbody')
    expect(fm).toEqual({ name: 'quaere-audit', license: 'MIT' })
  })

  it('parses block scalars with the pipe indicator', () => {
    const src = [
      '---',
      'name: quaere-evidence',
      'description: |',
      '  This skill should be used when evaluating claims.',
      '  Multiple lines are preserved.',
      'license: MIT',
      '---',
      'body',
    ].join('\n')
    const fm = parseFrontmatter(src)
    expect(fm?.name).toBe('quaere-evidence')
    expect(fm?.description).toContain('This skill should be used')
    expect(fm?.description).toContain('Multiple lines are preserved.')
    expect(fm?.license).toBe('MIT')
  })

  it('ignores body content after the closing delimiter', () => {
    const fm = parseFrontmatter('---\nname: x\n---\n# Heading\nname: not-frontmatter')
    expect(fm).toEqual({ name: 'x' })
  })
})
