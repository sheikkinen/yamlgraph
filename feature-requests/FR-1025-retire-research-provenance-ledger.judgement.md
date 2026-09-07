# Judgement: FR-1025 Retire the research provenance ledger — the judge is the check, once

**Prior art:** dispositioned in the parent FR header ([FR-1025](FR-1025-retire-research-provenance-ledger.md) — FR-896, FR-890, FR-1004, FR-1012, FR-504, FR-990, FR-1022).

**Route:** `scripts/judge.sh` (Copilot backend, `gpt-5.6-sol`), 2026-09-06. Promoted verbatim. REJECTED: brief was solution-contaminated; superseded by FR-1026 (neutral brief, fresh research, R-2..R-4 folded).

**Verdict:** REJECTED — the deletion is small and plausible, but the cited research is a solution-contaminated confirmation run rather than the substantive alternatives record required for authority; return to Plan, replace the research evidence, and re-enter judgement.

**Reviewed against:** `feature-requests/FR-1025-retire-research-provenance-ledger.md`; `feature-requests/FR-1025.research.md`; `feature-requests/research-briefs/retire-research-ledger.md`; `feature-requests/FR-896-research-route-precedent-traceability.md`; `feature-requests/FR-896-research-route-precedent-traceability.judgement.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.judgement.md`; `feature-requests/FR-1004-retire-outsider-ledger.md`; `feature-requests/FR-1012-chaplain-subtree-archive-and-removal.md`; `feature-requests/FR-504-retire-freetext-beat-fallback.md`; `feature-requests/FR-990-cap-journey-census.md`; historical committed artifacts `16512c04:feature-requests/FR-1022-judge-round-sentinel.md` and `16512c04:feature-requests/FR-1022.research.md`; historical committed artifact `15fc9164:docs/diary/2026-09-06-reflection-fr-1022-sha-acrobatics.md`; `scripts/research.sh`; `scripts/research_preflight.py`; `tests/unit/test_fr896_precedent_traceability.py`; `tests/unit/test_fr890_research_route.py`; `capabilities/CAP-248-research-sole-route.yaml`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`. The FR's direct links to `feature-requests/FR-1022-judge-round-sentinel.md` and `docs/diary/2026-09-06-reflection-fr-1022-sha-acrobatics.md` do not resolve in the current committed tree; the cited historical commits were consumed instead. Search-only reference checks also touched `docs/2026-09-04-research-durable-keyed-artifact-store.md`, `docs/2026-09-05-research-pi-agent-runtime.md`, `docs/diary/2026-08-30-reflection-fr-931-the-incumbent-signed-its-own-replacement.md`, and `docs/diary/diary-2026-08-30-the-cause-one-key-away.md`.

## What is sound

**Scope, single responsibility, and strategic classification:** the proposal is one coherent contrib/process-route subtraction, not a framework primitive and not a bundle. It names the exact ledger, producer, verifier, tests, requirement clause, generated architecture output, changelog, and diary surfaces while explicitly preserving the sole route, brief preflight, artifact verification, prior-art block, and promoted-record header (`feature-requests/FR-1025-retire-research-provenance-ledger.md:36-46`, `:71-83`). A smaller implementation would leave either dead code or a false active-contract claim, so the proposed deletion boundary is appropriately minimal.

**Feasibility and architecture alignment:** the removable behavior is isolated. The wrapper performs artifact verification before the provenance append, and the append occupies a self-contained block (`scripts/research.sh:62-82`); the verifier is a distinct function and CLI branch (`scripts/research_preflight.py:369-411`); and REQ-YG-623 states the same claim in one bounded clause (`capabilities/CAP-248-research-sole-route.yaml:42-48`). Removing those pieces while preserving `--verify-artifact` follows the repository's `detection_without_enforcement` and subtraction doctrines. FR-896 also deliberately limited this mechanism to same-actor hash consistency rather than execution proof (`feature-requests/FR-896-research-route-precedent-traceability.judgement.md:39-43`, `:86-89`), so FR-1025 is not silently discarding an attestation guarantee.

**Problem evidence:** the cited FR-1022 incident is real. The committed FR says its brief was corrected and the research route rerun solely to fold R-4 (`16512c04:feature-requests/FR-1022-judge-round-sentinel.md:83-85`, `:265-271`), and the diary records five model calls, replacement of the promoted record, and the resulting false answer to "what did the judge see?" (`15fc9164:docs/diary/2026-09-06-reflection-fr-1022-sha-acrobatics.md:3-27`). That establishes a concrete cost and failure mode rather than a hypothetical cleanup.

**Measurability and testability:** most implementation outcomes are direct assertions: the ledger is untracked, active references are absent, valid and invalid artifact behavior survives, REQ coverage passes, and the focused suites are green (`feature-requests/FR-1025-retire-research-provenance-ledger.md:85-103`). Those criteria can produce RED witnesses against the current append block and verifier.

## Required revisions

### R-1: Replace the solution-contaminated research evidence

Return to Plan and rewrite `feature-requests/research-briefs/retire-research-ledger.md` as a neutral problem brief before producing a replacement committed research record. Remove outcome-prescribing language, including "Adding the gate is the wrong direction" and "the deletion must retire..." (`feature-requests/research-briefs/retire-research-ledger.md:52-60`). Those statements decide the solution before the supposedly independent personas see the problem, violating the route's input-closure purpose (`feature-requests/FR-890-research-sole-route-closed-input-alternatives.md:65-79`).

The replacement record must contain 4–6 genuinely distinct solution classes, not five phrasings of deletion; preserve any disagreement rather than manufacturing unanimity; give every row an independently traceable precedent and an `is_this_a_graph` answer; and accurately attribute the librarian source. The current record announces unanimity before the table (`feature-requests/FR-1025.research.md:3-11`), then contains three subtraction rows, one schema-data deletion row, and one external-method argument for deletion, all with `verdict: pursue` (`feature-requests/FR-1025.research.md:27-33`). It therefore fails the local substance gate requiring genuine 4–6-class research rather than a shape-valid strawman (`.github/skills/judge-fr/doctrine.md:118-130`). The librarian row also attributes its claim to SLSA/CISA while citing neither a SLSA nor CISA source (`feature-requests/FR-1025.research.md:7-9`, `:33`); cite the claimed primary precedent or narrow the attribution to what the cited source actually establishes.

This revision requires a fresh judgement. Folding a new research record into this rejected judgement does not activate authority.

### R-2: Repair the committed evidence links

Replace the dangling links to `feature-requests/FR-1022-judge-round-sentinel.md` and `docs/diary/2026-09-06-reflection-fr-1022-sha-acrobatics.md` (`feature-requests/FR-1025-retire-research-provenance-ledger.md:32-34`, `:121-126`) with committed paths available in the proposal's base tree, or cite immutable commit-qualified artifacts and quote the exact incident lines in the FR. A judge must not need unrelated branch refs to recover the proposal's central witness.

### R-3: Correct the retired-option exit-code witness

Change the proposed `research_preflight.py --verify-promotion x y` expectation from exit 64 to exit 2 with the generic usage message, unless the FR explicitly authorizes a new unknown-option branch. After the dedicated branch is deleted, the existing dispatcher treats a three-argument invocation as invalid usage and returns 2 (`scripts/research_preflight.py:397-425`); exit 64 is reserved for a brief violation after a valid one-path invocation (`scripts/research_preflight.py:423-433`). Adding code solely to preserve exit 64 for a retired flag would contradict the no-replacement/minimal-deletion intent.

### R-4: Carry the human-review and implementation-record gates into the FR

Add acceptance criteria requiring (a) named human review of the research-enforcement deletion before it is treated as complete, as already required by the cited brief (`feature-requests/research-briefs/retire-research-ledger.md:61-63`), and (b) an FR implementation-status/decisions record naming the RED and GREEN commits. AC-7 currently requires only the changelog and diary (`feature-requests/FR-1025-retire-research-provenance-ledger.md:100-103`), omitting the repository's required source-of-truth update.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Neutral replacement brief at `feature-requests/research-briefs/retire-research-ledger.md` |
| D-2 | Substantive replacement record at `feature-requests/FR-1025.research.md` |
| D-3 | Revised FR with resolvable evidence, corrected CLI witness, human-review gate, and implementation-record criterion |

No implementation is authorized by this rejection. In particular, do not delete or edit `feature-requests/research-runs.jsonl`, `scripts/research.sh`, `scripts/research_preflight.py`, tests, CAP-248 / REQ-YG-623, or `ARCHITECTURE.md`; do not add a replacement ledger, gate, flag, or record-only variant; do not modify the research graph or prompts; and do not edit judge/review doctrine, hooks, CI, branch protection, or historical FR, judgement, research, diary, or released-changelog records. The code deletion may be frozen only by a fresh judgement after D-1 through D-3 are committed.

## Revised acceptance criteria

- [ ] AC-01: The replacement problem brief states the observed unwired-verifier behavior and mutable-input incident without prescribing deletion, enforcement, or any other solution.
- [ ] AC-02: The replacement committed research record presents 4–6 genuinely distinct solution classes, retains every generated disagreement, gives each row a traceable precedent and `is_this_a_graph` answer, and attributes the librarian claim to a source that actually supports it.
- [ ] AC-03: Every evidence link in FR-1025 resolves from the committed proposal base, or is an immutable commit-qualified citation with the relevant lines quoted in the FR.
- [ ] AC-04: A fresh judgement grants authority before any implementation edit.
- [ ] AC-05: `feature-requests/research-runs.jsonl` is not tracked after implementation.
- [ ] AC-06: `git grep -n -E 'verify_promotion|verify-promotion|research-runs\.jsonl|brief_sha256|artifact_sha256' -- scripts tests capabilities .github reference` returns no active implementation, contract, or instruction hit; historical FRs, judgements, research records, diaries, and released changelogs remain unchanged.
- [ ] AC-07: A stubbed valid `scripts/research.sh` run exits 0 and creates no `feature-requests/research-runs.jsonl`; a schema-invalid artifact still exits 65.
- [ ] AC-08: `research_preflight.py --verify-promotion x y` exits 2 with the generic usage message, and the imported module has no `verify_promotion` attribute.
- [ ] AC-09: `git ls-files feature-requests/research-runs.jsonl` is empty; the RED commit containing the retirement witnesses precedes the GREEN deletion commit.
- [ ] AC-10: REQ-YG-623 no longer claims provenance stamping or promotion verification; `ARCHITECTURE.md` is regenerated; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: `pytest tests/unit/test_fr896_precedent_traceability.py tests/unit/test_fr890_research_route.py -q --no-cov` passes.
- [ ] AC-12: The changelog fragment uses `type: removal`; the FR contains an implementation-status/decisions record citing RED and GREEN; the diary entry contains `**Seed:**`.
- [ ] AC-13: Named human review of the enforcement-surface deletion is recorded before completion.
- [ ] AC-14: No replacement gate, flag, ledger, or record-only provenance variant is introduced, and the sole route, closed-brief preflight, artifact schema check, prior-art block, failed-persona handling, and promoted-record header remain unchanged.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | FR-1025 remains rejected and grants no implementation authority; D-1 through D-3 must be committed and the proposal must re-enter the sole judge route. | GATE |
| C-2 | The replacement research must be generated from a neutral closed brief and satisfy the doctrine's substantive 4–6-class check; a shape-valid unanimity record is insufficient. | GATE |
| C-3 | Human review of the research-enforcement deletion must be recorded before the change is treated as complete. | GATE |
| C-4 | Any later implementation must preserve `check_brief`, `verify_artifact`, wrapper artifact verification, prior-art grounding, failed-persona handling, and promoted-record metadata. | GATE |
| C-5 | Historical records remain historical; cleanup is limited to active implementation, test, capability, generated architecture, changelog, FR implementation record, and diary surfaces authorized by a future judgement. | GATE |
| C-6 | No graph or prompt modification, new provenance mechanism, judge/review doctrine change, hook, CI gate, or branch-policy change is authorized. | GATE |

Authority granted: none; only the planning-artifact repairs D-1 through D-3 may proceed before FR-1025 is judged again.
