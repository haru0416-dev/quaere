import { cpSync, rmSync } from 'fs'
import { join } from 'path'
import { fileURLToPath } from 'url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))
const srcSkills = join(__dirname, '..', '..', 'skills')
const dstSkills = join(__dirname, '..', 'skills')

rmSync(dstSkills, { recursive: true, force: true })
cpSync(srcSkills, dstSkills, { recursive: true })
console.log(`skills/ copied to ${dstSkills}`)
