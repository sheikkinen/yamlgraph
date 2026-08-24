# Feature Request: Memory Curation Premise Wiring & Baseline Bootstrap

**Priority:** HIGH
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS (2026-08-24); R-1…R-3 folded, authority active
**Effort:** 0.5 day
**Requested:** 2026-08-24
**First consumer / first event:** the agent running the next real
memory-curation hygiene pass — today the graph accepts only free-text
`audience_premise`, while reconcile/apply require exact `premise_kind`;
the generated disposition therefore omits the field and apply fails closed
to tier 3 (export/publication), making the normal hygiene path unusable.

**Blast radius:** graph metadata, graph glue, fixture tests/docs, and one
machine-local real hygiene run. The real run uses the operator-approved
Vertex provider; raw notes/dispositions remain under `tmp/` and the live
memory root. No memory content is committed or transported.

## Summary

Close the integration gap discovered after FR-875/877/878 enforcement:
`premise_kind` is implemented and tested at the reconcile/apply boundary,
but `examples/memory-curation/graph.yaml` and `nodes/graph_nodes.py` never
carry it. Add an explicit required graph variable
(`hygiene | export_publication`), pass it unchanged into deterministic
reconciliation, prove the final disposition carries it, then run one real
hygiene pass to create the missing post-apply `.curation-state.json`
baseline. Correct FR-875's stale status header in the same implementation
record.

## Value Statement

The memory feature becomes operational end-to-end rather than green only
at its component boundaries: a graph-generated hygiene disposition gets
tier-1 semantics, apply writes the live baseline, and SessionStart becomes
quiet until real corpus drift crosses the FR-877 threshold.

## Problem

1. **Composition defect:** `reconcile.py` validates and emits
   `premise_kind`; `apply.py` computes tier 3 whenever it is absent or
   non-`hygiene`; but graph state has only `audience_premise`, and
   `reconcile_memory_dispositions()` never supplies `--premise-kind`.
   All 43 tests pass because tests invoke reconcile directly with
   `--premise-kind hygiene`; the end-to-end graph path is unwitnessed.
2. **Live state predates the marker:** the 57-note hygiene apply happened
   before FR-877 introduced `.curation-state.json`. The advisory therefore
   truthfully-but-misleadingly says "corpus never curated (57 notes)".
3. **Record drift:** FR-875's header says the first real run is pending,
   while its implementation record documents two completed real runs and
   one applied hygiene disposition.

## Ideal Result

A caller must explicitly choose `premise_kind`; the graph transports that
exact value without inference, reconciliation rejects unknown values, and
`disposition.json` always records it. Fixture smoke proves both hygiene and
export values survive end-to-end. A real Vertex hygiene run then follows
the FR-878 tier policy: tier 0/1 may apply under standing delegation and
writes a post-apply marker; any `forget` (tier 2) stops before apply and
presents one structured human question. After a successful tier 0/1
bootstrap, the live FR-877 advisory is silent at threshold 1 (zero
immediate drift).

## Proposed Solution

### 1. Governed graph-authoring correction

This task materially modifies `examples/memory-curation/graph.yaml`, so
**all graph changes use the sole route**:

```bash
scripts/author.sh feature-requests/authoring-briefs/fr-880-premise-wiring-brief.md
```

Frozen artifact boundary:

- Task brief (committed before route):
  `feature-requests/authoring-briefs/fr-880-premise-wiring-brief.md`
- Governed artifact: `examples/memory-curation/graph.yaml`
- Adjacent glue: `examples/memory-curation/nodes/graph_nodes.py`
- Docs: `examples/memory-curation/README.md`
- Tests: `tests/unit/test_memory_curation_premise.py`
- Retained authoring report: summarized in this FR's implementation record;
  raw report remains `tmp/draft-authoring-report.md`

The committed input-closure brief now exists at
`feature-requests/authoring-briefs/fr-880-premise-wiring-brief.md`
(R-1). It names the exact artifacts, no-prompt-change constraint,
transport witnesses, and lint/test/smoke commands. Enforcement must use
that file unchanged as the `scripts/author.sh` input.

Required wiring:

```yaml
state:
  premise_kind: str  # required runtime variable

nodes:
  reconcile:
    variables:
      premise_kind: "{state.premise_kind}"
```

`reconcile_memory_dispositions()` passes the value as
`--premise-kind <value>` to `reconcile.py`. No substring inference from
`audience_premise`; both inputs remain required and serve different jobs:
`premise_kind` controls policy tier, `audience_premise` grounds semantic
judgement.

### 2. End-to-end fixture witnesses

Add behavior-scoped tests/smokes using fixture roots only:

- `premise_kind=hygiene` → final disposition records `hygiene`.
- `premise_kind=export_publication` → records `export_publication`.
- Missing/unknown values fail before apply (graph/state validation or
  reconcile validation); never silently default to hygiene.
- Existing graph lint and 3-note fixture smoke remain green.

R-2 tightens the witness boundary: tests must exercise the graph/config
and `reconcile_memory_dispositions()` glue path, not only call
`reconcile.py` directly. Both exact values must reach the final JSON;
missing graph/glue state must fail before any apply call, and unknown
value must reach deterministic reconcile validation and fail there.

### 3. Live baseline bootstrap

After implementation/fixture validation, run the graph against the live
repo-scope corpus with:

- `PROVIDER=vertex` (operator-approved in FR-875),
- `premise_kind=hygiene`,
- machine-local hygiene audience premise from FR-875 run 2.

Read all non-keep rows. Apply policy:

- Tier 0: apply/no-op directly.
- Tier 1: apply under FR-878 standing delegation after reading every
  compression draft in full.
- Tier 2 (`forget` present): **do not apply**; present one structured
  question with forget rows, tombstone preview, and recommended default.
- Tier 3 is impossible for this run if wiring is correct; treat it as a
  failed witness.

A successful tier 0/1 apply must create `.curation-state.json`; immediately
run `memory-advisory.sh` at threshold 1 and require silence (zero drift).
Record aggregate verdict/audience/staleness counts only in the FR; no raw
note bodies or drafts.

R-3 freezes the durable evidence record. The FR implementation section
must record: exact command shape; provider; exact hygiene premise text;
manifest and disposition hashes; aggregate verdict/audience/staleness
counts; computed tier; action taken; and a bounded list of non-keep
relative paths with draft byte counts plus an explicit read-in-full
attestation. If tier 2/3 occurs, write
`tmp/memory-curation/fr-880-human-question.md` (options, evidence,
recommended default), record that path here, stop before apply, and do
not claim marker-bootstrap success.

### 4. Record correction

Update FR-875 header to reflect completed real runs and the marker
bootstrap result. Add the implementation evidence and any deviation to
this FR; extend CAP-247 with a new requirement only if REQ-YG-620..622 do
not already cover the end-to-end metadata transport contract.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: R-1…R-3 are folded and the committed authoring brief exists
  before enforcement (satisfied at judgement fold).
- [ ] AC-02: Graph authoring runs through `scripts/author.sh` using the
  committed FR-880 brief; report records artifact paths, precedent,
  lint/smoke commands, repairs, and blocked validation.
- [ ] AC-03: `graph.yaml` declares required `premise_kind` and passes it
      explicitly into the reconcile node; no prompt YAML changes.
- [ ] AC-04: `graph_nodes.py` passes `premise_kind` to reconcile as the
      exact `--premise-kind` argument; no default or free-text inference.
- [ ] AC-05: Fixture graph/glue witnesses prove hygiene and
      export_publication values appear unchanged in final
      `disposition.json`; missing/unknown premise fails closed.
- [ ] AC-06: Missing graph/glue state fails before any apply invocation;
  unknown value is rejected by deterministic reconcile validation.
- [ ] AC-07: `yamlgraph graph lint examples/memory-curation/graph.yaml`
      and the 3-note fixture smoke pass; all existing memory suites stay
      green.
- [ ] AC-08: Tests use temp/fixture memory roots only and are tagged to a
      CAP-247 requirement; no automated test reads the real memory store.
- [ ] AC-09: README run commands require both `premise_kind` and
      `audience_premise`, explaining policy-vs-judgement roles.
- [ ] AC-10: One real Vertex hygiene run is executed after fixture
      validation. Every non-keep row is read. Tier 0/1 may apply per
      FR-878; tier 2 stops for a structured human decision; tier 3 is a
      witness failure.
- [ ] AC-11: Live-run evidence records command/provider/exact premise,
  hashes, aggregate counts, tier/action, and non-keep paths plus
  draft byte counts/read attestation; no raw memory content committed.
- [ ] AC-12: After successful tier 0/1 apply,
      `.curation-state.json` exists and `memory-advisory.sh` at threshold
      1 emits no line; marker count equals the live corpus predicate.
- [ ] AC-13: Tier 2/3 writes the structured gitignored question artifact,
  stops before apply, and does not claim bootstrap success.
- [ ] AC-14: FR-875's status header and FR-880 implementation record match
      observed reality; only aggregate real-run counts are committed.
- [ ] AC-15: Diary reflection records the component-green/system-red
      composition trap and why end-to-end metadata transport needs its own
      witness.

## Alternatives Considered

- **Infer premise kind from `audience_premise`:** forbidden by FR-878 R-5;
  fuzzy policy detection is exactly the boundary that must fail closed.
- **Default missing premise to hygiene:** unsafe privilege reduction;
  missing metadata must remain tier 3 until the caller chooses explicitly.
- **Bootstrap marker directly from live files:** would silence the advisory
  without witnessing graph → disposition → tier → apply composition;
  symptom patch, rejected.
- **Reuse the old pre-marker disposition:** it lacks `premise_kind` and
  predates current corpus state; hash safety correctly makes it the wrong
  artifact.
- **Code-only fix in graph glue:** leaves graph input closure implicit and
  violates the graph-authoring sole route for the necessary graph change.

## Prior Art

**Prior art:** FR-875 (parent curation graph and two real runs), FR-878
(exact premise metadata and tier policy; this FR closes its missed graph
integration), FR-877 (post-apply marker/advisory; this FR bootstraps its
first live baseline), FR-874 (REJECTED — no transport or publication),
FR-767/graph-authoring doctrine (sole route for graph change). This is a
composition correction, not a new curation capability.

## Related

- `examples/memory-curation/graph.yaml`
- `examples/memory-curation/nodes/graph_nodes.py`
- `examples/memory-curation/nodes/reconcile.py`
- `examples/memory-curation/apply.py`
- `examples/memory-curation/advisory.py`
- CAP-247 / REQ-YG-620..622

## Judgement (2026-08-24)

**Verdict: APPROVED WITH REVISIONS.** Full artifact:
`feature-requests/FR-880-memory-curation-premise-wiring-and-baseline-bootstrap.judgement.md`.

- **R-1:** committed authoring brief required before authority — created
  and cited above.
- **R-2:** prove exact/missing/unknown behavior through graph/config and
  glue, not only direct reconcile tests — folded into witnesses/ACs.
- **R-3:** freeze bounded live evidence and tier-2/3 stop artifact —
  folded into bootstrap/ACs.

Authority is active. Enforcement remains pending and must not re-run the
judge (C-7).
