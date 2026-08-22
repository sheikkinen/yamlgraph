# Feature Request: Research-Agent Demo Rot — Unresolved Variable Bindings and Fabrication From Empty Findings

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced 2026-08-07 — RED 86457da5, GREEN via author.sh; all ACs met, see Implementation Status
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

## Evidence (admissible, R-1)

Embedded excerpts from the 2026-08-06 runs; this section is the committed witness — no session-local file is required to understand the defect.

**Marker run** (query `"XYZZY-MARKER how does purple frobnication work"`):

```
marker-run intent topic: "Structured research intent extraction"
"XYZZY" appears anywhere in final graph state: False
```

The extracted intent is a paraphrase of the extract_intent system prompt — the query never reached the model. The first (pre-marker) run on an agent/tool question invented the topic `"Researching security vulnerabilities in OAuth2 implementations"` with expected artifacts `auth-config.js`, `passport-strategy.ts` — none of which exist in this repository.

**Post-binding-fix run** (query on agent/tool integration, both agent loops capped):

```
2026-08-06 22:11:19 [WARNING] yamlgraph.tools.agent: Agent hit max iterations (5)    # plan_research
2026-08-06 22:11:36 [WARNING] yamlgraph.tools.agent: Agent hit max iterations (10)   # execute_research
findings repr: ''
validation: {"questions_answered": [], "gaps": ["How are agent node types and tools
  (shell, python, and FR-768 manifests) declared in YAML?", "How does the parse_tools
  function process these YAML declarations?", "How are the parsed tools utilized and
  executed within the agent loop?"], "confidence": "low", "notes": "No research
  findings were provided in the input context to validate against the original intent."}
report head: '# Architectural Report: Agent Node and Tool System Integration\n\nThis
  report details how **agent node types** and **tool systems** (including shell too'
```

Empty `findings`, `confidence: low` with every key question listed as a gap — and a fully-structured multi-section report synthesized anyway (its YAML "examples" cite `spec_version: "FR-768"` and `config/agents/analyst_agent.yaml` shapes that exist nowhere in this codebase).

The binding defect is also visible statically in the committed graph: bare `{query}`/`{scope}` at `HEAD:examples/demos/research-agent/graph.yaml` lines 42, 53, 65, 82, against the `{state.…}`-only resolver contract (`yamlgraph/utils/expressions.py` `resolve_template`, `reference/graph-yaml.md`).

## Ideal Result

`yamlgraph graph run examples/demos/research-agent/graph.yaml --var query="..."` either produces a report grounded in actual tool findings, or fails loudly naming the empty stage — and the committed demo witness proves the grounded path with a query-specific marker visible in the output. The demo is trustworthy enough to be published as the FR-777 toolbelt research tool without further hardening.

## Proposed Solution

### 1. Commit the binding fix (already drafted via author.sh, 2026-08-06)

`{query}` → `{state.query}`, `{scope}` → `{state.scope}` in the four affected node variable bindings, plus `state: {query: str, scope: str}` declarations (lint E007 otherwise). Adapter's marker smoke already verified the query reaches the prompt path.

### 2. Gate synthesis on validation (graph-level, no new node types)

**Terminal contract (R-2, frozen):** when `findings` is empty and `validation.confidence` is `low`, the graph terminates after `validate_findings`, preserves the validation verdict in state, and does not produce `report`. `synthesize_report` runs only for non-empty findings with non-low validation confidence. Enforced by graph topology (router/condition edge after `validate_findings`), not prompt wording. Process failure is explicitly NOT the chosen behavior — the honest terminal validation state is the output.

### 3. Regenerate the demo witness

New `demo-output.log` from a live run whose extracted intent visibly echoes the query topic (the anti-XYZZY check: the topic words must appear). Raise `plan_research`/`execute_research` iteration caps only if the grounded path requires it — cap increases are a measured decision, not a reflex.

### 4. Condemning tests (RED first)

- Test: graph config binds only `{state.…}` templates in `variables:` (mechanical rot guard — greps all committed demo graphs, not just this one; `partial_remediation` guard).
- Test: the graph's edge structure routes empty-findings/low-confidence away from `synthesize_report`.

**Sequence (R-3, frozen):** RED tests are committed BEFORE any governed graph mutation is applied to the working tree destined for commit; graph edits are then generated through `scripts/author.sh` with `tmp/draft-authoring-report.md` recording lint, validate, and smoke evidence. The 2026-08-06 uncommitted draft fix is diagnostic evidence only — it is not implementation proof and will be re-derived through the authoring route after RED.

**Traceability (R-4, frozen):** every new or changed test carries an exact `@pytest.mark.req("REQ-YG-XXX")` marker and `python scripts/req_coverage.py --strict` passes. No existing REQ covers demo variable-binding hygiene and empty-findings routing — enforcement adds a focused capability/REQ pair (CAP-221) rather than leaving unmarked tests.

## Acceptance Criteria (revised per judgement 2026-08-07)

- [x] AC-01: The FR contains committed admissible evidence showing the binding failure and empty-findings fabrication chain; no session-local `tmp/` or `logs/` file is required to understand the defect.
- [x] AC-02: RED test proves the committed research-agent graph contains bare non-`{state…}` node-variable bindings; GREEN changes the four affected bindings to `{state.query}` / `{state.scope}` and declares `state: {query: str, scope: str}`.
- [x] AC-03: A committed guard test asserts every committed demo graph uses only `{state…}` placeholders in node `variables:` mappings; if it finds violations outside research-agent, enforcement stops for split or re-judgement.
- [x] AC-04: A committed graph-structure or execution test proves an empty `findings` value with `validation.confidence: low` terminates after `validate_findings`, preserves the validation verdict, and never executes or produces `synthesize_report` / `report`.
- [x] AC-05: A committed positive-path test or demo witness proves non-empty findings with acceptable validation confidence can still reach `synthesize_report`.
- [x] AC-06: `examples/demos/research-agent/demo-output.log` is regenerated from a successful grounded run whose output visibly echoes the query topic, contains no fatal markers, and is committed with the graph change.
- [x] AC-07: Governed graph edits are authored through `scripts/author.sh`; `tmp/draft-authoring-report.md` records lint, validate, and smoke evidence for the changed graph.
- [x] AC-08: No `yamlgraph/` production files change; if a production change is genuinely required, enforcement stops and a separate bug FR is filed.
- [x] AC-09: Every new or changed test has an exact `@pytest.mark.req(...)` marker, the capability registry is updated if needed, and `python scripts/req_coverage.py --strict` passes.
- [x] AC-10: Changelog fragment, FR implementation-status update, and diary reflection are included.

## Alternatives Considered

- **Make `resolve_template` resolve bare `{var}` from state:** rejected — normalizes at the wrong boundary; `{state.…}` is the documented contract (`reference/graph-yaml.md` throughout), and widening the resolver grandfathers ambiguity between literals and references into every graph.
- **Lint rule (E-class) for bare placeholders in `variables:`:** stronger than a test sweep; considered in-scope as a stretch if the linter already has the AST hooks, otherwise a follow-up — the test sweep (AC-2) provides the blocking guard either way.
- **Prompt-level instruction "do not fabricate without findings":** rejected — `two_strike_split`: mechanizable levels defeat instruction text; the gate belongs in the graph's edge structure, not in prose.

## Related

- feature-requests/FR-779-research-agent-demo-rot.judgement.md — verdict APPROVED WITH REVISIONS (2026-08-07); scope table D-1..D-6 and conditions C-1..C-6 govern enforcement
- feature-requests/FR-215-research-agent-demo.md — created the demo
- feature-requests/FR-777-shared-shell-toolbelt-manifests.md — assumes this graph becomes a toolbelt tool
- yamlgraph/utils/expressions.py `resolve_template` — the boundary that defines `{state.…}`-only
- docs/diary/diary-2026-08-06-the-provider-was-innocent.md — the witness-rot seed this FR partially answers

## Judgement (2026-08-07)

**Verdict:** APPROVED WITH REVISIONS — see feature-requests/FR-779-research-agent-demo-rot.judgement.md. R-1 (admissible evidence), R-2 (single terminal empty-findings contract), R-3 (RED-before-authoring sequence), R-4 (req traceability) folded above. Conditions C-1..C-6 are GATE.

## Implementation Status (2026-08-07)

**Status: Enforced.**

- **RED** commit `86457da5` — `tests/unit/test_fr779_research_agent_demo.py` (8 tests, `REQ-YG-581`), CAP-221 registered; verified 7 failed / 1 passed against the committed graph before any graph mutation (R-3 sequence honored).
- **GREEN** — graph re-derived via `scripts/author.sh tmp/fr779-green-brief.md` (C-6); `tmp/draft-authoring-report.md` records lint (0 errors, 1 pre-existing W026 warning), validate (5 nodes, 7 edges), suite 8/8, and a live smoke where the empty-findings/low-confidence route selected `END`, preserved `validation`, and produced no `report` — the terminal contract exercised for real, not just structurally.
- **Diff is exactly frozen scope**: 4 bindings → `{state.query}`/`{state.scope}`, `state: {query: str, scope: str}` declared, unconditional `validate_findings → synthesize_report` replaced by conditional gate (`validation.confidence == 'low' or findings == ''` → END; negation → synthesize_report). No prompt, tool, or `yamlgraph/` changes (C-5, AC-08).
- **C-4 sweep result**: repo-wide demo sweep found violations only in research-agent. `security-cve-ignore` embeds literal GitHub Actions `${{ github.* }}` template text inside a variable *value*; the sweep regex anchors to whole-string bare placeholders (`^\{(?!state\.)[^{}]+\}$`), correctly excluding embedded literals. No stop triggered.
- **Witness (AC-06)**: `demo-output.log` regenerated from a grounded run (`PROVIDER=google`, query "Which LLM providers does the create_llm factory support?"); output cites `yamlgraph/utils/llm_factory.py` with line numbers and echoes the topic; route log shows `validate_findings → synthesize_report` via the positive condition (AC-05 witnessed live); validated against `scripts/demo_log_semantics.sh` (no fatal markers, success markers present).
- **Deviation**: none from judged scope. The lint-rule stretch (E-class bare-placeholder rule) was not taken — the AC-03 sweep test provides the blocking guard as judged.
- Follow-up: FR-780 (toolbelt conversion) filed and sequenced after this FR.

**Brief provenance (FR-852):** authoring brief committed at
`feature-requests/authoring-briefs/fr-779-green-brief.md`
(formerly `tmp/fr779-green-brief.md`).
