import { runInstall } from './commands/install.js'
import { runList } from './commands/list.js'
import { runUpdate } from './commands/update.js'
import { runDoctor } from './commands/doctor.js'
import type { Agent } from './lib/paths.js'

declare const __VERSION__: string

const USAGE = `
Usage: quaere-cli <command> [options]

Commands:
  install [all|claude|codex]  Install skills (default: auto-detect)
  list                         Show installed skills and version
  update                       Check for a newer release
  doctor                       Validate installed skill integrity

Options:
  --force     Force reinstall even if already up to date (install only)
  --version   Print version
  --help      Show this help

Examples:
  npx quaere-cli install
  npx quaere-cli install all
  bunx quaere-cli install
  quaere-cli doctor
`.trim()

async function main() {
  const args = process.argv.slice(2)
  const command = args[0]

  if (!command || command === '--help' || command === 'help' || command === '-h') {
    console.log(USAGE)
    return
  }

  if (command === '--version' || command === 'version' || command === '-v') {
    console.log(`quaere-cli v${__VERSION__}`)
    return
  }

  if (command === 'install') {
    const agentArg = args.find((a: string) => ['all', 'claude', 'codex'].includes(a))
    const agent = (agentArg as Agent | undefined) ?? 'auto'
    const force = args.includes('--force')
    await runInstall(agent, { force })
    return
  }

  if (command === 'list') {
    runList()
    return
  }

  if (command === 'update') {
    await runUpdate()
    return
  }

  if (command === 'doctor') {
    runDoctor()
    return
  }

  console.error(`Unknown command: ${command}`)
  console.error('Run quaere-cli --help for usage.')
  process.exit(1)
}

main().catch(err => {
  console.error((err as Error).message)
  process.exit(1)
})
