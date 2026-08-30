# Feature Request: Code-Owned FR-Reference Reconciliation in the Recap Demo

**Priority:** MEDIUM
**Type:** Bug (invariant enforced in the wrong layer)
**Status:** Judged — APPROVED WITH REVISIONS ([judgement](FR-930-recap-code-owned-fr-reference-reconciliation.judgement.md)); R-1–R-3 folded in below
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** every invocation of `examples/demos/recap/graph.yaml` — first event is the next recap run, whose output is currently unguarded against invented FR references outside of one sampled CI test.
**Research:** in-body Research Record below (R-1: solution classes, per-class evidence, preserved disagreement, `is_this_a_graph`); plus verified factual grounding — FR-922 investigation record (single LLM call, trace-cited causal chain); `create_python_node` calling convention (`yamlgraph/tools/python_tool.py` — python nodes receive the full state dict, so no `graph.yaml` change is required); model-authored surface from `examples/demos/recap/prompts/recap.yaml` schema (`workstreams`, `hotspots` — nothing else transits the model).
**Prior art:**
- **FR-700** created the recap demo and REQ-YG-531 (no hallucinated FR references on a conventions-free repo).
- **FR-702/703/704** progressively evicted transport from the model in this same graph: reference partition (702), status join (703), orphan assembly (704) — each moved a "the model must not X" hope into "the code makes X impossible." The anti-hallucination clause is the last such hope still enforced only by prompt instruction ("Never invent … FR references") plus one sampled live test.
- **FR-922** (closed, disposition d) kept the live witness unskipped but recorded it as a gray zone on three axes — time (13–283s), silent provider binding, and pipeline misfit ("an evaluation concern, not a regression gate") — and named relocation a candidate. Its judgement's scope freeze forbade deleting the test *within FR-922*; this FR re-opens that disposition with new evidence: the witness is not relocated but **replaced by construction**.
- **FR-923** (suite latency umbrella): removing this test's live cost from the keyed suite is complementary to, not dependent on, its lane work.
- **FR-677** (graph-level `verify:`) — considered and not used; see Alternatives.

## Ideal Result

A recap output **cannot** contain an FR/NC reference that is absent from the
deterministic git-collection inputs — on any repo, on every run, with zero
live-model witnesses needed in the regression suite. REQ-YG-531 is proved by
millisecond unit tests that exercise the enforcing code directly.

## Summary

The recap graph's honesty invariant (REQ-YG-531) is enforced today by asking
the model nicely (prompt: "Never invent … FR references") and sampling one
live output per keyed CI run
(`test_bare_repo_recap_no_hallucinated_conventions`, the suite's slowest
test). Move the invariant into `finalize_recap` — the existing deterministic
boundary node — by reconciling every `(FR|NC)-N` token in the model-authored
fields against the reference universe already present in state. Unverified
tokens are stripped and recorded, never silently. The live integration test is
then retired: its assertion becomes tautological, and its witness role passes
to unit tests of the reconciler.

This is `the_one_law` (normalize at the boundary where external data enters)
and `two_strike_split` (treat model output as a CLAIM; reconcile against the
source of truth at the boundary) applied to the one clause FR-702/703/704
left behind.

## Research Record (R-1)

**`is_this_a_graph`:** No. The task is a deterministic post-pass inside an
existing graph's python finalizer — arithmetic set membership, zero LLM calls,
no map/race/router shape. The graph already exists; this hardens one of its
nodes.

Solution classes considered, with precedent/evidence per class:

1. **Prompt hardening** — strengthen the "Never invent" instruction.
   Evidence against: `two_strike_split` (Scripture) — "zero prompt patches
   held" across FR-722/727/730; FR-702's field run already proved this graph's
   model ignores transport instructions (2/6 orphan false positives).
   Rejected.
2. **Live sampled witness (status quo)** — keep
   `test_bare_repo_recap_no_hallucinated_conventions`.
   Evidence against: FR-922 gray-zone verdict (time 13–283s, silent provider
   binding, eval concern in a regression suite); samples one output, guards
   zero production runs. Rejected.
3. **Evaluation-lane relocation** — FR-922's own candidate disposition,
   deferred to FR-923 lane work.
   Evidence: prices the witness correctly but still sampling, still
   vendor-bound, still guards nothing at runtime. Superseded by construction.
4. **Graph-level `verify:` postcondition (FR-677)** — declare
   `state.unverified_refs | length == 0` in `graph.yaml`.
   Evidence: FR-677 provides exactly this; but it requires a governed
   `graph.yaml` edit (authoring route) to assert a condition the reconciler
   makes tautological, and `halt` discards a mostly-valid recap over one
   token. Rejected — recorded as the *preserved disagreement*: a reasonable
   engineer could argue the declared postcondition belongs in the artifact
   for self-documentation even when tautological; we defer that to a future
   authoring-route pass rather than triggering it here.
5. **Deterministic boundary reconciliation in `finalize_recap`** — strip
   unverified `(FR|NC)-N` tokens, record them.
   Evidence for: the FR-702→703→704 eviction lineage in this same graph
   (each moved a prompt hope into code impossibility); full-state calling
   convention verified in `yamlgraph/tools/python_tool.py`. **Chosen.**
6. **Fuzzy repair** — map invented ids to nearest real id within a
   similarity floor (`two_strike_split` allows repair).
   Evidence against: FR ids have no meaningful similarity metric (FR-999 vs
   FR-909); silent repair manufactures a *plausible wrong answer*
   (Commandment 6). Rejected.

## Value Statement

For every consumer of the recap demo: the anti-hallucination guarantee
upgrades from "sampled once per CI run, on one fixture, under one vendor" to
"enforced on every invocation by construction." For the test suite: removes
its slowest test (13–283s observed) and the suite's only silent
provider binding, replacing them with deterministic millisecond witnesses.

## Problem

1. `examples/demos/recap/prompts/recap.yaml` instructs the model to never
   invent FR references. Prompt instructions are not enforcement
   (`two_strike_split`: "every mechanizable level eventually defeats
   instruction text").
2. The only executing witness is
   `tests/integration/test_recap_demo_integration.py::TestRecapOnBareRepo::test_bare_repo_recap_no_hallucinated_conventions`
   — a live Anthropic call per keyed run, 13–78s steady state, 283s worst
   observed (FR-922), asserting a vendor the graph never declares.
3. Production runs are entirely unguarded: the test samples one output; every
   real invocation trusts the prompt.

## Proposed Solution

All changes in `examples/demos/recap/nodes/partition.py` and tests. **No
`graph.yaml` or prompt change** — python nodes receive the full state dict,
so `finalize_recap` already has access to every deterministic input.

### 1. Reconciler in `partition.py`

- Build the **allowed universe** from **model-visible deterministic evidence
  only** (R-2): all `(FR|NC)-N` ids (uppercased) found by the existing
  `_REF_PATTERN` in `commits`/`referenced`, `churn`, `fr_changes`, and
  `fragments`. **`fr_statuses` is explicitly excluded** — it greps every FR
  at `HEAD`, not the recap window, and the model never sees it; admitting it
  would let a prompt-invisible but real FR id survive reconciliation and
  then collect a `[Status: …]` tag from `attach_statuses`. `fr_statuses` is
  consumed only *after* reconciliation, by the status join, for ids that
  survived.
- Scan the model-authored fields (`workstreams`, `hotspots` — the complete
  model surface per the prompt schema) for `(FR|NC)-N` tokens.
- Any token not in the universe is **stripped from the text** and **recorded**
  in a new `unverified_refs` list on the recap dict (Commandment 6: exposed,
  never silent). Normalization is frozen (R-3): uppercase, unique, first-seen
  order; exactly `[]` when nothing was stripped.
- Reconciliation runs **before** `attach_statuses` inside `finalize_recap`,
  so an invented id can never receive a status join or a `[no FR status]`
  tag that lends it credibility.
- `#N` issue tokens are out of scope: REQ-YG-531's clause is FR references,
  and `attach_statuses` already discards `#N` ids from joins.

### 2. Unit witnesses (TDD, RED then GREEN commits)

New tests in `tests/unit/test_recap_demo.py`, all
`@pytest.mark.req("REQ-YG-531")`, exercising `finalize_recap` directly with
synthetic state:

- Invented `FR-999` in a workstream line with an empty universe → stripped
  from the line, present in `unverified_refs`.
- Legitimate ref (present in `commits`/`referenced`) → preserved verbatim,
  status join untouched, `unverified_refs` exactly `[]`.
- Invented ref in `hotspots` → stripped and recorded.
- Case handling: lowercase `fr-999` in model text reconciles against the
  uppercased universe.
- Ordering: an invented ref never appears with a `[Status: …]` or
  `[no FR status]` tag in the final output.
- **Status-only negative witness (R-3):** `FR-999` present in `fr_statuses`
  but absent from `commits`/`referenced`, `churn`, `fr_changes`, and
  `fragments` → stripped, recorded as `["FR-999"]`, and the final workstream
  line carries neither `[Status: …]` nor `[no FR status]` for it.
- Normalization: duplicate and mixed-case stripped tokens collapse to one
  uppercase entry in first-seen order.

### 3. Retire the live witness

Delete `TestRecapOnBareRepo::test_bare_repo_recap_no_hallucinated_conventions`.
Disposition of its three assertions:

- *No hallucinated FR refs* → impossible by construction; witnessed by the
  unit tests above (stronger: proves the clause for all outputs, not one
  sample).
- *Orphan hash bit-exact* → code-owned since FR-704; already reachable by a
  deterministic unit test of `finalize_recap` (add one if not present).
- *Graph runs end-to-end without error* → retained by
  `TestRecapDispositionAxis::test_rejected_status_surfaces_verbatim`
  (REQ-YG-534, same file, still live-invokes the graph) and by the demo-gate
  (`demo-output.log` regenerated whenever `examples/demos/recap/` changes —
  including in this PR).

### 4. Gates

- Rerun the recap demo and commit the refreshed `demo-output.log`
  (demo-gate, FR-206).
- Changelog fragment (`req: REQ-YG-531`), diary reflection, FR status
  updates in this file.

## Acceptance Criteria (superseded by the judgement's revised AC-01…AC-12; kept for provenance)

The binding acceptance criteria are the twelve in the
[judgement](FR-930-recap-code-owned-fr-reference-reconciliation.judgement.md).
Original draft criteria:

- [ ] AC-01: RED commit exists with failing reconciler unit tests tagged `REQ-YG-531`; GREEN commit makes them pass (separate commits, per Commandment 7).
- [ ] AC-02: `finalize_recap` output contains no `(FR|NC)-N` token absent from the deterministic inputs, for any synthetic recap fed to it (property exercised by the unit tests).
- [ ] AC-03: Stripped tokens are recorded in `recap["unverified_refs"]`; the field is an empty list when nothing was stripped — no silent path.
- [ ] AC-04: Reconciliation precedes the status join: unit test proves an invented id receives no `[Status: …]`/`[no FR status]` tag.
- [ ] AC-05: `test_bare_repo_recap_no_hallucinated_conventions` is deleted; `python scripts/req_coverage.py --detail` still reports REQ-YG-531 covered, and the FR records the count before/after.
- [ ] AC-06: No change to `examples/demos/recap/graph.yaml`, `prompts/recap.yaml`, any `yamlgraph/` module, CI workflows, or pytest config.
- [ ] AC-07: Refreshed `demo-output.log` in the diff (demo-gate) showing `unverified_refs` absent-or-empty on a real run; changelog fragment and diary entry present.
- [ ] AC-08: Full unit lane green: `pytest tests/unit/ -q --no-cov -m "not slow"`.

## Out of Scope

- Graph-level `verify:` block, `guards`, or any `graph.yaml`/prompt edit
  (would trigger the graph-authoring route for a postcondition the code
  change makes tautological).
- `#N` issue-reference reconciliation.
- Latency/model/provider changes (FR-922 closed those; FR-923 owns lanes).
- Reconciling any field the model does not author.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Graph-level `verify:` rule (FR-677), e.g. `state.unverified_refs \| length == 0` | Rejected — requires a `graph.yaml` edit (authoring route) to assert a condition the reconciler makes tautological; a halt on hallucination is also worse UX than strip-and-record for a demo whose other output remains valid |
| Keep the live test alongside the reconciler | Rejected — post-fix it can only fail if the *reconciler* fails, which the unit tests prove in milliseconds without a vendor key; keeping it re-creates FR-922's gray zone for zero marginal coverage |
| Relocate the live test to an evaluation lane (FR-922's candidate) | Superseded — relocation prices the witness correctly but still guards nothing at runtime; construction beats sampling. Prompt-quality evaluation remains available via the demo-gate run |
| Reject/halt on unverified refs instead of strip-and-record | Rejected — halting a whole recap over one invented token discards the valid remainder; strip-and-record keeps the output honest and the incident visible (`unverified_refs`) |
| Repair (fuzzy-match `FR-999` → nearest real id) | Rejected — `two_strike_split` allows repair "within a similarity floor," but invented FR ids have no meaningful similarity metric; silent repair risks a *plausible wrong answer*, the exact failure Commandment 6 names |

## Related

- `examples/demos/recap/nodes/partition.py`, `examples/demos/recap/graph.yaml` (read-only), `examples/demos/recap/prompts/recap.yaml` (read-only)
- `tests/unit/test_recap_demo.py`, `tests/integration/test_recap_demo_integration.py`
- REQ-YG-531, CAP-195
- FR-700, FR-702, FR-703, FR-704 (eviction lineage), FR-922 (gray-zone verdict this FR resolves), FR-923, FR-677
