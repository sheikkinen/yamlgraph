# Problem brief: the research provenance ledger is checked by no gate, and the input it pins is mutable

**Prior art:** FR-896 (added `feature-requests/research-runs.jsonl` —
brief and artifact SHA-256 per run — and `research_preflight.py
--verify-promotion`, against finding 7 "research records are forgeable";
its judgement C-4: "Provenance checks may claim hash/integrity consistency
only; do not claim proof of execution"); FR-890 (the research sole route:
closed brief → five personas → promoted `FR-XXX.research.md`, read by the
judge for substance); FR-1005 (failed-persona demotion in the same route);
FR-1004 (a different ledger, `docs/census/outsider-ledger.jsonl`, retired
for write contention — precedent for how this repo has treated an
append-only file without a reader); FR-1025 (REJECTED 2026-09-06: a brief
on this same problem that prescribed its solution; this brief replaces it).

## Problem statement

Two mechanisms sit on the research route. The first is FR-890's: a brief
passes a closure preflight, the route produces an alternatives record, the
author promotes it beside the FR, and the judge reads it for substance
before granting authority. The second is FR-896's: `scripts/research.sh`
appends `{timestamp, brief_path, brief_sha256, artifact_sha256,
code_git_sha, graph}` to a committed ledger, and `research_preflight.py
--verify-promotion <record> <ledger>` recomputes the two hashes and reports
`matching` / `missing` / `mismatched`.

The second mechanism has no invoking caller: no hook, workflow, or script
runs `--verify-promotion`; `scripts/research.sh` mentions it once in a
comment. The only executable consumer is
`tests/unit/test_fr896_precedent_traceability.py`, which exercises the
function on fixtures. The ledger has no reader other than that verifier.

The hash pins the brief's bytes. A brief is a planning input: judges and
reviewers have asked for its wording to change after research was run
(FR-1022, R-4 and review P2), and an author who complies makes the ledger
report `mismatched` for that brief. The route's only sanctioned path back to
`matching` is to run research again, which produces a different record.

On FR-1022 (2026-09-06) that is what happened: a 5-line evidence correction
to the brief, a five-persona re-run, a second ledger line, and a research
record cited in the FR that postdates the judgement that approved the FR.
The judge had read the first record. Nothing required the re-run; the
author performed it because the verifier existed.

What the ledger was built to detect — a hand-written record with no run
behind it — is a record the judge would also read. What it cannot detect is
whether that record's content is substantive, which is the only property
the judge uses.

## Classification

enforcement/latency-critical

## Constraints

- FR-896 C-4 is binding on any claim made about the ledger: it evidences
  hash consistency, not execution.
- Scripture `detection_without_enforcement`: "Lint without gate = advisory
  → add CI block or remove claim." Both branches are open; this brief does
  not choose.
- Scripture `gate_checks_shape_not_substance`; `growth_as_default`
  (registry becomes honest by retiring phantom claims); `who_reads_this_when`
  (name the rung, the reader, the moment — else it is archived at birth);
  `artifact_carries_code_identity` (seed: stamp measurement artifacts with
  the producing code SHA — the ledger's `code_git_sha` field is the one
  place this seed was implemented).
- The research route's other checks — closed-brief preflight, artifact
  schema (`--verify-artifact`), prior-art block (FR-938), failed-persona
  rows (FR-1005), record header (brief, run date, personas) — are read by
  the judge and are in scope only insofar as any change must leave them
  behaving as today.
- Historical FRs, judgements, evidence files, and diaries that cite
  `research-runs.jsonl` are the record; they are not edited.
- A brief may need correction after research (witnessed: FR-1022). Whatever
  the outcome, the route must have a stated, cheap answer to "the brief
  changed after the run" that does not require the run to be repeated
  unless the question changed.
- Changes to research/judge enforcement are enforcement-infrastructure
  changes: human review is a gate.

## Witnessed incidents

- 2026-09-06, PR #633 (FR-1022): commit `16512c04` replaces
  `feature-requests/FR-1022.research.md` and appends a second
  `research-runs.jsonl` line for the same brief after the FR's judgement
  (`55cb4951`) had been rendered on the first record. Operator, same day:
  "clearly just for the show. some SHA acrobatics?" and "SHAs are
  acrobatics no one asked for."
- 2026-09-06: no invocation of `--verify-promotion` in
  `.pre-commit-config.yaml`, `.github/workflows`, `.github/hooks`, or
  `scripts/*.sh`; one comment mention in `scripts/research.sh`.
- 2026-08-28, FR-896 judgement C-4: hash consistency only, not proof of
  execution.
- 2026-09-06, FR-1025 judgement R-1: a brief on this problem that
  contained "Adding the gate is the wrong direction" and "the deletion must
  retire…" produced five personas unanimous for deletion; REJECTED as a
  confirmation run.
