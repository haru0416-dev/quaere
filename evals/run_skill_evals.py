#!/usr/bin/env python3
"""Portable skill evaluation runner for Codex, Claude Code, and similar CLIs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "evals" / "scenarios.json"
DEFAULT_SKILLS_DIR = ROOT / "skills"
DEFAULT_OUTPUT_DIR = ROOT / "eval-results"


@dataclass(frozen=True)
class Scenario:
    id: str
    skill: str
    prompt: str
    expected: list[str]
    assertions: list[dict[str, Any]]
    workspace: str | None


@dataclass(frozen=True)
class Runner:
    name: str
    command: str


@dataclass(frozen=True)
class EvalJob:
    runner: Runner
    scenario: Scenario
    mode: str
    prompt: str
    run_dir: Path
    workspace_dir: Path


def load_scenarios(path: Path) -> list[Scenario]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_scenarios = data.get("scenarios")
    if not isinstance(raw_scenarios, list):
        raise ValueError(f"{path}: scenarios must be a list")

    scenarios: list[Scenario] = []
    for index, raw in enumerate(raw_scenarios):
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: scenario {index} must be an object")
        scenario_id = require_str(raw, "id", path, index)
        skill = require_str(raw, "skill", path, index)
        prompt = require_str(raw, "prompt", path, index)
        expected = raw.get("expected", [])
        assertions = raw.get("assertions", [])
        workspace = raw.get("workspace")
        if not isinstance(expected, list) or not all(isinstance(item, str) for item in expected):
            raise ValueError(f"{path}: scenario {scenario_id!r} expected must be a list of strings")
        if not isinstance(assertions, list) or not all(isinstance(item, dict) for item in assertions):
            raise ValueError(f"{path}: scenario {scenario_id!r} assertions must be a list of objects")
        if workspace is not None and not isinstance(workspace, str):
            raise ValueError(f"{path}: scenario {scenario_id!r} workspace must be a string when present")
        scenarios.append(
            Scenario(
                id=scenario_id,
                skill=skill,
                prompt=prompt,
                expected=expected,
                assertions=assertions,
                workspace=workspace,
            )
        )
    return scenarios


def require_str(raw: dict[str, Any], key: str, path: Path, index: int) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{path}: scenario {index} missing non-empty string {key}")
    return value


def parse_runner(value: str) -> Runner:
    if "=" not in value:
        raise argparse.ArgumentTypeError("runner must be NAME=COMMAND_TEMPLATE")
    name, command = value.split("=", 1)
    name = name.strip()
    command = command.strip()
    if not name or not command:
        raise argparse.ArgumentTypeError("runner name and command template must be non-empty")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        raise argparse.ArgumentTypeError("runner name may contain only letters, digits, dot, dash, and underscore")
    return Runner(name=name, command=command)


def filter_scenarios(scenarios: list[Scenario], skill: str | None, scenario_ids: set[str]) -> list[Scenario]:
    selected = scenarios
    if skill:
        selected = [scenario for scenario in selected if scenario.skill == skill]
    if scenario_ids:
        selected = [scenario for scenario in selected if scenario.id in scenario_ids]
    return selected


def read_skill(skill_name: str, skills_dir: Path) -> tuple[Path, str]:
    skill_path = skills_dir / skill_name / "SKILL.md"
    if not skill_path.exists():
        raise FileNotFoundError(f"missing skill file for {skill_name!r}: {skill_path}")
    return skill_path, skill_path.read_text(encoding="utf-8")


def build_prompt(scenario: Scenario, mode: str, skills_dir: Path) -> str:
    if mode == "with-skill":
        skill_path, skill_text = read_skill(scenario.skill, skills_dir)
        skill_block = f"""Use this skill definition as the governing workflow for the task.

Skill path: {skill_path}

```markdown
{skill_text}
```
"""
    elif mode == "baseline":
        skill_block = "No skill definition is provided. Handle the task using only your default behavior.\n"
    else:
        raise ValueError(f"unknown mode: {mode}")

    return f"""You are running a portable agent-skill evaluation.

{skill_block}
Task:
{scenario.prompt}

Evaluation run rules:
- Work only in the current workspace.
- Follow the user's task exactly.
- Do not mention or optimize for a hidden rubric.
- If the task cannot be completed because required project files or fixtures are absent, say what evidence or files are missing and what the next safe probe would be.
"""


def create_job(
    runner: Runner,
    scenario: Scenario,
    mode: str,
    output_root: Path,
    skills_dir: Path,
    workspace_source: Path | None,
) -> EvalJob:
    run_dir = output_root / runner.name / scenario.skill / scenario.id / mode
    workspace_dir = run_dir / "workspace"
    prompt = build_prompt(scenario, mode, skills_dir)
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    if workspace_source:
        if not workspace_source.is_dir():
            raise FileNotFoundError(f"workspace source does not exist or is not a directory: {workspace_source}")
        ignore = shutil.ignore_patterns(".git", "eval-results", ".agent-state", "__pycache__", ".pytest_cache")
        shutil.copytree(workspace_source, workspace_dir, ignore=ignore)
    else:
        workspace_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    return EvalJob(
        runner=runner,
        scenario=scenario,
        mode=mode,
        prompt=prompt,
        run_dir=run_dir,
        workspace_dir=workspace_dir,
    )


def resolve_scenario_workspace(scenario: Scenario, scenarios_path: Path) -> Path | None:
    if scenario.workspace is None:
        return None
    workspace = Path(scenario.workspace)
    if not workspace.is_absolute():
        workspace = scenarios_path.parent / workspace
    return workspace.resolve()


def render_command(command_template: str, job: EvalJob, prompt_file: Path, output_file: Path) -> str:
    values = {
        "prompt_file": str(prompt_file),
        "output_file": str(output_file),
        "workspace": str(job.workspace_dir),
        "run_dir": str(job.run_dir),
        "scenario_id": job.scenario.id,
        "skill": job.scenario.skill,
        "mode": job.mode,
    }
    try:
        return Template(command_template).safe_substitute(values)
    except ValueError as exc:
        raise ValueError(f"invalid command template for runner {job.runner.name}: {exc}") from exc


def run_job(job: EvalJob, timeout_seconds: int, dry_run: bool) -> dict[str, Any]:
    prompt_file = job.run_dir / "prompt.md"
    output_file = job.run_dir / "output.txt"
    stderr_file = job.run_dir / "stderr.txt"
    metadata_file = job.run_dir / "metadata.json"
    grade_file = job.run_dir / "grade.json"

    prompt_file.write_text(job.prompt, encoding="utf-8")
    command = render_command(job.runner.command, job, prompt_file, output_file)
    started = dt.datetime.now(dt.timezone.utc)

    metadata: dict[str, Any] = {
        "runner": job.runner.name,
        "command": command,
        "scenario_id": job.scenario.id,
        "skill": job.scenario.skill,
        "mode": job.mode,
        "started_at": started.isoformat(),
        "workspace": str(job.workspace_dir),
        "prompt_file": str(prompt_file),
        "output_file": str(output_file),
        "dry_run": dry_run,
    }

    if dry_run:
        metadata.update(
            {
                "exit_code": None,
                "duration_seconds": 0,
                "status": "dry-run",
            }
        )
        output_file.write_text("", encoding="utf-8")
        stderr_file.write_text("", encoding="utf-8")
    else:
        try:
            completed = subprocess.run(
                command,
                cwd=job.workspace_dir,
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds,
                check=False,
            )
            exit_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
            status = "passed-command" if completed.returncode == 0 else "failed-command"
        except subprocess.TimeoutExpired as exc:
            exit_code = 124
            stdout = decode_timeout_stream(exc.stdout)
            stderr = decode_timeout_stream(exc.stderr)
            status = "timeout"
        finished = dt.datetime.now(dt.timezone.utc)
        if stdout or not output_file.exists():
            output_file.write_text(stdout, encoding="utf-8")
        stderr_file.write_text(stderr, encoding="utf-8")
        metadata.update(
            {
                "exit_code": exit_code,
                "finished_at": finished.isoformat(),
                "duration_seconds": round((finished - started).total_seconds(), 3),
                "status": status,
            }
        )

    metadata_file.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    grade = grade_output(job.scenario, output_file.read_text(encoding="utf-8"), metadata)
    # grade.json is written after finalize_cross_mode_assertions so cross-mode
    # checks (e.g., not_in_baseline) can update assertion results before the
    # file is committed to disk.
    return {"metadata": metadata, "grade": grade, "grade_file": grade_file, "output_file": output_file}


def grade_output(scenario: Scenario, output: str, metadata: dict[str, Any]) -> dict[str, Any]:
    if metadata.get("dry_run"):
        manual = [
            {
                "name": item,
                "status": "manual",
                "note": "Dry run only; review the generated prompt for this behavior.",
            }
            for item in scenario.expected
        ]
        skipped_assertions = [
            {
                "name": str(assertion.get("name") or assertion.get("type") or "unnamed"),
                "type": assertion.get("type"),
                "status": "manual",
                "detail": "Dry run did not invoke a runner, so output assertions were not evaluated.",
            }
            for assertion in scenario.assertions
        ]
        return {
            "scenario_id": scenario.id,
            "skill": scenario.skill,
            "status": "manual-only",
            "assertions": skipped_assertions,
            "manual_rubric": manual,
            "summary": {
                "assertions_passed": 0,
                "assertions_failed": 0,
                "manual_items": len(manual),
            },
        }

    assertion_results = [evaluate_assertion(assertion, output, metadata) for assertion in scenario.assertions]
    passed = sum(1 for result in assertion_results if result["status"] == "pass")
    failed = sum(1 for result in assertion_results if result["status"] == "fail")
    manual = [
        {
            "name": item,
            "status": "manual",
            "note": "Review the output for this behavior; no deterministic assertion is configured.",
        }
        for item in scenario.expected
    ]
    status = "manual-only"
    if assertion_results:
        status = "pass" if failed == 0 else "fail"
    return {
        "scenario_id": scenario.id,
        "skill": scenario.skill,
        "status": status,
        "assertions": assertion_results,
        "manual_rubric": manual,
        "summary": {
            "assertions_passed": passed,
            "assertions_failed": failed,
            "manual_items": len(manual),
        },
    }


def decode_timeout_stream(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def evaluate_assertion(assertion: dict[str, Any], output: str, metadata: dict[str, Any]) -> dict[str, Any]:
    name = str(assertion.get("name") or assertion.get("type") or "unnamed")
    assertion_type = assertion.get("type")
    if assertion_type == "contains":
        needle = str(assertion.get("text", ""))
        ok = needle in output
        detail = f"required text {needle!r}"
    elif assertion_type == "contains_any":
        needles = list_of_strings(assertion.get("texts", []))
        ok = any(needle in output for needle in needles)
        detail = f"required any of {needles!r}"
    elif assertion_type == "not_contains":
        needle = str(assertion.get("text", ""))
        ok = needle not in output
        detail = f"forbidden text {needle!r}"
    elif assertion_type == "regex":
        pattern = str(assertion.get("pattern", ""))
        ok = re.search(pattern, output, flags=re.MULTILINE) is not None
        detail = f"required regex {pattern!r}"
    elif assertion_type == "exit_code":
        expected = assertion.get("value", 0)
        ok = metadata.get("exit_code") == expected
        detail = f"expected exit_code {expected!r}, got {metadata.get('exit_code')!r}"
    elif assertion_type == "ordered_sections":
        patterns = list_of_strings(assertion.get("patterns", []))
        cursor = 0
        missing: list[str] = []
        for pattern in patterns:
            try:
                match = re.search(pattern, output[cursor:], flags=re.MULTILINE)
            except re.error as exc:
                return {
                    "name": name,
                    "type": assertion_type,
                    "status": "fail",
                    "detail": f"invalid regex {pattern!r}: {exc}",
                }
            if match is None:
                missing.append(pattern)
                break
            cursor += match.end()
        ok = not missing
        detail = (
            f"required {len(patterns)} patterns in order; all matched"
            if ok
            else f"missing or out-of-order at {missing[0]!r} (matched {len(patterns) - len(missing)} of {len(patterns)})"
        )
    elif assertion_type == "min_section_count":
        pattern = str(assertion.get("pattern", ""))
        try:
            min_count = int(assertion.get("min", 1))
        except (TypeError, ValueError):
            return {
                "name": name,
                "type": assertion_type,
                "status": "fail",
                "detail": f"min must be an integer; got {assertion.get('min')!r}",
            }
        try:
            found = len(re.findall(pattern, output, flags=re.MULTILINE))
        except re.error as exc:
            return {
                "name": name,
                "type": assertion_type,
                "status": "fail",
                "detail": f"invalid regex {pattern!r}: {exc}",
            }
        ok = found >= min_count
        detail = f"required at least {min_count} matches of {pattern!r}; found {found}"
    elif assertion_type == "requires_pair":
        if_pattern = str(assertion.get("if_contains", ""))
        must_pattern = str(assertion.get("must_also_contain", ""))
        try:
            antecedent = re.search(if_pattern, output, flags=re.MULTILINE)
            consequent = re.search(must_pattern, output, flags=re.MULTILINE)
        except re.error as exc:
            return {
                "name": name,
                "type": assertion_type,
                "status": "fail",
                "detail": f"invalid regex in pair: {exc}",
            }
        if antecedent is None:
            ok = True
            detail = f"{if_pattern!r} not present; pair check vacuously satisfied"
        else:
            ok = consequent is not None
            detail = (
                f"{if_pattern!r} present; required pair {must_pattern!r} present"
                if ok
                else f"{if_pattern!r} present but required pair {must_pattern!r} missing"
            )
    elif assertion_type == "not_in_baseline":
        # Cross-mode check; resolved by finalize_cross_mode_assertions after all
        # runs in the same (runner, scenario) pair are complete.
        patterns = list_of_strings(assertion.get("patterns", []))
        return {
            "name": name,
            "type": assertion_type,
            "status": "pending",
            "detail": "awaiting cross-mode evaluation against baseline",
            "patterns": patterns,
        }
    else:
        return {
            "name": name,
            "type": assertion_type,
            "status": "manual",
            "detail": "Unknown assertion type; review manually.",
        }
    return {
        "name": name,
        "type": assertion_type,
        "status": "pass" if ok else "fail",
        "detail": detail,
    }


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def recompute_grade_status(grade: dict[str, Any]) -> None:
    """Recompute grade status and summary counters from current assertion list."""
    assertion_results = grade.get("assertions", [])
    passed = sum(1 for r in assertion_results if r.get("status") == "pass")
    failed = sum(1 for r in assertion_results if r.get("status") == "fail")
    pending = sum(1 for r in assertion_results if r.get("status") == "pending")
    inconclusive = sum(1 for r in assertion_results if r.get("status") == "inconclusive")
    if not assertion_results:
        grade["status"] = "manual-only"
    elif failed:
        grade["status"] = "fail"
    elif pending:
        grade["status"] = "pending"
    elif inconclusive:
        grade["status"] = "inconclusive"
    else:
        grade["status"] = "pass"
    summary = grade.setdefault("summary", {})
    summary["assertions_passed"] = passed
    summary["assertions_failed"] = failed
    summary["assertions_pending"] = pending
    summary["assertions_inconclusive"] = inconclusive


def finalize_cross_mode_assertions(results: list[dict[str, Any]]) -> None:
    """Resolve assertions that need both baseline and with-skill output (e.g. not_in_baseline)."""
    pairs: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = {}
    for result in results:
        meta = result["metadata"]
        key = (meta["runner"], meta["skill"], meta["scenario_id"])
        pairs.setdefault(key, {})[meta["mode"]] = result

    for modes in pairs.values():
        with_skill = modes.get("with-skill")
        baseline = modes.get("baseline")
        for result in modes.values():
            if result["metadata"].get("dry_run"):
                continue
            grade = result["grade"]
            mutated = False
            for assertion in grade.get("assertions", []):
                if assertion.get("status") != "pending":
                    continue
                if assertion.get("type") != "not_in_baseline":
                    continue
                # not_in_baseline only meaningful on the with-skill side, and only when both modes ran.
                if result["metadata"]["mode"] != "with-skill":
                    assertion["status"] = "inconclusive"
                    assertion["detail"] = "not_in_baseline only evaluated against with-skill output"
                    mutated = True
                    continue
                if baseline is None:
                    assertion["status"] = "inconclusive"
                    assertion["detail"] = "not_in_baseline requires --mode both for this scenario"
                    mutated = True
                    continue
                ws_output = Path(with_skill["output_file"]).read_text(encoding="utf-8") if with_skill else ""
                bl_output = Path(baseline["output_file"]).read_text(encoding="utf-8")
                patterns = assertion.get("patterns", [])
                missing_in_ws = []
                appears_in_bl = []
                for pattern in patterns:
                    try:
                        in_ws = re.search(pattern, ws_output, flags=re.MULTILINE) is not None
                        in_bl = re.search(pattern, bl_output, flags=re.MULTILINE) is not None
                    except re.error as exc:
                        assertion["status"] = "fail"
                        assertion["detail"] = f"invalid regex {pattern!r}: {exc}"
                        mutated = True
                        break
                    if not in_ws:
                        missing_in_ws.append(pattern)
                    if in_bl:
                        appears_in_bl.append(pattern)
                else:
                    if missing_in_ws:
                        assertion["status"] = "fail"
                        assertion["detail"] = f"with-skill output missing required patterns: {missing_in_ws}"
                    elif appears_in_bl:
                        assertion["status"] = "fail"
                        assertion["detail"] = (
                            f"baseline output already contained patterns; skill effect not isolated: {appears_in_bl}"
                        )
                    else:
                        assertion["status"] = "pass"
                        assertion["detail"] = (
                            f"all {len(patterns)} patterns present in with-skill output and absent in baseline"
                        )
                    mutated = True
            if mutated:
                recompute_grade_status(grade)


def write_summary(output_root: Path, results: list[dict[str, Any]]) -> Path:
    summary_path = output_root / "summary.json"
    totals = {
        "runs": len(results),
        "failed_commands": sum(1 for item in results if item["metadata"].get("status") == "failed-command"),
        "timeouts": sum(1 for item in results if item["metadata"].get("status") == "timeout"),
        "passed_assertion_runs": sum(1 for item in results if item["grade"].get("status") == "pass"),
        "failed_assertion_runs": sum(1 for item in results if item["grade"].get("status") == "fail"),
        "pending_assertion_runs": sum(1 for item in results if item["grade"].get("status") == "pending"),
        "inconclusive_assertion_runs": sum(1 for item in results if item["grade"].get("status") == "inconclusive"),
        "manual_only_runs": sum(1 for item in results if item["grade"].get("status") == "manual-only"),
        "runs_with_assertions": sum(1 for item in results if item["grade"].get("assertions")),
    }
    public_runs = [{"metadata": item["metadata"], "grade": item["grade"]} for item in results]
    summary = {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "output_root": str(output_root),
        "totals": totals,
        "runs": public_runs,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary_path


def mode_list(value: str) -> list[str]:
    if value == "both":
        return ["baseline", "with-skill"]
    if value in {"baseline", "with-skill"}:
        return [value]
    raise argparse.ArgumentTypeError("mode must be one of: with-skill, baseline, both")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--runner", action="append", type=parse_runner, required=True)
    parser.add_argument("--skill", help="Run only scenarios for one skill.")
    parser.add_argument("--scenario", action="append", default=[], help="Run only the named scenario ID. Repeatable.")
    parser.add_argument("--mode", type=mode_list, default=["with-skill"])
    parser.add_argument("--workspace-source", type=Path, help="Directory copied into each isolated run workspace.")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--dry-run", action="store_true", help="Write prompts and metadata without invoking runners.")
    parser.add_argument("--fail-on-grade", action="store_true", help="Exit non-zero on command or assertion failure.")
    parser.add_argument(
        "--require-assertions",
        action="store_true",
        help="Exit non-zero if any run was graded manual-only (no deterministic assertions evaluated).",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    scenarios = filter_scenarios(load_scenarios(args.scenarios), args.skill, set(args.scenario))
    if not scenarios:
        print("No scenarios matched.", file=sys.stderr)
        return 2

    output_root = args.output_dir / dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for runner in args.runner:
        for scenario in scenarios:
            for mode in args.mode:
                workspace_source = args.workspace_source
                if workspace_source is not None:
                    workspace_source = workspace_source.resolve()
                else:
                    workspace_source = resolve_scenario_workspace(scenario, args.scenarios)
                job = create_job(
                    runner=runner,
                    scenario=scenario,
                    mode=mode,
                    output_root=output_root,
                    skills_dir=args.skills_dir,
                    workspace_source=workspace_source,
                )
                result = run_job(job, timeout_seconds=args.timeout, dry_run=args.dry_run)
                results.append(result)

    finalize_cross_mode_assertions(results)

    for result in results:
        result["grade_file"].write_text(
            json.dumps(result["grade"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        meta = result["metadata"]
        print(
            f"{meta['runner']}/{meta['scenario_id']}/{meta['mode']}: "
            f"{meta['status']} / {result['grade']['status']}"
        )

    summary_path = write_summary(output_root, results)
    print(f"summary: {summary_path}")

    failed = False
    if args.fail_on_grade:
        if any(
            result["metadata"].get("status") in {"failed-command", "timeout"}
            or result["grade"].get("status") == "fail"
            for result in results
        ):
            failed = True
    if args.require_assertions:
        manual_only = [
            f"{result['metadata']['runner']}/{result['metadata']['scenario_id']}/{result['metadata']['mode']}"
            for result in results
            if result["grade"].get("status") == "manual-only"
        ]
        if manual_only:
            print(
                f"--require-assertions: {len(manual_only)} run(s) lack deterministic assertions:",
                file=sys.stderr,
            )
            for label in manual_only:
                print(f"  - {label}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
