# Quaere skill evaluation harness

This directory contains the in-tree evaluation suite that measures the effect of each Quaere skill on a coding agent. The headline number lives in the [root README](../README.md#why-quaere); this document describes how to run the suite, what each assertion means, and how the `llm_judge` backends behave.

The runner is `run_skill_evals.py`. The canonical scenarios are in `scenarios.json` (18 prompts, seven of which use workspace fixtures under [`../eval-fixtures/`](../eval-fixtures/)). The runner copies each fixture into an isolated directory per run so concurrent evaluations do not interfere.

## Running the suite

```bash
python evals/run_skill_evals.py \
  --runner 'codex=codex exec - < $prompt_file' \
  --scenario sdk-version-grounding \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

`--output-dir` should be absolute so the runner can read `$prompt_file` from inside the workspace `cwd`. The runner writes isolated prompts, stdout/stderr, metadata, and per-assertion grades under `eval-results/<timestamp>/`. `--mode both` runs a baseline prompt without the skill and a with-skill prompt that injects the relevant `SKILL.md`.

### Runner command templates

Templates are shell commands. They can print the agent response to stdout or redirect it to `$output_file`. Available substitutions:

- `$prompt_file` — generated prompt file
- `$output_file` — stdout capture path
- `$workspace` — isolated working directory
- `$run_dir` — result directory
- `$scenario_id`, `$skill`, `$mode` — run metadata

## Assertions

Scenarios carry deterministic `assertions` for CI-friendly checks, alongside a manual rubric in `expected`:

| assertion type | purpose |
| --- | --- |
| `contains` / `contains_any` / `not_contains` | literal substring presence or absence |
| `regex` | one regex match anywhere in output |
| `ordered_sections` | a list of regex patterns must match in that order |
| `min_section_count` | a regex must match at least *N* times |
| `requires_pair` | if `if_contains` matches, then `must_also_contain` (or, optionally, `skip_when`) must also match |
| `not_in_baseline` | a pattern that *only* the with-skill mode should match (signal isolation) |
| `exit_code` | the runner exit code must equal the given integer |
| `behavior` | per-run resource thresholds against runtime metadata (`max_tool_calls` / `min_tool_calls` / `max_duration_seconds` / `max_tokens_output` / `max_tokens_input`); records `status: "manual"` when the runner did not emit the relevant metric |
| `llm_judge` | LLM grades the output against a free-form `rubric`; opt-in via `--enable-llm-judge`. Returns `pass` / `fail` / `manual` based on the judge's response and is skipped (`status: "skipped"`) when the flag is off |

The `skip_when` clause on `requires_pair` lets an assertion treat a labeled skip branch (e.g. `Final gate: skipped because <reason>`) as vacuously satisfied. Anchor `skip_when` tightly — the bare token `(?i)skipped` would silently flip fails to passes whenever the word appears anywhere in output.

## llm_judge backends

`llm_judge` is default-off so per-PR CI cost stays at zero. All three backends share the same grading contract; the cache key includes the backend so switching between them does not silently reuse responses from the other one. Responses are cached at `.llm_judge_cache/<sha>.json` keyed by `sha256(backend:model + rubric + output)`, so re-running with unchanged outputs is free.

### Anthropic SDK (default)

```bash
export ANTHROPIC_API_KEY=...
pip install anthropic
python evals/run_skill_evals.py \
  --runner 'codex=codex exec - < $prompt_file' \
  --enable-llm-judge \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

Default model is `claude-haiku-4-5-20251001`; per-call cost is approximately ¥0.4 (input $1 / MTok + output $5 / MTok, 2,200 input / 100 output tokens per judgement). A full 14-scenario sweep with ~3 judge assertions per scenario lands around ¥34.

### openai-compat (Ollama / vLLM / LM Studio / LocalAI / LiteLLM)

Any OpenAI-compatible endpoint works. Two extra flags:

```bash
pip install openai
python evals/run_skill_evals.py \
  --runner 'codex=codex exec - < $prompt_file' \
  --enable-llm-judge \
  --llm-judge-backend openai-compat \
  --llm-judge-base-url http://localhost:11434/v1 \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

`--llm-judge-base-url` can also come from `$QUAERE_LLM_JUDGE_BASE_URL`. The `OPENAI_API_KEY` env var is used if set; otherwise a placeholder is sent (most local servers ignore it). Smaller local models (7–13B) tend to be noisy on PASS / FAIL boundary cases; 30B+ class is recommended for stable grading.

### Codex CLI

Reuses the Codex CLI subprocess for grading. No extra Python SDK; the judge picks up whatever endpoint and auth Codex is already configured for (so the judge sees the same model / `OPENAI_BASE_URL` / OS auth that the agent under test does):

```bash
python evals/run_skill_evals.py \
  --runner 'codex=codex exec - < $prompt_file' \
  --enable-llm-judge \
  --llm-judge-backend codex \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

The codex backend invokes `codex exec --output-last-message <tmpfile> -`, reads the final message, and discards the rest. Per-call cost matches whatever Codex itself bills; pass `--llm-judge-model <id>` to pin a specific model.

## Locale alternates

The public surface of the project is English: skill bodies, scenario prompts, and assertion patterns in `scenarios.json` are English-only. Locale-specific token alternates (Japanese, paraphrases, etc.) live in `scenarios.ja.json` and are opt-in via `--scenarios-extra`:

```bash
python evals/run_skill_evals.py \
  --runner 'codex=codex exec - < $prompt_file' \
  --scenarios-extra evals/scenarios.ja.json \
  --mode both \
  --output-dir "$(pwd)/eval-results/$(date -u +%Y%m%dT%H%M%SZ)"
```

At load time the extras file is merged into the main scenarios by matching `(scenario id, assertion name)`. Regex / string fields get `|`-alternation appended; `ordered_sections.patterns` and `not_in_baseline.patterns` get per-position alternation; `contains_any.texts` get array concatenation. Unknown ids or names error out so stale extras files cannot silently drop alternates.

Real-LLM eval runs are gated behind a manual workflow trigger and are not required to pass on every PR.

## External benchmarks

For Terminal-Bench v2 integration (the closest external fit for `quaere-execution` and `quaere-grounding`), see [`terminal_bench/README.md`](terminal_bench/README.md). It ships two Codex-CLI-wrapping agents (`quaere-tb-codex-baseline` / `quaere-tb-codex-with-skill`) and a manual-trigger CI workflow with smoke / full / leaderboard phases.
