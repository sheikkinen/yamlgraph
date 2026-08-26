# Canary precommitment — diary trap recurrence census research (2026-08-26)

Held by initiator, absent from the brief.

- Primary canary: **per-entry cheap-LLM census over the full diary corpus
  with deterministic recurrence aggregation** — i.e. the corpus_census
  pipeline (FR-892) bound with diary discover/extract adapters, or an
  equivalent map+code-reduce shape. The textbook answer given the
  repo's own last-48h history; a research run that cannot rediscover it
  is invalid.
- Secondary (not gating): vocabulary normalization boundary — trap names
  drift ("tmp/msg.txt stale state" vs "stale commit-message file"), so
  the aggregation needs a canonicalization step (FR-593 lineage);
  genuine recurrence counting fails on exact string match.
- Run-output known-truths (for the eventual census itself, not this
  research run): tmp/msg.txt stale-state and line-pinned-gate traps
  must surface with ≥3 recurrences.
