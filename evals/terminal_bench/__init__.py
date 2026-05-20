"""Terminal-Bench v2 adapter for Quaere.

See `evals/terminal_bench/README.md` for usage. The package exposes two
`AbstractInstalledAgent` subclasses — baseline and with-skill — that share
the same Codex CLI installation and differ only in whether the Quaere
skill set is installed into the task container before dispatch.

Importing this package does NOT require terminal_bench to be installed;
class attributes resolve lazily via __getattr__ so packaging tools, IDEs,
and unit tests can introspect the module without the heavy dependency.
"""

from __future__ import annotations

from typing import Any


def __getattr__(name: str) -> Any:
    if name in {"QuaereTbCodexBaseline", "QuaereTbCodexWithSkill", "build_agent_classes"}:
        from evals.terminal_bench.agents import quaere_tb_codex
        return getattr(quaere_tb_codex, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "QuaereTbCodexBaseline",
    "QuaereTbCodexWithSkill",
    "build_agent_classes",
]
