# Judgement: FR-1026 Retire the research provenance ledger — the judge is the check, once

**Prior art:** dispositioned in the parent FR header ([FR-1026](FR-1026-retire-research-provenance-ledger.md) — FR-1025 REJECTED, FR-896, FR-890, FR-1004, FR-895, FR-940).

**Route:** `scripts/judge.sh` (Copilot backend, `gpt-5.6-sol`), 2026-09-07. Promoted verbatim. R-1, R-3 folded; R-2 refused by operator ruling (re-research banned) — see the FR Judgement table. No re-judge.

**Verdict:** REJECTED — the deletion is narrow, feasible, and well motivated, but the replacement research record still fails the binding 4–6-class substance gate and the FR contains factual and acceptance-test contradictions; no implementation authority exists until those planning defects are corrected and a fresh judgement is rendered.

**Reviewed against:** `feature-requests/FR-1026-retire-research-provenance-ledger.md`; `feature-requests/FR-1026.research.md`; `feature-requests/research-briefs/research-provenance-ledger.md`; `feature-requests/FR-1025-retire-research-provenance-ledger.md`; `feature-requests/FR-1025-retire-research-provenance-ledger.judgement.md`; `feature-requests/FR-896-research-route-precedent-traceability.md`; `feature-requests/FR-896-research-route-precedent-traceability.judgement.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.judgement.md`; `feature-requests/FR-1004-retire-outsider-ledger.md`; `feature-requests/FR-895-census-synthesize-tail.md`; `feature-requests/FR-940-census-judgement-normalization.md`; historical committed artifacts `16512c04:feature-requests/FR-1022-judge-round-sentinel.md`, `16512c04:feature-requests/FR-1022.research.md`, and `16512c04:feature-requests/research-runs.jsonl`; historical committed artifact `55cb4951:feature-requests/FR-1022-judge-round-sentinel.judgement.md`; `feature-requests/research-runs.jsonl`; `scripts/research.sh`; `scripts/research_preflight.py`; `tests/unit/test_fr896_precedent_traceability.py`; `tests/unit/test_fr890_research_route.py`; `capabilities/CAP-248-research-sole-route.yaml`; `ARCHITECTURE.md`; committed-tree reference searches over `.pre-commit-config.yaml`, `.github/workflows/**`, `.github/hooks/**`, and `scripts/*.sh`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

## What is sound

**Scope and single responsibility:** the proposal is one coherent process-route subtraction. It names the ledger, producer block, verifier function and dispatcher, positive tests, active capability clause, generated architecture output, changelog, implementation record, and diary while preserving the sole route, brief preflight, artifact verification, prior-art grounding, failed-persona handling, and promoted-record header (`feature-requests/FR-1026-retire-research-provenance-ledger.md:42-50`, `:92-103`, `:126-128`). A smaller deletion would leave either dead implementation or a false active-contract claim.

**Feasibility:** the removable behavior is isolated after artifact verification in one wrapper block (`scripts/research.sh:66-84`), one function and dispatcher branch (`scripts/research_preflight.py:369-425`), two bounded positive tests (`tests/unit/test_fr896_precedent_traceability.py:374-437`), and one requirement clause (`capabilities/CAP-248-research-sole-route.yaml:42-53`). The proposed retired-option witness is accurate: after the dedicated branch is removed, three arguments reach the generic one-path dispatcher and return 2 (`scripts/research_preflight.py:397-425`).

**Architecture alignment and strategic classification:** this is a contrib/process-route cleanup, not a framework primitive or a new graph. Removing an unwired verifier and its claim follows `detection_without_enforcement`, while deleting the unused artifact follows `growth_as_default` and the purge rule (`.github/copilot-instructions.md:85`, `:153`, `:199-211`). The census replacement is correctly rejected because it has no named reader (`feature-requests/FR-1026-retire-research-provenance-ledger.md:136-144`), and the proposal does not bundle that separate capability.

**Problem evidence and prior art:** the incident is concrete. FR-1022 records that its brief was corrected and the route rerun (`16512c04:feature-requests/FR-1022-judge-round-sentinel.md:83-85`, `:265-271`), while the ledger contains two entries for that brief with different brief, artifact, and code hashes (`16512c04:feature-requests/research-runs.jsonl:35-36`). FR-1026 also distinguishes the rejected FR-1025, preserves FR-890's substance check, and limits the reversal of FR-896 to the integrity ledger (`feature-requests/FR-1026-retire-research-provenance-ledger.md:18-38`). FR-896 itself narrowed the ledger to same-actor hash consistency rather than execution proof (`feature-requests/FR-896-research-route-precedent-traceability.judgement.md:39-43`).

**Measurability and testability:** the intended implementation outcomes are directly testable: no tracked ledger, no producer side effect, generic rejection of the retired flag, no imported verifier, preserved artifact exit taxonomy, updated requirement text, focused suites, and RED-before-GREEN history (`feature-requests/FR-1026-retire-research-provenance-ledger.md:105-128`). The tests can fail against the current append block and verifier rather than because of absent fixtures or imports. The conflict in AC-2 is mechanical to repair under R-3.

**Consistency:** Summary, Ideal Result, deletion table, and Alternatives consistently choose complete retirement without replacement (`feature-requests/FR-1026-retire-research-provenance-ledger.md:42-50`, `:82-103`, `:130-148`). The remaining inconsistencies are evidence and criterion defects, not evidence that the implementation direction should be split.

## Required revisions

### R-1: Correct the committed premise before producing replacement research

Correct both the FR and `feature-requests/research-briefs/research-provenance-ledger.md` so they report the committed evidence exactly.

- Replace the claim that `grep -rn 'verify-promotion\|verify_promotion' .pre-commit-config.yaml .github/workflows .github/hooks scripts/*.sh` returns no hits (`feature-requests/FR-1026-retire-research-provenance-ledger.md:59-62`; `feature-requests/research-briefs/research-provenance-ledger.md:26-31`). The committed search has one explanatory hit in `scripts/research.sh:73`. State the narrower supported claim: there is no invocation from a hook, workflow, or script; the shell wrapper only documents the optional command, and the verifier's executable consumer is its test.
- Remove the stale exact ledger length or update it from committed state. The FR and brief say 34 lines (`feature-requests/FR-1026-retire-research-provenance-ledger.md:54-55`; `feature-requests/research-briefs/research-provenance-ledger.md:30-31`), while the judged committed ledger has 36 lines. The count is not needed to establish the problem and will change when research runs append.
- Correct the FR's research run date from 2026-09-06 to the record's 2026-09-07 UTC date (`feature-requests/FR-1026-retire-research-provenance-ledger.md:13-17`; `feature-requests/FR-1026.research.md:18-20`).

These are factual corrections to the research input. Make them before the replacement run required by R-2 so the new record does not inherit a premise known to be false.

### R-2: Replace the record with substantive 4–6-class research

Run the corrected neutral brief through the research route and replace `feature-requests/FR-1026.research.md` with a committed record containing 4–6 genuinely distinct, concrete solution classes. Preserve every valid disagreement, and give every counted row a traceable precedent, one unambiguous `is_this_a_graph` answer, effort/risk, and rationale. If a persona fails schema validation, preserve the failed-persona row as required, but do not count prose embedded in that error as a completed alternative.

The current table has four valid rows but only three classes: two convergent subtraction rows, one graph-pipeline row, and one external-method row (`feature-requests/FR-1026.research.md:31-36`). The external row is itself an unresolved "gate or retire" fork, not one concrete candidate, and the graph row says both to retire the ledger and to read `research-runs.jsonl`, the artifact it proposes retiring (`feature-requests/FR-1026.research.md:34`, `:36`). The failed data/process output hints at a partial-hash option but lacks the required table fields and cannot supply the missing class (`feature-requests/FR-1026.research.md:7-9`, `:22`). This does not satisfy the local 4–6-class substance rule (`.github/skills/judge-fr/doctrine.md:118-128`) or FR-1025 R-1, which explicitly required 4–6 genuinely distinct classes before re-entry (`feature-requests/FR-1025-retire-research-provenance-ledger.judgement.md:23-29`, `:55-58`).

Repair the promoted header as part of replacement: `personas executed` must contain persona names, not model-authored candidate prose (`feature-requests/FR-1026.research.md:18-22`). Do not modify the research graph, prompts, reducer, or failed-persona policy under this FR merely to obtain a passing record.

### R-3: Make the absence criterion compatible with the retirement witnesses

Rewrite AC-2 so it does not require zero matches in `tests`. Witnesses 2–4 intentionally name `--verify-promotion`, `verify_promotion`, and `research-runs.jsonl` (`feature-requests/FR-1026-retire-research-provenance-ledger.md:105-120`), so the current AC-2 cannot be true at the same time as AC-4.

Use separate checks:

1. Require no active implementation, contract, or instruction references under `scripts`, `capabilities`, `.github`, `reference`, and `ARCHITECTURE.md`.
2. Require the old positive test functions `test_wrapper_appends_provenance_line` and `test_verify_promotion_matching_missing_mismatched` to be absent.
3. Permit the new retirement witnesses in `tests/unit/test_fr896_precedent_traceability.py`; their focused execution, not a zero-hit text search, proves the retired behavior.

After R-1 through R-3 are folded and committed, re-enter judgement. Folding them into this rejected draft does not activate implementation authority.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Factual corrections in `feature-requests/research-briefs/research-provenance-ledger.md` and the FR's research/evidence statements |
| D-2 | Substantive replacement `feature-requests/FR-1026.research.md` with 4–6 concrete solution classes and a clean promoted header |
| D-3 | Revised FR acceptance criteria separating active-reference removal from intentional retirement witnesses |

No implementation is authorized by this rejection. In particular, do not delete or edit `feature-requests/research-runs.jsonl`, `scripts/research.sh`, `scripts/research_preflight.py`, tests, CAP-248 / REQ-YG-623, or `ARCHITECTURE.md`; do not add a replacement ledger, gate, flag, census graph, or record-only variant; do not modify research graph or prompt artifacts, the research reducer, persona failure handling, judge/review doctrine, hooks, CI, branch protection, or historical FR, judgement, research, diary, and released-changelog records. A normal research-route run needed for D-2 may append its ordinary planning record; that does not authorize the proposed deletion.

## Revised acceptance criteria

- [ ] AC-01: The FR and problem brief accurately state that the committed caller search has one explanatory `scripts/research.sh` hit but no hook, workflow, or script invocation of `--verify-promotion`; neither artifact makes a stale exact ledger-line-count claim.
- [ ] AC-02: The FR's `**Research:**` field reports the replacement record's actual UTC run date and executed/failed persona count.
- [ ] AC-03: The replacement committed research record contains 4–6 genuinely distinct, concrete solution classes; every counted row has a traceable precedent, one `is_this_a_graph` answer, effort/risk, and rationale; disagreement and failed-persona evidence are preserved; the promoted header contains only valid metadata.
- [ ] AC-04: A fresh judgement grants authority before any implementation edit.
- [ ] AC-05: `feature-requests/research-runs.jsonl` is not tracked after implementation.
- [ ] AC-06: `git grep -n -E 'verify_promotion|verify-promotion|research-runs\.jsonl|brief_sha256|artifact_sha256' -- scripts capabilities .github reference ARCHITECTURE.md` returns no active implementation, contract, or instruction hit; `git grep -n -E 'test_wrapper_appends_provenance_line|test_verify_promotion_matching_missing_mismatched' -- tests` returns no hit. Historical FRs, judgements, research records, diaries, released changelogs, and the new retirement witnesses remain unchanged by this search rule.
- [ ] AC-07: A stubbed valid `scripts/research.sh` run exits 0 and creates no `feature-requests/research-runs.jsonl`; a schema-invalid artifact still exits 65.
- [ ] AC-08: `research_preflight.py --verify-promotion x y` exits 2 with the generic usage message, and the imported module has no `verify_promotion` attribute.
- [ ] AC-09: `git ls-files feature-requests/research-runs.jsonl` is empty; every new witness test is tagged `REQ-YG-623`; the RED commit containing the retirement witnesses precedes the GREEN deletion commit.
- [ ] AC-10: REQ-YG-623 no longer claims provenance stamping or promotion verification; `ARCHITECTURE.md` is regenerated; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: `pytest tests/unit/test_fr896_precedent_traceability.py tests/unit/test_fr890_research_route.py -q --no-cov` passes.
- [ ] AC-12: The changelog fragment uses `type: removal`; the FR contains an implementation-status/decisions record naming RED and GREEN commits; the diary entry contains `**Seed:**`.
- [ ] AC-13: A named human and review date are recorded in the implementation record before the enforcement-surface deletion is marked Completed.
- [ ] AC-14: No replacement gate, flag, ledger, census graph, or record-only provenance variant is introduced; the sole route, closed-brief preflight, artifact schema check, prior-art block, failed-persona handling, and promoted-record metadata remain unchanged.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | FR-1026 remains rejected and grants no implementation authority; D-1 through D-3 must be committed and the proposal must receive a fresh judgement. | GATE |
| C-2 | The replacement research must come from the corrected neutral brief and satisfy the Judge's substantive 4–6-class check; four rows containing duplicate deletion advice and an unresolved fork are insufficient. | GATE |
| C-3 | Any later implementation must preserve `check_brief`, `verify_artifact`, wrapper artifact verification, prior-art grounding, failed-persona handling, and promoted-record metadata. | GATE |
| C-4 | Named human review of the research-enforcement deletion must be recorded before the FR is marked Completed. | GATE |
| C-5 | Historical records remain historical; cleanup is limited to active implementation, tests, capability text, generated architecture, changelog, FR implementation record, and diary surfaces authorized by a future judgement. | GATE |
| C-6 | No graph or prompt modification, research-route repair, new provenance mechanism, judge/review doctrine change, hook, CI gate, or branch-policy change is authorized. | GATE |

Authority granted: none; only the planning-artifact repairs D-1 through D-3 may proceed before FR-1026 is judged again.
