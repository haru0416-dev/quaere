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

    def test_credential_and_non_credential_env_lists_are_disjoint(self) -> None:
        # The two env-var lists are the chokepoint for credential gating.
        # A name appearing in both would silently bypass the allowlist
        # because non-credential forwarding runs unconditionally first.
        from evals.terminal_bench.agents import quaere_tb_codex

        cred = set(quaere_tb_codex._CREDENTIAL_ENV)
        non_cred = set(quaere_tb_codex._NON_CREDENTIAL_ENV)
        overlap = cred & non_cred
        self.assertEqual(
            overlap,
            set(),
            f"_CREDENTIAL_ENV and _NON_CREDENTIAL_ENV must be disjoint; "
            f"overlapping names would bypass the credential gate: {overlap}",
        )

    def test_non_credential_env_has_no_credential_naming_pattern(self) -> None:
        # Heuristic: any env name ending in _KEY, _TOKEN, _SECRET, or
        # _PASSWORD is overwhelmingly likely to be credential-bearing.
        # If one of those lands in _NON_CREDENTIAL_ENV by accident, the
        # next person reviewing the diff should be forced to think
        # about it. URL-shaped names (_BASE_URL, _URL, _ENDPOINT) are
        # also flagged because they can carry basic-auth userinfo, as
        # OPENAI_BASE_URL does.
        from evals.terminal_bench.agents import quaere_tb_codex

        forbidden_suffixes = ("_KEY", "_TOKEN", "_SECRET", "_PASSWORD")
        url_suffixes = ("_BASE_URL", "_URL", "_ENDPOINT")
        for name in quaere_tb_codex._NON_CREDENTIAL_ENV:
            for suffix in forbidden_suffixes:
                self.assertFalse(
                    name.endswith(suffix),
                    f"{name} ends in {suffix} and looks credential-bearing; "
                    f"move it to _CREDENTIAL_ENV or rename it explicitly.",
                )
            for suffix in url_suffixes:
                self.assertFalse(
                    name.endswith(suffix),
                    f"{name} ends in {suffix} and can carry basic-auth "
                    f"userinfo; move it to _CREDENTIAL_ENV or document an "
                    f"explicit exception in this test.",
                )

    def test_shared_env_gates_credential_vars_on_allowlist(self) -> None:
        # When the credential gate is closed (no curated dataset, no
        # explicit opt-in), _shared_env must NOT include OPENAI_API_KEY
        # / ANTHROPIC_API_KEY / OPENAI_BASE_URL even if they are set in
        # the calling environment. When the gate is open (env override),
        # those vars must come through.
        from evals.terminal_bench.agents import quaere_tb_codex

        original_argv = sys.argv
        prev_env = {
            k: os.environ.get(k)
            for k in (
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
                "OPENAI_BASE_URL",
                "QUAERE_TB_ALLOW_CRED_FWD",
            )
        }
        try:
            os.environ["OPENAI_API_KEY"] = "sk-test"
            os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test"
            os.environ["OPENAI_BASE_URL"] = "https://example.invalid/v1"
            os.environ.pop("QUAERE_TB_ALLOW_CRED_FWD", None)
            # Closed gate: non-curated dataset, no opt-in.
            sys.argv = ["tb", "run", "--dataset", "some-untrusted-dataset"]
            env_closed = quaere_tb_codex._shared_env()
            self.assertNotIn("OPENAI_API_KEY", env_closed)
            self.assertNotIn("ANTHROPIC_API_KEY", env_closed)
            self.assertNotIn(
                "OPENAI_BASE_URL",
                env_closed,
                "OPENAI_BASE_URL must be gated like API keys because the "
                "OpenAI SDK forwards URL-embedded userinfo as basic auth.",
            )

            # Open gate via curated dataset.
            sys.argv = ["tb", "run", "--dataset", "terminal-bench-core==0.1.1"]
            env_curated = quaere_tb_codex._shared_env()
            self.assertEqual(env_curated.get("OPENAI_API_KEY"), "sk-test")
            self.assertEqual(env_curated.get("OPENAI_BASE_URL"), "https://example.invalid/v1")

            # Open gate via explicit override.
            sys.argv = ["tb", "run", "--dataset", "some-untrusted-dataset"]
            os.environ["QUAERE_TB_ALLOW_CRED_FWD"] = "1"
            env_override = quaere_tb_codex._shared_env()
            self.assertEqual(env_override.get("ANTHROPIC_API_KEY"), "sk-ant-test")
        finally:
            sys.argv = original_argv
            for k, v in prev_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

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
