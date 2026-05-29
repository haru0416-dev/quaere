from __future__ import annotations

import importlib.util
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_skills.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("quaere_validate_skills", VALIDATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["quaere_validate_skills"] = module
    spec.loader.exec_module(module)
    return module


vs = _load_validator()


def _write_skill(
    skills_dir: Path,
    name: str,
    *,
    description: str | None = None,
    license_: str = "MIT",
    compatibility: str = "claude-code",
    line_padding: int = 0,
    override_name: str | None = None,
) -> Path:
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True)
    body_lines = [
        "---",
        f"name: {override_name if override_name is not None else name}",
        f"description: {description or 'This skill should be used when running unit tests need a valid skill to exercise the validator without surprises.'}",
        f"compatibility: {compatibility}",
        f"license: {license_}",
        "---",
        f"# {name}",
        "",
        "Body.",
    ]
    body_lines.extend(["padding"] * line_padding)
    (skill_dir / "SKILL.md").write_text("\n".join(body_lines) + "\n", encoding="utf-8")
    return skill_dir


def _write_repo(
    root: Path,
    *,
    skills: list[str] | None = None,
    readme: str | None = None,
    examples: str | None = None,
    scenarios: list[dict[str, Any]] | None = None,
    group: str | None = None,
) -> None:
    skills = skills if skills is not None else ["sample-skill"]
    base = (root / "skills" / group) if group else (root / "skills")
    base.mkdir(parents=True, exist_ok=True)
    for name in skills:
        _write_skill(base, name)

    ref_prefix = f"skills/{group}" if group else "skills"
    readme_text = readme if readme is not None else "# Test repo\n\n" + "\n".join(
        f"- [{ref_prefix}/{name}]({ref_prefix}/{name}/SKILL.md)" for name in skills
    )
    (root / "README.md").write_text(readme_text + "\n", encoding="utf-8")

    examples_dir = root / "examples"
    examples_dir.mkdir(parents=True, exist_ok=True)
    examples_text = examples if examples is not None else "\n".join(
        f"## `{name}`\nExample." for name in skills
    )
    (examples_dir / "README.md").write_text(examples_text + "\n", encoding="utf-8")

    evals_dir = root / "evals"
    evals_dir.mkdir(parents=True, exist_ok=True)
    scenarios_data = {
        "scenarios": scenarios
        if scenarios is not None
        else [
            {
                "id": f"{name}-scenario",
                "skill": name,
                "expected": ["does the right thing"],
            }
            for name in skills
        ]
    }
    (evals_dir / "scenarios.json").write_text(json.dumps(scenarios_data), encoding="utf-8")


def _run_main(tmp_root: Path) -> tuple[int, str]:
    captured = io.StringIO()
    with patch.multiple(
        vs,
        ROOT=tmp_root,
        SKILLS_DIR=tmp_root / "skills",
        README=tmp_root / "README.md",
        EXAMPLES=tmp_root / "examples" / "README.md",
        SCENARIOS=tmp_root / "evals" / "scenarios.json",
    ), redirect_stdout(captured):
        rc = vs.main()
    return rc, captured.getvalue()


class ParseFrontmatterTest(unittest.TestCase):
    def test_happy_path(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(
                "---\nname: foo\ndescription: hi\n---\nbody\n", encoding="utf-8"
            )
            errors: list[str] = []
            meta = vs.parse_frontmatter(path, errors)
        self.assertEqual(meta, {"name": "foo", "description": "hi"})
        self.assertEqual(errors, [])

    def test_missing_opening_delimiter(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text("name: foo\n---\n", encoding="utf-8")
            errors: list[str] = []
            vs.parse_frontmatter(path, errors)
        self.assertTrue(any("missing opening frontmatter delimiter" in e for e in errors))

    def test_missing_closing_delimiter(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text("---\nname: foo\n", encoding="utf-8")
            errors: list[str] = []
            vs.parse_frontmatter(path, errors)
        self.assertTrue(any("missing closing frontmatter delimiter" in e for e in errors))

    def test_malformed_line_without_colon(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text("---\nname foo\n---\n", encoding="utf-8")
            errors: list[str] = []
            vs.parse_frontmatter(path, errors)
        self.assertTrue(any("frontmatter line must be key: value" in e for e in errors))

    def test_unquoted_colon_space_value_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(
                "---\ndescription: This: should be quoted\n---\n", encoding="utf-8"
            )
            errors: list[str] = []
            vs.parse_frontmatter(path, errors)
        self.assertTrue(any("must be quoted" in e for e in errors))

    def test_quoted_colon_space_value_passes(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(
                "---\ndescription: \"This: is fine\"\n---\n", encoding="utf-8"
            )
            errors: list[str] = []
            meta = vs.parse_frontmatter(path, errors)
        self.assertEqual(errors, [])
        self.assertEqual(meta["description"], "This: is fine")


class ValidateSkillTest(unittest.TestCase):
    def _validate(self, root: Path, *, skill_name: str = "sample-skill") -> list[str]:
        errors: list[str] = []
        readme = (root / "README.md").read_text(encoding="utf-8")
        examples = (root / "examples" / "README.md").read_text(encoding="utf-8")
        scenario_skills = {skill_name}
        vs.validate_skill(root / "skills" / skill_name, readme, examples, scenario_skills, errors)
        return errors

    def test_happy_path_no_errors(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_repo(root, skills=["sample-skill"])
            errors = self._validate(root)
        self.assertEqual(errors, [])

    def test_missing_skill_md(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_repo(root, skills=["sample-skill"])
            (root / "skills" / "sample-skill" / "SKILL.md").unlink()
            errors = self._validate(root)
        self.assertTrue(any("missing SKILL.md" in e for e in errors))

    def test_name_dir_mismatch(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills").mkdir()
            _write_skill(root / "skills", "sample-skill", override_name="different-name")
            _write_repo_extras(root, ["sample-skill"])
            errors = self._validate(root)
        self.assertTrue(
            any("must match directory" in e for e in errors),
            f"errors were: {errors}",
        )

    def test_non_kebab_case_name_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills").mkdir()
            skill_dir = root / "skills" / "Bad_Name"
            _write_skill(root / "skills", "Bad_Name")
            _write_repo_extras(root, ["Bad_Name"])
            errors = self._validate(root, skill_name="Bad_Name")
        self.assertTrue(any("must be kebab-case" in e for e in errors))

    def test_description_must_start_with_canonical_phrase(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills").mkdir()
            _write_skill(
                root / "skills",
                "sample-skill",
                description="Helps you do stuff with a sufficiently long description for the length check.",
            )
            _write_repo_extras(root, ["sample-skill"])
            errors = self._validate(root)
        self.assertTrue(any("description should start with" in e for e in errors))

    def test_description_too_short_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills").mkdir()
            _write_skill(
                root / "skills",
                "sample-skill",
                description="This skill should be used.",
            )
            _write_repo_extras(root, ["sample-skill"])
            errors = self._validate(root)
        self.assertTrue(any("too short" in e for e in errors))

    def test_non_mit_license_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills").mkdir()
            _write_skill(root / "skills", "sample-skill", license_="Apache-2.0")
            _write_repo_extras(root, ["sample-skill"])
            errors = self._validate(root)
        self.assertTrue(any("license should be MIT" in e for e in errors))

    def test_line_budget_overflow_is_detected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills").mkdir()
            _write_skill(root / "skills", "sample-skill", line_padding=vs.MAX_SKILL_LINES + 10)
            _write_repo_extras(root, ["sample-skill"])
            errors = self._validate(root)
        self.assertTrue(any("exceeds" in e and "line budget" in e for e in errors))

    def test_missing_readme_reference_is_detected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_repo(root, skills=["sample-skill"], readme="# Test repo\n\nNothing here.")
            errors = self._validate(root)
        self.assertTrue(any("missing reference to skills/sample-skill" in e for e in errors))

    def test_missing_examples_section_is_detected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_repo(root, skills=["sample-skill"], examples="## `other-thing`\n")
            errors = self._validate(root)
        self.assertTrue(any("missing example section" in e for e in errors))

    def test_missing_scenario_is_detected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_repo(root, skills=["sample-skill"])
            errors: list[str] = []
            readme = (root / "README.md").read_text(encoding="utf-8")
            examples = (root / "examples" / "README.md").read_text(encoding="utf-8")
            vs.validate_skill(root / "skills" / "sample-skill", readme, examples, set(), errors)
        self.assertTrue(any("missing scenario" in e for e in errors))


def _write_repo_extras(root: Path, skills: list[str]) -> None:
    readme_text = "# Test repo\n\n" + "\n".join(
        f"- [skills/{name}](skills/{name}/SKILL.md)" for name in skills
    )
    (root / "README.md").write_text(readme_text + "\n", encoding="utf-8")
    examples_dir = root / "examples"
    examples_dir.mkdir(parents=True, exist_ok=True)
    examples_text = "\n".join(f"## `{name}`\nExample." for name in skills)
    (examples_dir / "README.md").write_text(examples_text + "\n", encoding="utf-8")
    evals_dir = root / "evals"
    evals_dir.mkdir(parents=True, exist_ok=True)
    (evals_dir / "scenarios.json").write_text(
        json.dumps(
            {
                "scenarios": [
                    {"id": f"{name}-scenario", "skill": name, "expected": ["x"]}
                    for name in skills
                ]
            }
        ),
        encoding="utf-8",
    )


class LoadScenarioSkillsTest(unittest.TestCase):
    def _load(self, content: str | dict[str, Any], tmp: Path) -> tuple[set[str], list[str]]:
        path = tmp / "scenarios.json"
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            path.write_text(json.dumps(content), encoding="utf-8")
        errors: list[str] = []
        result = vs.load_scenario_skills(path, errors)
        return result, errors

    def test_missing_file_records_error(self) -> None:
        with TemporaryDirectory() as tmp:
            errors: list[str] = []
            result = vs.load_scenario_skills(Path(tmp) / "absent.json", errors)
        self.assertEqual(result, set())
        self.assertTrue(any("missing evals/scenarios.json" in e for e in errors))

    def test_invalid_json_is_reported(self) -> None:
        with TemporaryDirectory() as tmp:
            _, errors = self._load("{not json", Path(tmp))
        self.assertTrue(any("invalid JSON" in e for e in errors))

    def test_scenarios_must_be_list(self) -> None:
        with TemporaryDirectory() as tmp:
            _, errors = self._load({"scenarios": {}}, Path(tmp))
        self.assertTrue(any("scenarios must be a list" in e for e in errors))

    def test_non_object_scenario_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            _, errors = self._load({"scenarios": ["bad"]}, Path(tmp))
        self.assertTrue(any("must be an object" in e for e in errors))

    def test_missing_skill_field(self) -> None:
        with TemporaryDirectory() as tmp:
            _, errors = self._load(
                {"scenarios": [{"id": "x", "expected": ["y"]}]}, Path(tmp)
            )
        self.assertTrue(any("missing string skill" in e for e in errors))

    def test_expected_must_be_list_of_strings(self) -> None:
        with TemporaryDirectory() as tmp:
            _, errors = self._load(
                {"scenarios": [{"id": "x", "skill": "s", "expected": "not-a-list"}]},
                Path(tmp),
            )
        self.assertTrue(any("expected must be a list of strings" in e for e in errors))

    def test_workspace_must_be_string(self) -> None:
        with TemporaryDirectory() as tmp:
            _, errors = self._load(
                {
                    "scenarios": [
                        {"id": "x", "skill": "s", "expected": ["y"], "workspace": 123}
                    ]
                },
                Path(tmp),
            )
        self.assertTrue(any("workspace must be a string" in e for e in errors))

    def test_workspace_missing_dir_is_reported(self) -> None:
        with TemporaryDirectory() as tmp:
            _, errors = self._load(
                {
                    "scenarios": [
                        {
                            "id": "x",
                            "skill": "s",
                            "expected": ["y"],
                            "workspace": "../nope",
                        }
                    ]
                },
                Path(tmp),
            )
        self.assertTrue(any("workspace does not exist" in e for e in errors))

    def test_unsupported_assertion_type(self) -> None:
        with TemporaryDirectory() as tmp:
            _, errors = self._load(
                {
                    "scenarios": [
                        {
                            "id": "x",
                            "skill": "s",
                            "expected": ["y"],
                            "assertions": [{"type": "magic"}],
                        }
                    ]
                },
                Path(tmp),
            )
        self.assertTrue(any("unsupported type" in e for e in errors))

    def test_missing_required_assertion_key(self) -> None:
        with TemporaryDirectory() as tmp:
            _, errors = self._load(
                {
                    "scenarios": [
                        {
                            "id": "x",
                            "skill": "s",
                            "expected": ["y"],
                            "assertions": [{"type": "contains"}],
                        }
                    ]
                },
                Path(tmp),
            )
        self.assertTrue(any("missing required key 'text'" in e for e in errors))

    def test_exit_code_assertion_does_not_require_extra_keys(self) -> None:
        with TemporaryDirectory() as tmp:
            _, errors = self._load(
                {
                    "scenarios": [
                        {
                            "id": "x",
                            "skill": "s",
                            "expected": ["y"],
                            "assertions": [{"type": "exit_code"}],
                        }
                    ]
                },
                Path(tmp),
            )
        self.assertEqual(errors, [])


class ValidateMainTest(unittest.TestCase):
    def test_clean_repo_returns_zero(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_repo(root, skills=["alpha-skill"], group="core")
            rc, out = _run_main(root)
        self.assertEqual(rc, 0, out)
        self.assertIn("Skill validation passed", out)

    def test_missing_readme_returns_nonzero(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_repo(root, skills=["alpha-skill"], group="core")
            (root / "README.md").unlink()
            rc, out = _run_main(root)
        self.assertEqual(rc, 1)
        self.assertIn("missing README.md", out)

    def test_agent_state_directory_is_detected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_repo(root, skills=["alpha-skill"], group="core")
            (root / ".agent-state").mkdir()
            (root / ".agent-state" / "notes.md").write_text("local", encoding="utf-8")
            rc, out = _run_main(root)
        self.assertEqual(rc, 1)
        self.assertIn("local investigation state should not be committed", out)

    def test_empty_skills_dir_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_repo(root, skills=[])
            (root / "skills").mkdir(exist_ok=True)
            (root / "README.md").write_text("# empty\n", encoding="utf-8")
            (root / "examples").mkdir(exist_ok=True)
            (root / "examples" / "README.md").write_text("nothing\n", encoding="utf-8")
            (root / "evals" / "scenarios.json").write_text(
                json.dumps({"scenarios": []}), encoding="utf-8"
            )
            rc, out = _run_main(root)
        self.assertEqual(rc, 1)
        self.assertIn("skills/core and skills/extensions contain no skill directories", out)

    def test_unknown_scenario_skill_is_reported(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_repo(
                root,
                skills=["alpha-skill"],
                group="core",
                scenarios=[
                    {
                        "id": "alpha-scenario",
                        "skill": "alpha-skill",
                        "expected": ["ok"],
                    },
                    {
                        "id": "ghost-scenario",
                        "skill": "ghost-skill",
                        "expected": ["ok"],
                    },
                ],
            )
            rc, out = _run_main(root)
        self.assertEqual(rc, 1)
        self.assertIn("references unknown skill 'ghost-skill'", out)

    def test_real_repo_passes(self) -> None:
        rc, out = _run_main(ROOT)
        self.assertEqual(rc, 0, out)
        self.assertIn("Skill validation passed", out)


if __name__ == "__main__":
    unittest.main()
