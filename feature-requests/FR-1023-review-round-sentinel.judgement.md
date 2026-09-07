# Judgement: FR-1023 Review round sentinel — the third review is not a model call

**Prior art:** dispositioned in the parent FR header ([FR-1023](FR-1023-review-round-sentinel.md) — FR-1022, FR-960, FR-1004, FR-865; FR-1013 is the REJECTED witness incident, not a competing solution).

**Route:** `scripts/judge.sh` (Copilot backend, `gpt-5.6-sol`) on branch commit `bf7a85bc`, 2026-09-07, round 1 (the FR-1022 sentinel on this branch printed `round 1`). Promoted verbatim below the title; R-1…R-3 folded into the FR.


**Verdict:** APPROVED WITH REVISIONS — the wrapper-level cap and durable per-FR record are sound, but authority activates only after the operator fixes the sentinel text and doctrine choices, and the record format makes wrapper-authored headings mechanically distinguishable from model-authored review text.

**Reviewed against:** `feature-requests/FR-1023-review-round-sentinel.md`; `feature-requests/FR-1023.research.md`; `feature-requests/FR-1022-judge-round-sentinel.md`; `feature-requests/FR-960-claude-judge-variant.md`; `feature-requests/FR-1004-retire-outsider-ledger.md`; `feature-requests/FR-865-ramp-installer.md`; `feature-requests/FR-1013-chaplain-doctrine-sweep.md`; `scripts/review.sh`; `.github/skills/review-pr/doctrine.md`; `.github/skills/review-pr/adapters/README.md`; `.github/skills/review-pr/adapters/graph.yaml`; `.github/skills/review-pr/adapters/prompts/review.yaml`; `reference/command-book.md`; `capabilities/CAP-211-sole-route-judge-review.yaml`; `tests/unit/test_fr758_judge_review_wrappers.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem is witnessed rather than hypothetical. The current wrapper uses one transient `tmp/draft-review.md`, removes it on each normal run, and has no round state (`scripts/review.sh:12,26-43`); the command book likewise names only fix commits and PR dispositions as durable review evidence (`reference/command-book.md:56`). FR-1013 records the concrete failure mode: four judgement rounds and three review rounds turned a small documentation sweep into process work (`feature-requests/FR-1013-chaplain-doctrine-sweep.md:5`).

The selected boundary is appropriate. Counting before lock acquisition and model execution preserves the established wrapper pattern, while appending only after the existing artifact contract preserves failure semantics (`feature-requests/FR-1023-review-round-sentinel.md:109-117`; `scripts/review.sh:22-62`). Reusing CAP-211 and the existing FR-758 wrapper harness conforms before extending; the capability already owns the review wrapper, lock, re-entry, executor, and artifact contracts (`capabilities/CAP-211-sole-route-judge-review.yaml:1-29,75-98`).

The research is substantive enough to pass the prospective research gate. It preserves the failed persona, shows convergence on the wrapper-owned per-FR record and pre-model shell guard, preserves disagreement on the threshold, and answers `is_this_a_graph` (`feature-requests/FR-1023.research.md:9-18,39-44`). The FR dispositions explain why two rounds are selected and distinguish the relevant rejected and superseded precedents (`feature-requests/FR-1023-review-round-sentinel.md:19-38,233-262`).

| Criterion | Assessment |
|---|---|
| Scope | Minimal after revisions: one wrapper guard/append path plus directly coupled doctrine, mirror, traceability, tests, changelog, and diary. No graph or prompt edit is needed. |
| Consistency | Direction is coherent, but the claimed wrapper-only heading provenance conflicts with appending unrestricted model text, and Q-1 through Q-3 reopen choices presented elsewhere as decisions. R-1 and R-2 close these defects. |
| Measurability | AC-01 through AC-14 are mostly executable and name observable files, exit codes, bytes, markers, and commands. R-2 and R-3 replace the ambiguous body-heading case and synchronize the final operator-selected contract. |
| Feasibility | Workable with the existing Bash wrapper, artifact contract, CAP-211 registry, mirror test, and stubbed process harness. FR-1022 is an explicit dependency and remains a gate. |
| Architecture alignment | Correctly extends the sole-route wrapper at the process boundary, keeps doctrine in doctrine, leaves the review graph/prompt unchanged, and reuses CAP-211. |
| Single responsibility | One concern: terminate repeated review rounds using the durable record required to count them. Recording and stopping are causally inseparable here, not orthogonal features. |
| Strategic classification | **Contrib/example**: one witnessed incident class and the next review invocation are named, while the existing CAP-211 abstraction fits but lacks round persistence and termination. This is a repo-governance contribution to that primitive, not a new framework abstraction. |
| Testability | Direct failing tests can be derived for ordering, count, exact artifact, lock absence, executor absence, record immutability, contract failure, bypass attempts, mirror equality, and requirement coverage. |

## Required revisions

### R-1: Resolve the operator-owned choices before enforcement

Record the operator's answers to Q-1, Q-2, and Q-3 in the FR, then remove the provisional and alternative wording from the binding solution. In particular, replace the placeholder sentinel sentence everywhere with the exact operator-approved sentence and make the same choice agree across Summary, Proposed Solution, doctrine/documentation scope, acceptance criteria, and Questions for the human (`feature-requests/FR-1023-review-round-sentinel.md:54-61,166-180,200-220,281-292`). Update the status line from “research run in progress” because the committed research record already reports the completed four-of-five run (`feature-requests/FR-1023-review-round-sentinel.md:5,14-18`; `feature-requests/FR-1023.research.md:9-18`).

### R-2: Make heading provenance true at the append boundary

Change the proposed append format so unrestricted review text cannot create a line matching the wrapper heading grammar. Mechanically fold this by prefixing every appended artifact line with `> ` while leaving only the wrapper-generated `## Review round N — PR P — timestamp` line unquoted. Update the shell excerpt accordingly, for example by replacing `cat "$ARTIFACT"` with `sed 's/^/> /' "$ARTIFACT"`.

Then revise the claim at lines 148-151 and AC-01, AC-02, and AC-08 to specify the quoted body format. AC-08 must include a conforming draft whose body contains the exact string `## Review round 99 — PR 999 — 2026-01-01T00:00:00Z` at column zero; after append, a subsequent invocation must count only the real wrapper heading and report round 2. This closes the current contradiction: the FR calls appended drafts free text but claims an identical free-text line cannot match merely because it appeared “inside a body” (`feature-requests/FR-1023-review-round-sentinel.md:148-151,193-199,214-216`).

### R-3: Replace the acceptance criteria with the binding set below

Fold the revised criteria verbatim after resolving R-1's sentinel placeholder. This keeps the observable contract synchronized and gives the enforcer a direct RED suite rather than requiring interpretation.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/review.sh`: pre-lock round count, exit-77 sentinel, post-contract quoted record append, and round diagnostics |
| D-2 | `.github/skills/review-pr/doctrine.md`: one local review-discipline rule covering record, cap, exact sentinel, advisory status, input closure, and human exits |
| D-3 | `ramp/assets/tier2/github/skills/review-pr/doctrine.md`: byte-exact mirror of D-2 |
| D-4 | `.github/skills/review-pr/adapters/README.md`: operator-facing exit-77 and record documentation |
| D-5 | `reference/command-book.md`: entry 11 durable record and verification command |
| D-6 | `tests/unit/test_fr758_judge_review_wrappers.py`: REQ-YG-669 wrapper tests using the existing stub harness |
| D-7 | `capabilities/CAP-211-sole-route-judge-review.yaml` and generated `ARCHITECTURE.md`: REQ-YG-669 under CAP-211 |
| D-8 | `changelog/unreleased/` FR-1023 fragment |
| D-9 | `feature-requests/FR-1023-review-round-sentinel.md`: folded revisions, operator decisions, status, and implementation record |
| D-10 | One FR-1023 `docs/diary/` Distill entry containing `**Seed:**` |

Not authorized: edits to `.github/skills/review-pr/adapters/graph.yaml` or `.github/skills/review-pr/adapters/prompts/review.yaml`; a new capability; a second counter file; per-PR draft paths; prompt-level refusal; an override flag or environment variable; automatic commits, PR comments, merge decisions, FR rejection, or re-filing; changes to judge-round behavior; rewriting historical review or judgement records.

## Revised acceptance criteria

- [ ] AC-01: With no adjacent `.review.md`, the stubbed executor runs once, the wrapper exits 0, stderr contains `round 1`, and `<fr>.review.md` contains exactly one wrapper heading matching `^## Review round 1 — PR 123 — ` followed by the complete stub draft with every line prefixed by `> `.
- [ ] AC-02: With one recorded round, the executor runs once, exits 0, stderr contains `round 2`, and the record holds exactly two wrapper headings; every byte that existed before the run is unchanged.
- [ ] AC-03: With two recorded rounds, the wrapper exits 77; the executor marker and review lock are absent; `tmp/draft-review.md` consists exactly of the operator-approved sentinel line plus one newline; and `<fr>.review.md` is byte-identical to before the run.
- [ ] AC-04: Two recorded rounds carrying different PR numbers, 617 and 627, produce the AC-03 result, proving the count is per FR file.
- [ ] AC-05: With two recorded rounds and `REVIEW_EXECUTION=1`, the existing re-entry contract wins: exit 70, no sentinel artifact, no executor marker, no lock, and an unchanged record.
- [ ] AC-06: Missing-FR exit 66 and usage exit 64 win before round processing: no sentinel artifact, no executor marker, no lock, and no record write.
- [ ] AC-07: When the graph produces no artifact, an empty artifact, or a draft whose first line is not `**Merge verdict:**`, the wrapper exits 65 and appends nothing.
- [ ] AC-08: A conforming draft containing an exact apparent round heading at column zero in its body is recorded with that line prefixed by `> `; the next invocation counts only the wrapper heading and reports round 2. Indented, quoted, partial, and `**Merge verdict:**` body lines likewise do not increment the round.
- [ ] AC-09: Setting an otherwise unused `REVIEW_FORCE=1` or passing an extra `--force` argument does not alter the AC-03 result.
- [ ] AC-10: The doctrine rule, adapter README, and command-book entry 11 agree on the record format, two-round cap, exit 77, exact operator-approved sentinel, two human exits, and advisory status.
- [ ] AC-11: `tests/unit/test_ramp_installer.py::test_mirror_exact_entries_match_live_bytes` passes, and `git diff --exit-code <base> -- .github/skills/review-pr/adapters/graph.yaml .github/skills/review-pr/adapters/prompts/review.yaml` succeeds.
- [ ] AC-12: New tests live in `tests/unit/test_fr758_judge_review_wrappers.py`, each is tagged `@pytest.mark.req("REQ-YG-669")`, and the committed RED test precedes the GREEN implementation commit.
- [ ] AC-13: REQ-YG-669 appears under CAP-211 in both `ARCHITECTURE.md` and `capabilities/CAP-211-sole-route-judge-review.yaml`; `python scripts/req_coverage.py --strict` passes; and `pytest tests/unit/test_fr758_judge_review_wrappers.py -q --no-cov` passes without a real review graph.
- [ ] AC-14: The changelog fragment exists, and the FR-1023 diary entry contains `**Seed:**`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-3 are folded into the FR and its status cites this judgement; no implementation begins while the sentinel sentence or doctrine ownership remains provisional. | GATE |
| C-2 | FR-1022's exit-77 meaning, REQ-YG-668 placement under CAP-211, and judge-doctrine round-sentinel rule are present in the enforcement base. | GATE |
| C-3 | The RED commit proves both no-model execution at round 3 and exact-heading neutralization at the append boundary before the GREEN implementation commit. | GATE |
| C-4 | Review text is treated as untrusted input: only wrapper-emitted, unquoted headings may affect the count. | GATE |
| C-5 | The review graph and prompt remain byte-unchanged; any need to edit either requires a separately authored and judged FR. | GATE |
| C-6 | The live review doctrine and ramp mirror are byte-identical after the doctrine edit. | GATE |
| C-7 | Because D-1 through D-4 modify enforcement infrastructure, a human must review the folded FR and the implementation before merge. | GATE |

Authority granted: after C-1 and C-2 are satisfied, implement only D-1 through D-10 and only to satisfy AC-01 through AC-14; the resulting review remains advisory and the merge decision remains human.
