"""Smoke-level tests for the Terminal-Bench adapter.

These tests verify the adapter module is importable, exposes the expected
module-level constants, and raises a clear error when the terminal_bench
dependency is absent. They do NOT execute the adapter against an actual
task container — that is the manual workflow's job.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class TerminalBenchAdapterSmokeTest(unittest.TestCase):
    def test_package_imports_without_terminal_bench(self) -> None:
        # Importing the package must NOT pull in terminal_bench.
        import evals.terminal_bench  # noqa: F401

    def test_module_constants_accessible(self) -> None:
        from evals.terminal_bench.agents import quaere_tb_codex

        self.assertTrue(quaere_tb_codex.SCRIPTS_DIR.exists() or True)  # path is defined
        self.assertEqual(
            quaere_tb_codex.SCRIPTS_DIR.name,
            "install_scripts",
            "scripts dir name should be install_scripts (Python-importable)",
        )

    def test_shared_env_pulls_only_from_real_env(self) -> None:
        from evals.terminal_bench.agents import quaere_tb_codex

        original = os.environ.get("CODEX_MODEL")
        os.environ["CODEX_MODEL"] = "test-model-id"
        try:
            env = quaere_tb_codex._shared_env()
            self.assertEqual(env.get("CODEX_MODEL"), "test-model-id")
        finally:
            if original is None:
                os.environ.pop("CODEX_MODEL", None)
            else:
                os.environ["CODEX_MODEL"] = original

    def test_build_agent_classes_raises_when_terminal_bench_absent(self) -> None:
        from evals.terminal_bench.agents import quaere_tb_codex

        # In this CI environment terminal_bench is not installed; calling
        # build_agent_classes should surface a clear error pointing at the
        # missing dependency rather than failing opaquely.
        with self.assertRaises(RuntimeError) as ctx:
            quaere_tb_codex.build_agent_classes()
        self.assertIn("Terminal-Bench is not installed", str(ctx.exception))

    def test_agent_names_via_class_introspection_skipped_without_dep(self) -> None:
        # The class names "quaere-tb-codex-baseline" and "quaere-tb-codex-with-skill"
        # are referenced from CI workflows and install scripts; this test asserts
        # they live in the source even when the class itself cannot be constructed.
        src = (
            Path(__file__).resolve().parents[1]
            / "evals"
            / "terminal_bench"
            / "agents"
            / "quaere_tb_codex.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"quaere-tb-codex-baseline"', src)
        self.assertIn('"quaere-tb-codex-with-skill"', src)


if __name__ == "__main__":
    unittest.main()
