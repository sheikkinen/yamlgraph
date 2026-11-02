# Feature Request: Decision-node primitive with calibration audit and hello demo

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Requested:** 2026-11-02
**First consumer / first event:** `examples/demos/calibration-audit`, run by
the operator against the mock decision provider at enforcement time — the
gate every real decision provider must pass before any graph branches on
its confidence. First production-shaped event: a `smart-if` routing
decision once a real provider key is configured.
**Research:** [FR-1155.research.md](FR-1155.research.md)

## Summary

Add a `decision` node type to yamlgraph: a node that asks atomic typed
questions (choice from a list, rubric score, 0–1 truth) against a state
blob through a provider-agnostic decision client, and returns typed
answers with probabilities and confidence as first-class state values.
Ship with (1) a mock decision provider for network-free tests, (2) a
`calibration-audit` demo that empirically verifies a provider's
confidence before any graph is allowed to trust it, and (3) a
hello-grade `smart-if` demo (decide → branch → act). Interface target is
the public System One contract (`state` + named questions), exercisable
today via the vendor's LLM-backed `system-one-adapter` package — native
Jev access is not required by anything in this FR.

## Value Statement

Graph authors get decision-shaped nodes (routers, guards, census map
phases, verdict extraction) expressed as decisions instead of chat
calls, with confidence they can branch on only after our own harness has
proven it calibrated.

## Problem

The examples census (docs/2026-11-02-research-typesafe-system-one-jev.md)
shows decision-shaped nodes throughout the corpus, all paying chat-LLM
call shape: `cost-router` spends a full LLM call to decide routing;
`corpus_census/judge_item` hand-rolls abstain plus a self-reported
integer confidence with no calibration evidence; `hook_classifier`'s
PreToolUse consumer is latency-bounded beyond what chat calls allow. A
public decision-model contract now exists (Choice/Score/Noul questions,
parallel evaluation, probabilities + confidence), with a pip-installable
LLM-backed implementation — but yamlgraph has no node type to express
it, no provider seam to execute it, no typed ingestion for its answers,
and no empirical check of the calibration claim that makes
confidence-branching safe.

## Ideal Result

A graph author declares an atomic decision question in YAML; it executes
against any configured decision provider through one factory seam; the
typed answer, probabilities, and confidence land in state where
conditions branch on them; and the calibration-audit demo stands as the
mandatory first run for any new provider — no graph trusts confidence
the harness has not measured.

## Planned Operations

```yaml
probes:
  - "PyPI metadata for system-one-adapter (license, transitive deps, pins) — decides FR-761 optional extra vs thin internal client"
  - "read typesafe_sdk SystemOneResponse source — decides the Pydantic ingestion mapping for answers/probabilities/confidence"
  - "grep yamlgraph/ node-type registry and executor seams (prompt/tool nodes) — decides where the decision node registers and how sync/async split"
  - "one live Noul question through system-one-adapter with an existing provider key — decides the demo backing works before authoring demos"
  - "read 10 raw adapter responses end-to-end before writing the reliability-table reducer (read_raw_output_first)"
branches:
  - "adapter fails FR-761 governance (license/audit/pins) → implement a thin internal client against the documented public contract instead"
  - "a question type returns no confidence → calibration-audit scopes to the types that do; FR records the exclusion"
  - "harness fails to flag planted miscalibration in the mock provider → fix harness before any real-provider run"
  - "demo graph or prompt artifact needed → scripts/author.sh sole route, never manual (FR-767)"
delegations:
  - "research.sh: 1 run (complete — FR-1155.research.md)"
  - "judge.sh: 1 run, 2 if revisions are disputed"
  - "author.sh: 2 runs (calibration-audit demo, smart-if demo)"
waits:
  - "judge"
  - "FR-761 dependency verdict"
commands:
  - scripts/judge.sh feature-requests/FR-1155-decision-node-calibration-audit.md
  - scripts/author.sh tmp/brief-calibration-audit.md
  - scripts/author.sh tmp/brief-smart-if.md
  - yamlgraph graph lint examples/demos/calibration-audit/graph.yaml
  - yamlgraph graph run examples/demos/smart-if/graph.yaml --full
  - pytest tests/unit/ -q --no-cov -m "not slow" -n auto
  - python scripts/req_coverage.py --strict
```

## Proposed Solution

Three slices, each independently testable:

### 1. Decision provider seam + mock

`create_decision_client()` factory (mirror of `create_llm`, CAP-03
precedent) in `yamlgraph/utils/`; no provider-specific imports outside
it (import-linter contract extended). Two backends:

- `system_one_adapter` — the vendor's public LLM-backed client, added as
  an optional extra (`pip install yamlgraph[decision]`) after FR-761
  governance.
- `mock` — deterministic fixture provider (same pattern as the mock-LLM
  test fixtures) with *configurable planted miscalibration*, so the
  calibration harness can be proven to detect what it exists to detect.

Answers normalize at this boundary into Pydantic models (Commandment 5):
per question, `answer`, `probabilities`, `confidence` — never raw dicts.

### 2. `decision` node type

```yaml
nodes:
  - name: triage
    type: decision
    state_template: "{{ ticket }}"
    questions:
      urgent:
        kind: noul
        instructions: "The ticket is urgent."
      category:
        kind: choice
        options: [billing, bug, feature_request]
        instructions: "Primary category of the ticket."
      severity:
        kind: score
        rubric: "1 = cosmetic, 5 = production outage."
    state_key: triage

edges:
  - from: triage
    condition: "state['triage'].urgent.confidence < 0.8"
    to: human_review
```

One request carries all questions (the contract evaluates them in
parallel and in isolation); choice cardinality is linted against the
255 cap. Sync and async execution paths behave identically (FR-679/
FR-998 precedent). This is a new call shape (`state` + questions), not a
fork of the FR-998 chat structured-output policy — the lint rule that
guards FR-998's single surface is untouched.

### 3. Demos (authored via `scripts/author.sh`, FR-767)

- `examples/demos/calibration-audit` — N labeled fixture items → decision
  node per item → reducer emits a reliability table (confidence buckets
  vs observed accuracy, expected calibration error). Run against the
  mock provider with planted miscalibration, the table must flag it; the
  README records an honest run.
- `examples/demos/smart-if` — the hello: one noul decision →
  conditional edge → two terminal actions. The decision-provider analog
  of `demos/hello`, runnable against the mock provider with no keys.

## Acceptance Criteria

- [ ] `decision` node type registers, lints (unknown `kind`, missing
      `instructions`, choice cardinality > 255 are lint errors), and
      executes sync + async
- [ ] Unit tests run without network against the mock provider; a test
      witnesses a condition branching on `confidence`
      (`@pytest.mark.req("REQ-YG-XXX")`, new REQ in ARCHITECTURE.md,
      `python scripts/req_coverage.py --strict` passes)
- [ ] Decision answers enter state as typed Pydantic values
      (answer/probabilities/confidence); no untyped dicts
- [ ] No provider-specific imports outside the factory module;
      `lint-imports` passes with the extended contract
- [ ] `system-one-adapter` passes FR-761 governance as an optional
      extra, or the FR records the thin-internal-client fallback
      decision with rationale
- [ ] `examples/demos/calibration-audit` lints and smokes; a test
      asserts the reliability table flags the mock's planted
      miscalibration
- [ ] `examples/demos/smart-if` lints and smokes keyless against the
      mock provider; README quickstart included
- [ ] Both demos authored via the sole route — witnessed by
      `tmp/draft-authoring-report.md` artifacts
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

From [FR-1155.research.md](FR-1155.research.md):

| Alternative | Disposition |
|---|---|
| Decision node type + factory seam (os-infra-primitivist, data-process-planner, yamlgraph-native-planner — convergent x3) | **Adopted** — this FR. |
| Subtractionist: standalone `decision-harness` CLI outside yamlgraph | Rejected: decision-shaped nodes already live inside graphs (routers, census maps, guards); a separate tool splits the examples corpus and forfeits conditional-edge branching on confidence, which is the point. The FR-588 precedent cuts the same way — standalone harnesses fighting the framework's own thesis is what got FR-588 rejected. |
| Librarian: "Pydantic AI decision models" (pydantic.dev link) | Dispositioned as unverified: the cited page does not correspond to a known Pydantic AI feature; treated as a search-result conflation of the same System One contract. No committed claim depends on it. |
| Defer everything until native Jev GA | Rejected: the public adapter makes the interface, the node type, and the calibration harness buildable and testable today; deferral only delays the gate we will need on day one of access. |

**Prior-art disposition (FR-737 duty):** FR-588 [REJECTED] surfaced on
the calibration keyword. Its rejection rationale — orchestration
hand-rolled in Python instead of a YAMLGraph example — is affirmed here,
not re-entered: both demos in this FR are graphs run via
`yamlgraph graph run`, and the calibration harness follows FR-589's
rebuilt-as-example doctrine.

## Related

- Research note: `docs/2026-11-02-research-typesafe-system-one-jev.md`
  (vendor claims, examples census, native samples, feasibility)
- Problem brief:
  `feature-requests/research-briefs/fr1155-decision-node-calibration-brief.md`
- FR-998 structured-output policy (surface not forked); FR-761
  dependency governance; FR-767 authoring sole route; CAP-03 provider
  factory precedent
- Public contract: <https://docs.typesafe.ai/introduction>; adapter:
  <https://github.com/typesafe-ai/system-one-adapter-python>
