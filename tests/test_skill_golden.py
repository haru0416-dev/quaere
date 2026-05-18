from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
SKILLS_DIR = ROOT / "skills"


def _load_golden(skill: str) -> dict:
    path = GOLDEN_DIR / f"{skill}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _skill_text(skill: str) -> str:
    return (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")


class SkillGoldenTest(unittest.TestCase):
    """Verify each SKILL.md matches its golden contract.

    Golden files (tests/golden/<skill>.json) declare:
      - required_sections: regex patterns that must match at least one line
      - forbidden_patterns: regex patterns that must not appear anywhere
      - max_lines: hard line budget for the SKILL.md file

    This catches three failure modes: a skill silently losing a structural
    H2 section, regressing to a banned vocabulary (e.g. old skill names,
    TODO leftovers), or expanding past the agreed-on length budget.
    """

    def _check_skill(self, skill: str) -> None:
        golden = _load_golden(skill)
        text = _skill_text(skill)
        lines = text.splitlines()

        # Required sections
        missing = [
            pattern
            for pattern in golden["required_sections"]
            if not any(re.search(pattern, line) for line in lines)
        ]
        self.assertEqual(
            missing,
            [],
            f"{skill}: missing required H2 sections: {missing}",
        )

        # Forbidden patterns
        present = [
            pattern
            for pattern in golden["forbidden_patterns"]
            if re.search(pattern, text)
        ]
        self.assertEqual(
            present,
            [],
            f"{skill}: forbidden patterns appeared: {present}",
        )

        # Line budget
        self.assertLessEqual(
            len(lines),
            golden["max_lines"],
            f"{skill}: {len(lines)} lines exceeds budget of {golden['max_lines']}",
        )

    def test_quaere_semantic(self) -> None:
        self._check_skill("quaere-semantic")

    def test_quaere_grounding(self) -> None:
        self._check_skill("quaere-grounding")

    def test_quaere_evidence(self) -> None:
        self._check_skill("quaere-evidence")

    def test_quaere_execution(self) -> None:
        self._check_skill("quaere-execution")

    def test_quaere_audit(self) -> None:
        self._check_skill("quaere-audit")

    def test_every_skill_has_a_golden(self) -> None:
        skill_dirs = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir())
        golden_files = sorted(p.stem for p in GOLDEN_DIR.glob("*.json"))
        self.assertEqual(
            skill_dirs,
            golden_files,
            "every skill must have a matching tests/golden/<skill>.json",
        )


if __name__ == "__main__":
    unittest.main()
