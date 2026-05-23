#!/usr/bin/env node
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, renameSync, rmSync, writeFileSync } from "fs";
import { dirname, join } from "path";
import { homedir } from "os";
import { fileURLToPath } from "url";
//#region src/lib/manifest.ts
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
	return {
		quaere_version: version,
		skills: [...new Set([...existing?.skills ?? [], ...newSkills])].sort()
	};
}
//#endregion
//#region src/lib/paths.ts
const distDir = dirname(fileURLToPath(import.meta.url));
function getPackageSkillsDir() {
	return join(distDir, "..", "skills");
}
function getClaudeSkillsDir() {
	return join(homedir(), ".claude", "skills");
}
function getCodexSkillsDir() {
	return join(homedir(), ".agents", "skills");
}
function resolveTargetDirs(agent) {
	if (agent === "claude") return [getClaudeSkillsDir()];
	if (agent === "codex") return [getCodexSkillsDir()];
	if (agent === "all") return [getClaudeSkillsDir(), getCodexSkillsDir()];
	const hasClaude = existsSync(join(homedir(), ".claude"));
	const hasCodex = existsSync(join(homedir(), ".agents"));
	if (hasClaude && hasCodex) return [getClaudeSkillsDir(), getCodexSkillsDir()];
	if (hasCodex) return [getCodexSkillsDir()];
	return [getClaudeSkillsDir()];
}
//#endregion
//#region src/lib/skills.ts
function getBundledSkills() {
	const skillsDir = getPackageSkillsDir();
	return readdirSync(skillsDir, { withFileTypes: true }).filter((d) => d.isDirectory() && /^quaere-/.test(d.name)).map((d) => ({
		name: d.name,
		dir: join(skillsDir, d.name)
	})).sort((a, b) => a.name.localeCompare(b.name));
}
//#endregion
//#region src/commands/install.ts
async function runInstall(agent, opts = {}) {
	const skills = getBundledSkills();
	if (skills.length === 0) {
		console.error("error: no bundled skills found — package may be corrupted");
		process.exit(1);
	}
	const targets = resolveTargetDirs(agent);
	for (const targetDir of targets) {
		mkdirSync(targetDir, { recursive: true });
		const installed = [];
		const skipped = [];
		for (const skill of skills) {
			const dest = join(targetDir, skill.name);
			const staging = join(targetDir, `.${skill.name}.staging`);
			const backup = join(targetDir, `.${skill.name}.backup`);
			if (!opts.force && existsSync(dest)) {
				const existing = readManifest(targetDir);
				if (existing?.quaere_version === "0.3.2" && existing.skills.includes(skill.name)) {
					skipped.push(skill.name);
					continue;
				}
			}
			rmSync(staging, {
				recursive: true,
				force: true
			});
			cpSync(skill.dir, staging, { recursive: true });
			if (existsSync(dest)) {
				rmSync(backup, {
					recursive: true,
					force: true
				});
				renameSync(dest, backup);
			}
			renameSync(staging, dest);
			rmSync(backup, {
				recursive: true,
				force: true
			});
			installed.push(skill.name);
		}
		if (installed.length === 0 && skipped.length > 0) {
			console.log(`\n${targetDir}`);
			console.log(`  Already up to date (${skipped.length} skill${skipped.length === 1 ? "" : "s"}, v0.3.2)`);
			console.log("  Use --force to reinstall anyway.");
			continue;
		}
		writeManifest(targetDir, mergeManifest(readManifest(targetDir), "0.3.2", installed));
		console.log(`\nInstalled to ${targetDir}:`);
		for (const name of installed) console.log(`  ✓ ${name}`);
		if (skipped.length > 0) console.log(`  (skipped ${skipped.length} already up-to-date)`);
		console.log();
		console.log("Commands:");
		for (const { name } of skills) console.log(`  /${name}`);
	}
}
//#endregion
//#region src/commands/list.ts
const TARGETS = [{
	label: "Claude Code",
	dir: getClaudeSkillsDir()
}, {
	label: "Codex CLI",
	dir: getCodexSkillsDir()
}];
function runList() {
	let found = false;
	for (const { label, dir } of TARGETS) {
		const manifest = readManifest(dir);
		if (!manifest) continue;
		found = true;
		console.log(`\n${label}  (${dir})`);
		console.log(`  version  ${manifest.quaere_version}`);
		if (manifest.skills.length === 0) {
			console.log("  (no skills recorded)");
			continue;
		}
		for (const name of manifest.skills) {
			const onDisk = existsSync(dir + "/" + name);
			console.log(`  ${onDisk ? "✓" : "✗"} ${name}${onDisk ? "" : "  [missing on disk]"}`);
		}
	}
	if (!found) {
		console.log("No Quaere skills installed.");
		console.log("Run: npx quaere-cli install");
	}
}
//#endregion
//#region src/commands/update.ts
const API_URL = `https://api.github.com/repos/haru0416-dev/quaere/releases/latest`;
/** Compares two semver strings (strips leading 'v'). Returns -1, 0, or 1. */
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
	console.log(`Current version: v0.3.2`);
	console.log("Checking GitHub for latest release…");
	let res;
	try {
		res = await fetch(API_URL, { headers: {
			"User-Agent": `quaere-cli/0.3.2`,
			Accept: "application/vnd.github+json"
		} });
	} catch (err) {
		console.error(`error: could not reach GitHub — ${err.message}`);
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
	if (compareSemver(latest, "0.3.2") <= 0) {
		console.log(`Already up to date (${latest}).`);
		return;
	}
	console.log(`\nNew version available: ${latest}`);
	console.log();
	console.log("To update:");
	console.log(`  npx quaere-cli@${latest} install`);
	console.log(`  bunx quaere-cli@${latest} install`);
	if (data.html_url) {
		console.log();
		console.log(`Release notes: ${data.html_url}`);
	}
}
//#endregion
//#region src/lib/frontmatter.ts
/**
* Parses YAML frontmatter from a Markdown file.
* Handles plain scalar values and block scalars (| and >).
*/
function parseFrontmatter(content) {
	const lines = content.split("\n");
	if (lines[0]?.trim() !== "---") return null;
	let endIdx = -1;
	for (let i = 1; i < lines.length; i++) if (lines[i]?.trim() === "---") {
		endIdx = i;
		break;
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
			if (val === "|" || val === ">") isBlock = true;
			else result[currentKey] = val;
		} else if (isBlock) blockLines.push(line.replace(/^  /, ""));
	}
	flushBlock();
	return result;
}
//#endregion
//#region src/commands/doctor.ts
const MAX_LINES = 500;
const KEBAB_RE = /^[a-z][a-z0-9]*(-[a-z0-9]+)*$/;
function checkSkill(skillDir, name) {
	const issues = [];
	const skillMd = join(skillDir, "SKILL.md");
	if (!existsSync(skillMd)) {
		issues.push("SKILL.md not found");
		return issues;
	}
	const content = readFileSync(skillMd, "utf-8");
	const lineCount = content.split("\n").length;
	if (lineCount > MAX_LINES) issues.push(`SKILL.md exceeds ${MAX_LINES} lines (${lineCount} lines)`);
	const fm = parseFrontmatter(content);
	if (!fm) {
		issues.push("SKILL.md missing or malformed frontmatter");
		return issues;
	}
	if (!fm.name) issues.push("frontmatter missing required field: name");
	else {
		if (fm.name !== name) issues.push(`name mismatch: frontmatter says "${fm.name}", directory is "${name}"`);
		if (!KEBAB_RE.test(fm.name)) issues.push(`name "${fm.name}" is not valid kebab-case`);
	}
	if (!fm.description) issues.push("frontmatter missing required field: description");
	else {
		const desc = fm.description.trimStart();
		if (desc.length < 80) issues.push(`description is too short (${desc.length} chars, minimum 80)`);
	}
	if (!fm.compatibility) issues.push("frontmatter missing required field: compatibility");
	if (!fm.license) issues.push("frontmatter missing required field: license");
	else if (fm.license.toUpperCase() !== "MIT") issues.push(`license must be MIT, got "${fm.license}"`);
	return issues;
}
function checkTarget(label, dir) {
	const result = {
		label,
		dir,
		issues: [],
		ok: [],
		orphans: []
	};
	const manifest = readManifest(dir);
	if (!manifest) return result;
	const manifestedSet = new Set(manifest.skills);
	for (const name of manifest.skills) {
		const skillDir = join(dir, name);
		if (!existsSync(skillDir)) {
			result.issues.push({
				skill: name,
				message: "recorded in manifest but not found on disk"
			});
			continue;
		}
		const problems = checkSkill(skillDir, name);
		if (problems.length > 0) for (const msg of problems) result.issues.push({
			skill: name,
			message: msg
		});
		else result.ok.push(name);
	}
	if (existsSync(dir)) {
		const entries = readdirSync(dir, { withFileTypes: true });
		for (const entry of entries) if (entry.isDirectory() && /^quaere-/.test(entry.name) && !manifestedSet.has(entry.name)) result.orphans.push(entry.name);
	}
	return result;
}
function runDoctor() {
	const targets = [{
		label: "Claude Code",
		dir: getClaudeSkillsDir()
	}, {
		label: "Codex CLI",
		dir: getCodexSkillsDir()
	}];
	let totalIssues = 0;
	for (const { label, dir } of targets) {
		const result = checkTarget(label, dir);
		if (!readManifest(dir)) continue;
		console.log(`\n${label}  (${dir})`);
		for (const name of result.ok) console.log(`  ✓ ${name}`);
		for (const { skill, message } of result.issues) {
			console.log(`  ✗ ${skill}: ${message}`);
			totalIssues++;
		}
		for (const name of result.orphans) {
			console.log(`  ? ${name}: orphan directory (not in manifest) — run install to adopt or remove manually`);
			totalIssues++;
		}
	}
	if (totalIssues === 0) if (targets.filter(({ dir }) => readManifest(dir) !== null).length === 0) console.log("No Quaere skills installed. Run: npx quaere-cli install");
	else console.log("\nAll checks passed.");
	else {
		console.log(`\n${totalIssues} issue${totalIssues === 1 ? "" : "s"} found.`);
		process.exit(1);
	}
}
//#endregion
//#region src/cli.ts
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
`.trim();
async function main() {
	const args = process.argv.slice(2);
	const command = args[0];
	if (!command || command === "--help" || command === "help" || command === "-h") {
		console.log(USAGE);
		return;
	}
	if (command === "--version" || command === "version" || command === "-v") {
		console.log(`quaere-cli v0.3.2`);
		return;
	}
	if (command === "install") {
		await runInstall(args.find((a) => [
			"all",
			"claude",
			"codex"
		].includes(a)) ?? "auto", { force: args.includes("--force") });
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
//#endregion
export {};
