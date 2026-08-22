# Feature Request: Requirement-Witness Audit — LLM Batch Review of REQ–Test–Code Triples

**Priority:** MEDIUM
**Type:** Tooling (LLM pipeline)
**Status:** Enforced 2026-08-22 — real run complete (412/412 audited, evidence committed); judgement advisory until human-reviewed
**Effort:** 1–2 days
**Requested:** 2026-08-22
**First consumer / first event:** the operator, reading the first audit
report's worst-witnessed-REQ ranking to decide which thin or hollow
witnesses get strengthened first. First event: one manual run —
constructor script, then the audit graph over the generated questions.

## Summary

Answer the spine's one non-mechanical question — *does the tagged test
actually witness its requirement?* (citation vs entailment, diary
2026-08-22 Addendum 4, question 7) — with the machinery this repo
exists to provide. Two halves, exactly the plan's payload contract:

1. **Deterministic constructor (no LLM, plain Python):** walk the
   requirements–test–code mapping (`req_coverage.py` loaders) and emit
   one question file per REQ into a temp folder (`tmp/req-audit/`),
   each carrying the full requirement text, its CAP and declared
   modules, its tagged tests with resolution class
   (coverage/AST/no-link/doc-witness), and resolved source files. The
   question is fixed: *are requirement, test, and code properly
   covered — what would improve the witness?*
2. **Audit graph (LLM, yamlgraph):** a map-node graph batches the
   question files (~10 REQs/batch → ~41 calls for 410 REQs) to a
   haiku-tier model, returning a typed verdict per REQ:
   `witnessed: yes|partial|no`, gap, improvement suggestion.

## Value Statement

The operator gets the first-ever substance ranking of the spine's 410
gated presence checks — which green checkmarks are hollow — at
haiku-batch cost; yamlgraph gets a dogfooding consumer that is a named
recurring task, not a generic affordance.

## Problem

Every REQ has a witness test (410/410, gated) but a
`@pytest.mark.req` marker is a citation, not an entailment. A REQ
witnessed only by doc-contract tests, or by a single test asserting an
adjacent behavior, passes the gate daily
(`gate_checks_shape_not_substance`). No deterministic join can read a
test body and judge relevance — this is the one question in the canon
that needs a judge, and this repo builds judges.

## Raw Output Read (measurement / metric-tooling FRs only)

- **Samples read:** per-REQ sections of the full ctrace-backed
  `req_coverage.py --implementation` output (2026-08-22, tree
  6f05d33d), which is the constructor's exact input.
- **What I saw:**
  - REQ descriptions vary from one line to 150+ word specs
    (REQ-YG-566's FR-Atlas paragraph enumerates collector, chunker,
    coverage post-pass, and render rules) — batch construction must
    carry full text, and batch size must respect token budget, not
    just REQ count.
  - Evidence thinness is real and visible: CAP-103 has 1 req / 1 test;
    `test_race_pipeline_docs` witnesses REQ content with 16 tests
    touching zero source. Without the resolution class in the question
    file, a model would grade doc-witness REQs as unwitnessed — the
    class label is load-bearing input, not decoration.
  - Test names alone often state the seam precisely
    (`test_gate_passes_when_sha_unresolvable`) — name + resolution
    class + file list may suffice for a haiku-tier verdict without
    shipping test bodies; the constructor should support both levels
    (names-only first; bodies as escalation for `partial` verdicts).

### Raw-input read table (R-2; ctrace log, tree 6f05d33d, 2026-08-22)

| REQ | CAP | Tests | Class | Files | Surprising detail |
|-----|-----|-------|-------|-------|-------------------|
| REQ-YG-245 | CAP-103 A2A SDK v1.0 | 1: `test_a2a_contrib_client::TestV1PartFormat::test_payload_uses_v1_part_format` | coverage | 1: `contrib/a2a_client.py` | A ~130-word spec enumerating a dozen API breaks (protobuf types, Role enums, EventQueue.close removal…) is witnessed by ONE test checking part format — the canonical thin witness this audit exists to find |
| REQ-YG-320 | CAP-142 Skill Export | 1: `test_fr348_skill_export_red::test_ac01_cli_registers_skill_export_subcommand` | coverage | 1: `cli/__init__.py` | The standing witness is a named RED-phase test — the TDD condemnation artifact became the permanent evidence, name and all |
| REQ-YG-321 | CAP-142 Skill Export | 1 test | coverage | 14 files (`graph_loader.py`…`skill_writer.py`) | Inverse thinness: one test fanning to 14 modules — coverage links measure execution *reach*, not entailment; breadth is not witness depth |
| REQ-YG-566 | FR Atlas (FR-748) | 20+: `test_fr748_fr_atlas::TestAssembly::test_bracket_wrapped_ids_repaired_at_assembly` et al. | coverage | atlas modules | The 150-word spec's assembly tests witness *model-output repair* behaviors (bracket-wrap, shortened-id reconciliation) — the corpus already fights drift at boundaries, and the audit prompt can cite it as in-repo precedent |
| REQ (CAP-99 docs) | CAP-99 Race/Pipeline Docs | 16: `test_race_pipeline_docs::*` | no-link (doc-witness) | 0 | Zero source files is *correct* here — tests assert reference-doc headings/examples; without the class label in the question file the model must grade this unwitnessed |

## Ideal Result

One command sequence produces a ranked list: every REQ graded
yes/partial/no with a one-line gap and suggestion, hallucination-proof
(every returned REQ id verified against the batch input at the
boundary), cheap enough to re-run monthly, with the raw model responses
on disk and read before any aggregate is trusted.

## Proposed Solution

```bash
# 1. Deterministic: construct questions (no LLM)
python scripts/req_audit_questions.py --out tmp/req-audit/questions/

# 2. LLM: audit graph maps batches (authored via the governed route)
yamlgraph graph run examples/demos/req_witness_audit/graph.yaml \
  --var questions_dir=tmp/req-audit/questions/ --full
# → tmp/req-audit/report.md + raw responses in tmp/req-audit/raw/
```

Constraints (binding):

- The graph + prompts are authored SOLELY via
  `scripts/author.sh <task-brief.md>` (graph-authoring doctrine) — this
  FR's enforce step writes the task brief, never the YAML. Target:
  `examples/demos/req_witness_audit/`; committed map precedent:
  `examples/demos/map` (authoring route may substitute a better one,
  recorded in `tmp/draft-authoring-report.md`).
- **Question-file schema (frozen, R-3):** one JSON file per REQ —
  `req_id`, `req_text` (full), `cap_id`, `cap_name`,
  `declared_modules[]`, `tests[]` (each `{test_id, resolution}` with
  enum `coverage|ast|no-link-ran|no-link-unrecorded|doc-witness`),
  `resolved_files[]`, `evidence_depth`, `question` (fixed text).
- **Evidence depth is two-stage (R-3):** Stage 1 is names-only
  (`evidence_depth: names`) and its verdict is explicitly **witness
  plausibility from names and declared links** — the report labels it
  so. REQs graded `partial`/`no` are re-queued in Stage 2 with test
  bodies and ±20-line source excerpts (`evidence_depth: bodies`) for
  the entailment check. Only Stage-2 verdicts may claim entailment.
- **Resolution-class ownership (R-1, judgement C-2):** FR-851 owns the
  minimum class derivation it consumes (doc-witness = resolved targets
  outside `yamlgraph/`; no-link split by context-table membership),
  implemented in the constructor with tests — no dependency on FR-850's
  completion; FR-850 may later absorb the shared logic.
- **Batching (R-4):** deterministic estimator (chars/4, documented
  approximation), configurable max (default 8000 tokens/batch),
  ordering by `req_id`; an oversized single REQ gets its own batch —
  isolated, never truncated.
- Model: haiku-tier default, provider-configurable via the factory; map
  node with per-batch `on_error: retry`.
- Output schema (Pydantic, inline in prompt YAML): `req_id`,
  `witnessed: yes|partial|no`, `gap: str`, `suggestion: str`.
  **Reconciliation lives in deterministic Python** (report-assembly
  tool invoked post-map, R-4), per `two_strike_split`: returned
  `req_id`s must be a subset of the batch's input ids — hallucinated
  ids reject the result, duplicates keep first and log, missing ids
  re-queue once then surface as `unaudited`; no input REQ disappears
  silently.
- No aggregate acceptance threshold on verdict distribution
  (`threshold_encodes_forecast`) — the deliverable is the ranked list,
  not a score.
- **Evidence outputs (R-5):** raw responses stay in
  `tmp/req-audit/raw/` (never committed in bulk); the committed
  evidence artifact is `feature-requests/evidence/FR-851-req-witness-audit.md`
  — ranked report, model/provider, tree SHA, batch count,
  reconciliation summary, ≥5 raw-response citations with concrete
  surprising details (`read_raw_output_first`).

## Acceptance Criteria (revised per judgement 2026-08-22)

- [x] AC-01: Related/precedent section names only committed paths; the
  authoring task brief targets `examples/demos/req_witness_audit/` and
  names `examples/demos/map` as precedent (or delegates the choice to
  the authoring route report).
- [x] AC-02: Raw-input read table with ≥5 concrete samples (REQ id,
  CAP, tests, resolution class, files, surprising detail) — present
  above.
- [x] AC-03: Constructor emits one deterministic machine-readable
  question file per current registry requirement count (not hard-coded
  410); byte-identical output for the same tree witnessed by test; no
  LLM.
- [x] AC-04: Each question file contains the frozen schema (see
  Constraints), including the resolution-class enum, evidence-depth
  marker, and the fixed audit question.
- [x] AC-05: Resolution-class dependency closed inside this FR: minimum
  derivation implemented and tested, including the doc-witness fixture
  for `test_race_pipeline_docs`.
- [x] AC-06: Batching uses the deterministic estimator and configured
  maximum; a REQ-YG-566-sized fixture proves oversized REQs are
  isolated without overflow.
- [x] AC-07: Graph and prompts authored solely via
  `scripts/author.sh <task-brief.md>`; `tmp/draft-authoring-report.md`
  exists, non-empty, with `Artifacts`, `Precedent`, `Validation`,
  `Repairs`, `Blocked validation` headings, listing existing
  repo-relative authored paths.
- [x] AC-08: `yamlgraph graph lint` and the narrow smoke run recorded
  in the authoring report; blocked validation records the exact blocked
  command and reason, never a substitute success.
- [x] AC-09: Reconciliation covered by tests for hallucinated,
  duplicate, and missing `req_id`s; hallucinated rejects, missing
  re-queues once then `unaudited`; no input REQ disappears silently.
- [x] AC-10: Report ranks `no`, `partial`, `unaudited` first with gap +
  suggestion; `yes` collapses to counts; report includes
  model/provider, tree SHA, batch count, reconciliation summary, and
  the Stage-1 plausibility vs Stage-2 entailment labeling.
- [x] AC-11: One real full run: raw responses under
  `tmp/req-audit/raw/`, durable committed evidence at
  `feature-requests/evidence/FR-851-req-witness-audit.md` with ≥5
  raw-response citations containing concrete surprising details. No
  mocked substitute (judgement C-4).
- [x] AC-12: Constructor/reconciliation tests tagged per ADR-001;
  changelog fragment included.

## Implementation Status (2026-08-22)

- RED af20e0f3 (SKIP=pytest), GREEN 33043358: CAP-243 / REQ-YG-606,
  REQ-YG-607; 19 tests in `tests/unit/test_fr851_req_audit_red.py`.
- Graph authored via `scripts/author.sh tmp/fr851-audit-graph-brief.md`
  (gpt-5.5, session 01d66261): `examples/demos/req_witness_audit/`
  — graph.yaml, prompts/audit_batch.yaml, graph-local tools.py (batch
  enumeration + raw persistence). Lint + live 2-batch smoke recorded in
  the authoring report; zero repairs, zero blocked validations.
- Real run: 412 questions / 41 batches / claude-haiku-4-5; 412 audited,
  0 unaudited, 0 rejected, 0 duplicates; 167 yes / 235 partial / 10 no.
  Evidence: `feature-requests/evidence/FR-851-req-witness-audit.md`.
- Decisions / deviations:
  - The pipeline is three commands, not two: reconciliation + report is
    a separate deterministic script invocation after the graph
    (`scripts/req_audit_report.py`), satisfying "deterministic Python
    invoked post-map" without complicating the authored graph.
  - Minimum doc-witness derivation: a test file with no yamlgraph
    linkage that references `.md` document paths (AST string-constant
    scan, file-level). Live distribution: 3339 coverage / 509 ast /
    1465 doc-witness / 1261 no-link-unrecorded / 0 no-link-ran.
  - Stage-2 emission (`build_stage2_question`: test bodies + 40-line
    head excerpts of resolved files) is implemented and tested but not
    executed in the first pass; the Stage-1 report is the deliverable.

## Alternatives Considered

- **Deterministic heuristics (name similarity, keyword overlap):**
  answers a different, weaker question; the entailment judgement is
  irreducibly semantic.
- **Frontier-model single-pass over the whole registry:** one giant
  context invites the 658-token-novel failure mode (FR-596/597); map
  batches keep each judgement small, cheap, and individually readable.
- **Waiting until FR-850's cheaper questions are answered:** rejected
  by the operator — in this repo the LLM-shaped question is the
  *easiest*: the machinery (map nodes, typed schemas, provider factory)
  is the product; ranking by mechanical answerability was a
  script-writer's frame (diary Addendum 5).

## Related

- Plan: `docs/2026-08-21-plan-architecture-claims-pipeline.md` (payload
  contract — this FR instantiates both branches in one feature)
- Diary: `docs/diary/diary-2026-08-22-the-spine-is-a-claim-store.md`
  (Addendum 4 question 7; Addendum 5)
- `feature-requests/FR-850-req-coverage-usable-form.md` (independent;
  this FR owns its minimum resolution-class derivation — judgement C-2)
- Precedents: `examples/demos/map` (map node),
  `scripts/req_coverage.py` loaders, FR-727/730 boundary reconciliation

## Judgement (2026-08-22)

**Verdict:** APPROVED WITH REVISIONS — rendered via the sole adapter
route (`scripts/judge.sh`, gpt-5.5, draft `tmp/draft-judgement.md`);
advisory until human-reviewed.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | Stale citations (`map_demo`, unnamed FR-850 path); FR-850 dependency open | Fixed: `examples/demos/map`, exact FR-850 path; FR-851 owns minimum resolution-class derivation (C-2) |
| R-2 | Raw-input narrative, no sample table | Table of 5 samples added with per-REQ surprising details |
| R-3 | Question-file schema and evidence depth unfrozen | Schema frozen in Constraints; two-stage depth: Stage 1 names-only = plausibility verdict, Stage 2 bodies = entailment |
| R-4 | Batching estimator and reconciliation surface unnamed | chars/4 estimator, 8000-token default, req_id ordering, isolate-oversized; reconciliation in deterministic post-map Python with hallucinated/duplicate/missing tests |
| R-5 | Evidence committed from `tmp/` | Durable artifact `feature-requests/evidence/FR-851-req-witness-audit.md`; bulk raw stays in `tmp/` |

**Conditions (GATE):** C-1 revisions folded (done above); C-2
resolution-class ownership (folded); C-3 authoring only via
`scripts/author.sh`; C-4 AC-11 needs a real LLM run — no mocked
substitute; C-5 runtime/hook/CI/doctrine changes need a separate FR.

**Purge list:** hard-coded 410 count; committed bulk raw dumps;
aggregate verdict thresholds; entailment claims from names-only
payloads.

**Scope frozen:** D-1 constructor + tests; D-2 question files in
`tmp/req-audit/questions/`; D-3 graph via authoring route at
`examples/demos/req_witness_audit/`; D-4 reconciliation/report
assembly; D-5 one durable evidence report; D-6 ADR-001 markers +
changelog fragment. Not authorized: new node types, provider factory
changes, CI/pre-commit gates, scheduled automation, doctrine changes.

### Questions for the human (as options, or 'none')

None — the two open choices in the draft (FR-850 gate vs ownership;
evidence location) had clear defaults and were resolved per the
judgement's own recommendations.
