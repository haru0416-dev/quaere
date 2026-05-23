#!/usr/bin/env node

// src/commands/install.ts
import { cpSync, existsSync as existsSync3, mkdirSync as mkdirSync2, renameSync as renameSync2, rmSync } from "fs";
import { join as join4 } from "path";

// src/lib/manifest.ts
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "fs";
import { join } from "path";
function readManifest(targetDir) {
  const p = join(targetDir, ".quaere", "manifest.json");
  if (!existsSync(p)) return null;
  try {
    return JSON.parse(readFileSync(p, "utf-8"));
  } catch {
    return null;
  }
}
function writeManifest(targetDir, manifest) {
  const dir = join(targetDir, ".quaere");
  mkdirSync(dir, { recursive: true });
  const p = join(dir, "manifest.json");
  const tmp = `${p}.tmp`;
  writeFileSync(tmp, JSON.stringify(manifest, null, 2) + "\n", "utf-8");
  renameSync(tmp, p);
}
function mergeManifest(existing, version, newSkills) {
  const skills = /* @__PURE__ */ new Set([...existing?.skills ?? [], ...newSkills]);
  return { quaere_version: version, skills: [...skills].sort() };
}

// src/lib/paths.ts
import { existsSync as existsSync2 } from "fs";
import { homedir } from "os";
import { dirname, join as join2 } from "path";
import { fileURLToPath } from "url";
var distDir = dirname(fileURLToPath(import.meta.url));
function getPackageSkillsDir() {
  return join2(distDir, "..", "skills");
}
function getClaudeSkillsDir() {
  return join2(homedir(), ".claude", "skills");
}
function getCodexSkillsDir() {
  return join2(homedir(), ".agents", "skills");
}
function resolveTargetDirs(agent) {
  if (agent === "claude") return [getClaudeSkillsDir()];
  if (agent === "codex") return [getCodexSkillsDir()];
  if (agent === "all") return [getClaudeSkillsDir(), getCodexSkillsDir()];
  const hasClaude = existsSync2(join2(homedir(), ".claude"));
  const hasCodex = existsSync2(join2(homedir(), ".agents"));
  if (hasClaude && hasCodex) return [getClaudeSkillsDir(), getCodexSkillsDir()];
  if (hasCodex) return [getCodexSkillsDir()];
  return [getClaudeSkillsDir()];
}

// src/lib/skills.ts
import { readdirSync } from "fs";
import { join as join3 } from "path";
function getBundledSkills() {
  const skillsDir = getPackageSkillsDir();
  return readdirSync(skillsDir, { withFileTypes: true }).filter((d) => d.isDirectory() && /^quaere-/.test(d.name)).map((d) => ({ name: d.name, dir: join3(skillsDir, d.name) })).sort((a, b) => a.name.localeCompare(b.name));
}

// src/commands/install.ts
async function runInstall(agent, opts = {}) {
  const skills = getBundledSkills();
  if (skills.length === 0) {
    console.error("error: no bundled skills found \u2014 package may be corrupted");
    process.exit(1);
  }
  const targets = resolveTargetDirs(agent);
  for (const targetDir of targets) {
    mkdirSync2(targetDir, { recursive: true });
    const installed = [];
    const skipped = [];
    for (const skill of skills) {
      const dest = join4(targetDir, skill.name);
      const staging = join4(targetDir, `.${skill.name}.staging`);
      const backup = join4(targetDir, `.${skill.name}.backup`);
      if (!opts.force && existsSync3(dest)) {
        const existing2 = readManifest(targetDir);
        if (existing2?.quaere_version === "0.3.2" && existing2.skills.includes(skill.name)) {
          skipped.push(skill.name);
          continue;
        }
      }
      rmSync(staging, { recursive: true, force: true });
      cpSync(skill.dir, staging, { recursive: true });
      if (existsSync3(dest)) {
        rmSync(backup, { recursive: true, force: true });
        renameSync2(dest, backup);
      }
      renameSync2(staging, dest);
      rmSync(backup, { recursive: true, force: true });
      installed.push(skill.name);
    }
    if (installed.length === 0 && skipped.length > 0) {
      console.log(`
${targetDir}`);
      console.log(`  Already up to date (${skipped.length} skill${skipped.length === 1 ? "" : "s"}, v${"0.3.2"})`);
      console.log("  Use --force to reinstall anyway.");
      continue;
    }
    const existing = readManifest(targetDir);
    writeManifest(targetDir, mergeManifest(existing, "0.3.2", installed));
    console.log(`
Installed to ${targetDir}:`);
    for (const name of installed) {
      console.log(`  \u2713 ${name}`);
    }
    if (skipped.length > 0) {
      console.log(`  (skipped ${skipped.length} already up-to-date)`);
    }
    console.log();
    console.log("Commands:");
    for (const { name } of skills) {
      console.log(`  /${name}`);
    }
  }
}

// src/commands/list.ts
import { existsSync as existsSync4 } from "fs";
var TARGETS = [
  { label: "Claude Code", dir: getClaudeSkillsDir() },
  { label: "Codex CLI", dir: getCodexSkillsDir() }
];
function runList() {
  let found = false;
  for (const { label, dir } of TARGETS) {
    const manifest = readManifest(dir);
    if (!manifest) continue;
    found = true;
    console.log(`
${label}  (${dir})`);
    console.log(`  version  ${manifest.quaere_version}`);
    if (manifest.skills.length === 0) {
      console.log("  (no skills recorded)");
      continue;
    }
    for (const name of manifest.skills) {
      const onDisk = existsSync4(dir + "/" + name);
      const marker = onDisk ? "\u2713" : "\u2717";
      const note = onDisk ? "" : "  [missing on disk]";
      console.log(`  ${marker} ${name}${note}`);
    }
  }
  if (!found) {
    console.log("No Quaere skills installed.");
    console.log("Run: npx quaere-cli install");
  }
}

// src/commands/update.ts
var REPO = "haru0416-dev/quaere";
var API_URL = `https://api.github.com/repos/${REPO}/releases/latest`;
function compareSemver(a, b) {
  const parse = (s) => s.replace(/^v/, "").split(".").map(Number);
  const [aMaj = 0, aMin = 0, aPat = 0] = parse(a);
  const [bMaj = 0, bMin = 0, bPat = 0] = parse(b);
  if (aMaj !== bMaj) return aMaj > bMaj ? 1 : -1;
  if (aMin !== bMin) return aMin > bMin ? 1 : -1;
  if (aPat !== bPat) return aPat > bPat ? 1 : -1;
  return 0;
}
async function runUpdate() {
  console.log(`Current version: v${"0.3.2"}`);
  console.log("Checking GitHub for latest release\u2026");
  let res;
  try {
    res = await fetch(API_URL, {
      headers: {
        "User-Agent": `quaere-cli/${"0.3.2"}`,
        Accept: "application/vnd.github+json"
      }
    });
  } catch (err) {
    console.error(`error: could not reach GitHub \u2014 ${err.message}`);
    process.exit(1);
  }
  if (!res.ok) {
    console.error(`error: GitHub API returned ${res.status}`);
    process.exit(1);
  }
  const data = await res.json();
  const latest = data.tag_name;
  if (!latest) {
    console.error("error: unexpected API response (missing tag_name)");
    process.exit(1);
  }
  const cmp = compareSemver(latest, "0.3.2");
  if (cmp <= 0) {
    console.log(`Already up to date (${latest}).`);
    return;
  }
  console.log(`
New version available: ${latest}`);
  console.log();
  console.log("To update:");
  console.log(`  npx quaere-cli@${latest} install`);
  console.log(`  bunx quaere-cli@${latest} install`);
  if (data.html_url) {
    console.log();
    console.log(`Release notes: ${data.html_url}`);
  }
}

// src/commands/doctor.ts
import { existsSync as existsSync5, readFileSync as readFileSync2, readdirSync as readdirSync2 } from "fs";
import { join as join5 } from "path";

// src/lib/frontmatter.ts
function parseFrontmatter(content) {
  const lines = content.split("\n");
  if (lines[0]?.trim() !== "---") return null;
  let endIdx = -1;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i]?.trim() === "---") {
      endIdx = i;
      break;
    }
  }
  if (endIdx === -1) return null;
  const result = {};
  let currentKey = "";
  let isBlock = false;
  const blockLines = [];
  const flushBlock = () => {
    if (currentKey && isBlock) {
      result[currentKey] = blockLines.join("\n").trimEnd();
      blockLines.length = 0;
      isBlock = false;
    }
  };
  for (let i = 1; i < endIdx; i++) {
    const line = lines[i] ?? "";
    const keyMatch = /^([a-zA-Z][\w-]*):\s*(.*)$/.exec(line);
    if (keyMatch) {
      flushBlock();
      currentKey = keyMatch[1] ?? "";
      const val = (keyMatch[2] ?? "").trim();
      if (val === "|" || val === ">") {
        isBlock = true;
      } else {
        result[currentKey] = val;
      }
    } else if (isBlock) {
      blockLines.push(line.replace(/^  /, ""));
    }
  }
  flushBlock();
  return result;
}

// src/commands/doctor.ts
var MAX_LINES = 500;
var KEBAB_RE = /^[a-z][a-z0-9]*(-[a-z0-9]+)*$/;
function checkSkill(skillDir, name) {
  const issues = [];
  const skillMd = join5(skillDir, "SKILL.md");
  if (!existsSync5(skillMd)) {
    issues.push("SKILL.md not found");
    return issues;
  }
  const content = readFileSync2(skillMd, "utf-8");
  const lineCount = content.split("\n").length;
  if (lineCount > MAX_LINES) {
    issues.push(`SKILL.md exceeds ${MAX_LINES} lines (${lineCount} lines)`);
  }
  const fm = parseFrontmatter(content);
  if (!fm) {
    issues.push("SKILL.md missing or malformed frontmatter");
    return issues;
  }
  if (!fm.name) {
    issues.push("frontmatter missing required field: name");
  } else {
    if (fm.name !== name) {
      issues.push(`name mismatch: frontmatter says "${fm.name}", directory is "${name}"`);
    }
    if (!KEBAB_RE.test(fm.name)) {
      issues.push(`name "${fm.name}" is not valid kebab-case`);
    }
  }
  if (!fm.description) {
    issues.push("frontmatter missing required field: description");
  } else {
    const desc = fm.description.trimStart();
    if (desc.length < 80) {
      issues.push(`description is too short (${desc.length} chars, minimum 80)`);
    }
  }
  if (!fm.compatibility) {
    issues.push("frontmatter missing required field: compatibility");
  }
  if (!fm.license) {
    issues.push("frontmatter missing required field: license");
  } else if (fm.license.toUpperCase() !== "MIT") {
    issues.push(`license must be MIT, got "${fm.license}"`);
  }
  return issues;
}
function checkTarget(label, dir) {
  const result = { label, dir, issues: [], ok: [], orphans: [] };
  const manifest = readManifest(dir);
  if (!manifest) {
    return result;
  }
  const manifestedSet = new Set(manifest.skills);
  for (const name of manifest.skills) {
    const skillDir = join5(dir, name);
    if (!existsSync5(skillDir)) {
      result.issues.push({ skill: name, message: "recorded in manifest but not found on disk" });
      continue;
    }
    const problems = checkSkill(skillDir, name);
    if (problems.length > 0) {
      for (const msg of problems) result.issues.push({ skill: name, message: msg });
    } else {
      result.ok.push(name);
    }
  }
  if (existsSync5(dir)) {
    const entries = readdirSync2(dir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isDirectory() && /^quaere-/.test(entry.name) && !manifestedSet.has(entry.name)) {
        result.orphans.push(entry.name);
      }
    }
  }
  return result;
}
function runDoctor() {
  const targets = [
    { label: "Claude Code", dir: getClaudeSkillsDir() },
    { label: "Codex CLI", dir: getCodexSkillsDir() }
  ];
  let totalIssues = 0;
  for (const { label, dir } of targets) {
    const result = checkTarget(label, dir);
    const manifest = readManifest(dir);
    if (!manifest) continue;
    console.log(`
${label}  (${dir})`);
    for (const name of result.ok) {
      console.log(`  \u2713 ${name}`);
    }
    for (const { skill, message } of result.issues) {
      console.log(`  \u2717 ${skill}: ${message}`);
      totalIssues++;
    }
    for (const name of result.orphans) {
      console.log(`  ? ${name}: orphan directory (not in manifest) \u2014 run install to adopt or remove manually`);
      totalIssues++;
    }
  }
  if (totalIssues === 0) {
    const checked = targets.filter(({ dir }) => readManifest(dir) !== null).length;
    if (checked === 0) {
      console.log("No Quaere skills installed. Run: npx quaere-cli install");
    } else {
      console.log("\nAll checks passed.");
    }
  } else {
    console.log(`
${totalIssues} issue${totalIssues === 1 ? "" : "s"} found.`);
    process.exit(1);
  }
}

// src/cli.ts
var USAGE = `
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
`.trim();
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  if (!command || command === "--help" || command === "help" || command === "-h") {
    console.log(USAGE);
    return;
  }
  if (command === "--version" || command === "version" || command === "-v") {
    console.log(`quaere-cli v${"0.3.2"}`);
    return;
  }
  if (command === "install") {
    const agentArg = args.find((a) => ["all", "claude", "codex"].includes(a));
    const agent = agentArg ?? "auto";
    const force = args.includes("--force");
    await runInstall(agent, { force });
    return;
  }
  if (command === "list") {
    runList();
    return;
  }
  if (command === "update") {
    await runUpdate();
    return;
  }
  if (command === "doctor") {
    runDoctor();
    return;
  }
  console.error(`Unknown command: ${command}`);
  console.error("Run quaere-cli --help for usage.");
  process.exit(1);
}
main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
