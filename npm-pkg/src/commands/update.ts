declare const __VERSION__: string

const REPO = 'haru0416-dev/quaere'
const API_URL = `https://api.github.com/repos/${REPO}/releases/latest`

/** Compares two semver strings (strips leading 'v'). Returns -1, 0, or 1. */
function compareSemver(a: string, b: string): number {
  const parse = (s: string) => s.replace(/^v/, '').split('.').map(Number)
  const [aMaj = 0, aMin = 0, aPat = 0] = parse(a)
  const [bMaj = 0, bMin = 0, bPat = 0] = parse(b)
  if (aMaj !== bMaj) return aMaj > bMaj ? 1 : -1
  if (aMin !== bMin) return aMin > bMin ? 1 : -1
  if (aPat !== bPat) return aPat > bPat ? 1 : -1
  return 0
}

export async function runUpdate(): Promise<void> {
  console.log(`Current version: v${__VERSION__}`)
  console.log('Checking GitHub for latest release…')

  let res: Response
  try {
    res = await fetch(API_URL, {
      headers: {
        'User-Agent': `quaere-cli/${__VERSION__}`,
        Accept: 'application/vnd.github+json',
      },
    })
  } catch (err) {
    console.error(`error: could not reach GitHub — ${(err as Error).message}`)
    process.exit(1)
  }

  if (!res.ok) {
    console.error(`error: GitHub API returned ${res.status}`)
    process.exit(1)
  }

  const data = (await res.json()) as { tag_name?: string; html_url?: string }
  const latest = data.tag_name

  if (!latest) {
    console.error('error: unexpected API response (missing tag_name)')
    process.exit(1)
  }

  const cmp = compareSemver(latest as string, __VERSION__)

  if (cmp <= 0) {
    console.log(`Already up to date (${latest}).`)
    return
  }

  console.log(`\nNew version available: ${latest}`)
  console.log()
  console.log('To update:')
  console.log(`  npx quaere-cli@${latest} install`)
  console.log(`  bunx quaere-cli@${latest} install`)
  if (data.html_url) {
    console.log()
    console.log(`Release notes: ${data.html_url}`)
  }
}
