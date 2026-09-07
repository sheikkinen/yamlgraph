# Problem brief: the research provenance ledger is verified by no one and edited into theatre

**Prior art:** FR-896 (added `feature-requests/research-runs.jsonl` with
brief/artifact SHA-256 and `research_preflight.py --verify-promotion`
against the threat "research records are forgeable"; its own judgement C-4
limited the claim to "hash consistency only, not proof of run, since the
log is committed by the same actor"); FR-890 (the research sole route and
the judge's substance check of the promoted record — the intent the ledger
was bolted onto); FR-1022 (the witnessed incident: a 5-line brief
correction after judgement led to a full research re-run so the hashes
would match); `docs/diary/2026-09-06-reflection-fr-1022-sha-acrobatics.md`
(`hash_over_witness`, `satisfy_over_argue`).

## Problem statement

FR-890's intent is one sentence: research happens before planning, and the
judge reads the promoted record for substance — once. FR-896 added a second
mechanism on top: `scripts/research.sh` appends a JSON line with the
brief's and artifact's SHA-256 to a committed ledger, and
`research_preflight.py --verify-promotion` recomputes them. The check is
wired to nothing — no pre-commit hook, no CI step, no test over real
records; only a unit test of the function itself. It can therefore never be
*required*, only *satisfied*, and the sole way to satisfy it after any
edit to a brief is to re-run the research route.

That is what happened on FR-1022: a judge revision asked for two evidence
bullets to be removed from the brief; the agent removed them, then spent
five model calls re-running research so the ledger would print `matching`.
The second run produced a different record; the FR was rewritten to cite
it. The judge had read the first. The ledger's one purpose — make "what did
the judge see?" answerable by hash equality — was inverted by the act of
satisfying it.

The threat the ledger defends against (an agent hand-writes a plausible
research record) is already covered by the judge, which reads the record
for substance: a hollow record dies there and a substantive one is fine
regardless of route. The ledger pins the bytes of the brief — a planning
input that legitimately changes — while the only thing anyone reads is the
record's content.

## Classification

enforcement/latency-critical

## Constraints

- The research sole route itself (FR-890), the closed-brief preflight, the
  artifact schema check (`--verify-artifact`), prior-art retrieval
  (FR-938), failed-persona demotion (FR-1005) and the record header
  (brief filename, run date, personas) are NOT in question; they check
  substance at the moment of use and the judge reads them.
- `detection_without_enforcement` (Scripture): lint without gate is
  advisory — add the gate or remove the claim. Adding the gate is the wrong
  direction: a hash gate on a mutable planning input would mandate the
  FR-1022 re-run dance for every brief correction.
- `growth_as_default` / `working_system_inertia`: a mature system benefits
  from pruning claims; the deletion must retire the requirement text, the
  capability description, the script code, the verifier, its unit tests,
  the committed ledger file, and every doctrine/skill sentence that tells
  an author to run the verifier.
- Historical FRs and judgements that cite `research-runs.jsonl` are the
  record and stay as written.
- Enforcement-infrastructure change: human review is a GATE.

## Witnessed incidents

- 2026-09-06, PR #633 / FR-1022: `git log -- feature-requests/FR-1022.research.md`
  shows the record replaced after judgement (`16512c04`); the ledger gained
  a second line for the same brief; the FR's `**Research:**` field was
  rewritten to describe the post-judgement run. Operator: "clearly just for
  the show. some SHA acrobatics?" and "SHAs are acrobatics no one asked
  for."
- 2026-09-06, `grep -rn verify-promotion .pre-commit-config.yaml
  .github/workflows .github/hooks scripts/*.sh` → no hits; the only caller
  is `tests/unit/test_fr896_precedent_traceability.py` testing the
  function on fixtures.
- FR-896 judgement C-4 (2026-08-28): "Provenance checks may claim
  hash/integrity consistency only; do not claim proof of execution."
- `feature-requests/research-runs.jsonl`: 34 lines; no reader in scripts,
  hooks, CI, or docs beyond the verifier that nobody runs.
