#!/usr/bin/env python3
"""Portable skill evaluation runner for Codex, Claude Code, and similar CLIs."""

from __future__ import annotations

import argparse
import atexit
import contextlib
import datetime as dt
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import signal
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
DEFAULT_LLM_JUDGE_CACHE = ROOT / "evals" / ".llm_judge_cache"
DEFAULT_LLM_JUDGE_MODEL = "claude-haiku-4-5-20251001"
SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9_.-]+$")
# Skill directories an Agent-Skills-aware CLI (Codex, Claude Code) auto-discovers
# at runtime. `--isolate-skills` relocates these for the sweep so a baseline run
# cannot silently read an installed SKILL.md the prompt deliberately omitted.
INSTALLED_SKILL_DIRS = [
    Path.home() / ".agents" / "skills",
    Path.home() / ".claude" / "skills",
]


def require_safe_component(value: str, label: str, path: Path | None = None, index: int | None = None) -> None:
    if SAFE_COMPONENT.fullmatch(value):
        return
    location = ""
    if path is not None and index is not None:
        location = f"{path}: scenario {index} "
    raise ValueError(
        f"{location}{label} {value!r} may contain only letters, digits, dot, dash, and underscore"
    )


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
    run_index: int = 1
    total_runs: int = 1


def load_scenarios(path: Path, extras_path: Path | None = None) -> list[Scenario]:
    raw_scenarios = _load_raw_scenarios(path)
    if extras_path is not None:
        raw_extras = _load_raw_scenarios(extras_path)
        _apply_scenario_extras(raw_scenarios, raw_extras, path, extras_path)
    return _build_scenarios(raw_scenarios, path)


def _load_raw_scenarios(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_scenarios = data.get("scenarios")
    if not isinstance(raw_scenarios, list):
        raise ValueError(f"{path}: scenarios must be a list")
    if not all(isinstance(item, dict) for item in raw_scenarios):
        raise ValueError(f"{path}: every scenarios entry must be an object")
    return raw_scenarios


def _build_scenarios(raw_scenarios: list[dict[str, Any]], path: Path) -> list[Scenario]:
    scenarios: list[Scenario] = []
    for index, raw in enumerate(raw_scenarios):
        scenario_id = require_str(raw, "id", path, index)
        skill = require_str(raw, "skill", path, index)
        require_safe_component(scenario_id, "id", path, index)
        require_safe_component(skill, "skill", path, index)
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


def _apply_scenario_extras(
    main_scenarios: list[dict[str, Any]],
    extra_scenarios: list[dict[str, Any]],
    main_path: Path,
    extras_path: Path,
) -> None:
    """Merge extras into main scenarios in place.

    Match by `id` then by assertion `name`. Locale alternates are appended
    via `|`-alternation onto regex/string fields and concatenated onto
    array fields. Unknown ids or names error out so a stale extras file
    cannot silently drop alternates.
    """
    main_by_id = {scn.get("id"): scn for scn in main_scenarios}
    for extra in extra_scenarios:
        sid = extra.get("id")
        if not isinstance(sid, str) or sid not in main_by_id:
            raise ValueError(
                f"{extras_path}: scenario id {sid!r} not found in {main_path}"
            )
        main_scenario = main_by_id[sid]
        main_assertions = main_scenario.get("assertions", [])
        if not isinstance(main_assertions, list):
            raise ValueError(
                f"{main_path}: scenario {sid!r} assertions must be a list"
            )
        assertions_by_name = {a.get("name"): a for a in main_assertions if isinstance(a, dict)}
        for extra_assertion in extra.get("assertions", []):
            if not isinstance(extra_assertion, dict):
                raise ValueError(
                    f"{extras_path}: scenario {sid!r} extra assertion must be an object"
                )
            name = extra_assertion.get("name")
            if not isinstance(name, str) or name not in assertions_by_name:
                raise ValueError(
                    f"{extras_path}: assertion {name!r} not found in scenario {sid!r}"
                )
            _merge_extra_assertion(
                assertions_by_name[name], extra_assertion, extras_path, sid, name
            )


def _merge_extra_assertion(
    main: dict[str, Any],
    extra: dict[str, Any],
    extras_path: Path,
    sid: str,
    name: str,
) -> None:
    extra_type = extra.get("type")
    if extra_type is not None and extra_type != main.get("type"):
        raise ValueError(
            f"{extras_path}: assertion type mismatch for {sid}/{name} "
            f"(main={main.get('type')!r}, extra={extra_type!r})"
        )
    # Single-string regex/alternation fields.
    for key in ("pattern", "if_contains", "must_also_contain", "skip_when"):
        if key in extra:
            fragment = extra[key]
            if not isinstance(fragment, str) or not fragment:
                raise ValueError(
                    f"{extras_path}: {sid}/{name} {key!r} alternate must be a non-empty string"
                )
            existing = main.get(key)
            if not isinstance(existing, str) or not existing:
                raise ValueError(
                    f"{extras_path}: {sid}/{name} {key!r} alternation requires existing {key} in main"
                )
            main[key] = existing + "|" + fragment
    # Per-position regex alternation (ordered_sections / not_in_baseline).
    if "patterns" in extra:
        fragments = extra["patterns"]
        if not isinstance(fragments, list) or not all(
            isinstance(item, str) for item in fragments
        ):
            raise ValueError(
                f"{extras_path}: {sid}/{name} patterns alternates must be a list of strings"
            )
        existing = main.get("patterns")
        if not isinstance(existing, list):
            raise ValueError(
                f"{extras_path}: {sid}/{name} patterns alternation requires existing patterns list"
            )
        if len(fragments) != len(existing):
            raise ValueError(
                f"{extras_path}: {sid}/{name} patterns length mismatch "
                f"(main={len(existing)}, extra={len(fragments)})"
            )
        for idx, fragment in enumerate(fragments):
            if fragment:
                existing[idx] = existing[idx] + "|" + fragment
    # Array concatenation (contains_any texts).
    if "texts" in extra:
        fragments = extra["texts"]
        if not isinstance(fragments, list) or not all(
            isinstance(item, str) for item in fragments
        ):
            raise ValueError(
                f"{extras_path}: {sid}/{name} texts alternates must be a list of strings"
            )
        existing = main.get("texts")
        if not isinstance(existing, list):
            raise ValueError(
                f"{extras_path}: {sid}/{name} texts concatenation requires existing texts list"
            )
        existing.extend(fragments)


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
    if not SAFE_COMPONENT.fullmatch(name):
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
    # Skills live under skills/core/ or skills/extensions/ (ADR-0010). Fall back to
    # the legacy flat skills/<name>/ layout for compatibility.
    candidates = [
        skills_dir / "core" / skill_name / "SKILL.md",
        skills_dir / "extensions" / skill_name / "SKILL.md",
        skills_dir / skill_name / "SKILL.md",
    ]
    for skill_path in candidates:
        if skill_path.exists():
            return skill_path, skill_path.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"missing skill file for {skill_name!r}: looked in "
        f"{', '.join(str(c) for c in candidates)}"
    )


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
    run_index: int = 1,
    total_runs: int = 1,
) -> EvalJob:
    cell_dir = output_root / runner.name / scenario.skill / scenario.id / mode
    # Single-run sweeps keep the flat .../mode/ layout; repeated runs nest each
    # sample under .../mode/run-NN/ so the per-run artifacts do not clobber.
    run_dir = cell_dir if total_runs == 1 else cell_dir / f"run-{run_index:02d}"
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
        run_index=run_index,
        total_runs=total_runs,
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
        "prompt_file": shlex.quote(str(prompt_file)),
        "output_file": shlex.quote(str(output_file)),
        "workspace": shlex.quote(str(job.workspace_dir)),
        "run_dir": shlex.quote(str(job.run_dir)),
        "scenario_id": shlex.quote(job.scenario.id),
        "skill": shlex.quote(job.scenario.skill),
        "mode": shlex.quote(job.mode),
    }
    try:
        return Template(command_template).safe_substitute(values)
    except ValueError as exc:
        raise ValueError(f"invalid command template for runner {job.runner.name}: {exc}") from exc


def run_job(
    job: EvalJob,
    timeout_seconds: int,
    dry_run: bool,
    *,
    enable_llm_judge: bool = False,
    llm_judge_cache_dir: Path | None = None,
    llm_judge_backend: str = "anthropic",
    llm_judge_base_url: str | None = None,
) -> dict[str, Any]:
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
        "run_index": job.run_index,
        "total_runs": job.total_runs,
        "started_at": started.isoformat(),
        "workspace": str(job.workspace_dir),
        "prompt_file": str(prompt_file),
        "output_file": str(output_file),
        "dry_run": dry_run,
        "__enable_llm_judge": enable_llm_judge,
        "__llm_judge_cache_dir": llm_judge_cache_dir,
        "__llm_judge_backend": llm_judge_backend,
        "__llm_judge_base_url": llm_judge_base_url,
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
        # GIT_CEILING_DIRECTORIES caps the agent's `git` invocations at the
        # scenario workspace, so a scenario that runs `git commit` cannot
        # walk up and accidentally land its commit in the parent Quaere
        # repo (which had happened in the v0.3.1 sweep, producing two
        # eval-results blobs that had to be filter-repo'd out of history).
        # `os.path.dirname(workspace_dir)` is the ceiling — any ancestor of
        # it is invisible to git.
        run_env = os.environ.copy()
        run_env["GIT_CEILING_DIRECTORIES"] = str(job.workspace_dir.parent)
        try:
            completed = subprocess.run(
                command,
                cwd=job.workspace_dir,
                env=run_env,
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
        metadata.update(extract_usage(stdout, stderr))

    persisted = public_metadata(metadata)
    metadata_file.write_text(json.dumps(persisted, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    grade = grade_output(job.scenario, output_file.read_text(encoding="utf-8"), metadata)
    # grade.json is written after finalize_cross_mode_assertions so cross-mode
    # checks (e.g., not_in_baseline) can update assertion results before the
    # file is committed to disk.
    return {"metadata": metadata, "grade": grade, "grade_file": grade_file, "output_file": output_file}


def public_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Return metadata safe for JSON reports.

    Runtime-only config keys start with `__`; they may contain non-serializable
    objects such as Path instances and should not be published in per-run
    metadata or summary output.
    """
    public = {k: v for k, v in metadata.items() if not k.startswith("__")}
    return {k: (str(v) if isinstance(v, Path) else v) for k, v in public.items()}


# --- usage / cost measurement -------------------------------------------------
# codex exec (human output) prints `model: <id>` and a trailing `tokens used\n<N>`
# to stderr; `codex exec --json` emits a `turn.completed` event with a structured
# `usage` object on stdout. extract_usage prefers the precise JSON split and falls
# back to the stderr total, so token/cost reporting works with the existing runner
# (no --json needed) and gets sharper when --json is used. Parsing is defensive: a
# runner-format change degrades to "no usage captured", never a failed run.
_TOKENS_USED_RE = re.compile(r"tokens?\s+used[\s:]*([\d,]+)", re.IGNORECASE)
_MODEL_RE = re.compile(r"^\s*model:\s*(\S+)", re.IGNORECASE | re.MULTILINE)


def extract_usage(stdout: str, stderr: str) -> dict[str, Any]:
    """Best-effort token + model extraction from a runner's captured streams.

    Returns any of {model, tokens_total, tokens_input, tokens_output,
    cached_input_tokens}; empty when the runner emits none. tokens_input/output
    are only set when a precise split is available, so they never feed the
    behavior grader with a guessed value.
    """
    usage: dict[str, Any] = {}
    model = _MODEL_RE.search(stderr or "")
    if model:
        usage["model"] = model.group(1)

    # Precise split from a codex --json `turn.completed` usage event (last wins).
    precise: dict[str, Any] | None = None
    for line in (stdout or "").splitlines():
        stripped = line.strip()
        if not stripped.startswith("{") or '"usage"' not in stripped:
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        candidate = event.get("usage")
        if isinstance(candidate, dict) and "input_tokens" in candidate and "output_tokens" in candidate:
            precise = candidate
    if precise is not None:
        inp = int(precise.get("input_tokens", 0) or 0)
        out = int(precise.get("output_tokens", 0) or 0) + int(precise.get("reasoning_output_tokens", 0) or 0)
        usage["tokens_input"] = inp
        usage["tokens_output"] = out
        usage["cached_input_tokens"] = int(precise.get("cached_input_tokens", 0) or 0)
        usage["tokens_total"] = inp + out
        return usage

    # Fallback: codex human-output stderr total ("tokens used\n13,184"). The
    # running total is printed last, so take the final match.
    matches = _TOKENS_USED_RE.findall(stderr or "")
    if matches:
        usage["tokens_total"] = int(matches[-1].replace(",", ""))
    return usage


def cost_usd(usage: dict[str, Any], price_input: float | None, price_output: float | None) -> dict[str, Any] | None:
    """USD estimate for one run from per-MTok prices, or None if not priceable.

    Exact when the input/output split is known; otherwise approximates the total
    at the output rate (an upper bound) and labels the basis so it is not mistaken
    for exact. No separate cached rate: cached input is billed at the input rate
    (a small, conservative over-estimate).
    """
    if price_input is None or price_output is None:
        return None
    inp = usage.get("tokens_input")
    out = usage.get("tokens_output")
    if inp is not None and out is not None:
        usd = inp / 1_000_000 * price_input + out / 1_000_000 * price_output
        return {"usd": round(usd, 6), "basis": "exact-split"}
    total = usage.get("tokens_total")
    if total is None:
        return None
    return {"usd": round(total / 1_000_000 * price_output, 6), "basis": "approx-total-at-output-rate"}


def summarize_usage(
    results: list[dict[str, Any]],
    price_input: float | None = None,
    price_output: float | None = None,
) -> dict[str, Any]:
    """Aggregate token + duration (+ optional USD) per mode, per skill, and overall,
    plus the with-skill-vs-baseline overhead delta. Runs missing token data are
    tracked via runs_with_tokens so partial capture stays visible, not hidden.
    """

    def blank() -> dict[str, Any]:
        return {"runs": 0, "runs_with_tokens": 0, "tokens_total": 0, "duration_seconds": 0.0, "usd": 0.0, "usd_priced_runs": 0}

    overall = blank()
    by_mode: dict[str, dict[str, Any]] = {}
    by_skill: dict[str, dict[str, Any]] = {}

    for item in results:
        meta = item["metadata"]
        if meta.get("dry_run"):
            continue
        buckets = (
            overall,
            by_mode.setdefault(meta.get("mode", "?"), blank()),
            by_skill.setdefault(meta.get("skill", "?"), blank()),
        )
        tokens = meta.get("tokens_total")
        duration = float(meta.get("duration_seconds") or 0.0)
        cost = cost_usd(meta, price_input, price_output)
        for b in buckets:
            b["runs"] += 1
            b["duration_seconds"] = round(b["duration_seconds"] + duration, 3)
            if isinstance(tokens, int):
                b["runs_with_tokens"] += 1
                b["tokens_total"] += tokens
            if cost is not None:
                b["usd"] = round(b["usd"] + cost["usd"], 6)
                b["usd_priced_runs"] += 1

    def finalize(b: dict[str, Any]) -> dict[str, Any]:
        out = dict(b)
        out["mean_tokens_per_run"] = round(b["tokens_total"] / b["runs_with_tokens"]) if b["runs_with_tokens"] else None
        out["mean_duration_seconds"] = round(b["duration_seconds"] / b["runs"], 3) if b["runs"] else None
        if not b["usd_priced_runs"]:
            out["usd"] = None  # nothing priced -> n/a, not a misleading 0.0
        return out

    by_mode_f = {k: finalize(v) for k, v in by_mode.items()}
    base, skill = by_mode_f.get("baseline"), by_mode_f.get("with-skill")
    overhead: dict[str, Any] | None = None
    if base and skill and base.get("mean_tokens_per_run") and skill.get("mean_tokens_per_run"):
        bt, st = base["mean_tokens_per_run"], skill["mean_tokens_per_run"]
        overhead = {
            "baseline_mean_tokens": bt,
            "with_skill_mean_tokens": st,
            "extra_tokens_per_run": st - bt,
            "token_overhead_pct": round((st - bt) / bt * 100, 1) if bt else None,
        }
        if base.get("usd") is not None and skill.get("usd") is not None and base["runs"] and skill["runs"]:
            overhead["extra_usd_per_run"] = round(skill["usd"] / skill["runs"] - base["usd"] / base["runs"], 6)

    return {
        "overall": finalize(overall),
        "by_mode": by_mode_f,
        "by_skill": {k: finalize(v) for k, v in by_skill.items()},
        "overhead": overhead,
        "priced": price_input is not None and price_output is not None,
        "price_input_per_mtok": price_input,
        "price_output_per_mtok": price_output,
    }


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
                "axis": assertion_axis(assertion),
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

    enable_llm_judge = bool(metadata.get("__enable_llm_judge"))
    llm_judge_cache_dir = metadata.get("__llm_judge_cache_dir")
    llm_judge_backend = str(metadata.get("__llm_judge_backend") or "anthropic")
    llm_judge_base_url = metadata.get("__llm_judge_base_url")
    assertion_results = [
        evaluate_assertion(
            assertion,
            output,
            metadata,
            enable_llm_judge=enable_llm_judge,
            llm_judge_cache_dir=llm_judge_cache_dir,
            llm_judge_backend=llm_judge_backend,
            llm_judge_base_url=llm_judge_base_url,
        )
        for assertion in scenario.assertions
    ]
    for assertion, result in zip(scenario.assertions, assertion_results):
        result["axis"] = assertion_axis(assertion)
    manual = [
        {
            "name": item,
            "status": "manual",
            "note": "Review the output for this behavior; no deterministic assertion is configured.",
        }
        for item in scenario.expected
    ]
    grade = {
        "scenario_id": scenario.id,
        "skill": scenario.skill,
        "status": "manual-only",
        "assertions": assertion_results,
        "manual_rubric": manual,
        "summary": {
            "manual_items": len(manual),
        },
    }
    recompute_grade_status(grade)
    return grade


def decode_timeout_stream(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _llm_judge_cache_key(model: str, rubric: str, output: str) -> str:
    """sha256(model identity | rubric | output) — stable key for cache hits across runs."""
    h = hashlib.sha256()
    h.update(model.encode("utf-8"))
    h.update(b"\x00")
    h.update(rubric.encode("utf-8"))
    h.update(b"\x00")
    h.update(output.encode("utf-8"))
    return h.hexdigest()


def _llm_judge_cache_read(cache_dir: Path, key: str) -> dict[str, Any] | None:
    path = cache_dir / f"{key}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _llm_judge_cache_write(cache_dir: Path, key: str, payload: dict[str, Any]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    tmp = cache_dir / f"{key}.json.tmp"
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(cache_dir / f"{key}.json")


JUDGE_PROMPT_TEMPLATE = (
    "You are grading agent output against a rubric. Read the rubric, "
    "read the output, and respond with one of the keywords the rubric "
    "specifies (typically PASS or FAIL) followed by a short reason.\n\n"
    "--- RUBRIC ---\n{rubric}\n\n"
    "--- AGENT OUTPUT ---\n{output}\n"
)


def _call_anthropic_judge(model: str, rubric: str, output: str) -> str:
    """Single LLM call (Anthropic API) returning the judge's text response.

    Lazy-imports the anthropic SDK so users who never enable llm_judge do
    not pay the import cost or need the dep. Errors propagate up; callers
    map them to assertion-level fail/manual results.
    """
    try:
        import anthropic  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover — environment-dependent
        raise RuntimeError(
            "llm_judge anthropic backend requires `pip install anthropic`. "
            "Install it, switch to --llm-judge-backend openai-compat, or "
            "omit --enable-llm-judge."
        ) from exc

    client = anthropic.Anthropic()  # picks up ANTHROPIC_API_KEY from env
    message = client.messages.create(
        model=model,
        max_tokens=512,
        temperature=0.0,  # determinism over creativity for grading
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT_TEMPLATE.format(rubric=rubric, output=output),
            }
        ],
    )
    return "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    )


def _call_codex_judge(model: str, rubric: str, output: str) -> str:
    """Single LLM call via the Codex CLI subprocess.

    Invokes `codex exec --output-last-message <tmpfile> -` with the rubric +
    output piped on stdin, then reads the final message from the temp file.
    This route adds no Python SDK dependency: it only needs the `codex` CLI
    on PATH (already required if Codex is the in-tree eval runner). The
    actual API endpoint Codex hits is controlled by Codex's own env vars
    (OPENAI_BASE_URL etc.), so this backend automatically picks up the
    same local-AI setup the agent uses.
    """
    import tempfile

    prompt = JUDGE_PROMPT_TEMPLATE.format(rubric=rubric, output=output)
    fd, out_path = tempfile.mkstemp(prefix="quaere-judge-", suffix=".txt")
    os.close(fd)
    try:
        cmd = ["codex", "exec"]
        if model:
            cmd += ["--model", model]
        cmd += ["--output-last-message", out_path, "-"]
        completed = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        if completed.returncode != 0:
            stderr_tail = (completed.stderr or "").strip().splitlines()[-3:]
            raise RuntimeError(
                f"codex exec returned {completed.returncode}: "
                + " | ".join(stderr_tail)
            )
        try:
            return Path(out_path).read_text(encoding="utf-8")
        except OSError as exc:
            raise RuntimeError(f"codex did not write the output file: {exc}") from exc
    finally:
        try:
            os.unlink(out_path)
        except OSError:
            pass


def _call_openai_compat_judge(base_url: str, model: str, rubric: str, output: str) -> str:
    """Single LLM call (OpenAI-compatible chat completions) returning the judge's text.

    Targets any server speaking the OpenAI chat completions schema —
    Ollama (`http://localhost:11434/v1`), vLLM, LM Studio, LocalAI,
    LiteLLM proxy, etc. The `openai` SDK is lazy-imported so the
    anthropic-only path does not pull it in.

    API key is taken from OPENAI_API_KEY when present; a placeholder
    is sent otherwise (most local servers ignore the key).
    """
    if not base_url:
        raise RuntimeError(
            "openai-compat backend requires --llm-judge-base-url (or "
            "QUAERE_LLM_JUDGE_BASE_URL) pointing at the OpenAI-compatible "
            "endpoint (e.g. http://localhost:11434/v1)."
        )
    try:
        from openai import OpenAI  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover — environment-dependent
        raise RuntimeError(
            "llm_judge openai-compat backend requires `pip install openai`. "
            "Install it, switch to --llm-judge-backend anthropic, or "
            "omit --enable-llm-judge."
        ) from exc

    client = OpenAI(base_url=base_url, api_key=os.environ.get("OPENAI_API_KEY", "dummy"))
    resp = client.chat.completions.create(
        model=model,
        max_tokens=512,
        temperature=0.0,
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT_TEMPLATE.format(rubric=rubric, output=output),
            }
        ],
    )
    choice = resp.choices[0] if resp.choices else None
    return (choice.message.content if choice and choice.message else "") or ""


def evaluate_assertion(
    assertion: dict[str, Any],
    output: str,
    metadata: dict[str, Any],
    *,
    enable_llm_judge: bool = False,
    llm_judge_cache_dir: Path | None = None,
    llm_judge_backend: str = "anthropic",
    llm_judge_base_url: str | None = None,
    llm_judge_call: Any = None,
) -> dict[str, Any]:
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
    elif assertion_type == "not_regex":
        pattern = str(assertion.get("pattern", ""))
        ok = re.search(pattern, output, flags=re.MULTILINE) is None
        detail = f"forbidden regex {pattern!r}"
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
        # `skip_when` (optional) lets the assertion pass when the antecedent
        # is present, the consequent is missing, but the agent explicitly
        # declared a vacuous-pair branch (e.g. "Final gate: skipped because
        # ..."). Authors MUST anchor `skip_when` tightly to the specific
        # vacuous branch — a bare pattern like `(?i)skipped` would silently
        # flip fails to passes whenever the word appears anywhere in output.
        # Anchor on the label that owns the skip (e.g. `Final gate: skipped
        # because`, `targeted.*skipped because`, `diff review.*skipped
        # because`), not on the skip token alone.
        if_pattern = str(assertion.get("if_contains", ""))
        must_pattern = str(assertion.get("must_also_contain", ""))
        skip_when_pattern = assertion.get("skip_when")
        try:
            antecedent = re.search(if_pattern, output, flags=re.MULTILINE)
            consequent = re.search(must_pattern, output, flags=re.MULTILINE)
            skip_match = (
                re.search(str(skip_when_pattern), output, flags=re.MULTILINE)
                if skip_when_pattern is not None
                else None
            )
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
        elif consequent is not None:
            ok = True
            detail = f"{if_pattern!r} present; required pair {must_pattern!r} present"
        elif skip_match is not None:
            ok = True
            detail = (
                f"{if_pattern!r} present; pair {must_pattern!r} missing but "
                f"skip clause {str(skip_when_pattern)!r} matched — unconditional pair "
                "treated as vacuous"
            )
        else:
            ok = False
            detail = (
                f"{if_pattern!r} present but required pair {must_pattern!r} missing"
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
    elif assertion_type == "llm_judge":
        if not enable_llm_judge:
            return {
                "name": name,
                "type": assertion_type,
                "status": "skipped",
                "detail": "llm-judge not enabled for this run (re-run with --enable-llm-judge)",
            }
        model = str(assertion.get("model") or DEFAULT_LLM_JUDGE_MODEL)
        rubric = str(assertion.get("rubric", ""))
        if not rubric:
            return {
                "name": name,
                "type": assertion_type,
                "status": "fail",
                "detail": "llm_judge assertion missing required 'rubric'",
            }
        pass_keyword = str(assertion.get("pass_keyword", "PASS"))
        fail_keyword = str(assertion.get("fail_keyword", "FAIL"))
        cache_dir = llm_judge_cache_dir or DEFAULT_LLM_JUDGE_CACHE
        # Cache key includes the backend and endpoint identity so switches
        # between Anthropic, Codex, or different OpenAI-compatible servers do
        # not silently reuse cached responses from another judge surface.
        endpoint = str(llm_judge_base_url or "") if llm_judge_backend == "openai-compat" else ""
        key = _llm_judge_cache_key(f"{llm_judge_backend}:{endpoint}:{model}", rubric, output)
        cached = _llm_judge_cache_read(cache_dir, key)
        if cached is not None:
            response_text = str(cached.get("response", ""))
            from_cache = True
        else:
            if llm_judge_call is not None:
                caller = llm_judge_call
            elif llm_judge_backend == "anthropic":
                caller = _call_anthropic_judge
            elif llm_judge_backend == "openai-compat":
                base_url = llm_judge_base_url
                caller = lambda m, r, o: _call_openai_compat_judge(base_url, m, r, o)  # noqa: E731
            elif llm_judge_backend == "codex":
                caller = _call_codex_judge
            else:
                return {
                    "name": name,
                    "type": assertion_type,
                    "status": "fail",
                    "detail": (
                        f"unknown llm_judge_backend {llm_judge_backend!r}; "
                        "expected 'anthropic', 'openai-compat', or 'codex'"
                    ),
                }
            try:
                response_text = caller(model, rubric, output)
            except Exception as exc:  # noqa: BLE001 — surface any judge failure to the assertion result
                return {
                    "name": name,
                    "type": assertion_type,
                    "status": "fail",
                    "detail": f"llm_judge call failed: {exc}",
                }
            _llm_judge_cache_write(
                cache_dir,
                key,
                {
                    "model": model,
                    "backend": llm_judge_backend,
                    "base_url": endpoint or None,
                    "rubric_sha": hashlib.sha256(rubric.encode("utf-8")).hexdigest(),
                    "response": response_text,
                    "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                },
            )
            from_cache = False
        has_pass = pass_keyword in response_text
        has_fail = fail_keyword in response_text
        cache_tag = " (cache hit)" if from_cache else ""
        if has_pass and not has_fail:
            return {
                "name": name,
                "type": assertion_type,
                "status": "pass",
                "detail": f"judge: {pass_keyword!r} present{cache_tag}; reason: {response_text.strip()[:200]}",
            }
        if has_fail and not has_pass:
            return {
                "name": name,
                "type": assertion_type,
                "status": "fail",
                "detail": f"judge: {fail_keyword!r} present{cache_tag}; reason: {response_text.strip()[:200]}",
            }
        return {
            "name": name,
            "type": assertion_type,
            "status": "manual",
            "detail": (
                f"judge response ambiguous (neither {pass_keyword!r} nor "
                f"{fail_keyword!r} cleanly present){cache_tag}; "
                f"response: {response_text.strip()[:200]}"
            ),
        }
    elif assertion_type == "behavior":
        # Behavior grader: per-run resource thresholds (tool calls, duration,
        # tokens). Records `status: "manual"` when the underlying runner did
        # not emit the required metadata so reviewers can audit which runs
        # are missing instrumentation. Each configured threshold counts as
        # one check; pass requires every configured threshold to hold.
        thresholds = {
            "max_tool_calls": ("tool_calls", lambda v, t: v <= t),
            "min_tool_calls": ("tool_calls", lambda v, t: v >= t),
            "max_duration_seconds": ("duration_seconds", lambda v, t: v <= t),
            "max_tokens_output": ("tokens_output", lambda v, t: v <= t),
            "max_tokens_input": ("tokens_input", lambda v, t: v <= t),
        }
        configured = {k: assertion[k] for k in thresholds if k in assertion}
        if not configured:
            return {
                "name": name,
                "type": assertion_type,
                "status": "fail",
                "detail": "behavior grader requires at least one threshold",
            }
        missing_metrics: list[str] = []
        violations: list[str] = []
        for option, threshold in configured.items():
            metric_key, predicate = thresholds[option]
            observed = metadata.get(metric_key)
            if observed is None:
                missing_metrics.append(metric_key)
                continue
            if not predicate(observed, threshold):
                violations.append(
                    f"{option}={threshold!r} but {metric_key}={observed!r}"
                )
        if missing_metrics:
            return {
                "name": name,
                "type": assertion_type,
                "status": "manual",
                "detail": (
                    "runner did not emit "
                    f"{sorted(set(missing_metrics))}; behavior grader cannot evaluate"
                ),
            }
        ok = not violations
        detail = (
            "all behavior thresholds satisfied "
            f"({list(configured.keys())})"
            if ok
            else f"violations: {violations}"
        )
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


VALID_AXES = {"outcome", "form"}


def assertion_axis(assertion: dict[str, Any]) -> str:
    """Axis an assertion measures: 'outcome' (task resolved / safe) or 'form' (surface shape).

    Defaults to 'form' so untagged assertions never inflate the headline outcome
    number — opting an assertion into the outcome axis is an explicit author act.
    """
    axis = assertion.get("axis", "form")
    return axis if axis in VALID_AXES else "form"


def recompute_grade_status(grade: dict[str, Any]) -> None:
    """Recompute grade status and summary counters from current assertion list."""
    assertion_results = grade.get("assertions", [])
    passed = sum(1 for r in assertion_results if r.get("status") == "pass")
    failed = sum(1 for r in assertion_results if r.get("status") == "fail")
    pending = sum(1 for r in assertion_results if r.get("status") == "pending")
    inconclusive = sum(1 for r in assertion_results if r.get("status") == "inconclusive")
    manual = sum(1 for r in assertion_results if r.get("status") == "manual")
    skipped = sum(1 for r in assertion_results if r.get("status") == "skipped")
    if not assertion_results:
        grade["status"] = "manual-only"
    elif failed:
        grade["status"] = "fail"
    elif pending:
        grade["status"] = "pending"
    elif inconclusive:
        grade["status"] = "inconclusive"
    elif skipped > 0 and passed == 0 and (manual + inconclusive + pending) == 0:
        grade["status"] = "skipped"
    elif passed == 0:
        grade["status"] = "manual-only"
    else:
        grade["status"] = "pass"
    summary = grade.setdefault("summary", {})
    summary["assertions_passed"] = passed
    summary["assertions_failed"] = failed
    summary["assertions_pending"] = pending
    summary["assertions_inconclusive"] = inconclusive
    summary["assertions_manual"] = manual
    summary["assertions_skipped"] = skipped
    summary["assertions_skipped"] = skipped


def finalize_cross_mode_assertions(results: list[dict[str, Any]]) -> None:
    """Resolve assertions that need both baseline and with-skill output (e.g. not_in_baseline)."""
    # Key includes run_index so with-skill run i pairs with baseline run i; otherwise
    # repeated runs would collapse to last-write-wins and mis-pair cross-mode checks.
    pairs: dict[tuple[str, str, str, int], dict[str, dict[str, Any]]] = {}
    for result in results:
        meta = result["metadata"]
        key = (meta["runner"], meta["skill"], meta["scenario_id"], meta.get("run_index", 1))
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


def _axis_run_status(grade: dict[str, Any], axis: str) -> tuple[bool, bool]:
    """(applicable, passed) for one run on one axis.

    applicable = the run had >=1 pass/fail assertion on this axis.
    passed     = applicable and no assertion on this axis failed.
    """
    rel = [a for a in grade.get("assertions", []) if a.get("axis", "form") == axis]
    passed = sum(1 for a in rel if a.get("status") == "pass")
    failed = sum(1 for a in rel if a.get("status") == "fail")
    applicable = (passed + failed) >= 1
    return applicable, applicable and failed == 0


def aggregate_cells(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per (runner, skill, scenario, mode) with run-level pass-rates."""
    order: list[tuple[str, str, str, str]] = []
    cells: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for result in results:
        meta = result["metadata"]
        if meta.get("dry_run"):
            continue
        key = (meta["runner"], meta["skill"], meta["scenario_id"], meta["mode"])
        if key not in cells:
            order.append(key)
            cells[key] = {
                "runner": meta["runner"],
                "skill": meta["skill"],
                "scenario_id": meta["scenario_id"],
                "mode": meta["mode"],
                "runs": 0,
                "status_pass_runs": 0,
                "outcome_applicable": 0,
                "outcome_pass": 0,
                "form_applicable": 0,
                "form_pass": 0,
            }
        cell = cells[key]
        cell["runs"] += 1
        if result["grade"].get("status") == "pass":
            cell["status_pass_runs"] += 1
        for axis in ("outcome", "form"):
            applicable, passed = _axis_run_status(result["grade"], axis)
            if applicable:
                cell[f"{axis}_applicable"] += 1
                if passed:
                    cell[f"{axis}_pass"] += 1
    return [cells[key] for key in order]


def mcnemar_exact_p(b01: int, b10: int) -> float | None:
    """Two-sided exact (binomial) McNemar p-value over discordant pairs; None if no discordants."""
    n = b01 + b10
    if n == 0:
        return None
    k = min(b01, b10)
    tail = sum(math.comb(n, i) for i in range(k + 1)) * (0.5 ** n)
    return min(1.0, 2.0 * tail)


def build_pairs(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Paired baseline-vs-with-skill comparison per scenario, on the outcome axis.

    Per-scenario deltas are descriptive (independent runs, not matched pairs). The
    cross-scenario McNemar treats each scenario's outcome-axis majority as one paired
    binary observation (baseline vs with-skill) and is the closest valid inferential
    summary; it is still weak at small scenario counts.
    """
    cells = {(c["runner"], c["skill"], c["scenario_id"], c["mode"]): c for c in aggregate_cells(results)}
    scenario_keys: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for c in cells.values():
        sk = (c["runner"], c["skill"], c["scenario_id"])
        if sk not in seen:
            seen.add(sk)
            scenario_keys.append(sk)

    per_scenario: list[dict[str, Any]] = []
    b01 = b10 = 0  # baseline-pass/skill-fail, skill-pass/baseline-fail (outcome majority)
    for runner, skill, scenario_id in scenario_keys:
        base = cells.get((runner, skill, scenario_id, "baseline"))
        skl = cells.get((runner, skill, scenario_id, "with-skill"))
        if base is None or skl is None:
            continue

        def rate(cell: dict[str, Any]) -> float | None:
            denom = cell["outcome_applicable"]
            return (cell["outcome_pass"] / denom) if denom else None

        base_rate, skill_rate = rate(base), rate(skl)
        entry = {
            "runner": runner,
            "skill": skill,
            "scenario_id": scenario_id,
            "axis": "outcome",
            "baseline": f"{base['outcome_pass']}/{base['outcome_applicable']}",
            "with_skill": f"{skl['outcome_pass']}/{skl['outcome_applicable']}",
            "delta": None if (base_rate is None or skill_rate is None) else round(skill_rate - base_rate, 3),
            "note": "descriptive (independent runs, not matched pairs)",
        }
        per_scenario.append(entry)
        # Cross-scenario McNemar: majority-pass per arm as the paired binary.
        if base["outcome_applicable"] and skl["outcome_applicable"]:
            base_majority = base["outcome_pass"] * 2 >= base["outcome_applicable"]
            skill_majority = skl["outcome_pass"] * 2 >= skl["outcome_applicable"]
            if base_majority and not skill_majority:
                b01 += 1
            elif skill_majority and not base_majority:
                b10 += 1

    p_value = mcnemar_exact_p(b01, b10)
    mcnemar: dict[str, Any] = {
        "discordant_baseline_only": b01,
        "discordant_skill_only": b10,
        "exact_two_sided_p": None if p_value is None else round(p_value, 4),
        "note": (
            "outcome-axis majority per scenario; exact binomial McNemar. "
            "Descriptive at small scenario counts — do not over-read."
        ),
    }
    return {"per_scenario": per_scenario, "mcnemar": mcnemar}


def write_summary(
    output_root: Path,
    results: list[dict[str, Any]],
    price_input: float | None = None,
    price_output: float | None = None,
) -> Path:
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
    public_runs = [{"metadata": public_metadata(item["metadata"]), "grade": item["grade"]} for item in results]
    cells = aggregate_cells(results)
    summary = {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "output_root": str(output_root),
        "totals": totals,
        "usage": summarize_usage(results, price_input, price_output),
        "cells": cells,
        "pairs": build_pairs(results),
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
    parser.add_argument(
        "--scenarios-extra",
        type=Path,
        default=None,
        help=(
            "Optional path to a locale-alternates file (same JSON shape as "
            "--scenarios) whose assertion fields are appended via "
            "`|`-alternation to the main scenarios at load time. Match is "
            "by (scenario id, assertion name)."
        ),
    )
    parser.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--price-input",
        type=float,
        default=None,
        help=(
            "Agent model price in USD per million INPUT tokens. Tokens and "
            "duration are always measured; a USD estimate is only computed when "
            "both --price-input and --price-output are set (omit for a "
            "subscription/ChatGPT runner, where there is no per-token bill)."
        ),
    )
    parser.add_argument(
        "--price-output",
        type=float,
        default=None,
        help="Agent model price in USD per million OUTPUT tokens. See --price-input.",
    )
    parser.add_argument("--runner", action="append", type=parse_runner, required=True)
    parser.add_argument("--skill", help="Run only scenarios for one skill.")
    parser.add_argument("--scenario", action="append", default=[], help="Run only the named scenario ID. Repeatable.")
    parser.add_argument("--mode", type=mode_list, default=["with-skill"])
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help=(
            "Independent runs per (scenario, mode) cell. Default 5 — a single "
            "sweep cannot separate a real 2-3pp effect from run-to-run noise. "
            "Use --runs 1 for quick local iteration (single-sample, "
            "non-authoritative). Forced to 1 under --dry-run."
        ),
    )
    parser.add_argument("--workspace-source", type=Path, help="Directory copied into each isolated run workspace.")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--dry-run", action="store_true", help="Write prompts and metadata without invoking runners.")
    parser.add_argument("--fail-on-grade", action="store_true", help="Exit non-zero on command or assertion failure.")
    parser.add_argument(
        "--enable-llm-judge",
        action="store_true",
        help=(
            "Run `llm_judge` assertions against an LLM (default: skipped). "
            "Requires the `anthropic` package and ANTHROPIC_API_KEY in the "
            "environment. Responses are cached under evals/.llm_judge_cache/ "
            "keyed by sha256(model+rubric+output)."
        ),
    )
    parser.add_argument(
        "--llm-judge-cache-dir",
        type=Path,
        default=None,
        help=(
            "Override the cache directory for llm_judge responses "
            "(default: evals/.llm_judge_cache/)."
        ),
    )
    parser.add_argument(
        "--llm-judge-backend",
        choices=("anthropic", "openai-compat", "codex"),
        default="anthropic",
        help=(
            "Backend the llm_judge grader calls. `anthropic` uses the "
            "official Anthropic SDK with ANTHROPIC_API_KEY (default). "
            "`openai-compat` uses the openai SDK with --llm-judge-base-url "
            "pointing at any OpenAI-compatible endpoint — Ollama "
            "(http://localhost:11434/v1), vLLM, LM Studio, LocalAI, "
            "LiteLLM proxy, etc. `codex` shells out to `codex exec "
            "--output-last-message`, reusing whatever endpoint and auth "
            "Codex CLI is already configured for (no extra Python SDK)."
        ),
    )
    parser.add_argument(
        "--llm-judge-base-url",
        default=os.environ.get("QUAERE_LLM_JUDGE_BASE_URL"),
        help=(
            "Base URL for the openai-compat backend "
            "(e.g. http://localhost:11434/v1). Ignored when "
            "--llm-judge-backend=anthropic. Defaults to "
            "$QUAERE_LLM_JUDGE_BASE_URL."
        ),
    )
    parser.add_argument(
        "--require-assertions",
        action="store_true",
        help="Exit non-zero if any run was graded manual-only (no deterministic assertions evaluated).",
    )
    parser.add_argument(
        "--isolate-skills",
        action="store_true",
        help=(
            "Temporarily relocate installed skill dirs (~/.agents/skills, "
            "~/.claude/skills) for the duration of the sweep so the runner cannot "
            "auto-discover them. Required for an uncontaminated baseline: without "
            "it, Codex reads ~/.agents/skills/<skill>/SKILL.md even in baseline "
            "mode. Restored on exit, exception, and SIGINT/SIGTERM."
        ),
    )
    return parser.parse_args(argv)


@contextlib.contextmanager
def isolated_installed_skills(enabled: bool, dirs: list[Path]):
    """Relocate installed skill dirs for the sweep so the runner cannot auto-load them.

    Without this, `--mode baseline` is contaminated: an Agent-Skills-aware CLI such
    as Codex discovers and reads ~/.agents/skills/<skill>/SKILL.md on its own even
    though `build_prompt` omitted the skill, which compresses the measured
    baseline-vs-skill delta. Relocation is restored on normal exit, on exception
    (finally), on interpreter exit (atexit), and on SIGINT/SIGTERM.
    """
    if not enabled:
        yield
        return

    moved: list[tuple[Path, Path]] = []

    def restore() -> None:
        while moved:
            src, bak = moved.pop()
            try:
                if bak.exists() and not src.exists():
                    bak.rename(src)
                    print(f"--isolate-skills: restored {src}", file=sys.stderr)
            except OSError as exc:  # pragma: no cover - defensive
                print(f"WARNING: could not restore {src} from {bak}: {exc}", file=sys.stderr)

    for d in dirs:
        if d.exists():
            bak = d.with_name(f"{d.name}.quaere-isolated-{os.getpid()}")
            if bak.exists():
                shutil.rmtree(bak)
            d.rename(bak)
            moved.append((d, bak))
            print(f"--isolate-skills: relocated {d} (restored on exit)", file=sys.stderr)

    atexit.register(restore)
    prev_handlers: dict[int, Any] = {}

    def _on_signal(signum, _frame):
        restore()
        handler = prev_handlers.get(signum, signal.SIG_DFL)
        signal.signal(signum, handler)
        os.kill(os.getpid(), signum)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            prev_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, _on_signal)
        except (ValueError, OSError):  # pragma: no cover - non-main thread / unsupported
            pass

    try:
        yield
    finally:
        restore()
        for sig, handler in prev_handlers.items():
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):  # pragma: no cover
                pass


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    scenarios = filter_scenarios(
        load_scenarios(args.scenarios, args.scenarios_extra),
        args.skill,
        set(args.scenario),
    )
    if not scenarios:
        print("No scenarios matched.", file=sys.stderr)
        return 2

    output_root = args.output_dir / dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    total_runs = 1 if args.dry_run else max(1, args.runs)

    with isolated_installed_skills(args.isolate_skills, INSTALLED_SKILL_DIRS):
        for runner in args.runner:
            for scenario in scenarios:
                for mode in args.mode:
                    workspace_source = args.workspace_source
                    if workspace_source is not None:
                        workspace_source = workspace_source.resolve()
                    else:
                        workspace_source = resolve_scenario_workspace(scenario, args.scenarios)
                    for run_index in range(1, total_runs + 1):
                        job = create_job(
                            runner=runner,
                            scenario=scenario,
                            mode=mode,
                            output_root=output_root,
                            skills_dir=args.skills_dir,
                            workspace_source=workspace_source,
                            run_index=run_index,
                            total_runs=total_runs,
                        )
                        result = run_job(
                            job,
                            timeout_seconds=args.timeout,
                            dry_run=args.dry_run,
                            enable_llm_judge=args.enable_llm_judge,
                            llm_judge_cache_dir=args.llm_judge_cache_dir,
                            llm_judge_backend=args.llm_judge_backend,
                            llm_judge_base_url=args.llm_judge_base_url,
                        )
                        results.append(result)

    finalize_cross_mode_assertions(results)

    for result in results:
        result["grade_file"].write_text(
            json.dumps(result["grade"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        meta = result["metadata"]
        run_tag = f"/run-{meta['run_index']:02d}" if meta.get("total_runs", 1) > 1 else ""
        print(
            f"{meta['runner']}/{meta['scenario_id']}/{meta['mode']}{run_tag}: "
            f"{meta['status']} / {result['grade']['status']}"
        )

    summary_path = write_summary(output_root, results, args.price_input, args.price_output)

    if not args.dry_run:
        print(f"--- cell pass-rates (runs={total_runs}) ---")
        for cell in aggregate_cells(results):
            outcome = (
                f"outcome {cell['outcome_pass']}/{cell['outcome_applicable']}"
                if cell["outcome_applicable"]
                else "outcome n/a"
            )
            print(
                f"{cell['runner']}/{cell['scenario_id']}/{cell['mode']}: "
                f"status {cell['status_pass_runs']}/{cell['runs']}, {outcome}, "
                f"form {cell['form_pass']}/{cell['form_applicable']}"
            )
        if len(args.mode) == 2:
            mcnemar = build_pairs(results)["mcnemar"]
            print(
                f"McNemar (outcome majority): baseline-only={mcnemar['discordant_baseline_only']}, "
                f"skill-only={mcnemar['discordant_skill_only']}, "
                f"exact p={mcnemar['exact_two_sided_p']} — {mcnemar['note']}"
            )
        if total_runs == 1:
            print("note: --runs 1 is single-sample and non-authoritative; use --runs 5+ for a measured result.")

        usage = summarize_usage(results, args.price_input, args.price_output)
        overall = usage["overall"]
        if overall["runs"]:
            print("--- usage / cost ---")
            for mode in sorted(usage["by_mode"]):
                b = usage["by_mode"][mode]
                mean = f"{b['mean_tokens_per_run']:,}" if b["mean_tokens_per_run"] is not None else "n/a"
                cost = f", ~${b['usd']:.4f}" if b["usd"] is not None else ""
                print(
                    f"{mode}: {b['runs']} runs, {b['tokens_total']:,} tokens "
                    f"(mean {mean}/run), {b['duration_seconds']:.0f}s{cost}"
                )
            oh = usage["overhead"]
            if oh:
                pct = f" ({oh['token_overhead_pct']:+.1f}%)" if oh.get("token_overhead_pct") is not None else ""
                extra_usd = f", ~${oh['extra_usd_per_run']:+.5f}/run" if oh.get("extra_usd_per_run") is not None else ""
                print(f"skill token overhead: {oh['extra_tokens_per_run']:+,}/run{pct}{extra_usd} vs baseline")
            if overall["usd"] is not None:
                print(f"total: {overall['tokens_total']:,} tokens, ~${overall['usd']:.4f} over {overall['runs']} runs")
            else:
                print(
                    f"total: {overall['tokens_total']:,} tokens over {overall['runs']} runs "
                    "(set --price-input/--price-output for a $ estimate)"
                )
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
