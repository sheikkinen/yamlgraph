# Feature Request: Decision-node primitive with calibration audit and hello demo

**Priority:** MEDIUM
**Type:** Feature
**Status:** Completed 2026-11-02 — judged APPROVED WITH REVISIONS ([judgement](FR-1155-decision-node-calibration-audit.judgement.md)); R-1..R-6 folded; D-1..D-7 enforced (RED a38e7ff2, GREEN d1f11db8); AC-01..AC-14 met
**Requested:** 2026-11-02
**First consumer / first event:** `examples/demos/calibration-audit`, run by
the operator against the mock decision provider at enforcement time. The
audit is the documented operator onboarding step for any real provider:
run it against representative labeled data and record the result before
adopting confidence-based routing (no runtime enforcement is part of this
FR). First production-shaped event: a `smart-if` routing decision once a
real provider key is configured.
**Research:** [FR-1155.research.md](FR-1155.research.md)

## Summary

Add a `decision` node type to yamlgraph: a node that asks atomic typed
questions (choice from labeled alternatives, rubric score, 0–1 truth)
against a state blob through a provider-agnostic decision client, and
returns typed answers with probabilities — and, for choice and score,
confidence — as first-class state values. Ship with (1) a mock decision
provider for network-free tests, (2) a `calibration-audit` demo that
measures a provider's confidence reliability, documented as the operator
onboarding step before confidence-based routing is adopted, and (3) a
hello-grade `smart-if` demo (decide → branch → act). Interface target is
the public System One contract (`state` + named questions), exercised
via the vendor's LLM-backed `system-one-adapter` package — native
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
typed answer, probabilities, and (for choice/score) confidence land in
state where conditions branch on them; and the calibration-audit demo is
the documented operator gate for onboarding a provider — run it against
representative labeled data and record the result before any graph
routes on that provider's confidence. No runtime certification store or
execution guard is part of this FR; the demo README states that
confidence-based production routing is unsupported until the operator
has run the audit and recorded the result.

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

## Raw-output read (R-1)

Ten live responses from the selected non-mock backend
(`system-one-adapter` 0.2.1 → OpenAI `gpt-4o-mini`,
`structured_outputs=True`, `llm_answer_mode="probabilities"`,
`normalize_probabilities=True`), captured 2026-11-02 by
`tmp/probe_fr1155.py` and committed sanitized as
[FR-1155-raw-samples.json](FR-1155-raw-samples.json). All ten were read
end-to-end before the reducer or contract table below was designed.

| # | Sample | Answer digest | Sample-specific boundary observation |
|---|---|---|---|
| 1 | `noul_clear_true` | `{"noul": 1.0}` | Exactly 1.0 — degenerate certainty, and the whole answer object is two fields: `NoulAnswer` carries **no confidence field**; the `noul` value *is* the probability. 8 output tokens. |
| 2 | `noul_clear_false` | `{"noul": 0.0}` | Exactly 0.0 — both clear noul cases collapse to the distribution endpoints; no intermediate value was emitted for any clear case. |
| 3 | `noul_ambiguous` | `{"noul": 0.5}` | Exactly 0.5 — the adapter's generated schema text documents "0.5 means uncertain" and the model echoes the documented anchor verbatim: anchor quantization, not continuous estimation. |
| 4 | `choice_easy` | `billing`, conf `0.7000000000000001`, p=0.8/0.2/0.0 | Confidence ≠ top probability; the float artifact exposes it as computed — `(0.8−1/3)/(1−1/3)=0.7`, matching `choice_confidence` in adapter source (`_utils/confidence_metrics.py`). |
| 5 | `choice_ambiguous` | `engineering`, conf 0.4, p=0.6/0.3/0.1 | Probabilities arrive in tidy 0.1 steps — the LLM emits a coarsely quantized distribution; genuine ambiguity (export bug: engineering vs finance_ops) shows as spread, which the audit must distinguish from miscalibration. |
| 6 | `choice_high_cardinality` | `billing_export`, conf 0.890909…, 12 labels | Ten of twelve labels get exact 0.0; confidence `(0.9−1/12)/(1−1/12)`; 84 output tokens vs 24 for the 3-label case — cost grows with cardinality on the LLM path. |
| 7 | `choice_no_instructions` | `positive`, conf 0.25, p=0.5/0.25/0.25 | Omitted `instructions` becomes the literal schema text "Question: No additional instructions." — the adapter inserts a placeholder the model actually reads; undescribed labels likewise get "No additional instructions." |
| 8 | `score_three_level` | score 1.2, conf 0.4, p=0.1/0.6/0.3 | `score` is the probability-weighted mean and lands **between** legend levels (1.2); the SDK coerces legend/probability keys to `int`. |
| 9 | `score_five_level` | score 2.0, conf 0.16666…, p=.1/.2/.3/.4/0 | Confidence 1/6 although the mode holds p=0.4 — `score_confidence` penalizes mass *distance from mode*, so adjacent-level spread crushes confidence far below what choice margin would give. |
| 10 | `score_subjective` | score 1.6, conf 0.4, p=.1/.3/.5/.1 | The mixed review lands "Good" with real mass at "Mediocre"; the raw request shows rubric levels embedded as schema property descriptions keyed "0".."3" — the rubric travels inside the generated JSON schema, not the prompt body. |

Cross-sample observations: end-to-end latency ran 0.585–3.108 s per call
at 8–84 output tokens — the floor is the chat round-trip, the exact gap
the native model class claims to close. On the adapter backend,
confidence is a **deterministic function of the probabilities**
(formulas above), not independent model output; on native Jev it is
model-emitted. The audit therefore measures the probabilities' honesty
either way.

## Decision contract (R-2)

**Backend decision (closed):** the selected non-mock backend is
`system-one-adapter` (PyPI 0.2.1, MIT; core deps `pydantic>=2.12`,
`typesafe-sdk>=0.7.0` (MIT), `tenacity`, `typing-extensions`; provider
SDKs are extras) as the optional yamlgraph extra `decision`, with the
`openai` provider extra in demos. Probed 2026-11-02: installs clean on
Python 3.12 against the repo's `pydantic 2.13.4`. Remaining FR-761 steps
(constraints artifact, pip-audit, direct-import scan) run at enforcement
and their results are recorded in the implementation status. The
thin-internal-client alternative is dead: the adapter is MIT, small, and
vendor-maintained against the same wire contract.

Per-kind contract, fixed from committed raw samples and SDK source
(`typesafe_sdk._core.question_types`, `response_types`,
`_schemas.models`):

| Kind | Required YAML fields | Optional | Answer fields (typed) | Confidence | Probabilities | Validation failures (lint/runtime) |
|---|---|---|---|---|---|---|
| `noul` | `instructions: str` | — | `noul: float` (0–1, P(true)) | **none** — `noul` is the probability; branch on it directly | none (the scalar is the distribution) | missing `instructions` |
| `choice` | `options: mapping label→description-or-null`, non-empty, ≤255 labels | `instructions: str` | `choice: str` (a label), `confidence: float` (0–1), `probabilities: dict[str, float]` (~sum 1) | yes | per label | empty `options`; >255 labels; returned label not in `options` |
| `score` | `levels: ordered list of level descriptions` (one per score from 0), non-empty | `instructions: str` | `score: float` (expected value — may fall between levels), `confidence: float`, `legend: dict[int, str]`, `probabilities: dict[int, float]` | yes | per integer level | empty `levels` |

The earlier draft's uniform "answers carry confidence" claim is
withdrawn: noul has no confidence field (sample 1), so
confidence-branching examples and tests use choice/score; noul branches
on the `noul` value itself.

## Calibration algorithm (R-3)

Input schema (`CalibrationItem`): `{id: str, state: str, question:
<one decision question>, expected: str|int|bool}`. An item is **correct**
when the answer matches `expected` (choice: selected label; score:
`round(score)`; noul: `noul >= 0.5` vs a bool). The item's **reported
confidence** is `confidence` for choice/score and `max(noul, 1−noul)`
for noul.

- **Buckets:** 5 fixed-width over [0,1]: `[0,0.2) [0.2,0.4) [0.4,0.6)
  [0.6,0.8) [0.8,1.0]` — half-open, last closed.
- **Empty buckets:** weight 0 in ECE, rendered `—` in the table.
- **ECE** = Σ_b (n_b/N) · |accuracy_b − mean_confidence_b|.
- **Output** (`ReliabilityReport`, Pydantic): `buckets: list[{lo, hi, n,
  mean_confidence, accuracy, gap}]`, `ece`, `n_total`, `threshold`,
  `flagged: bool` (= `ece > threshold`). Threshold configurable,
  default **0.15**.

Deterministic fixtures with hand-computed expectations (mock provider
plants both answers and confidence):

- **Planted-miscalibrated** (10 items): every item answered at
  confidence 0.9; exactly 5 of 10 correct. One occupied bucket
  `[0.8,1.0]`: n=10, mean_conf=0.9, acc=0.5, gap=0.4. **ECE = 0.4 >
  0.15 → flagged.**
- **Calibrated** (20 items): 10 items at confidence 0.9 with 9 correct
  (bucket `[0.8,1.0]`: gap |0.9−0.9|=0.0) and 10 items at confidence
  0.5 with 5 correct (bucket `[0.4,0.6)`: gap 0.0). **ECE = 0.0 ≤ 0.15
  → not flagged.**

Unit tests assert the exact serialized table and ECE for both fixtures
(C-3: these tests are written RED before the reducer exists).

## Proposed Solution

Three slices, each independently testable:

### 1. Decision provider seam + mock

`create_decision_client()` factory (mirror of `create_llm`, CAP-03
precedent) in `yamlgraph/utils/`; no provider-specific imports outside
it (import-linter contract extended). Two backends:

- `system_one_adapter` — the vendor's public LLM-backed client, added as
  the optional extra `decision` (`pip install yamlgraph[decision]`) —
  backend decision closed above (R-2); FR-761 artifacts recorded at
  enforcement.
- `mock` — deterministic fixture provider (same pattern as the mock-LLM
  test fixtures) with *configurable planted answers and confidence*, so
  the calibration harness can be proven to detect what it exists to
  detect.

Answers normalize at this boundary into Pydantic models (Commandment 5):
per the contract table above — never raw dicts. On the adapter backend
confidence is derived from the probabilities by documented formulas; the
node contract treats it as opaque provider output either way.

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
        instructions: "Primary category of the ticket."
        options:
          billing: "Invoicing, payments, exports of financial documents"
          bug: "A defect in the product"
          feature_request: "A request for new functionality"
      severity:
        kind: score
        instructions: "Severity of the underlying defect."
        levels:
          - "Cosmetic"
          - "Degraded workflow with a workaround"
          - "Production outage or data loss"
    state_key: triage

edges:
  - from: triage
    condition: "state['triage'].category.confidence < 0.6"
    to: human_review
```

One request carries all questions (the contract evaluates them in
parallel and in isolation); choice cardinality is linted against the
255 cap. Sync and async execution paths behave identically (FR-679/
FR-998 precedent). This is a new call shape (`state` + questions), not a
fork of the FR-998 chat structured-output policy — the lint rule that
guards FR-998's single surface is untouched.

### 3. Demos (authored via `scripts/author.sh`, FR-767)

- `examples/demos/calibration-audit` — labeled fixture items → decision
  node per item → reducer emits the `ReliabilityReport` specified above
  (R-3). Run keyless against the mock provider with both deterministic
  fixtures; the planted-miscalibrated fixture must be flagged; the
  README records the exact command and observed result, and states that
  confidence-based production routing is unsupported until the operator
  runs the audit against representative labeled data and records the
  result.
- `examples/demos/smart-if` — the hello: one noul decision →
  conditional edge → two terminal actions, with deterministic fixtures
  that visit both branches. The decision-provider analog of
  `demos/hello`, runnable against the mock provider with no keys.

## Acceptance Criteria

Adopted verbatim from the [judgement](FR-1155-decision-node-calibration-audit.judgement.md)
(R-6); requirement ID fixed as **REQ-YG-726** (capability CAP-302).

- [x] AC-01: A committed artifact contains 10 sanitized raw responses
      from the selected non-mock backend, and the FR cites all 10 with
      one sample-specific boundary observation each.
- [x] AC-02: The FR names exactly one non-mock backend and records
      either its completed FR-761 governance result or the exact
      thin-client contract and rationale.
- [x] AC-03: A per-kind contract table defines required fields and typed
      response fields for `choice`, `score`, and `noul`; unit tests
      accept every valid kind and reject unknown kinds, missing required
      fields, and choice cardinality above 255.
- [x] AC-04: Decision responses cross the provider boundary as Pydantic
      models with the documented answer, probabilities, and confidence
      contract; tests prove raw provider dictionaries do not enter graph
      state.
- [x] AC-05: The `decision` node registers and executes the same request
      and normalized result through sync and async paths against the
      deterministic mock backend.
- [x] AC-06: A unit test proves a graph condition branches on the
      documented confidence field, and all decision tests carry
      `@pytest.mark.req("REQ-YG-726")`.
- [x] AC-07: Provider-specific imports exist only in the selected
      backend/factory boundary; `lint-imports` and any FR-761
      direct-import/dependency checks pass.
- [x] AC-08: The calibration reducer has a documented bucket rule,
      empty-bucket rule, ECE formula, output schema, and configurable
      pass threshold; unit tests assert the exact table and ECE for
      deterministic calibrated and planted-miscalibrated fixtures.
- [x] AC-09: `examples/demos/calibration-audit/graph.yaml` lints and
      completes a keyless mock-provider smoke; its output flags the
      planted fixture and its README records the exact command and
      observed result.
- [x] AC-10: `examples/demos/smart-if/graph.yaml` lints and completes a
      keyless mock-provider smoke that visits both conditional branches
      across deterministic fixtures; its README contains the exact
      quickstart.
- [x] AC-11: Each demo is authored through `scripts/author.sh`; the
      implementation record identifies the target and verdict from each
      distinct `tmp/draft-authoring-report.md` run.
- [x] AC-12: `python scripts/req_coverage.py --strict`, the targeted
      unit tests, and the non-slow unit suite pass.
- [x] AC-13: The FR implementation record states that calibration is an
      operator onboarding gate only and that no runtime
      certification/enforcement mechanism was added.
- [x] AC-14: A changelog fragment exists in `changelog/unreleased/`.

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

Dispositions of the remaining research-retrieved precedents (R-5):

- **FR-532** (DM v2 reviewer continuity human calibration, ENFORCED):
  "calibration" there aligns an LLM scorer with hand labels on a sample.
  **Inherited constraint:** calibration evidence comes from labeled data
  measured on our own harness, never from the scorer's self-report —
  exactly the audit's design. **Distinct surface:** narrative-axis
  scoring; no decision-provider seam.
- **FR-722** (ICPC-2 RFE classifier map/reducer, Completed): the
  incumbent chat-LLM pattern for exactly the decision shape this node
  serves; its boundary lessons (`two_strike_split`, `junk_drawer_cap` —
  reconcile model claims in code at the boundary) carry into the
  contract table's label-membership validation. **Distinct:** FR-1155
  migrates nothing — existing classifiers stay on their route (not
  authorized).
- **FR-995** (outsider reader, Enforced): a verdict pipeline whose
  instrument is explicitly non-deterministic ("recorded as the
  instrument's nature"). **Inherited constraint:** instrument variance
  is documented, not hidden — the audit README records observed results,
  not idealized ones. **Distinct:** prose judgement; no confidence
  contract.
- **FR-1001** (standalone outsider demo repo, Implemented with AC-13
  open): precedent for the *cost* of standalone-repo demos — an open
  acceptance criterion at merge. Supports rejecting the subtractionist's
  standalone decision-harness: these demos stay in-repo where lint,
  smoke, and req-coverage gates reach them. **Distinct:** different
  artifact class entirely.

## Implementation record (2026-11-02)

Enforced in commits: RED `a38e7ff2` (failing suite, 28 tests), GREEN
`d1f11db8` (primitive + demos + gates), judgement fold `3ffccf94`
(raw samples + revisions), adapter-era fixes included in GREEN.

**AC-13 statement:** calibration is an operator onboarding gate only; no
runtime certification store, execution guard, or enforcement mechanism
was added. The audit reports; the operator decides.

**Decisions and deviations:**

- Backend closed as `system-one-adapter` 0.2.1 (optional extra
  `decision`; MIT; rationale in `docs/dependency-rationale.yaml`;
  lazy-imported in `yamlgraph/utils/decision_factory.py`; AC-07
  witnessed by `test_factory_module_does_not_import_vendor_sdk`).
  pip-audit runs in CI's existing dependency lane; the extra is not a
  core dependency.
- The calibration-audit demo asks ten parallel choice questions in ONE
  decision call (the System One parallel-questions shape) instead of a
  map fan-out: map sub-node dispatch does not include decision nodes and
  that integration is outside frozen scope (C-6 territory).
- Two size-gate splits were forced by the addition and performed at
  cohesive seams: `SubgraphNodeConfig` → `yamlgraph/models/subgraph_schema.py`
  (node_schema crossed 400) and cache-policy helpers →
  `yamlgraph/compile/cache_policy.py` (node_compiler crossed 450).
- The linter's hard-coded `VALID_NODE_TYPES` omitted `decision` (E005) —
  found honestly by the first authoring run and fixed in GREEN.
- The authoring adapter's pinned CLI model `gpt-5.5` is retired from CLI
  accounts; re-pinned to `gpt-5.6-sol` (the judge/review adapters' pin) —
  route fixed, never bypassed (FR-767).
- `noul` answers have no confidence field (confirmed in raw samples 1–3);
  the smart-if demo branches on the `noul` probability itself, and
  confidence-branching tests use `choice`.

**Planned-operations reconciliation:**

| Planned operation | Outcome | Witness |
|---|---|---|
| PyPI metadata probe for system-one-adapter | ran | FR R-2 section (recorded result); `docs/dependency-rationale.yaml` entry |
| Read typesafe_sdk SystemOneResponse source | ran | R-2 contract table (per-kind fields incl. int-keyed score maps) |
| grep node-type registry and executor seams | ran | GREEN commit `d1f11db8` touches `compile/node_compiler.py`, `constants.py`, `compile/loop_limits.py` |
| Live Noul question through adapter | changed — expanded to the full 10-sample probe | `feature-requests/FR-1155-raw-samples.json` (commit `3ffccf94`) |
| Read 10 raw adapter responses before reducer design | ran | R-1 table, one boundary observation per sample |
| adapter fails FR-761 → thin client | did not run (adapter passed: MIT, clean install, pins satisfied) | R-2 backend decision |
| question type without confidence → scope exclusion | ran (noul) | R-2 contract table; smart-if branches on `noul` |
| harness misses planted miscalibration → fix first | did not run (tests condemned reducer before implementation, C-3) | RED `a38e7ff2` then GREEN `d1f11db8` |
| graph artifacts via author.sh | ran (2 runs) | `tmp/draft-authoring-report.md` (both runs concatenated, per-run copies preserved); adapter model re-pin was required first |
| research.sh 1 run | ran | `FR-1155.research.md` |
| judge.sh 1 run | ran | `FR-1155-decision-node-calibration-audit.judgement.md` |
| author.sh 2 runs | ran (3 invocations: 1 failed on retired model pin, 2 succeeded) | `tmp/author-*.log`; chore note in GREEN commit |
| yamlgraph graph lint (both demos) | ran | demo READMEs; `demo-output.log` files |
| yamlgraph graph run calibration-audit | ran — ECE 0.4, flagged true | `examples/demos/calibration-audit/demo-output.log` |
| pytest non-slow unit suite | ran — 7711 passed | GREEN commit pre-commit gate |
| req_coverage --strict | ran — exit 0 | GREEN commit pre-commit gate |

**Unplanned operations:** authoring-adapter model re-pin (`gpt-5.5` →
`gpt-5.6-sol`); linter `VALID_NODE_TYPES` fix; two size-gate module
splits (`subgraph_schema.py`, `cache_policy.py`); FR-1050 loop-limit
classification + builders for the decision type; hedging-allowlist and
noqa-confession line-shift updates; demo-proof success log line in
`decision_nodes.py`.

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
