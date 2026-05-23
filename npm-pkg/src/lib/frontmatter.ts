export interface Frontmatter {
  name?: string
  description?: string
  license?: string
  compatibility?: string
  [key: string]: string | undefined
}

/**
 * Parses YAML frontmatter from a Markdown file.
 * Handles plain scalar values and block scalars (| and >).
 */
export function parseFrontmatter(content: string): Frontmatter | null {
  const lines = content.split('\n')
  if (lines[0]?.trim() !== '---') return null

  let endIdx = -1
  for (let i = 1; i < lines.length; i++) {
    if (lines[i]?.trim() === '---') {
      endIdx = i
      break
    }
  }
  if (endIdx === -1) return null

  const result: Frontmatter = {}
  let currentKey = ''
  let isBlock = false
  const blockLines: string[] = []

  const flushBlock = () => {
    if (currentKey && isBlock) {
      result[currentKey] = blockLines.join('\n').trimEnd()
      blockLines.length = 0
      isBlock = false
    }
  }

  for (let i = 1; i < endIdx; i++) {
    const line = lines[i] ?? ''
    const keyMatch = /^([a-zA-Z][\w-]*):\s*(.*)$/.exec(line)
    if (keyMatch) {
      flushBlock()
      currentKey = keyMatch[1] ?? ''
      const val = (keyMatch[2] ?? '').trim()
      if (val === '|' || val === '>') {
        isBlock = true
      } else {
        result[currentKey] = val
      }
    } else if (isBlock) {
      // Strip 2-space YAML indent for block scalars
      blockLines.push(line.replace(/^  /, ''))
    }
  }
  flushBlock()

  return result
}
