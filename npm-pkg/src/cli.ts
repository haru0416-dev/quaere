import { defineCommand, runMain } from 'citty'
import { runDoctor } from './commands/doctor.js'
import { runInstall } from './commands/install.js'
import { runList } from './commands/list.js'
import { runUpdate } from './commands/update.js'
import type { Agent } from './lib/paths.js'

declare const __VERSION__: string

const installCommand = defineCommand({
  meta: {
    name: 'install',
    description: 'Install skills to ~/.claude/skills and/or ~/.agents/skills',
  },
  args: {
    agent: {
      type: 'positional',
      required: false,
      description: 'Target agent: all | claude | codex (default: auto-detect)',
    },
    force: {
      type: 'boolean',
      description: 'Force reinstall even if already up to date',
    },
  },
  async run({ args }) {
    const agentArg = args.agent
    if (agentArg && !['all', 'claude', 'codex'].includes(agentArg)) {
      console.error(`error: unknown agent "${agentArg}" (expected: all | claude | codex)`)
      process.exit(2)
    }
    const agent = (agentArg as Agent | undefined) ?? 'auto'
    await runInstall(agent, { force: args.force })
  },
})

const listCommand = defineCommand({
  meta: {
    name: 'list',
    description: 'Show installed skills and version',
  },
  run() {
    runList()
  },
})

const updateCommand = defineCommand({
  meta: {
    name: 'update',
    description: 'Check GitHub for a newer release',
  },
  async run() {
    await runUpdate()
  },
})

const doctorCommand = defineCommand({
  meta: {
    name: 'doctor',
    description: 'Validate installed skill integrity',
  },
  run() {
    runDoctor()
  },
})

const main = defineCommand({
  meta: {
    name: 'quaere-cli',
    version: __VERSION__,
    description: 'Install Quaere process-correction skills for Claude Code and Codex',
  },
  subCommands: {
    install: installCommand,
    list: listCommand,
    update: updateCommand,
    doctor: doctorCommand,
  },
})

runMain(main)
