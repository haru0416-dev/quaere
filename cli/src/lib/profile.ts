// Profile assembly: a SKILL.md is a single source whose sections are tagged
// with layers; installing assembles the subset a given agent actually needs.
//
// Layers (measured 2026-07: see docs/profile-separation.md):
//   gate      — the load-bearing rule, claim shape, decision labels
//   method    — process guidance: budgets, ordering, handoffs
//   pedagogy  — deep forms, worked examples, state-file conventions
//
// Untagged lines (frontmatter, title) are always kept.

export type Layer = 'gate' | 'method' | 'pedagogy'
export type Profile = 'full' | 'lean' | 'contract'

export const PROFILE_LAYERS: Record<Profile, readonly Layer[]> = {
  full: ['gate', 'method', 'pedagogy'],
  lean: ['gate', 'method'],
  contract: ['gate'],
}

const OPEN = /^<!--\s*quaere:layer\s+(\w+)\s*-->\s*$/
const CLOSE = /^<!--\s*\/quaere:layer\s*-->\s*$/
const LAYERS: ReadonlySet<string> = new Set(['gate', 'method', 'pedagogy'])

export class ProfileTagError extends Error {}

/** Assembles the given profile from a tagged SKILL.md source. */
export function assembleProfile(source: string, profile: Profile): string {
  const keep = new Set<string>(PROFILE_LAYERS[profile])
  const out: string[] = []
  let current: string | null = null

  for (const [index, line] of source.split('\n').entries()) {
    const open = OPEN.exec(line)
    if (open) {
      const layer = open[1] ?? ''
      if (current !== null)
        throw new ProfileTagError(`line ${index + 1}: nested quaere:layer (already inside "${current}")`)
      if (!LAYERS.has(layer)) throw new ProfileTagError(`line ${index + 1}: unknown layer "${layer}"`)
      current = layer
      continue
    }
    if (CLOSE.test(line)) {
      if (current === null) throw new ProfileTagError(`line ${index + 1}: closing tag without an open layer`)
      current = null
      continue
    }
    if (current === null || keep.has(current)) out.push(line)
  }

  if (current !== null) throw new ProfileTagError(`unclosed quaere:layer "${current}"`)

  // Collapse the blank runs left where dropped sections used to be.
  return out
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/\n+$/, '\n')
}

/** True when the source carries any layer tags — untagged skills install as-is. */
export function hasProfileTags(source: string): boolean {
  return source.split('\n').some((line) => OPEN.test(line))
}
