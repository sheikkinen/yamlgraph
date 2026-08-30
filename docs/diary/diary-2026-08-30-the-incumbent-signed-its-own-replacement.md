# Diary — 2026-08-30 — The Incumbent Signed Its Own Replacement

## What happened

Operator: "research, fr - upgrade pinned gpt-5.5 to gpt-5.6-sol for judge
and review". Two YAML literals. The change itself is `1 1` in numstat per
file. Everything else in the session was ceremony around those two lines —
research route, FR, judgement, RED witness, GREEN, two live evidence runs.

The judgement of FR-931 was rendered by `gpt-5.5` — the model being
retired. It returned APPROVED WITH REVISIONS and one revision (R-1: the
changelog fragment must be `type: feat`, not `chore`, because the pin is
behaviour-affecting). The incumbent granted authority to replace itself,
and its last act was to tighten the record of its own succession.

## Traps encountered

- **Survivor-record run log.** `feature-requests/research-runs.jsonl`
  appends only on success. Reading it, the research route looks flawless.
  In this session it failed five times out of seven — twice on a precedent
  citing `examples/demos/data-files-demo/graph.yaml` (the real path is
  `examples/demos/data-files/`), once on an unknown Scripture key, once on
  a 400-char field overflow, once on a missing persona finding. A log that
  records only successes is not evidence of reliability; it is evidence of
  the shape of success. The 70% failure rate is invisible in the artifact
  that exists precisely to make the route auditable.
- **One hallucinated cell discards the map.** Each of those failures threw
  away a whole multi-persona map-reduce because the deterministic reducer
  is all-or-nothing. A single fabricated path in one persona's finding
  costs every other persona's work. Quarantine-the-cell, not
  abort-the-reduce, is the missing policy — recorded in the FR as a
  follow-up candidate, deliberately out of scope here.
- **"Pre-existing failure" offered itself.** The GREEN commit's pre-commit
  suite came back `1 failed, 6184 passed` on
  `test_telemetry_hostname_label_classified` — a test that touches nothing
  FR-931 touches. The forbidden framing was right there and it was even
  *true*. Reading the traceback instead: a `node -e` subprocess timed out
  at 30s under xdist contention on `gw9`; it runs in 1.74s alone. Retrying
  the commit ran the suite green. The honest diagnosis (wall-clock budget
  starved by parallel load) took one grep; the excuse would have taken
  none, and would have left a real ordering bug undistinguished from a
  contention flake had one existed. The ban on the phrase is not about
  blame — it is about forcing the read that separates the two.

## Insight

The evidence acceptance criteria (AC-06/AC-07) are the only parts of this
FR that could not have been satisfied by a lucky diff. A pin change is
mechanically trivial and semantically load-bearing: the test proves the
literal, the live run proves the literal *resolves to a model that still
withholds authority correctly*. AC-06 returned `model='gpt-5.6-sol'` and
`REJECTED — no implementation authority` on the missing-research fixture.
That pairing — a static invariant test plus one live artifact — is the
minimum honest shape for any configuration change whose failure mode is
silent competence loss rather than a crash.

## Heuristic

**append_only_log_hides_denominator** — a run log that appends only on
success reports a rate of 100% by construction. Before citing such a log
as reliability evidence, count the attempts from an independent source
(shell history, CI logs, wall-clock gaps). If the denominator is
unrecoverable, the log evidences shape, not health.

**Seed:** If the judge is itself a pinned model, what does a judgement of
its own replacement mean — and should the sole route render one FR class
(model-pin changes) under *both* the outgoing and incoming pin, so the
verdict is an agreement rather than a self-assessment?
