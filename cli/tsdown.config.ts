import { readFileSync } from 'node:fs'
import { defineConfig } from 'tsdown'

const pkg = JSON.parse(readFileSync('./package.json', 'utf-8')) as { version: string }

export default defineConfig({
  entry: ['src/cli.ts'],
  format: 'esm',
  outDir: 'dist',
  banner: { js: '#!/usr/bin/env node' },
  copy: [{ from: '../skills', to: 'dist' }],
  define: {
    __VERSION__: JSON.stringify(pkg.version),
  },
})
