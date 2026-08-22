# 2026-08-22 — The Auditor Audits the Instrument

**Arc:** FR-851 enforcement — RED (af20e0f3) → GREEN (33043358) →
authoring route → 41 real haiku batches → 412/412 reconciled → evidence.

## What happened

The repo's first substance-ranking of its own traceability spine ran
end-to-end in one session: deterministic constructor, governed-route
graph, deterministic reconciliation. Zero hallucinated req_ids in 412
verdicts — the boundary guard never fired. And the single most useful
finding was not about tests at all.

## The insight: the audit graded the instrument, not just the witnesses

Nine of the ten "no" verdicts were `no-link-unrecorded` REQs with empty
resolved_files — example/demo capabilities whose tests never run under
the unit-coverage instrument. The model, asked "is this requirement
witnessed?", answered a sharper question: "your linkage instrument
cannot see this requirement's witnesses." REQ-YG-072 went further: its
one coverage-linked file was `logging.py` — the coverage link itself was
a false witness (execution reach ≠ evidence relevance). The Stage-1
plausibility framing was designed to weaken the model's claims; instead
it redirected them at the measurement layer, where they were strongest.

Trap avoided (barely): `plausible_wrong_answer` at the distribution
level. 167/235/10 looks like a verdict on the test suite. Read row by
row, half the signal is a verdict on the *linkage pipeline* — the FR-850
polish work, graded by an LLM that was never told FR-850 exists.

## Heuristic

**An audit over joined data always audits the join.** When an LLM grades
payloads assembled from N sources, its "no" verdicts cluster where the
join is weakest, not where the subject is worst. Partition flagged
verdicts by *cause stratum* (instrument gap vs subject gap) before
treating the ranking as a worklist — otherwise you assign test-writing
work where a coverage-run flag was the actual fix.

## Small scar

The enforcement hit five hook rejections in sequence (ruff-format,
noqa confession line drift, foreign staged diary, demo-proof log,
FR-board drift, per-commit changelog fragment). None was a defect; all
were the boring enforcement of prior judgements. Boring = the Judgement
was good. The foreign staged diary was the one real hazard —
`one_session_one_repo`'s staged-check ritual caught another session's
git-report diary sitting in my index before it was swept into an FR-851
commit under an FR-851 message.

**Seed:** the verdict payloads now exist as structured data
(`witnessed`, `gap`, `suggestion` × 412). The gap texts name concrete
missing links ("add genesis.yaml to resolved_files"). Could a Stage-3
graph consume its own Stage-1 gaps and emit constructor patches —
closing the loop from audit to instrument repair without a human
routing each row?
