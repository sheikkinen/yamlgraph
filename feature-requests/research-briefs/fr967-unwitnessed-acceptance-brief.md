# Problem brief: FR-962 shipped a demo with zero tests and a self-asserted enforcement claim

**Prior art:** FR-962
(`feature-requests/FR-962-person-profile-census-authored-prs.md`) is the
parent whose acceptance criteria went unmet; this brief concerns the
enforcement hole that let it merge, not the census feature itself.
FR-206 (`feature-requests/FR-206-demo-proof-gate.md`, Implemented)
established the demo-proof gate that requires a `demo-output.log` for a
demo directory with staged changes — the FR-962 demo carries one, so
that gate passed while the demo remained untested; FR-206's shape check
is the floor this brief must distinguish itself from. FR-145
(`feature-requests/FR-145-phantom-requirement-detection.md`,
Implemented) detects requirement IDs claimed but never registered — the
same class of phantom claim, detected in the REQ registry rather than in
prose. FR-107
(`feature-requests/FR-107-req-architecture-cross-check.md`) cross-checks
the requirement registry against ARCHITECTURE.md. None of these observe
an unchecked acceptance criterion or a README asserting an enforcement
that does not exist. A REJECTED-FR sweep for acceptance-criteria and
merge-gate nouns found no prior proposal on unchecked-AC detection.

## Problem statement

FR-962 merged as PR #562 on 2026-09-02. Its 17 acceptance criteria
(`feature-requests/FR-962-person-profile-census-authored-prs.md:330-346`)
are all recorded as `- [ ]`, and the shipped artifact has no test of any
kind. Repository-wide, no file under `tests/` contains the strings
`person_profile_census`, `reduce_pr_ledger`, `PRLedgerRow`, or
`gh_authored_prs_discover`. The untested surface is
`examples/demos/person_profile_census/tools.py` (about 650 lines:
preflight, a Pydantic ledger row, a mechanical rollup, a canary gate, a
citation boundary) plus the shared PR adapters in
`examples/demos/corpus_census/adapters/corpus_adapters.py:168-300`. The
directly comparable sibling, FR-899's repo census, has
`tests/unit/test_fr899_repo_census.py`.

Ten of the seventeen criteria name a test explicitly ("a configuration
test fails on any other resolution", "a prompt-input test proves ...",
"tests prove no LLM output can add, remove, or alter mechanical
fields", "fixture tests assert exact values"). None of those tests
exists, and nothing in CI, pre-commit, or the review route observed
their absence. The FR-206 demo-proof gate passed because the demo
directory contains a `demo-output.log`; that gate checks that a demo
produced output, not that any claim about the demo is witnessed.

The gap then propagated into prose. The demo README asserted "The
committed sibling graph retains `provider: azure` and is enforced by
tests (FR-962 AC-07)" — a claim of enforcement whose subject does not
exist. Two further README statements were false against the tree it
described: it instructed the reader to create and later delete
`smoke_preflight.tool.yaml`, a file that is committed (deleting it
removes a tracked artifact), and it attributed the committed proofs to
a command whose `source` date disagreed with the `run.json` the proofs
carry. All three survived FR-962's judgement and its PR review.

Two defects in the shipped code were found on 2026-09-04 by manual
inspection and probing, four days after merge, not by any gate: the
unsatisfiable multi-value `visibility` conjunction (separate brief), and
run metadata that records `"azure_model": "unknown"` for the committed
public proofs, so the model attribution for the repository's own
evidence rests on prose rather than on the artifact.

The problem is not that one FR was under-tested. It is that the
repository has no mechanism connecting an acceptance criterion's
checkbox state to the merge decision: the criteria are prose in a
markdown file, the gates check artifact presence and format, and the
review route reads the diff against the FR without being required to
resolve each criterion. An FR can therefore claim seventeen witnessed
behaviours, ship zero, assert enforcement in its documentation, and
merge clean.

## Classification

enforcement/latency-critical — the missing thing is a gate at the merge
boundary and the tests it would demand; the detection path is
deterministic.

## Constraints

- The parent census feature's design is frozen by FR-962's judgement
  (R-1 through R-5, D-1 through D-8, C-1 through C-9). This brief may
  not redesign the graph, prompts, reducer, or ledger schema; it covers
  the missing witnesses and the enforcement hole only.
- Corp identifiers, endpoints, deployment names, and private repository
  names must not enter committed surfaces (FR-962 AC-16 locality audit);
  any test must use fixtures, never the live GitHub or Azure APIs.
- Any new gate must block at the merge boundary, not merely report:
  `detection_without_enforcement` — lint without a gate is advisory
  (Scripture).
- A gate that checks presence must also check substance
  (`gate_checks_shape_not_substance`); counting checked boxes is a shape
  check and would be satisfiable by editing the checkboxes.
- Retroactive application to the full FR corpus is out of bounds unless
  the corpus cost is estimated first (`map_reduce_the_corpus`, FR-965).
- `@pytest.mark.req("REQ-YG-XXX")` traceability and the CAP registry
  rules apply to every test added (ADR-001).

## Witnessed incidents

- 2026-09-04, this repository: an inspection of
  `examples/demos/person_profile_census/` found zero referencing tests,
  17 of 17 unchecked acceptance criteria on a merged FR, and a README
  asserting test enforcement of the Azure provider pin that no test
  performs.
- 2026-09-04, same inspection: the README's quickstart instructed
  deletion of the committed `smoke_preflight.tool.yaml`, and its proof
  provenance paragraph cited a `source` date (`2026-08-28`) that
  contradicts the committed `proofs/smoke-ledger.run.json`
  (`2026-08-25`). Both survived judgement and review.
- 2026-09-04, same inspection: `proofs/smoke-ledger.run.json` records
  `"azure_model": "unknown"` because the smoke path renames the state
  key, so the repository's own committed evidence cannot name the model
  that produced it — AC-13 required run metadata to record the model.
- 2026-09-02, PR #562: the FR-206 demo-proof gate, pre-commit, CI, and
  the review route all passed a change whose own acceptance criteria
  were entirely unchecked.
