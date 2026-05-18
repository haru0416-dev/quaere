from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "evals" / "run_skill_evals.py"


def _make_demo_skill(skills_dir: Path) -> Path:
    skill_dir = skills_dir / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo\ndescription: demo\n---\n# Demo\n",
        encoding="utf-8",
    )
    return skill_dir


def _write_scenarios(path: Path, scenarios: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps({"scenarios": scenarios}), encoding="utf-8")


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _load_grade(output_dir: Path, scenario_id: str, mode: str) -> dict[str, Any]:
    matches = list(output_dir.glob(f"*/*/demo/{scenario_id}/{mode}/grade.json"))
    if len(matches) != 1:
        raise AssertionError(f"expected 1 grade.json for {scenario_id}/{mode}, got {matches}")
    return json.loads(matches[0].read_text(encoding="utf-8"))


def _load_summary(output_dir: Path) -> dict[str, Any]:
    summaries = list(output_dir.glob("*/summary.json"))
    if len(summaries) != 1:
        raise AssertionError(f"expected 1 summary.json, got {summaries}")
    return json.loads(summaries[0].read_text(encoding="utf-8"))


class RunSkillEvalsTest(unittest.TestCase):
    def test_dry_run_writes_prompt_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            output_dir = temp_path / "results"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--runner",
                    "noop=printf ''",
                    "--scenario",
                    "sdk-version-grounding",
                    "--mode",
                    "both",
                    "--output-dir",
                    str(output_dir),
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            summaries = list(output_dir.glob("*/summary.json"))
            self.assertEqual(len(summaries), 1)

            summary = json.loads(summaries[0].read_text(encoding="utf-8"))
            self.assertEqual(summary["totals"]["runs"], 2)
            self.assertEqual(summary["totals"]["manual_only_runs"], 2)

            prompts = list(output_dir.glob("*/noop/quaere-grounding/sdk-version-grounding/*/prompt.md"))
            self.assertEqual(len(prompts), 2)
            prompt_text = "\n".join(path.read_text(encoding="utf-8") for path in prompts)
            self.assertIn("External Grounding", prompt_text)
            self.assertIn("No skill definition is provided", prompt_text)

    def test_assertion_failure_can_fail_process(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            scenarios = temp_path / "scenarios.json"
            skills_dir = temp_path / "skills"
            skill_dir = skills_dir / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: demo\n---\n# Demo\n",
                encoding="utf-8",
            )
            scenarios.write_text(
                json.dumps(
                    {
                        "scenarios": [
                            {
                                "id": "demo-case",
                                "skill": "demo",
                                "prompt": "Say hello",
                                "expected": [],
                                "assertions": [
                                    {"name": "requires missing word", "type": "contains", "text": "missing"}
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--scenarios",
                    str(scenarios),
                    "--skills-dir",
                    str(skills_dir),
                    "--runner",
                    "fake=printf hello",
                    "--output-dir",
                    str(temp_path / "results"),
                    "--fail-on-grade",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertTrue("failed" in completed.stdout or "fail" in completed.stdout)

    def test_scenario_workspace_is_copied(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            scenarios = temp_path / "scenarios.json"
            skills_dir = temp_path / "skills"
            skill_dir = skills_dir / "demo"
            fixture_dir = temp_path / "fixtures" / "demo-workspace"
            skill_dir.mkdir(parents=True)
            fixture_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: demo\n---\n# Demo\n",
                encoding="utf-8",
            )
            (fixture_dir / "evidence.txt").write_text("local anchor\n", encoding="utf-8")
            scenarios.write_text(
                json.dumps(
                    {
                        "scenarios": [
                            {
                                "id": "demo-case",
                                "skill": "demo",
                                "prompt": "Inspect the workspace",
                                "workspace": "fixtures/demo-workspace",
                                "expected": [],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--scenarios",
                    str(scenarios),
                    "--skills-dir",
                    str(skills_dir),
                    "--runner",
                    "noop=printf ''",
                    "--output-dir",
                    str(temp_path / "results"),
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            copied = list((temp_path / "results").glob("*/noop/demo/demo-case/with-skill/workspace/evidence.txt"))
            self.assertEqual(len(copied), 1)
            self.assertEqual(copied[0].read_text(encoding="utf-8"), "local anchor\n")


class AssertionTypesTest(unittest.TestCase):
    def test_ordered_sections_pass_and_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            skills_dir = temp_path / "skills"
            _make_demo_skill(skills_dir)
            scenarios = temp_path / "scenarios.json"
            output_dir = temp_path / "results"
            _write_scenarios(
                scenarios,
                [
                    {
                        "id": "ordered-pass",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {
                                "name": "in order",
                                "type": "ordered_sections",
                                "patterns": ["Findings", "Defense", "Decision"],
                            }
                        ],
                    },
                    {
                        "id": "ordered-fail",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {
                                "name": "wrong order",
                                "type": "ordered_sections",
                                "patterns": ["Decision", "Findings"],
                            }
                        ],
                    },
                ],
            )
            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--runner", "fake=printf 'Findings\\nDefense\\nDecision\\n'",
                    "--output-dir", str(output_dir),
                ],
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(_load_grade(output_dir, "ordered-pass", "with-skill")["status"], "pass")
            fail_grade = _load_grade(output_dir, "ordered-fail", "with-skill")
            self.assertEqual(fail_grade["status"], "fail")
            self.assertIn("Findings", fail_grade["assertions"][0]["detail"])

    def test_min_section_count_enforces_minimum(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            skills_dir = temp_path / "skills"
            _make_demo_skill(skills_dir)
            scenarios = temp_path / "scenarios.json"
            output_dir = temp_path / "results"
            _write_scenarios(
                scenarios,
                [
                    {
                        "id": "count-pass",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {"name": "two findings", "type": "min_section_count", "pattern": r"F-\d+", "min": 2}
                        ],
                    },
                    {
                        "id": "count-fail",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {"name": "three findings", "type": "min_section_count", "pattern": r"F-\d+", "min": 3}
                        ],
                    },
                ],
            )
            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--runner", "fake=printf 'F-001 F-002\\n'",
                    "--output-dir", str(output_dir),
                ],
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(_load_grade(output_dir, "count-pass", "with-skill")["status"], "pass")
            self.assertEqual(_load_grade(output_dir, "count-fail", "with-skill")["status"], "fail")

    def test_requires_pair_vacuous_and_violated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            skills_dir = temp_path / "skills"
            _make_demo_skill(skills_dir)
            scenarios = temp_path / "scenarios.json"
            output_dir = temp_path / "results"
            _write_scenarios(
                scenarios,
                [
                    {
                        "id": "pair-vacuous",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {
                                "name": "no antecedent",
                                "type": "requires_pair",
                                "if_contains": "confirmed",
                                "must_also_contain": "evidence",
                            }
                        ],
                    },
                    {
                        "id": "pair-violated",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {
                                "name": "claim without evidence",
                                "type": "requires_pair",
                                "if_contains": "confirmed",
                                "must_also_contain": "evidence",
                            }
                        ],
                    },
                ],
            )
            # First scenario: output has no "confirmed" so check is vacuous → pass.
            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--scenario", "pair-vacuous",
                    "--runner", "fake=printf 'rejected\\n'",
                    "--output-dir", str(output_dir / "v"),
                ],
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(_load_grade(output_dir / "v", "pair-vacuous", "with-skill")["status"], "pass")

            # Second scenario: output has "confirmed" but not "evidence" → fail.
            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--scenario", "pair-violated",
                    "--runner", "fake=printf 'confirmed\\n'",
                    "--output-dir", str(output_dir / "f"),
                ],
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(_load_grade(output_dir / "f", "pair-violated", "with-skill")["status"], "fail")

    def test_not_in_baseline_evaluates_cross_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            skills_dir = temp_path / "skills"
            _make_demo_skill(skills_dir)
            scenarios = temp_path / "scenarios.json"
            output_dir = temp_path / "results"
            _write_scenarios(
                scenarios,
                [
                    {
                        "id": "isolated-skill-effect",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {
                                "name": "with-skill produces Decision token absent in baseline",
                                "type": "not_in_baseline",
                                "patterns": ["with-skill"],
                            }
                        ],
                    },
                ],
            )
            # Runner template uses $mode so baseline outputs "baseline" and with-skill outputs "with-skill".
            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--runner", "fake=printf '%s' \"$mode\"",
                    "--mode", "both",
                    "--output-dir", str(output_dir),
                ],
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            grade = _load_grade(output_dir, "isolated-skill-effect", "with-skill")
            self.assertEqual(grade["status"], "pass", grade)
            baseline_grade = _load_grade(output_dir, "isolated-skill-effect", "baseline")
            # not_in_baseline assertions on the baseline side resolve to inconclusive.
            self.assertEqual(baseline_grade["assertions"][0]["status"], "inconclusive")

    def test_not_in_baseline_fails_when_baseline_already_contains_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            skills_dir = temp_path / "skills"
            _make_demo_skill(skills_dir)
            scenarios = temp_path / "scenarios.json"
            output_dir = temp_path / "results"
            _write_scenarios(
                scenarios,
                [
                    {
                        "id": "skill-effect-not-isolated",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {
                                "name": "skill effect must be isolated",
                                "type": "not_in_baseline",
                                "patterns": ["constant"],
                            }
                        ],
                    },
                ],
            )
            # Runner emits the same constant string regardless of mode.
            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--runner", "fake=printf 'constant'",
                    "--mode", "both",
                    "--output-dir", str(output_dir),
                ],
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            grade = _load_grade(output_dir, "skill-effect-not-isolated", "with-skill")
            self.assertEqual(grade["status"], "fail")
            self.assertIn("baseline", grade["assertions"][0]["detail"])

    def test_summary_counters_include_passed_and_assertion_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            skills_dir = temp_path / "skills"
            _make_demo_skill(skills_dir)
            scenarios = temp_path / "scenarios.json"
            output_dir = temp_path / "results"
            _write_scenarios(
                scenarios,
                [
                    {
                        "id": "passing",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {"name": "has hello", "type": "contains", "text": "hello"}
                        ],
                    },
                    {
                        "id": "manual",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": ["something only a human can verify"],
                    },
                ],
            )
            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--runner", "fake=printf hello",
                    "--output-dir", str(output_dir),
                ],
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            totals = _load_summary(output_dir)["totals"]
            self.assertEqual(totals["runs"], 2)
            self.assertEqual(totals["passed_assertion_runs"], 1)
            self.assertEqual(totals["manual_only_runs"], 1)
            self.assertEqual(totals["runs_with_assertions"], 1)


class RequireAssertionsFlagTest(unittest.TestCase):
    def test_require_assertions_fails_when_any_run_is_manual_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            skills_dir = temp_path / "skills"
            _make_demo_skill(skills_dir)
            scenarios = temp_path / "scenarios.json"
            output_dir = temp_path / "results"
            _write_scenarios(
                scenarios,
                [
                    {
                        "id": "manual",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": ["needs human review"],
                    }
                ],
            )
            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--runner", "fake=printf hello",
                    "--output-dir", str(output_dir),
                    "--require-assertions",
                ],
            )
            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertIn("require-assertions", completed.stderr)


if __name__ == "__main__":
    unittest.main()
