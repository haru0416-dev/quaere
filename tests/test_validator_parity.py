"""Parity test: Python validate_skills.py and Rust `quaere doctor` agree.

Both the Python-side `scripts/validate_skills.py` (writer-side, pre-commit /
CI) and the Rust-side `cli/src/skill_meta.rs::check_skill` (reader-side,
post-install) re-implement the same SKILL.md structural contract:

  - REQUIRED_FIELDS present (name, description, compatibility, license)
  - name kebab-case and matching the directory
  - description starts with "This skill should be used" and is >= 80 chars
  - license == "MIT"
  - line count <= 500

This file exists to catch silent drift between the two implementations.
For each rule, the test constructs a minimal target containing one
SKILL.md, mutates the rule to violate it, then asserts that Python and
Rust agree on whether the resulting skill is valid.

The Rust side is exercised through `quaere doctor` against the temp
target. If the release binary has not been built (cargo build --release
in cli/), each Rust-side assertion skips with a clear message so this
suite still runs in Python-only environments.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_skills.py"
QUAERE_BIN = ROOT / "cli" / "target" / "release" / "quaere"


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "quaere_validate_skills_parity", VALIDATOR_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["quaere_validate_skills_parity"] = module
    spec.loader.exec_module(module)
    return module


vs = _load_validator()


VALID_SKILL = """\
---
name: quaere-sample
description: This skill should be used when running parity tests need a syntactically valid SKILL.md to compare both validators against without surprises.
compatibility: claude-code
license: MIT
---

# quaere-sample

Body.
"""


def _make_target(tmp: Path, skill_md: str, skill_name: str = "quaere-sample") -> tuple[Path, Path]:
    target = tmp / "target"
    skill_dir = target / skill_name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    manifest_dir = target / ".quaere"
    manifest_dir.mkdir()
    (manifest_dir / "manifest.json").write_text(
        json.dumps({"quaere_version": "0.1.0", "skills": [skill_name]}),
        encoding="utf-8",
    )
    return target, skill_dir


def _python_issues(skill_dir: Path, skill_name: str) -> list[str]:
    """Run Python validate_skill against an isolated skill_dir.

    The validate_skill helper also enforces cross-references (README, examples,
    scenarios) that are orthogonal to the SKILL.md structural contract under
    test. We pre-populate the cross-reference inputs with the skill name so
    that those rules never fire and the resulting issues list contains only
    SKILL.md-specific errors.
    """
    errors: list[str] = []
    readme_text = f"See skills/{skill_name}/SKILL.md for details.\n"
    examples_text = f"## `{skill_name}`\nExample.\n"
    scenario_skills = {skill_name}
    vs.validate_skill(skill_dir, readme_text, examples_text, scenario_skills, errors)
    return errors


def _rust_failed(test: unittest.TestCase, target: Path) -> bool:
    if not QUAERE_BIN.is_file():
        test.skipTest(
            f"Rust binary at {QUAERE_BIN} not built; run `cargo build --release` "
            f"in cli/ before invoking the parity suite."
        )
    completed = subprocess.run(
        [str(QUAERE_BIN), "doctor", "--target", str(target)],
        capture_output=True,
        text=True,
    )
    return completed.returncode != 0


class ValidatorParityTest(unittest.TestCase):
    def _both_accept(self, skill_md: str, skill_name: str = "quaere-sample") -> None:
        with TemporaryDirectory() as tmp:
            target, skill_dir = _make_target(Path(tmp), skill_md, skill_name)
            python_issues = _python_issues(skill_dir, skill_name)
            self.assertEqual(
                python_issues, [], f"Python rejected what Rust may accept: {python_issues}"
            )
            self.assertFalse(
                _rust_failed(self, target),
                "Rust rejected what Python accepted",
            )

    def _both_reject(
        self, skill_md: str, skill_name: str = "quaere-sample", message: str = ""
    ) -> None:
        with TemporaryDirectory() as tmp:
            target, skill_dir = _make_target(Path(tmp), skill_md, skill_name)
            python_issues = _python_issues(skill_dir, skill_name)
            self.assertNotEqual(
                python_issues, [], f"Python accepted invalid skill ({message})"
            )
            self.assertTrue(
                _rust_failed(self, target),
                f"Rust accepted invalid skill ({message})",
            )

    # --- baseline ---

    def test_valid_skill_accepted_by_both(self) -> None:
        self._both_accept(VALID_SKILL)

    # --- per-rule mutation tests ---

    def test_name_mismatch_rejected_by_both(self) -> None:
        broken = VALID_SKILL.replace("name: quaere-sample", "name: other-name")
        self._both_reject(broken, message="name does not match directory")

    def test_non_kebab_name_rejected_by_both(self) -> None:
        # Both the dir and the frontmatter use the bad name so that the
        # name-vs-dir check passes and the kebab check is what fires.
        broken = VALID_SKILL.replace("name: quaere-sample", "name: BadName")
        self._both_reject(broken, skill_name="BadName", message="name not kebab-case")

    def test_description_missing_canonical_prefix_rejected_by_both(self) -> None:
        broken = VALID_SKILL.replace(
            "description: This skill should be used when running parity tests need a syntactically valid SKILL.md to compare both validators against without surprises.",
            "description: A long enough description that does not start with the required canonical phrase mandated by both validators.",
        )
        self._both_reject(broken, message="description prefix missing")

    def test_description_too_short_rejected_by_both(self) -> None:
        broken = VALID_SKILL.replace(
            "description: This skill should be used when running parity tests need a syntactically valid SKILL.md to compare both validators against without surprises.",
            "description: This skill should be used.",
        )
        self._both_reject(broken, message="description too short")

    def test_non_mit_license_rejected_by_both(self) -> None:
        broken = VALID_SKILL.replace("license: MIT", "license: Apache-2.0")
        self._both_reject(broken, message="non-MIT license")

    def test_missing_required_field_rejected_by_both(self) -> None:
        broken = VALID_SKILL.replace("compatibility: claude-code\n", "")
        self._both_reject(broken, message="missing required field compatibility")

    def test_line_budget_overflow_rejected_by_both(self) -> None:
        # Pad past MAX_SKILL_LINES = 500.
        broken = VALID_SKILL.rstrip("\n") + "\n" + ("padding\n" * 600)
        self._both_reject(broken, message="line budget exceeded")

    def test_unquoted_colon_space_in_value_rejected_by_both(self) -> None:
        # A frontmatter value containing ': ' must be quoted so that YAML-
        # compatible skill loaders don't misparse it as a nested mapping.
        broken = VALID_SKILL.replace(
            "compatibility: claude-code",
            "compatibility: claude-code: extra",
        )
        self._both_reject(broken, message="unquoted ': ' in frontmatter value")


if __name__ == "__main__":
    unittest.main()
