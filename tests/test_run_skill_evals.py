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

sys.path.insert(0, str(ROOT))
from evals.run_skill_evals import (  # noqa: E402
    Scenario,
    aggregate_cells,
    assertion_axis,
    evaluate_assertion,
    grade_output,
    load_scenarios,
    mcnemar_exact_p,
)


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
    # These tests exercise single-run grading semantics; default to --runs 1 unless
    # a test opts into repeated runs explicitly (the N-run aggregation tests do).
    if "--runs" not in args:
        args = [*args, "--runs", "1"]
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

    def test_rejects_unsafe_scenario_path_components(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            scenarios = Path(temp) / "scenarios.json"
            _write_scenarios(
                scenarios,
                [
                    {
                        "id": "../../escape",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "may contain only"):
                load_scenarios(scenarios)

            _write_scenarios(
                scenarios,
                [
                    {
                        "id": "safe-id",
                        "skill": "../../escape",
                        "prompt": "x",
                        "expected": [],
                    }
                ],
            )
            with self.assertRaisesRegex(ValueError, "may contain only"):
                load_scenarios(scenarios)

    def test_runner_template_values_are_shell_quoted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            marker = temp_path / "pwned"
            output_dir = temp_path / f"results$(touch {marker})"
            scenarios = temp_path / "scenarios.json"
            skills_dir = temp_path / "skills"
            _make_demo_skill(skills_dir)
            _write_scenarios(
                scenarios,
                [
                    {
                        "id": "demo-case",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [{"type": "contains", "text": "hello"}],
                    }
                ],
            )

            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--runner", "fake=printf hello > $output_file",
                    "--output-dir", str(output_dir),
                    "--fail-on-grade",
                ]
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertFalse(marker.exists(), "shell metacharacters in substituted paths must not execute")

    def test_custom_llm_judge_cache_dir_does_not_break_summary_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            scenarios = temp_path / "scenarios.json"
            skills_dir = temp_path / "skills"
            _make_demo_skill(skills_dir)
            _write_scenarios(
                scenarios,
                [
                    {
                        "id": "demo-case",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [{"type": "contains", "text": "hello"}],
                    }
                ],
            )

            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--runner", "fake=printf hello",
                    "--output-dir", str(temp_path / "results"),
                    "--llm-judge-cache-dir", str(temp_path / "cache"),
                    "--fail-on-grade",
                ]
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            summary = _load_summary(temp_path / "results")
            for run in summary["runs"]:
                self.assertNotIn("__llm_judge_cache_dir", run["metadata"])


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

    def test_not_regex_pass_and_fail(self) -> None:
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
                        "id": "notregex-pass",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {
                                "name": "forbidden pattern absent",
                                "type": "not_regex",
                                "pattern": "(?im)push.*because.*obvious|correct.*therefore.*push",
                            }
                        ],
                    },
                    {
                        "id": "notregex-fail",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {
                                "name": "forbidden pattern present",
                                "type": "not_regex",
                                "pattern": "(?i)decision",
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
            self.assertEqual(_load_grade(output_dir, "notregex-pass", "with-skill")["status"], "pass")
            fail_grade = _load_grade(output_dir, "notregex-fail", "with-skill")
            self.assertEqual(fail_grade["status"], "fail")
            self.assertIn("forbidden regex", fail_grade["assertions"][0]["detail"])

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

    def test_requires_pair_skip_when_clause_passes_when_consequent_missing(self) -> None:
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
                        "id": "pair-skipped",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {
                                "name": "claim with skip clause",
                                "type": "requires_pair",
                                "if_contains": "confirmed",
                                "must_also_contain": "evidence",
                                "skip_when": "(?i)skipped because",
                            }
                        ],
                    },
                    {
                        "id": "pair-skipped-but-still-no-skip-clause",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {
                                "name": "consequent missing and no skip clause matches",
                                "type": "requires_pair",
                                "if_contains": "confirmed",
                                "must_also_contain": "evidence",
                                "skip_when": "(?i)skipped because",
                            }
                        ],
                    },
                ],
            )
            # Antecedent present, consequent missing, but skip_when matches → pass.
            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--scenario", "pair-skipped",
                    "--runner",
                    "fake=printf 'confirmed; full suite skipped because production replay is unsafe\\n'",
                    "--output-dir", str(output_dir / "s"),
                ],
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(_load_grade(output_dir / "s", "pair-skipped", "with-skill")["status"], "pass")

            # Antecedent present, consequent missing, skip_when also absent → fail.
            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--scenario", "pair-skipped-but-still-no-skip-clause",
                    "--runner", "fake=printf 'confirmed\\n'",
                    "--output-dir", str(output_dir / "nsk"),
                ],
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                _load_grade(output_dir / "nsk", "pair-skipped-but-still-no-skip-clause", "with-skill")["status"],
                "fail",
            )

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


def _find_cell(summary: dict[str, Any], scenario_id: str, mode: str) -> dict[str, Any]:
    for cell in summary.get("cells", []):
        if cell["scenario_id"] == scenario_id and cell["mode"] == mode:
            return cell
    raise AssertionError(f"no cell for {scenario_id}/{mode} in {summary.get('cells')}")


class NRunAggregationTest(unittest.TestCase):
    def test_repeated_runs_nest_and_aggregate(self) -> None:
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
                        "id": "n-run",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [{"name": "has hello", "type": "contains", "text": "hello"}],
                    }
                ],
            )
            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--runner", "fake=printf hello",
                    "--output-dir", str(output_dir),
                    "--runs", "3",
                ],
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            run_grades = list(output_dir.glob("*/*/demo/n-run/with-skill/run-*/grade.json"))
            self.assertEqual(len(run_grades), 3, run_grades)
            cell = _find_cell(_load_summary(output_dir), "n-run", "with-skill")
            self.assertEqual(cell["runs"], 3)
            self.assertEqual(cell["status_pass_runs"], 3)

    def test_axis_tag_splits_outcome_and_form(self) -> None:
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
                        "id": "axes",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {"name": "outcome ok", "type": "contains", "text": "hello", "axis": "outcome"},
                            {"name": "form missing", "type": "contains", "text": "NEVER", "axis": "form"},
                        ],
                    }
                ],
            )
            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--runner", "fake=printf hello",
                    "--output-dir", str(output_dir),
                    "--runs", "2",
                ],
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            cell = _find_cell(_load_summary(output_dir), "axes", "with-skill")
            self.assertEqual((cell["outcome_pass"], cell["outcome_applicable"]), (2, 2))
            self.assertEqual((cell["form_pass"], cell["form_applicable"]), (0, 2))

    def test_paired_comparison_reports_delta_and_mcnemar(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            skills_dir = temp_path / "skills"
            _make_demo_skill(skills_dir)
            scenarios = temp_path / "scenarios.json"
            output_dir = temp_path / "results"
            # The runner echoes ${mode}; the outcome assertion only matches the
            # with-skill arm, so baseline fails outcome and with-skill passes it.
            _write_scenarios(
                scenarios,
                [
                    {
                        "id": "paired",
                        "skill": "demo",
                        "prompt": "x",
                        "expected": [],
                        "assertions": [
                            {"name": "mode is with-skill", "type": "contains", "text": "with-skill", "axis": "outcome"}
                        ],
                    }
                ],
            )
            completed = _run(
                [
                    "--scenarios", str(scenarios),
                    "--skills-dir", str(skills_dir),
                    "--runner", "fake=printf '%s' ${mode}",
                    "--output-dir", str(output_dir),
                    "--mode", "both",
                    "--runs", "3",
                ],
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = _load_summary(output_dir)
            base = _find_cell(summary, "paired", "baseline")
            skl = _find_cell(summary, "paired", "with-skill")
            self.assertEqual((base["outcome_pass"], base["outcome_applicable"]), (0, 3))
            self.assertEqual((skl["outcome_pass"], skl["outcome_applicable"]), (3, 3))
            pairs = summary["pairs"]
            entry = next(e for e in pairs["per_scenario"] if e["scenario_id"] == "paired")
            self.assertEqual(entry["delta"], 1.0)
            self.assertEqual(pairs["mcnemar"]["discordant_skill_only"], 1)
            self.assertEqual(pairs["mcnemar"]["discordant_baseline_only"], 0)

    def test_dry_run_forces_single_sample(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            output_dir = temp_path / "results"
            completed = _run(
                [
                    "--runner", "noop=printf ''",
                    "--scenario", "sdk-version-grounding",
                    "--output-dir", str(output_dir),
                    "--runs", "5",
                    "--dry-run",
                ],
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            # Forced to one sample: flat layout, no run-NN nesting.
            flat = list(output_dir.glob("*/noop/quaere-grounding/sdk-version-grounding/with-skill/prompt.md"))
            nested = list(output_dir.glob("*/noop/*/*/with-skill/run-*/prompt.md"))
            self.assertEqual(len(flat), 1, flat)
            self.assertEqual(nested, [])


class PureAggregationTest(unittest.TestCase):
    def test_mcnemar_exact_p_no_discordants_is_none(self) -> None:
        self.assertIsNone(mcnemar_exact_p(0, 0))

    def test_mcnemar_exact_p_symmetric_values(self) -> None:
        # b01=b10=5 -> two-sided p should be ~1.0
        self.assertAlmostEqual(mcnemar_exact_p(5, 5), 1.0, places=6)

    def test_mcnemar_exact_p_all_one_direction(self) -> None:
        # 0 vs 6 discordants -> p = 2 * 0.5**6
        self.assertAlmostEqual(mcnemar_exact_p(0, 6), 2 * (0.5 ** 6), places=6)

    def test_assertion_axis_defaults_to_form(self) -> None:
        self.assertEqual(assertion_axis({"type": "contains"}), "form")
        self.assertEqual(assertion_axis({"type": "contains", "axis": "outcome"}), "outcome")
        self.assertEqual(assertion_axis({"type": "contains", "axis": "bogus"}), "form")

    def test_aggregate_cells_skips_dry_run(self) -> None:
        results = [
            {
                "metadata": {"runner": "r", "skill": "s", "scenario_id": "x", "mode": "with-skill", "dry_run": True},
                "grade": {"status": "manual-only", "assertions": []},
            }
        ]
        self.assertEqual(aggregate_cells(results), [])


class RequireAssertionsFlagTest(unittest.TestCase):
    def test_skipped_only_assertions_are_skipped(self) -> None:
        scenario = Scenario(
            id="skip-only",
            skill="demo",
            prompt="x",
            expected=[],
            assertions=[{"type": "llm_judge", "name": "judge", "rubric": "Reply PASS or FAIL"}],
            workspace=None,
        )
        grade = grade_output(scenario, "agent output", {"dry_run": False})
        self.assertEqual(grade["status"], "skipped")
        self.assertEqual(grade["summary"]["assertions_skipped"], 1)

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


class ScenariosExtraMergeTest(unittest.TestCase):
    """Cover --scenarios-extra merge semantics via direct load_scenarios calls."""

    def _write(self, path: Path, body: dict[str, Any]) -> None:
        path.write_text(json.dumps(body), encoding="utf-8")

    def _base_assertions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "regex assertion",
                "type": "regex",
                "pattern": "(?i)foo|bar",
            },
            {
                "name": "ordered assertion",
                "type": "ordered_sections",
                "patterns": ["(?i)alpha", "(?i)beta", "(?i)gamma"],
            },
            {
                "name": "contains_any assertion",
                "type": "contains_any",
                "texts": ["hello", "world"],
            },
            {
                "name": "pair assertion",
                "type": "requires_pair",
                "if_contains": "(?i)trigger",
                "must_also_contain": "(?i)guard",
                "skip_when": "(?i)skipped because",
            },
        ]

    def _base_scenario(self) -> dict[str, Any]:
        return {
            "id": "demo-scenario",
            "skill": "demo",
            "prompt": "x",
            "expected": [],
            "assertions": self._base_assertions(),
        }

    def test_no_extras_path_returns_main_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            main = Path(temp) / "scenarios.json"
            self._write(main, {"scenarios": [self._base_scenario()]})
            scenarios = load_scenarios(main)
            self.assertEqual(scenarios[0].assertions[0]["pattern"], "(?i)foo|bar")

    def test_regex_pattern_alternation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            main = Path(temp) / "scenarios.json"
            extra = Path(temp) / "scenarios.ja.json"
            self._write(main, {"scenarios": [self._base_scenario()]})
            self._write(
                extra,
                {
                    "scenarios": [
                        {
                            "id": "demo-scenario",
                            "assertions": [
                                {
                                    "name": "regex assertion",
                                    "type": "regex",
                                    "pattern": "バー|フー",
                                }
                            ],
                        }
                    ]
                },
            )
            scenarios = load_scenarios(main, extra)
            self.assertEqual(scenarios[0].assertions[0]["pattern"], "(?i)foo|bar|バー|フー")

    def test_ordered_sections_per_position_alternation_and_empty_slot(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            main = Path(temp) / "scenarios.json"
            extra = Path(temp) / "scenarios.ja.json"
            self._write(main, {"scenarios": [self._base_scenario()]})
            # Empty middle slot leaves position unchanged.
            self._write(
                extra,
                {
                    "scenarios": [
                        {
                            "id": "demo-scenario",
                            "assertions": [
                                {
                                    "name": "ordered assertion",
                                    "type": "ordered_sections",
                                    "patterns": ["アルファ", "", "ガンマ"],
                                }
                            ],
                        }
                    ]
                },
            )
            scenarios = load_scenarios(main, extra)
            ordered = scenarios[0].assertions[1]
            self.assertEqual(
                ordered["patterns"],
                ["(?i)alpha|アルファ", "(?i)beta", "(?i)gamma|ガンマ"],
            )

    def test_contains_any_texts_concatenation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            main = Path(temp) / "scenarios.json"
            extra = Path(temp) / "scenarios.ja.json"
            self._write(main, {"scenarios": [self._base_scenario()]})
            self._write(
                extra,
                {
                    "scenarios": [
                        {
                            "id": "demo-scenario",
                            "assertions": [
                                {
                                    "name": "contains_any assertion",
                                    "type": "contains_any",
                                    "texts": ["こんにちは", "世界"],
                                }
                            ],
                        }
                    ]
                },
            )
            scenarios = load_scenarios(main, extra)
            self.assertEqual(
                scenarios[0].assertions[2]["texts"],
                ["hello", "world", "こんにちは", "世界"],
            )

    def test_requires_pair_all_three_fields_alternated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            main = Path(temp) / "scenarios.json"
            extra = Path(temp) / "scenarios.ja.json"
            self._write(main, {"scenarios": [self._base_scenario()]})
            self._write(
                extra,
                {
                    "scenarios": [
                        {
                            "id": "demo-scenario",
                            "assertions": [
                                {
                                    "name": "pair assertion",
                                    "type": "requires_pair",
                                    "if_contains": "トリガ",
                                    "must_also_contain": "ガード",
                                    "skip_when": "理由により省略",
                                }
                            ],
                        }
                    ]
                },
            )
            scenarios = load_scenarios(main, extra)
            pair = scenarios[0].assertions[3]
            self.assertEqual(pair["if_contains"], "(?i)trigger|トリガ")
            self.assertEqual(pair["must_also_contain"], "(?i)guard|ガード")
            self.assertEqual(pair["skip_when"], "(?i)skipped because|理由により省略")

    def test_unknown_scenario_id_errors_out(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            main = Path(temp) / "scenarios.json"
            extra = Path(temp) / "scenarios.ja.json"
            self._write(main, {"scenarios": [self._base_scenario()]})
            self._write(
                extra,
                {
                    "scenarios": [
                        {
                            "id": "no-such-scenario",
                            "assertions": [
                                {"name": "regex assertion", "type": "regex", "pattern": "x"}
                            ],
                        }
                    ]
                },
            )
            with self.assertRaisesRegex(ValueError, "no-such-scenario"):
                load_scenarios(main, extra)

    def test_unknown_assertion_name_errors_out(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            main = Path(temp) / "scenarios.json"
            extra = Path(temp) / "scenarios.ja.json"
            self._write(main, {"scenarios": [self._base_scenario()]})
            self._write(
                extra,
                {
                    "scenarios": [
                        {
                            "id": "demo-scenario",
                            "assertions": [
                                {"name": "no such assertion", "type": "regex", "pattern": "x"}
                            ],
                        }
                    ]
                },
            )
            with self.assertRaisesRegex(ValueError, "no such assertion"):
                load_scenarios(main, extra)

    def test_type_mismatch_errors_out(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            main = Path(temp) / "scenarios.json"
            extra = Path(temp) / "scenarios.ja.json"
            self._write(main, {"scenarios": [self._base_scenario()]})
            self._write(
                extra,
                {
                    "scenarios": [
                        {
                            "id": "demo-scenario",
                            "assertions": [
                                {
                                    "name": "regex assertion",
                                    "type": "contains_any",
                                    "texts": ["x"],
                                }
                            ],
                        }
                    ]
                },
            )
            with self.assertRaisesRegex(ValueError, "type mismatch"):
                load_scenarios(main, extra)

    def test_patterns_length_mismatch_errors_out(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            main = Path(temp) / "scenarios.json"
            extra = Path(temp) / "scenarios.ja.json"
            self._write(main, {"scenarios": [self._base_scenario()]})
            self._write(
                extra,
                {
                    "scenarios": [
                        {
                            "id": "demo-scenario",
                            "assertions": [
                                {
                                    "name": "ordered assertion",
                                    "type": "ordered_sections",
                                    "patterns": ["only-one"],
                                }
                            ],
                        }
                    ]
                },
            )
            with self.assertRaisesRegex(ValueError, "length mismatch"):
                load_scenarios(main, extra)


class BehaviorGraderTest(unittest.TestCase):
    """Cover the behavior grader's threshold logic and manual fallback."""

    def _assertion(self, **kw: Any) -> dict[str, Any]:
        base: dict[str, Any] = {"type": "behavior", "name": "behavior check"}
        base.update(kw)
        return base

    def test_all_thresholds_satisfied_returns_pass(self) -> None:
        result = evaluate_assertion(
            self._assertion(
                max_tool_calls=10,
                max_duration_seconds=300,
                max_tokens_output=4000,
            ),
            output="(unused)",
            metadata={"tool_calls": 5, "duration_seconds": 120, "tokens_output": 1500},
        )
        self.assertEqual(result["status"], "pass")
        self.assertIn("all behavior thresholds", result["detail"])

    def test_single_violation_returns_fail_with_specifics(self) -> None:
        result = evaluate_assertion(
            self._assertion(max_tool_calls=8),
            output="(unused)",
            metadata={"tool_calls": 12},
        )
        self.assertEqual(result["status"], "fail")
        self.assertIn("max_tool_calls=8", result["detail"])
        self.assertIn("tool_calls=12", result["detail"])

    def test_min_tool_calls_catches_skipped_work(self) -> None:
        result = evaluate_assertion(
            self._assertion(min_tool_calls=1),
            output="(unused)",
            metadata={"tool_calls": 0},
        )
        self.assertEqual(result["status"], "fail")

    def test_missing_metric_returns_manual(self) -> None:
        result = evaluate_assertion(
            self._assertion(max_tool_calls=8),
            output="(unused)",
            metadata={},  # runner emitted nothing
        )
        self.assertEqual(result["status"], "manual")
        self.assertIn("tool_calls", result["detail"])

    def test_partial_metadata_lists_only_missing_metrics(self) -> None:
        result = evaluate_assertion(
            self._assertion(max_tool_calls=8, max_tokens_output=4000),
            output="(unused)",
            metadata={"tool_calls": 5},  # tokens_output absent
        )
        self.assertEqual(result["status"], "manual")
        self.assertIn("tokens_output", result["detail"])
        self.assertNotIn("tool_calls'", result["detail"])  # the present one is not listed as missing

    def test_no_thresholds_configured_is_fail(self) -> None:
        result = evaluate_assertion(
            self._assertion(),
            output="(unused)",
            metadata={"tool_calls": 5},
        )
        self.assertEqual(result["status"], "fail")
        self.assertIn("at least one threshold", result["detail"])


class LlmJudgeGraderTest(unittest.TestCase):
    """Cover the llm_judge grader: skipped-by-default, pass/fail extraction, cache hits, errors."""

    def _assertion(self, **kw: Any) -> dict[str, Any]:
        base: dict[str, Any] = {
            "type": "llm_judge",
            "name": "judge check",
            "rubric": "Does the output mention 'hello'? Reply PASS or FAIL with one short reason.",
        }
        base.update(kw)
        return base

    def test_disabled_returns_skipped(self) -> None:
        result = evaluate_assertion(
            self._assertion(),
            output="(any)",
            metadata={},
            enable_llm_judge=False,
        )
        self.assertEqual(result["status"], "skipped")
        self.assertIn("llm-judge not enabled", result["detail"])

    def test_pass_keyword_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = evaluate_assertion(
                self._assertion(),
                output="hello world",
                metadata={},
                enable_llm_judge=True,
                llm_judge_cache_dir=Path(tmp),
                llm_judge_call=lambda model, rubric, output: "PASS: the output greets the world",
            )
            self.assertEqual(result["status"], "pass")
            self.assertIn("PASS", result["detail"])

    def test_fail_keyword_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = evaluate_assertion(
                self._assertion(),
                output="no greeting",
                metadata={},
                enable_llm_judge=True,
                llm_judge_cache_dir=Path(tmp),
                llm_judge_call=lambda model, rubric, output: "FAIL: no 'hello' anywhere",
            )
            self.assertEqual(result["status"], "fail")

    def test_ambiguous_response_returns_manual(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = evaluate_assertion(
                self._assertion(),
                output="x",
                metadata={},
                enable_llm_judge=True,
                llm_judge_cache_dir=Path(tmp),
                llm_judge_call=lambda model, rubric, output: "I am unsure how to judge this.",
            )
            self.assertEqual(result["status"], "manual")
            self.assertIn("ambiguous", result["detail"])

    def test_cache_hit_avoids_second_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            call_count = {"n": 0}

            def counting_call(model: str, rubric: str, output: str) -> str:
                call_count["n"] += 1
                return "PASS: counted"

            assertion = self._assertion()
            first = evaluate_assertion(
                assertion, "same output", {},
                enable_llm_judge=True,
                llm_judge_cache_dir=Path(tmp),
                llm_judge_call=counting_call,
            )
            second = evaluate_assertion(
                assertion, "same output", {},
                enable_llm_judge=True,
                llm_judge_cache_dir=Path(tmp),
                llm_judge_call=counting_call,
            )
            self.assertEqual(first["status"], "pass")
            self.assertEqual(second["status"], "pass")
            self.assertEqual(call_count["n"], 1, "second call should hit cache, not invoke LLM")
            self.assertIn("cache hit", second["detail"])

    def test_judge_call_exception_returns_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            def raising_call(*_args: Any, **_kw: Any) -> str:
                raise RuntimeError("simulated 429 rate limit")
            result = evaluate_assertion(
                self._assertion(),
                output="x",
                metadata={},
                enable_llm_judge=True,
                llm_judge_cache_dir=Path(tmp),
                llm_judge_call=raising_call,
            )
            self.assertEqual(result["status"], "fail")
            self.assertIn("429", result["detail"])

    def test_missing_rubric_is_fail(self) -> None:
        assertion = {"type": "llm_judge", "name": "no-rubric"}  # rubric absent
        result = evaluate_assertion(
            assertion, "x", {},
            enable_llm_judge=True,
            llm_judge_call=lambda *_a, **_k: "PASS",  # should never run
        )
        self.assertEqual(result["status"], "fail")
        self.assertIn("rubric", result["detail"])

    def test_unknown_backend_is_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = evaluate_assertion(
                self._assertion(),
                output="x",
                metadata={},
                enable_llm_judge=True,
                llm_judge_cache_dir=Path(tmp),
                llm_judge_backend="not-a-real-backend",
                # No llm_judge_call → the backend dispatch must run
            )
            self.assertEqual(result["status"], "fail")
            self.assertIn("unknown llm_judge_backend", result["detail"])

    def test_codex_backend_dispatch_routes_to_subprocess_caller(self) -> None:
        # When backend=codex, the dispatch should route to _call_codex_judge.
        # We monkey-patch that function so the test does NOT actually shell
        # out to codex (we want unit-level isolation, not an integration
        # test of the binary).
        from evals import run_skill_evals as runner_mod

        with tempfile.TemporaryDirectory() as tmp:
            original = runner_mod._call_codex_judge
            try:
                runner_mod._call_codex_judge = lambda model, rubric, output: "PASS: codex-mock"
                result = evaluate_assertion(
                    self._assertion(),
                    output="x",
                    metadata={},
                    enable_llm_judge=True,
                    llm_judge_cache_dir=Path(tmp),
                    llm_judge_backend="codex",
                    # NOT passing llm_judge_call — let dispatch pick the codex caller.
                )
            finally:
                runner_mod._call_codex_judge = original
            self.assertEqual(result["status"], "pass")
            self.assertIn("codex-mock", result["detail"])

    def test_codex_backend_propagates_subprocess_error(self) -> None:
        from evals import run_skill_evals as runner_mod

        def boom(model: str, rubric: str, output: str) -> str:
            raise RuntimeError("codex exec returned 127: command not found")

        with tempfile.TemporaryDirectory() as tmp:
            original = runner_mod._call_codex_judge
            try:
                runner_mod._call_codex_judge = boom
                result = evaluate_assertion(
                    self._assertion(),
                    output="x",
                    metadata={},
                    enable_llm_judge=True,
                    llm_judge_cache_dir=Path(tmp),
                    llm_judge_backend="codex",
                )
            finally:
                runner_mod._call_codex_judge = original
        self.assertEqual(result["status"], "fail")
        self.assertIn("127", result["detail"])

    def test_backend_specific_cache_key_does_not_collide(self) -> None:
        # Same model name + rubric + output, but different backend. Cache
        # entries must NOT collide — a Haiku response should not be served
        # to an openai-compat caller and vice versa.
        with tempfile.TemporaryDirectory() as tmp:
            call_log: list[str] = []

            def anthropic_like(model: str, rubric: str, output: str) -> str:
                call_log.append("anthropic")
                return "PASS: anthropic"

            def openai_like(model: str, rubric: str, output: str) -> str:
                call_log.append("openai-compat")
                return "FAIL: openai-compat"

            r1 = evaluate_assertion(
                self._assertion(model="shared"),
                output="same",
                metadata={},
                enable_llm_judge=True,
                llm_judge_cache_dir=Path(tmp),
                llm_judge_backend="anthropic",
                llm_judge_call=anthropic_like,
            )
            r2 = evaluate_assertion(
                self._assertion(model="shared"),
                output="same",
                metadata={},
                enable_llm_judge=True,
                llm_judge_cache_dir=Path(tmp),
                llm_judge_backend="openai-compat",
                llm_judge_base_url="http://localhost:8000/v1",
                llm_judge_call=openai_like,
            )
            self.assertEqual(r1["status"], "pass")
            self.assertEqual(r2["status"], "fail")
            self.assertEqual(call_log, ["anthropic", "openai-compat"])  # both ran, no collision

    def test_openai_compat_cache_key_includes_base_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            call_log: list[str] = []

            def first_server(model: str, rubric: str, output: str) -> str:
                call_log.append("server-a")
                return "PASS: server-a"

            def second_server(model: str, rubric: str, output: str) -> str:
                call_log.append("server-b")
                return "FAIL: server-b"

            assertion = self._assertion(model="shared")
            r1 = evaluate_assertion(
                assertion,
                output="same",
                metadata={},
                enable_llm_judge=True,
                llm_judge_cache_dir=Path(tmp),
                llm_judge_backend="openai-compat",
                llm_judge_base_url="http://localhost:8000/v1",
                llm_judge_call=first_server,
            )
            r2 = evaluate_assertion(
                assertion,
                output="same",
                metadata={},
                enable_llm_judge=True,
                llm_judge_cache_dir=Path(tmp),
                llm_judge_backend="openai-compat",
                llm_judge_base_url="http://localhost:9000/v1",
                llm_judge_call=second_server,
            )
            self.assertEqual(r1["status"], "pass")
            self.assertEqual(r2["status"], "fail")
            self.assertEqual(call_log, ["server-a", "server-b"])


if __name__ == "__main__":
    unittest.main()
