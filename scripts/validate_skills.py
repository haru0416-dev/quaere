#!/usr/bin/env python3
"""Lightweight repository validation for Agent Skills."""

from __future__ import annotations

import re
import sys
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
README = ROOT / "README.md"
EXAMPLES = ROOT / "examples" / "README.md"
SCENARIOS = ROOT / "evals" / "scenarios.json"
MAX_SKILL_LINES = 500
REQUIRED_FIELDS = {"name", "description", "compatibility", "license"}
KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
YAML_QUOTED_SCALAR = re.compile(r"^(['\"]).*\1$")
ASSERTION_REQUIRED_KEYS = {
    "contains": ("text",),
    "contains_any": ("texts",),
    "not_contains": ("text",),
    "regex": ("pattern",),
    "ordered_sections": ("patterns",),
    "min_section_count": ("pattern", "min"),
    "requires_pair": ("if_contains", "must_also_contain"),
    "not_in_baseline": ("patterns",),
    # exit_code: value is optional and defaults to 0 in the runner
    # behavior: at least one threshold is required, but any of five may carry it;
    #           validator does not enforce which one beyond "type is recognized".
    # llm_judge: rubric is required; checked at runtime, not here.
    "llm_judge": ("rubric",),
}
SUPPORTED_ASSERTION_TYPES = set(ASSERTION_REQUIRED_KEYS.keys()) | {"exit_code", "behavior"}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def parse_frontmatter(path: Path, errors: list[str]) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        fail(errors, f"{path}: missing opening frontmatter delimiter")
        return {}

    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        fail(errors, f"{path}: missing closing frontmatter delimiter")
        return {}

    metadata: dict[str, str] = {}
    for line_no, line in enumerate(lines[1:end], start=2):
        if not line.strip():
            continue
        if ":" not in line:
            fail(errors, f"{path}:{line_no}: frontmatter line must be key: value")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if ": " in value and not YAML_QUOTED_SCALAR.fullmatch(value):
            fail(errors, f"{path}:{line_no}: frontmatter value containing ': ' must be quoted for YAML-compatible skill loaders")
        metadata[key] = value.strip('"').strip("'")
    return metadata


def validate_skill(
    skill_dir: Path,
    readme_text: str,
    examples_text: str,
    scenario_skills: set[str],
    errors: list[str],
) -> None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        fail(errors, f"{skill_dir}: missing SKILL.md")
        return

    metadata = parse_frontmatter(skill_md, errors)
    missing = REQUIRED_FIELDS - metadata.keys()
    if missing:
        fail(errors, f"{skill_md}: missing frontmatter fields: {', '.join(sorted(missing))}")

    name = metadata.get("name")
    if name != skill_dir.name:
        fail(errors, f"{skill_md}: name {name!r} must match directory {skill_dir.name!r}")
    if name and not KEBAB_CASE.fullmatch(name):
        fail(errors, f"{skill_md}: name {name!r} must be kebab-case ([a-z0-9-]+ without leading/trailing/double dashes)")

    description = metadata.get("description", "")
    if not description.startswith("This skill should be used"):
        fail(errors, f"{skill_md}: description should start with 'This skill should be used'")
    if len(description) < 80:
        fail(errors, f"{skill_md}: description is too short to guide triggering")

    if metadata.get("license") != "MIT":
        fail(errors, f"{skill_md}: license should be MIT")

    line_count = len(skill_md.read_text(encoding="utf-8").splitlines())
    if line_count > MAX_SKILL_LINES:
        fail(errors, f"{skill_md}: {line_count} lines exceeds {MAX_SKILL_LINES}-line budget")

    readme_ref = f"skills/{skill_dir.name}"
    if readme_ref not in readme_text:
        fail(errors, f"README.md: missing reference to {readme_ref}")

    example_heading = f"## `{skill_dir.name}`"
    if example_heading not in examples_text:
        fail(errors, f"examples/README.md: missing example section for {skill_dir.name}")

    if skill_dir.name not in scenario_skills:
        fail(errors, f"evals/scenarios.json: missing scenario for {skill_dir.name}")


def load_scenario_skills(path: Path, errors: list[str]) -> set[str]:
    if not path.exists():
        fail(errors, "missing evals/scenarios.json")
        return set()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(errors, f"{path}: invalid JSON: {exc}")
        return set()

    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list):
        fail(errors, f"{path}: scenarios must be a list")
        return set()

    scenario_skills: set[str] = set()
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            fail(errors, f"{path}: scenario {index} must be an object")
            continue
        skill = scenario.get("skill")
        if isinstance(skill, str):
            scenario_skills.add(skill)
        else:
            fail(errors, f"{path}: scenario {index} missing string skill")
        scenario_id = scenario.get("id", f"index {index}")
        expected = scenario.get("expected")
        if not isinstance(expected, list) or not all(isinstance(item, str) for item in expected):
            fail(errors, f"{path}: scenario {scenario_id!r} expected must be a list of strings")
        workspace = scenario.get("workspace")
        if workspace is not None:
            if not isinstance(workspace, str):
                fail(errors, f"{path}: scenario {scenario_id!r} workspace must be a string when present")
            elif not (path.parent / workspace).is_dir():
                fail(errors, f"{path}: scenario {scenario_id!r} workspace does not exist: {workspace}")
        assertions = scenario.get("assertions", [])
        if not isinstance(assertions, list):
            fail(errors, f"{path}: scenario {scenario_id!r} assertions must be a list when present")
            continue
        for assertion_index, assertion in enumerate(assertions):
            if not isinstance(assertion, dict):
                fail(errors, f"{path}: scenario {scenario_id!r} assertion {assertion_index} must be an object")
                continue
            assertion_type = assertion.get("type")
            if assertion_type not in SUPPORTED_ASSERTION_TYPES:
                fail(
                    errors,
                    f"{path}: scenario {scenario_id!r} assertion {assertion_index} has unsupported type {assertion_type!r}",
                )
                continue
            for required_key in ASSERTION_REQUIRED_KEYS.get(assertion_type, ()):
                if required_key not in assertion:
                    fail(
                        errors,
                        f"{path}: scenario {scenario_id!r} assertion {assertion_index} of type {assertion_type!r} missing required key {required_key!r}",
                    )

    return scenario_skills


def main() -> int:
    errors: list[str] = []

    if not SKILLS_DIR.is_dir():
        fail(errors, "missing skills/ directory")
    if not README.exists():
        fail(errors, "missing README.md")
    if not EXAMPLES.exists():
        fail(errors, "missing examples/README.md")

    readme_text = README.read_text(encoding="utf-8") if README.exists() else ""
    examples_text = EXAMPLES.read_text(encoding="utf-8") if EXAMPLES.exists() else ""
    scenario_skills = load_scenario_skills(SCENARIOS, errors)

    for path in ROOT.rglob(".agent-state"):
        if ".git" not in path.parts:
            fail(errors, f"local investigation state should not be committed: {path}")

    skill_names: set[str] = set()
    if SKILLS_DIR.is_dir():
        skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
        if not skill_dirs:
            fail(errors, "skills/ contains no skill directories")
        for skill_dir in skill_dirs:
            skill_names.add(skill_dir.name)
            validate_skill(skill_dir, readme_text, examples_text, scenario_skills, errors)

    for scenario_skill in sorted(scenario_skills - skill_names):
        fail(errors, f"evals/scenarios.json: scenario references unknown skill {scenario_skill!r}")

    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Skill validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
