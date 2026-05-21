# Roadmap

The in-tree eval does not substitute for third-party validation. External benchmarks are tracked in this priority order.

## 1. Terminal-Bench v2

[Terminal-Bench v2](https://www.tbench.ai/) includes the 80-task `terminal-bench-core` v0.1.1 public leaderboard subset, out of 241 tasks in the broader pool.

This is the closest fit for `quaere-execution` and `quaere-grounding`, and it has the highest expected delta. v0.3.0 shipped the adapter at [`evals/terminal_bench/`](../evals/terminal_bench/) with two Codex-CLI-wrapping agents:

- `quaere-tb-codex-baseline`
- `quaere-tb-codex-with-skill`

Smoke, full, and leaderboard phases are documented in the adapter README.

## 2. SWE-bench Verified

[SWE-bench Verified](https://www.swebench.com/) contains 500 human-verified GitHub-issue patches. It is the standard credibility test for coding agents and is non-optional eventually.

The blocker is cost and infrastructure: at least 120 GB storage, 16 GB RAM, 8 CPU, and substantial API budget. Targeted for v1.0.

## 3. SkillsBench

[SkillsBench](https://www.skillsbench.ai/) contains 84 domain-skill tasks across areas such as 3D, robotics, security PCAP, and energy. The submission unit is an agent that uses skills.

Expected delta is lower because domain skills dominate; Quaere's process-correction angle is less visible. Tracked, not committed.

## 4. SWE-Bench Pro

SWE-Bench Pro is a harder successor to Verified. It is considered only after Verified.

## What the roadmap is testing

Quaere's claim is that process-correction skills raise an agent's deliberation quality. Terminal-Bench tests this claim head-on. SWE-bench Verified tests whether the effect carries over to long-form patch generation.

Until those numbers exist, the only published evidence is the in-tree eval result in [`docs/evaluation.md`](evaluation.md).
