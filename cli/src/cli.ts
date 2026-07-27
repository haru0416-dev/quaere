import { defineCommand, runMain } from 'citty'
import { runDoctor } from './commands/doctor.js'
import { runInstall, type InstallOptions } from './commands/install.js'
import { runList } from './commands/list.js'
import { runUpdate } from './commands/update.js'
import type { Agent } from './lib/paths.js'

declare const __VERSION__: string

const installCommand = defineCommand({
  meta: {
    name: 'install',
    description: 'Install the core skills (and optionally extensions) to ~/.claude/skills and/or ~/.agents/skills',
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
    extensions: {
      type: 'boolean',
      description: 'Install all extension skills alongside the core set',
    },
    skill: {
      type: 'string',
      description: 'Install a named extension alongside the core set (repeatable, e.g. --skill audit)',
    },
    profile: {
      type: 'string',
      description: 'Assembly profile: full | lean | contract | auto (default: full; auto = codex→lean, claude→contract)',
    },
  },
  async run({ args }) {
    const agentArg = args.agent
    if (agentArg && !['all', 'claude', 'codex'].includes(agentArg)) {
      console.error(`error: unknown agent "${agentArg}" (expected: all | claude | codex)`)
      process.exit(2)
    }
    const agent = (agentArg as Agent | undefined) ?? 'auto'
    const skillArg = args.skill
    const skills = skillArg ? (Array.isArray(skillArg) ? skillArg : [skillArg]) : undefined
    const profileArg = args.profile
    if (profileArg && !['full', 'lean', 'contract', 'auto'].includes(profileArg)) {
      console.error(`error: unknown profile "${profileArg}" (expected: full | lean | contract | auto)`)
      process.exit(2)
    }
    await runInstall(agent, {
      force: args.force,
      extensions: args.extensions,
      skills,
      profile: profileArg as InstallOptions['profile'],
    })
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
