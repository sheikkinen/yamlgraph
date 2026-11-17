# Feature Request: FR-1169 Haiku 5.5 replaces Haiku 4.5 as the Anthropic default and in live graphs

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Requested:** 2026-11-17
**First consumer / first event:** game-engine (brief 487). Its operator asked on
2026-11-17 that Haiku 4.5 be upgraded to 5.5 wherever a graph still picks it.
The first event is the next `yamlgraph graph run` with `PROVIDER=anthropic` and
no `ANTHROPIC_MODEL`: today it logs `Creating LLM: anthropic/claude-haiku-4-5`;
after this FR it logs `anthropic/claude-haiku-5-5`.
**Research:** in-body record, [Alternatives](#alternatives) (FR-889 style).
**Prior art:** [FR-1162](FR-1162-adapter-model-pin-gpt61sol.md) moved the
Copilot adapter pins to a served model and kept historic records unchanged;
this FR does the same for the Anthropic default and the example graphs, and
touches no adapter. [FR-1146](FR-1146-anthropic-temperature-deprecated.md) and
FR-1154 decide when temperature is sent; this FR leaves that list as it is
(see Problem). [FR-931](FR-931-judge-review-model-pin-gpt56sol.md): pin-move
witness design, reused here.

## Summary

Change `DEFAULT_MODELS["anthropic"]` in `yamlgraph/config.py` from
`claude-haiku-4-5` to `claude-haiku-5-5`, and replace `claude-haiku-4-5` with
`claude-haiku-5-5` in every graph, prompt, script default, run command and
setup document that picks a model to run. Records stay unchanged.

## Value Statement

A run with no model set uses the current Haiku, which costs a tenth of Haiku
4.5 ($0.10 / $0.50 per MTok against $1 / $5).

## Problem

- `yamlgraph/config.py:67` defaults Anthropic runs to `claude-haiku-4-5`, the
  previous Haiku. README, `.env.sample` and ARCHITECTURE.md repeat it.
- 13 example and enforcement graphs or prompts pin `model: claude-haiku-4-5`
  (beautify, book_translator, codegen, cost-router, storyboard, five demos,
  `graphs/fr_triage`, `graphs/enforcement/changelog-req-check.yaml`), and
  script defaults (`scripts/req_audit.sh`, `scripts/diary_census.sh`,
  `examples/shared/vision_tool.py`, the plot_modeller spikes, corpus_census
  tools) fall back to it.
- Haiku 5.5's request surface (claude-api reference, cached 2026-11-03):
  non-default `temperature` returns 400, and `thinking.budget_tokens` returns
  400. `llm_factory` already omits temperature for any Anthropic id outside
  `ANTHROPIC_SAMPLING_MODEL_PREFIXES` (FR-1146), so graphs that set
  temperature keep working. None of the graphs moved here sets
  `thinking_budget`. The sampling list keeps `claude-haiku-4-5` (still true)
  and does not gain `claude-haiku-5-5`.

## Ideal Result

A run without `ANTHROPIC_MODEL` uses `claude-haiku-5-5`, and no live graph,
prompt, script default or setup document picks `claude-haiku-4-5`.

## Proposed Solution

1. `yamlgraph/config.py`: default `claude-haiku-5-5`.
2. Live files: replace the id in graphs, prompts, script defaults, run
   commands in READMEs and docstrings, `.env.sample`, README, ARCHITECTURE.md's
   provider snippet, `reference/` guides, and the cost notes that price Haiku
   (re-priced at $0.10 / $0.50 per MTok, or the line marked with its date).
3. Tests that assert those files' values (`test_req_audit_runner`,
   `test_fr1126_ramp_rtm_showcase`, and any other the suite names).

Out of scope, unchanged: `demo-output.log`, `proofs/`, `run-evidence.txt`,
`manifest.json`, `gate1-result.md`, outsider-view fixtures, plan and paper-test
documents under `examples/*/docs/`, `docs/`, `feature-requests/`, `changelog/`
and `scripts/probe_fr1164_truncation.py` (a probe record), and test fixtures
that use the id only as an arbitrary string or as a fact about Haiku 4.5
(sampling list, FR-1148 thinking-off payloads).

## Alternatives

| Alternative | Disposition |
|---|---|
| Change only `config.py` | Rejected: pinned graphs and script defaults keep Haiku 4.5. |
| Replace every occurrence, records included | Rejected: a record says what ran then. |
| Add `claude-haiku-5-5` to the sampling list | Rejected: Haiku 5.5 rejects non-default temperature. |
| Remove the explicit `model:` pins so graphs follow the default | Rejected: changes graph meaning beyond the model move. |

## Acceptance Criteria

- [ ] AC-01: With `ANTHROPIC_MODEL` unset, `DEFAULT_MODELS["anthropic"]` is
  `claude-haiku-5-5` (witness RED before the change).
- [ ] AC-02: No graph or prompt YAML under `examples/` or `graphs/` names
  `claude-haiku-4-5` (witness RED before the change).
- [ ] AC-03: A live run with `ANTHROPIC_MODEL` unset logs
  `Creating LLM: anthropic/claude-haiku-5-5` and completes.
- [ ] AC-04: The unit suite passes in CI.

## Implementation Status

Not started.
