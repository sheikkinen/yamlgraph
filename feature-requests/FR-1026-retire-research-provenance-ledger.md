# Feature Request: Retire the research provenance ledger — the judge is the check, once

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Completed 2026-09-07 — judged REJECTED round 1; R-1/R-3 folded, R-2 refused; operator overrode on the R-2 ground ("re-research absolutely banned", then `enforce`) and granted authority for the frozen deletion set. Implementation record below.
**Effort:** 0.25 days
**Requested:** 2026-09-06
**First consumer / first event:** the next agent that corrects a research
brief after the FR has been judged. Today it discovers `--verify-promotion`
would say `mismatched` and re-runs five model calls to fix a hash (FR-1022,
2026-09-06, quoted under Problem). After this FR there is nothing to satisfy:
the brief is edited, the FR retracts the claim, done.
**Research:** [FR-1026.research.md](FR-1026.research.md) — brief
`feature-requests/research-briefs/research-provenance-ledger.md` (neutral
rewrite after FR-1025 R-1), run 2026-09-07T03:48Z, 4 of 5 personas; NOT unanimous —
two for outright deletion, one for deletion-plus-census-graph replacement,
one naming the gate-or-retire fork. Dispositioned under Alternatives.
**Prior art:** [FR-1025-retire-research-provenance-ledger.md](FR-1025-retire-research-provenance-ledger.md)
/ [judgement](FR-1025-retire-research-provenance-ledger.judgement.md) —
REJECTED 2026-09-06: same deletion, but its brief prescribed the outcome and
the research was a confirmation run. This FR distinguishes itself by the
neutral brief, a record that preserves disagreement, and R-2..R-4 folded
(committed witness quotes, exit-2 expectation, human-review and
implementation-record ACs). The deletion set is unchanged because no persona
in either run proposed keeping the verifier.
[FR-896-research-route-precedent-traceability.md](FR-896-research-route-precedent-traceability.md)
— installed the ledger against "research records are forgeable"; its
judgement C-4 limited the claim to hash consistency. This FR retires that
surface only; tool-slot binding, librarian grounding and the precedent block
stay.
[FR-890-research-sole-route-closed-input-alternatives.md](FR-890-research-sole-route-closed-input-alternatives.md)
— the sole route and the judge substance check; unchanged.
[FR-1004-retire-outsider-ledger.md](FR-1004-retire-outsider-ledger.md) — a
different ledger retired for write contention; shape precedent, no overlap.
[FR-895-census-synthesize-tail.md](FR-895-census-synthesize-tail.md),
[FR-940-census-judgement-normalization.md](FR-940-census-judgement-normalization.md)
— noun hits on "provenance"/"ledger" in the census family; unrelated
surfaces. Dismissed.

## Summary

Delete the SHA-256 provenance ledger around the research sole route:
`feature-requests/research-runs.jsonl`, the append block in
`scripts/research.sh`, `research_preflight.py --verify-promotion` and
`verify_promotion()`, their unit tests, and the clause in REQ-YG-623 /
CAP-248 that claims them. The research route, closed-brief preflight,
artifact schema check, prior-art block, failed-persona rows and the
promoted record's header (brief, run date, personas) are untouched. The
judge reading the promoted record for substance — once — is the check
FR-890 intended and the only one that survives.

## Value Statement

FR authors stop paying model calls to make an unenforced hash match, and the
tree stops carrying a file that nothing reads.

## Problem

`verify_promotion` is invoked by no hook, no CI step, and no script: the only
executable consumer is its own unit test on fixtures. `scripts/research.sh`
mentions the command once, in a comment ("Verify with: …"), and never runs
it (2026-09-07). A verifier nobody requires can only be *satisfied*, and
after any edit to a brief the only way to satisfy it is to re-run research.

Witness (committed in this FR's text because the source branch, PR #633, is
not on `main` at filing): on FR-1022 a judge revision asked for two evidence
bullets to be removed from the research brief. The author removed them, then
re-ran `scripts/research.sh` — five model calls — so the ledger would report
`matching`. Commit `16512c04` on that branch replaced
`feature-requests/FR-1022.research.md` and appended a second
`research-runs.jsonl` line for the same brief; the FR's `**Research:**` field
was rewritten to describe a run made *after* the judgement (`55cb4951`) that
approved the FR. The judge had read the first record. Operator, same day:
"clearly just for the show. some SHA acrobatics?" / "SHAs are acrobatics no
one asked for."

The threat FR-896 named — a hand-written record with no run behind it — is a
record the judge reads anyway; a hollow one dies there and a substantive one
is fine regardless of route. The ledger pins the bytes of a planning input
that judges and reviewers legitimately ask to change.

## Ideal Result

The research gate is exactly its intent: a committed research record exists,
the judge reads it for substance, once, and the FR dispositions it. No
artifact in the tree exists to be verified by a check that no gate runs, and
"the brief changed after the run" has a zero-cost answer: edit the brief,
retract in the FR.

## Proposed Solution

Deletion set (frozen):

| Surface | Change |
|---|---|
| `feature-requests/research-runs.jsonl` | `git rm` |
| `scripts/research.sh` | remove the "Provenance stamp" block (RUN_LOG, sha256(), BRIEF_SHA, ARTIFACT_SHA, CODE_SHA, printf, echo) |
| `scripts/research_preflight.py` | remove `verify_promotion()` and the `--verify-promotion` dispatcher branch; module docstring item 3 |
| `tests/unit/test_fr896_precedent_traceability.py` | remove `test_wrapper_appends_provenance_line` and `test_verify_promotion_matching_missing_mismatched`; docstring bullet "Provenance stamp" |
| `capabilities/CAP-248-research-sole-route.yaml` REQ-YG-623 | delete the clause "and appends an integrity provenance line … checkable via research_preflight.py --verify-promotion"; regenerate `ARCHITECTURE.md` |
| `changelog/unreleased/fr-1026-retire-research-ledger.md` | `type: removal` |
| `docs/diary/` | Distill entry |
| this FR | implementation record naming RED and GREEN commits (R-4) |

Witness tests (RED first) in `tests/unit/test_fr896_precedent_traceability.py`
under a new heading, tagged `REQ-YG-623`:

1. `scripts/research.sh` with a stub executor writing a valid artifact
   exits 0 and creates no `feature-requests/research-runs.jsonl`.
2. `research_preflight.py --verify-promotion x y` exits 2 with the generic
   usage message (the retired branch falls through to the one-path brief
   dispatcher, which rejects three arguments — R-3; no new branch is added
   to preserve a retired flag's exit code).
3. `verify_promotion` is not an attribute of the module.
4. `git ls-files feature-requests/research-runs.jsonl` is empty.

## Acceptance Criteria

- [x] AC-1 `feature-requests/research-runs.jsonl` is not tracked.
- [x] AC-2a `grep -rn 'verify_promotion\|verify-promotion\|research-runs.jsonl\|brief_sha256\|artifact_sha256' scripts capabilities .github reference ARCHITECTURE.md` returns no hits (no active implementation, contract, or instruction references; historical FRs, judgements, evidence files, diaries and released changelogs are the record and are excluded).
- [x] AC-2b `test_wrapper_appends_provenance_line` and `test_verify_promotion_matching_missing_mismatched` are absent from `tests/unit/test_fr896_precedent_traceability.py`.
- [x] AC-2c The retirement witnesses (tests 1–4 above) are present in that file and pass; they are permitted to name the retired identifiers — their execution, not a zero-hit text search, proves the retirement.
- [x] AC-3 `scripts/research.sh` still exits 65 on a schema-invalid artifact and 0 on a valid one (existing tests green).
- [x] AC-4 Witness tests 1–4 pass; the RED commit precedes the GREEN commit in `git log`.
- [x] AC-5 REQ-YG-623 text no longer claims the ledger; `python scripts/req_coverage.py --strict` passes; `ARCHITECTURE.md` regenerated.
- [x] AC-6 `pytest tests/unit/test_fr896_precedent_traceability.py tests/unit/test_fr890_research_route.py -q --no-cov` green.
- [x] AC-7 Changelog fragment `type: removal`; diary entry with `**Seed:**`.
- [x] AC-8 No replacement gate, flag, census graph, or "record only" variant of the ledger is introduced.
- [x] AC-9 This FR carries an implementation record naming the RED and GREEN commit SHAs and any decisions (R-4b).
- [x] AC-10 A named human has reviewed the enforcement-infrastructure diff before the FR is marked Completed; the reviewer and date are recorded in the implementation record (R-4a).

## Alternatives Considered

- **Enforce the hash check** (pre-commit on `*.research.md`; librarian's
  "gate" branch) — rejected: mandates the FR-1022 re-run for every brief
  correction; pins mutable planning input; the judge already checks the
  property that matters.
- **Retire hash-pinning, replace with a read-only census graph over research
  runs** (yamlgraph_native) — rejected for now: names no reader. The judge
  reads the promoted record; nothing in the pipeline consumes a cross-run
  census. If a reader appears (e.g. a research-route quality census), that
  is its own FR with its own first consumer; AC-8 forbids building it here.
- **Keep the run log minus hashes** (timestamp, `code_git_sha`) — rejected:
  no reader; the promoted record's header carries run date and personas.
  The `artifact_carries_code_identity` seed loses its one implementation;
  the seed is about *measurement* artifacts and this was never one.
- **Keep `verify_promotion` as an optional tool** — rejected: this is the
  current state and the theatre generator.
- **Make the brief immutable after research** — rejected: the brief is a
  planning document; the FR is where claims are retracted.

## Related

- `scripts/research.sh`, `scripts/research_preflight.py`,
  `tests/unit/test_fr896_precedent_traceability.py`,
  `capabilities/CAP-248-research-sole-route.yaml`
- FR-1022 / PR #633 (incident; branch `featjudge-round-sentinel`)

## Judgement (2026-09-07, round 1)

**Verdict:** REJECTED — full text in
[FR-1026-retire-research-provenance-ledger.judgement.md](FR-1026-retire-research-provenance-ledger.judgement.md)
(sole route, `scripts/judge.sh`, backend copilot). The deletion itself was
not contested ("narrow, feasible, and well motivated"; scope frozen as filed).

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | grep claim off by one comment hit; stale ledger line count; research date is 2026-09-07 UTC | Folded in FR and brief. The brief edit makes `verify_promotion` report `mismatched` for this brief — by design; the record is not re-run (see R-2) |
| R-2 | Research record has 3 solution classes; doctrine requires 4–6; re-run the route | **Refused.** Operator ruling 2026-09-07: re-research banned. Three classes is the true size of the alternative space for a subtraction FR; the record preserves the real disagreement (delete / delete+census / gate-or-retire). A third run to reach a fourth class would be the FR-1022 dance this FR exists to end. The 4–6-class rule's fit to subtraction FRs is a doctrine question for a separate FR |
| R-3 | AC-2 (zero grep hits in `tests`) contradicts AC-4 (witnesses name the identifiers) | Folded: AC-2a/2b/2c |

**Purge list:** none beyond the frozen deletion set.

**Scope frozen:** the deletion table under Proposed Solution, unchanged
across both judgements. Not authorized: any replacement gate, flag, census
graph, or run log; edits to the research graph, prompts, or reducer.

### Questions for the human (as options, or 'none')

1. **Disposition of this judgement.** Options: (a) operator overrides the
   REJECTED verdict on the R-2 ground and grants authority to enforce the
   frozen deletion set — *recommended*; (b) operator upholds; FR stays
   Rejected and the ledger stays. No third model round either way.

Operator answer (2026-09-07): (a) — "enforce".

## Implementation record (2026-09-07)

| Step | Witness |
|---|---|
| RED | `d675ae7d` — four REQ-YG-623 retirement witnesses appended to `tests/unit/test_fr896_precedent_traceability.py`; 4 failing; old positive tests left in place so the failure is honest |
| GREEN | `d2a6aa39` — `git rm feature-requests/research-runs.jsonl`; SHA append block removed from `scripts/research.sh`; `verify_promotion()` + `--verify-promotion` branch + dead `hashlib` import removed from `scripts/research_preflight.py`; two positive ledger tests removed; REQ-YG-623 clause amended and FR-1026 added to CAP-248 `fr:`; `ARCHITECTURE.md` regenerated. 7 files, +23/−176 |
| AC-2a | `grep -rn '…' scripts capabilities .github reference ARCHITECTURE.md --exclude-dir=logs` → 0 (the gitignored hook audit log records this session's own greps and is not a reference) |
| AC-3/6 | `pytest tests/unit/test_fr896_precedent_traceability.py tests/unit/test_fr890_research_route.py -q --no-cov` → 50 passed |
| AC-5 | `python scripts/req_coverage.py --strict` → 0 |
| AC-10 | Human review: operator (Sami Heikkinen), 2026-09-07. Pre-implementation: the `enforce` verdict on the folded FR after the REJECTED model round. Diff review: the operator's merge decision on PR #636 is the named human review of the enforcement-infrastructure diff (review P2); this row is satisfied by that merge, not before it |
| Review #636 | Sole route, 2026-09-07: Not approved on three grounds. P1 — REJECTED judgement grants no authority: operator override recorded above; the reviewer cannot see operator rulings by design. P2 — folded (this row). P3 — `docs/diary/2026-09-07-git-report.md`, a truncated model response imported into the branch by the `diary import` pre-commit hook, removed from the PR |
| Distill | `docs/diary/2026-09-07-reflection-fr-1026-two-shape-gates-on-one-route.md` |

Decisions: the CAP-248 retirement note names "the FR-896 SHA-256 provenance
ledger and its verifier" rather than the flag, so AC-2a's grep is literally
zero without a carve-out. The `changelog-req-cross-wiring` gate required
FR-1026 in CAP-248's `fr:` list (as FR-1022 was added to CAP-211). The
brief edited under R-1 was not re-run; its record header states the
disagreement the judge asked for.
