# Feature Request: Research-Agent Demo Rot — Unresolved Variable Bindings and Fabrication From Empty Findings

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-07
**First consumer / first event:** anyone running `examples/demos/research-agent` as a research tool — concretely, the FR-777 assumption path (research graph published as a toolbelt tool, consumed by the judge_fr adapter) inherits both defects the moment it is wired up. The first event already happened: a 2026-08-06 research run on "agent/tool integration" returned a wholesale-hallucinated OAuth2 report.

**Prior art:** FR-215 created this demo (2026-04-07 witness, last touch). FR-777 assumed it as the future research toolbelt tool. `plausible_wrong_answer` trap and Commandment 6 ("when a filter yields nothing, raise — never substitute everything") are the doctrine anchors. No prior FR addresses demo variable-binding rot or empty-findings synthesis.

## Summary

Two live defects found by dogfooding the research-agent demo (2026-08-06):

1. **Binding rot (fix drafted, uncommitted):** `graph.yaml` bound node variables as bare `{query}`/`{scope}`, but `resolve_template` (`yamlgraph/utils/expressions.py`) only resolves `{state.…}` paths — the literal string `Research question: {query}` reached the model, which hallucinated an OAuth2 research topic wholesale. Proven with an XYZZY-marker query: the marker never appeared in the extracted intent.
2. **Fabrication from empty findings:** both agent loops hit `max_iterations` without a final answer, `findings` came back empty, `validate_findings` honestly reported `confidence: low` with all questions listed as gaps — and `synthesize_report` fabricated a plausible, fully-structured, entirely invented report anyway. The pipeline's own validation verdict was ignored by its final stage.

## Value Statement

Anyone consuming the research graph gets either a grounded report or an honest failure — never a confident fabrication that costs more to detect than a crash.

## Problem

- Defect 1 is silent: the graph lints clean, runs green, and produces well-shaped output on the wrong topic. Nothing re-runs committed demos, so the binding rotted invisibly since 2026-04-07 (`recent_changes_blindness` in demo form — the witness only fails when someone next touches the demo).
- Defect 2 is the `plausible_wrong_answer` trap made structural: the graph *has* a validation node that correctly detected the empty-findings condition, but its verdict gates nothing. `synthesize_report` runs unconditionally and the LLM fills the vacuum with fiction. Commandment 6 forbids exactly this: "when a filter yields nothing, raise — never substitute everything."
- Evidence: `tmp/research-agent-result.json` (empty `findings`, low-confidence `validation`, fabricated `report`), `tmp/research-agent-tool-report.md` (the fabricated OAuth2-free but ungrounded second report), `logs/research-agent.err` (both loops hitting caps: plan_research 5/5, execute_research 10/10).

## Ideal Result

`yamlgraph graph run examples/demos/research-agent/graph.yaml --var query="..."` either produces a report grounded in actual tool findings, or fails loudly naming the empty stage — and the committed demo witness proves the grounded path with a query-specific marker visible in the output. The demo is trustworthy enough to be published as the FR-777 toolbelt research tool without further hardening.

## Proposed Solution

### 1. Commit the binding fix (already drafted via author.sh, 2026-08-06)

`{query}` → `{state.query}`, `{scope}` → `{state.scope}` in the four affected node variable bindings, plus `state: {query: str, scope: str}` declarations (lint E007 otherwise). Adapter's marker smoke already verified the query reaches the prompt path.

### 2. Gate synthesis on validation (graph-level, no new node types)

Route on the existing validation verdict: `confidence: low` + empty findings must not reach `synthesize_report`. Minimal shape — a router/condition edge after `validate_findings` that ends the graph with the honest validation verdict as the terminal output (or raises via `on_error: fail` semantics), instead of unconditionally synthesizing. Implementation stays in YAML (Logic layer); no `yamlgraph/` changes expected.

### 3. Regenerate the demo witness

New `demo-output.log` from a live run whose extracted intent visibly echoes the query topic (the anti-XYZZY check: the topic words must appear). Raise `plan_research`/`execute_research` iteration caps only if the grounded path requires it — cap increases are a measured decision, not a reflex.

### 4. Condemning tests (RED first)

- Test: graph config binds only `{state.…}` templates in `variables:` (mechanical rot guard — greps all committed demo graphs, not just this one; `partial_remediation` guard).
- Test: the graph's edge structure routes empty-findings/low-confidence away from `synthesize_report`.

## Acceptance Criteria

- [ ] AC-1 RED: failing test proving bare `{var}` bindings exist in research-agent graph (then GREEN via the committed fix).
- [ ] AC-2 Mechanical guard: test asserting no committed demo graph binds bare non-`{state.…}` placeholders in node `variables:` (all demos, one sweep).
- [ ] AC-3 Empty-findings path: low-confidence validation never reaches `synthesize_report`; graph output is the honest verdict or a loud failure.
- [ ] AC-4 Regenerated `demo-output.log` from a successful grounded run; extracted intent echoes the query topic; no fatal markers; demo-gate compliant.
- [ ] AC-5 Graph changes via `scripts/author.sh` route only (FR-767); lint + validate green.
- [ ] AC-6 No `yamlgraph/` production changes; if the fix genuinely requires one, stop and split per doctrine.
- [ ] AC-7 Changelog fragment, FR status fold, diary entry.

## Alternatives Considered

- **Make `resolve_template` resolve bare `{var}` from state:** rejected — normalizes at the wrong boundary; `{state.…}` is the documented contract (`reference/graph-yaml.md` throughout), and widening the resolver grandfathers ambiguity between literals and references into every graph.
- **Lint rule (E-class) for bare placeholders in `variables:`:** stronger than a test sweep; considered in-scope as a stretch if the linter already has the AST hooks, otherwise a follow-up — the test sweep (AC-2) provides the blocking guard either way.
- **Prompt-level instruction "do not fabricate without findings":** rejected — `two_strike_split`: mechanizable levels defeat instruction text; the gate belongs in the graph's edge structure, not in prose.

## Related

- feature-requests/FR-215-research-agent-demo.md — created the demo
- feature-requests/FR-777-shared-shell-toolbelt-manifests.md — assumes this graph becomes a toolbelt tool
- yamlgraph/utils/expressions.py `resolve_template` — the boundary that defines `{state.…}`-only
- tmp/research-agent-result.json, tmp/research-agent-tool-report.md, logs/research-agent.err — evidence artifacts (uncommitted, session-local)
- docs/diary/diary-2026-08-06-the-provider-was-innocent.md — the witness-rot seed this FR partially answers

## Judgement (pending)

**Verdict:** —
