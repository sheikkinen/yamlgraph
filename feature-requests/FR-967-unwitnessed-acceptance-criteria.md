# Feature Request: witness FR-962's shipped behaviour and gate acceptance-criterion disposition at merge

**Priority:** HIGH
**Type:** Bug
**Status:** Halted — D-1 stopped at the third contract violation (AC-04)
**Effort:** 2 days
**Requested:** 2026-09-04
**First consumer / first event:** two, one per deliverable (judgement R-5).
D-1's consumer is **the maintainer enforcing FR-966**, who needs a
trustworthy test harness for `gh_authored_prs_discover` and finds none;
the event is that enforcement, dated 2026-09-04. D-2's consumer is **the
reviewer of the first FR-linked PR containing an invalid criterion
disposition**; the event is that PR's first CI run.
**Research:** [FR-967.research.md](FR-967.research.md)
**Prior art:** [FR-962-person-profile-census-authored-prs.md](FR-962-person-profile-census-authored-prs.md) — the parent whose criteria went unwitnessed; this FR does not reopen its frozen design. [CAP-116](../capabilities/CAP-116-acceptance-tests-before-enforce.yaml) "Acceptance Tests Before Enforce" — already requires acceptance tests before enforce, but only inside the **chaplain watcher FSM** (`.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/graphs/watcher-plan/...`); FR-962 was authored and enforced outside that runtime, so CAP-116's protocol never ran — this FR moves the same requirement to the merge boundary, where runtime does not matter. [FR-851-requirement-witness-audit.md](FR-851-requirement-witness-audit.md) (Enforced) — audits REQ→test→code triples in the requirement registry; FR-962's demo registered no REQ, so the audit is structurally blind to it, and acceptance criteria are not registry objects. [FR-206-demo-proof-gate.md](FR-206-demo-proof-gate.md) (Implemented) — requires a `demo-output.log` per changed demo directory; it passed on FR-962 because the log exists, which is precisely `gate_checks_shape_not_substance`. [FR-145-phantom-requirement-detection.md](FR-145-phantom-requirement-detection.md) (Implemented) — detects REQ IDs claimed but unregistered; the same phantom class, different registry. [FR-636-demo-coverage-gate.md](FR-636-demo-coverage-gate.md) (Judged — APPROVED, scope reduced) — surfaced by the prior-art gate and genuinely adjacent: also a coverage gate. Distinguished by subject: FR-636 runs curated demos under `coverage.py` to prove `yamlgraph/` **framework modules** are reachable, detecting dead core code. It reads module coverage, never an FR document, and reports nothing about an unchecked acceptance criterion. Complementary, no shared code. FR-777, FR-880, FR-949, FR-950 surfaced by IDF retrieval on the words "unwitnessed/acceptance/brief" — dismissed as vocabulary collisions (shell toolbelt manifests, memory curation, issue-queue delegation).

## Summary

FR-962 merged with all seventeen acceptance criteria unchecked and zero
tests; ten of those criteria name a test explicitly. Two defects and
three false README statements were found four days later by hand. Pay
the witness debt on the shipped surfaces (D-1), and add a merge-boundary
gate that requires every acceptance criterion to carry an explicit
disposition (D-2).

**The gate checks disposition, not truth.** It cannot tell whether a
checked box is true. What it removes is the *silent* zero: after this
FR, a criterion is either checked, or deferred in writing with a reason
visible in the diff. An author who checks a box falsely now tells a
deliberate lie in a reviewable artifact instead of shipping seventeen
unanswered questions that no gate ever reads.

## Value Statement

A reviewer opening an FR-linked PR sees an explicit disposition for
every acceptance criterion, because a criterion left blank at merge
blocks the merge. The reviewer still has to judge whether a checked
criterion is true — but they are now judging a claim, not an absence.

## Problem

`feature-requests/FR-962-person-profile-census-authored-prs.md:330-346`
records seventeen criteria, all `- [ ]`. PR #562 merged on 2026-09-02.
No file under `tests/` contains `person_profile_census`,
`reduce_pr_ledger`, `PRLedgerRow`, or `gh_authored_prs_discover`. The
untested surface is `examples/demos/person_profile_census/tools.py`
(~650 lines) plus `corpus_adapters.py:168-300`. The directly comparable
sibling has `tests/unit/test_fr899_repo_census.py`.

What the absent witnesses cost, measured 2026-09-04:

- A multi-value `visibility` list produces an unsatisfiable query and an
  always-empty population (FR-966). AC-02 claimed discovery validation.
- `proofs/smoke-ledger.run.json` records `"azure_model": "unknown"`, so
  the repository's own committed evidence cannot name the model that
  produced it. AC-13 required run metadata to record the model.
- The demo README asserted the Azure pin "is enforced by tests
  (FR-962 AC-07)" — an enforcement claim whose subject does not exist.
- The README instructed deletion of `smoke_preflight.tool.yaml`, a
  committed file, and attributed the proofs to a `source` date that
  contradicts the `run.json` beside them.

Every existing gate passed. FR-206's demo-proof gate saw a
`demo-output.log` and was satisfied. FR-851's witness audit reads the
REQ registry, which the demo never entered. CAP-116 requires acceptance
tests before enforce, but only within the chaplain watcher FSM, and this
FR was enforced outside it. Nothing in pre-commit, CI, or the review
route reads an acceptance-criterion checkbox. The criteria are prose;
the merge decision never consults them.

## Ideal Result

An acceptance criterion is never silently unanswered. At the moment a PR
merges, every criterion of every FR it names carries an explicit
disposition — checked, or deferred with a stated reason — and the merge
is blocked otherwise. FR-962's own seventeen criteria, retroactively,
are in one of those two states rather than seventeen silent zeros, and
the criteria that named a test are checked *because the test was
written*, not because a box was ticked.

The minimal path back from that end state has exactly two steps: pay
FR-962's witness debt (D-1), and make the disposition mandatory at the
merge boundary (D-2). Verifying that a checked box is *true* is a
strictly larger problem — it needs a machine-checkable relation from
criterion prose to committed test evidence, which this repository does
not have. It is named as the successor in Alternatives, not smuggled in
here.

## Proposed Solution

**D-1 — witness the shipped surfaces.** Add
`tests/unit/test_fr962_person_profile_census.py` and
`tests/unit/test_fr962_pr_adapters.py`, fixture-driven, no live GitHub
or Azure, covering the criteria that name a test: the Azure provider pin
resolving from `graph.yaml` (AC-07), the classify prompt receiving
neither rollup instructions nor the canary family (AC-08), `PRLedgerRow`
refusing LLM-supplied mechanical fields (AC-10), typed `row_failed`
containment versus batch abort (AC-11), rollup arithmetic from frozen
fixtures (AC-12), run-metadata exact values including model attribution
(AC-13), fabricated-URL rejection in the brief boundary (AC-14), the
canary gate's absent/miss/drift cases (AC-15), and the discovery/extract
validation surface (AC-02, AC-04).

These tests **enforce FR-962's frozen contract**; they do not
characterise whatever the code happens to do. Where the shipped code
violates that contract the test stays RED and the production code is
corrected. Two such corrections are already known and are the only ones
authorised here:

1. **AC-07 (Azure pin).** Presently a convention with no enforcement.
   The witness asserts every LLM node in the demo `graph.yaml` resolves
   to `azure`. No production change expected; if the graph violates it,
   the graph is corrected.
2. **AC-13 (run metadata records the model).** `reduce_pr_ledger` writes
   `azure_model` from state or `AZURE_MODEL`, defaulting to the string
   `"unknown"` — which is how `proofs/smoke-ledger.run.json` came to be
   unable to name the model that produced it. The witness requires a
   resolved model; the reduce boundary must raise rather than record
   `"unknown"`.

Any *third* contract violation discovered while writing these witnesses
halts the work and is reported, not absorbed. **`**Deferred:**` must not
be used to convert a failing frozen requirement into a success** — it is
for a criterion the repository consciously declines to answer, never for
one it has answered wrongly (judgement C-2).

**D-2 — the acceptance-criterion disposition gate.** A deterministic,
LLM-free CI check (`scripts/ac_disposition_gate.py`) that reads the FR
files named by a PR title at the PR head and fails when any acceptance
criterion carries no disposition. Its grammar and applicability are
frozen below (judgement R-4) so the gate's blast radius is a matter of
record rather than of implementation accident.

| question | frozen answer |
|---|---|
| which PRs must *carry* an FR ID | unchanged by this FR: `.github/workflows/commitlint.yml:52-59` mandates an FR ID for `feat` titles **only**. This FR adds no new obligation to carry one, and does not extend the mandate to `fix`. |
| which PRs the gate *runs on* | every PR, of every conventional-commit type. The gate is triggered by the presence of an FR ID in the title, not by the type. |
| zero FR IDs in the title | pass, with an explicit "no FR referenced" conclusion in the check output. Never skipped, so the required status context always resolves. |
| exactly one FR ID | resolve and evaluate it. |
| multiple FR IDs | resolve and evaluate **every** one; the gate fails if any single FR fails. No first-match shortcut. |
| FR file resolution | glob `feature-requests/FR-<NNN>-*.md`, excluding `*.judgement.md` and `*.research.md`. Exactly one match is required. |
| zero matches (missing, deleted, or renamed FR file) | **fail loudly**, naming the unresolved ID. Never a silent pass. |
| two or more matches | **fail loudly** as ambiguous, listing every candidate path. |
| acceptance-criteria section boundary | begins at a heading matching `^#{2,}\s+Acceptance Criteria\s*$` (case-insensitive); ends at the next heading of the same or shallower level, or EOF. A file with no such heading fails loudly. |
| checkbox syntax | `^\s*-\s\[[ xX]\]\s` inside that section. `- [x]` and `- [X]` are checked. |
| non-FR checkboxes | ignored. Only checkbox lines inside the resolved FR file's acceptance-criteria section are read; checkboxes elsewhere in the file, and in every other file, are out of scope. |
| `**Deferred:**` association | the annotation belongs to the nearest preceding checkbox line, on that line or on any continuation line before the next checkbox line or the end of the section. An annotation appearing before any checkbox belongs to nothing and is ignored. |
| deferral substance | at least 12 non-whitespace characters of reason must follow `**Deferred:**`. `**Deferred:** n/a` does not satisfy the gate (`substance_over_presence`). |
| CI events | `pull_request` **and** `merge_group`, so the required status context reaches a conclusion on both the PR and the merge queue and cannot become a permanently-pending block. |

Unchecked-and-undeferred blocks; checked passes; deferred-with-substance
passes and is visible in the diff.

Research disposition: four of five personas converged on a
merge-boundary gate (`boundary-enforcement`); `librarian` supplied the
external precedent (threshold-driven merge gates backed by
marker-traceable acceptance tests). The dissent is preserved and
partially adopted below.

## Acceptance Criteria

Folded 2026-09-04 against the judgement. D-1 commits before D-2.

**D-1 — witness debt**

- [ ] AC-01: `tests/unit/test_fr962_person_profile_census.py` and
  `tests/unit/test_fr962_pr_adapters.py` exist and cover, one test per
  criterion, FR-962 AC-02, AC-04, AC-07, AC-08, AC-10, AC-11, AC-12,
  AC-13, AC-14, AC-15; each test names in its docstring the criterion it
  witnesses.
- [ ] AC-02: No test in either file performs a network call — the `gh`
  and LLM boundaries are stubbed by a fail-if-called stub that raises on
  unexpected invocation.
- [ ] AC-03: The tests enforce FR-962's frozen contract rather than
  characterising current behaviour. The Azure-pin witness fails if any
  LLM node in `examples/demos/person_profile_census/graph.yaml` resolves
  to a provider other than `azure`; the run-metadata witness fails if
  `reduce_pr_ledger` records an unresolved model instead of raising.
- [ ] AC-04: Exactly the two production corrections enumerated in the
  Proposed Solution are made. A third contract violation halts the work
  and is reported in this FR; it is not absorbed and not deferred.
- [ ] AC-05: Every criterion in FR-962 is left either checked or
  annotated `**Deferred:** <reason>` with at least 12 non-whitespace
  characters of reason; none remains bare `- [ ]`. No criterion that the
  code fails is marked deferred.

**D-2 — disposition gate**

- [ ] AC-06: `scripts/ac_disposition_gate.py` implements the frozen
  grammar table verbatim and is LLM-free. Fixture FR files witness every
  row of that table: zero / one / multiple FR IDs in the title; zero,
  one and two file matches; a missing acceptance-criteria heading; `- [x]`
  and `- [X]`; a same-line deferral; a continuation-line deferral; a
  deferral preceding any checkbox; a deferral under 12 non-whitespace
  characters; a checkbox outside the section.
- [ ] AC-07: The gate fails loudly — naming the unresolved or ambiguous
  ID and listing candidate paths — and never silently passes, for a
  missing, deleted, renamed, or ambiguous FR file.
- [ ] AC-08: The gate runs on `pull_request` and `merge_group` and
  blocks the merge; a PR carrying no FR ID reaches a passing conclusion
  rather than being skipped, so the required status context always
  resolves.
- [ ] AC-09: A fixture reproducing FR-962 as merged (seventeen bare
  `- [ ]`) makes the gate exit non-zero.
- [ ] AC-10: This FR claims nowhere that a checked criterion is
  witnessed. The gate's name, help text, failure message, and CI check
  name all say *disposition*, not *witness*.

**Both**

- [ ] AC-11: Corp identifiers, endpoints, deployment names, and private
  repository names appear in no committed file added by this FR.
- [ ] AC-12: Every new test carries `@pytest.mark.req(...)`; CAP/REQ
  registry wiring added; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-13: Changelog fragment in `changelog/unreleased/`; diary entry
  in `docs/diary/` with a `Seed:`.
- [ ] AC-14: A human reviews and accepts the gate's semantics and CI
  blast radius before D-2 merges (judgement C-4). The frozen grammar
  table is the artifact under review.

## Judgement Fold — 2026-09-04

Verdict: **SPLIT**
([judgement](FR-967-unwitnessed-acceptance-criteria.judgement.md)),
authority granted: none.

**Deviation — the split is overridden by explicit human instruction**
("fold findings, no split", 2026-09-04). D-1 and D-2 remain one FR. The
record is kept here rather than argued away: the judge's reasoning — two
concerns, two consumers, two blast radii — stands unrefuted, and the
choice to carry them together is the operator's, not a rebuttal. Every
*substantive* revision is folded, and every condition except C-1 (which
the override displaces) is honoured. D-1 commits before D-2 so the two
concerns remain separable in `git log` even though they share an FR.

| revision | fold |
|---|---|
| R-1 extract the witness repair | Not extracted (override). Its substance is folded: the tests are declared to **enforce FR-962's frozen contract**, not characterise behaviour, and the only two authorised production corrections are enumerated. AC-04 halts on a third. |
| R-2 extract the merge-boundary policy | Not extracted (override). Its substance is folded: the policy is enforcement infrastructure, so AC-14 requires explicit human acceptance of the semantics and CI blast radius before it merges (C-4). |
| R-3 choose witness enforcement (A) or state-only disposition (B) | **B chosen** by the operator. The hybrid is removed: the FR no longer claims a checked box is witnessed. Title, Summary, Value Statement, gate name, and AC-10 all say *disposition*. Witness enforcement is named as the successor in Alternatives, not smuggled in. |
| R-4 freeze the grammar and applicability | Frozen as a thirteen-row table in the Proposed Solution, each row witnessed by a fixture (AC-06). **Corrected:** the draft's AC-07 said the gate resolves the FR ID "using the existing convention", which reads as though `fix` PRs must carry one. `.github/workflows/commitlint.yml:52-59` mandates an FR ID for `feat` **only**; the gate is triggered by an FR ID's presence, and adds no obligation to carry one. |
| R-5 one consumer per concern | Two named consumers in the header, one per deliverable. |

**Deferral discipline (C-2).** `**Deferred:**` records a criterion the
repository consciously declines to answer. It is never applied to a
criterion the code *fails* — that is a defect, and hiding it behind a
deferral would rebuild the exact hole this FR exists to close.

## Implementation Status — 2026-09-04

**Halted before any witness was written.** AC-04's stop rule fired.

The Proposed Solution authorised exactly two production corrections and
required that a third contract violation halt the work. The third was
found while dispositioning FR-962's criteria, before a single test file
was created, so no work was wasted and no scope was absorbed.

**Violation 3 — FR-962 AC-16's locality audit does not exist.** AC-16
froze "the locality audit scans all named committed person-profile
surfaces and rejects any other visibility, source, repository owner, or
output root". No such audit exists for this demo. The only locality
audit in the repository is `TestDataLocality` in
`tests/unit/test_fr899_repo_census.py`, scoped to `repo_census` through
its `PUBLIC_DEMO_ORG` constant; `person_profile_census` defines no
equivalent constant, test, or script. The remaining `locality` matches in
the tree belong to the unrelated `self-portrait` demo, where the word
means geography.

This is not merely an unwitnessed criterion. The demo README cited the
audit as an active control ("the FR-767 sentinel + the FR-962 locality
audit both refuse it"), the same phantom-enforcement class as the AC-07
"enforced by tests" claim. It also matters more than its size: an audit
over the committed person-profile surfaces is the control that would have
caught the FR-966 finding, where an Azure deployment name reached an
artifact bound for a public repository. AC-16 names "any other ... output
root"; a corp deployment identifier is exactly what such an audit
rejects.

**Operator disposition (2026-09-04): halt.** Neither the audit nor the
AC-07 configuration test was built. Instead the false claims were
retired: `examples/demos/person_profile_census/README.md` now states
that both mechanisms are documented intent rather than enforcement, and
names this FR as their successor. Retiring a phantom claim is always in
scope and strictly more truthful than leaving a reader believing a
control protects them.

**Nothing in D-1 or D-2 was implemented.** No test file was created; no
production code was changed; `scripts/ac_disposition_gate.py` does not
exist. Every acceptance criterion of this FR remains unchecked, which is
the honest state and — fittingly — precisely the condition D-2 exists to
make impossible.

What this FR did deliver, and what should not be re-derived:

- The measurement. FR-962 shipped seventeen criteria, ten naming a test,
  and zero tests, while its sibling `repo_census` shipped ~460 lines of
  witnesses over the same surfaces. Coverage tracked what was checked,
  not what was known.
- The gap analysis. Four existing gates were dispositioned and none
  covers this failure: the demo-proof gate checks a log's presence,
  FR-851's audit reads a registry the demo never entered, CAP-116 is
  scoped to the chaplain runtime, and nothing anywhere reads an
  acceptance-criterion checkbox.
- The frozen thirteen-row grammar table for the disposition gate, ready
  to implement verbatim.
- The evidence that the estimate was wrong. Two violations were forecast;
  a third arrived before any test was written. That is data about the
  defect density here, and any successor should budget for more.

Reflection: `docs/diary/diary-2026-09-04-the-tests-that-were-cited-but-never-written.md`.

## Alternatives Considered

| Candidate | Class | Verdict | Why |
|---|---|---|---|
| Disposition gate on criterion state, plus the missing witnesses (adopted) | boundary-enforcement | pursue | Blocks at the only place enforcement holds (`enforcement_at_merge_boundary`); deterministic, no LLM; claims only what it can check. |
| **Witness enforcement** — a machine-checkable relation from every checked criterion to committed test evidence | boundary-enforcement | **named successor**, deliberately not adopted | This is what the FR's title originally implied and what the judge recommended. It is the honest form of "an acceptance criterion is a promise the repository can collect on". It is not adopted because the relation does not exist: criterion prose is not linked to test identity anywhere in the repo, and inventing that link here would couple criterion text to test filenames — false-positive on naming drift, and silent on the majority of criteria witnessed by a test they do not name. D-1 is the experiment that shows whether the naming discipline is stable enough to support it. |
| Extend FR-851's requirement-witness audit to acceptance criteria | boundary-enforcement | rejected | FR-851 is an LLM batch audit over the REQ registry; acceptance criteria are not registry objects, and an audit reports where a gate must block (`audit_gate`). |
| Delete FR-962's seventeen criteria and retire the enforcement claims (subtractionist dissent) | boundary-enforcement | partially adopted | Correctly identifies that unwitnessed criteria are noise, and its README-claim retirement is already done. Rejected as the whole answer by its own author's reasoning: deletion leaves the hole open for the next FR. Its residue survives as the `**Deferred:**` annotation — a criterion may be honestly retired, but only in writing, with substance. |
| Rely on CAP-116 (acceptance tests before enforce) | — | rejected | Scoped to the chaplain watcher FSM; FR-962 was enforced outside it. Runtime-scoped enforcement cannot cover a runtime-independent failure. |

## Related

- `examples/demos/person_profile_census/` (untested surface)
- `examples/demos/corpus_census/adapters/corpus_adapters.py:168-300`
- [FR-966-visibility-conjunction-unsatisfiable.md](FR-966-visibility-conjunction-unsatisfiable.md) — the defect this absence let through; it fixes the bug, this FR closes the hole.
