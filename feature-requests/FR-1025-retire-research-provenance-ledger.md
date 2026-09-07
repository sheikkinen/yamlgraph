# Feature Request: Retire the research provenance ledger — the judge is the check, once

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.25 days
**Requested:** 2026-09-06
**First consumer / first event:** the next agent that corrects a research
brief after the FR has been judged. Today it discovers `--verify-promotion`
would say `mismatched` and re-runs five model calls to fix a hash (FR-1022,
2026-09-06). After this FR there is nothing to satisfy: the brief is edited,
the FR retracts the claim, done.
**Research:** [FR-1025.research.md](FR-1025.research.md) — brief
`feature-requests/research-briefs/retire-research-ledger.md`, run
2026-09-06, 5 of 5 personas, unanimous on deletion; librarian's external
precedent (SLSA/CISA: unenforced provenance verification is decorative).
**Prior art:** [FR-896-research-route-precedent-traceability.md](FR-896-research-route-precedent-traceability.md)
— installed the ledger against "research records are forgeable"; its judgement
C-4 already limited the claim to hash consistency, not proof of run. This FR
retires that surface and nothing else FR-896 delivered (tool-slot binding,
librarian grounding, precedent block stay).
[FR-890-research-sole-route-closed-input-alternatives.md](FR-890-research-sole-route-closed-input-alternatives.md)
— the research sole route and the judge substance check; unchanged.
[FR-1004-retire-outsider-ledger.md](FR-1004-retire-outsider-ledger.md) —
retrieval hit on "retire ledger"; a different ledger (outsider runs, write
contention) with a different reason; shape precedent for a ledger
retirement FR, not overlapping.
[FR-1012-chaplain-subtree-archive-and-removal.md](FR-1012-chaplain-subtree-archive-and-removal.md),
[FR-504-retire-freetext-beat-fallback.md](FR-504-retire-freetext-beat-fallback.md),
[FR-990-cap-journey-census.md](FR-990-cap-journey-census.md) — noun hits on
"retire"/"research"; unrelated surfaces. Dismissed.
[FR-1022-judge-round-sentinel.md](FR-1022-judge-round-sentinel.md) — the
witnessed incident; PR #633 carries the re-run record. Not a competing
solution.

## Summary

Delete the SHA-256 provenance ledger around the research sole route:
`feature-requests/research-runs.jsonl`, the append block in
`scripts/research.sh`, `research_preflight.py --verify-promotion` and
`verify_promotion()`, their unit tests, and the sentence in REQ-YG-623 /
CAP-248 that claims them. The research route, closed-brief preflight,
artifact schema check, prior-art block, and the promoted record's own
header (brief, run date, personas) are untouched. The judge reading the
promoted record for substance — once — is the check FR-890 intended and the
only one that survives.

## Value Statement

FR authors stop paying model calls to make an unenforced hash match, and the
tree stops carrying a 34-line file that nothing reads.

## Problem

`verify_promotion` is called by no hook, no CI step, no script — only by its
own unit test on fixtures. A verifier nobody requires can only be
*satisfied*, and after any edit to a brief the only way to satisfy it is to
re-run research. On FR-1022 that produced a second record, cited in the FR
*after* the judge had read the first: the ledger's one purpose ("what did
the judge see?" by hash equality) was inverted by the act of satisfying it.
The forgery threat FR-896 named is covered by the judge, which reads the
record for substance; the ledger pins bytes of a planning input that
legitimately changes.

## Ideal Result

The research gate is exactly its intent: a committed research record exists,
the judge reads it for substance, once, and the FR dispositions it. No
artifact in the tree exists to be verified by a check that no gate runs.

## Proposed Solution

Deletion set (frozen):

| Surface | Change |
|---|---|
| `feature-requests/research-runs.jsonl` | `git rm` |
| `scripts/research.sh` | remove the "Provenance stamp" block (RUN_LOG, sha256(), BRIEF_SHA, ARTIFACT_SHA, CODE_SHA, printf, echo) |
| `scripts/research_preflight.py` | remove `verify_promotion()` and the `--verify-promotion` CLI branch; module docstring item 3 |
| `tests/unit/test_fr896_precedent_traceability.py` | remove `test_wrapper_appends_provenance_line` and `test_verify_promotion_matching_missing_mismatched`; docstring bullet "Provenance stamp" |
| `capabilities/CAP-248-research-sole-route.yaml` REQ-YG-623 | delete the clause "and appends an integrity provenance line … checkable via research_preflight.py --verify-promotion"; regenerate `ARCHITECTURE.md` |
| `changelog/unreleased/fr-1025-retire-research-ledger.md` | `type: removal` |
| `docs/diary/` | Distill entry |

Witness test (RED first), in `tests/unit/test_fr896_precedent_traceability.py`
under a new heading, tagged `REQ-YG-623`:

1. `scripts/research.sh` with a stub executor writing a valid artifact
   exits 0 and creates no `feature-requests/research-runs.jsonl`.
2. `research_preflight.py --verify-promotion x y` exits 64 (unknown usage)
   and `verify_promotion` is not an attribute of the module.
3. `git ls-files feature-requests/research-runs.jsonl` is empty.

## Acceptance Criteria

- [ ] AC-1 `feature-requests/research-runs.jsonl` is not tracked.
- [ ] AC-2 `grep -rn 'verify_promotion\|verify-promotion\|research-runs.jsonl\|brief_sha256\|artifact_sha256' scripts tests capabilities .github reference` returns no hits (historical FRs, judgements, evidence files, diaries and released changelogs excluded — they are the record).
- [ ] AC-3 `scripts/research.sh` still exits 65 on a schema-invalid artifact and 0 on a valid one (existing tests green).
- [ ] AC-4 The three witness tests above pass; RED commit precedes GREEN.
- [ ] AC-5 REQ-YG-623 text no longer claims the ledger; `python scripts/req_coverage.py --strict` passes; `ARCHITECTURE.md` regenerated.
- [ ] AC-6 `pytest tests/unit/test_fr896_precedent_traceability.py tests/unit/test_fr890_research_route.py -q --no-cov` green.
- [ ] AC-7 Changelog fragment `type: removal`; diary entry with `**Seed:**`.
- [ ] AC-8 No replacement gate, flag, or "record only" variant of the ledger is introduced.

## Alternatives Considered

- **Enforce the hash check instead** (pre-commit on `*.research.md`) —
  rejected: mandates the FR-1022 re-run dance for every brief correction;
  pins mutable planning input; the judge already checks the thing that
  matters.
- **Keep the run log minus hashes** (timestamp, code SHA) — rejected: no
  reader exists; a record without a reader is `growth_as_default` kept out
  of sentiment. The promoted record's header already carries run date and
  personas.
- **Keep `verify_promotion` as an optional tool** — rejected: this is the
  current state; an optional verifier is the theatre generator.
- **Make brief immutable after research** (refuse edits) — rejected: the
  brief is a planning document; the correct place to retract a claim is the
  FR, which is what the judge reads.

## Related

- `scripts/research.sh`, `scripts/research_preflight.py`,
  `tests/unit/test_fr896_precedent_traceability.py`,
  `capabilities/CAP-248-research-sole-route.yaml`
- `docs/diary/2026-09-06-reflection-fr-1022-sha-acrobatics.md`
