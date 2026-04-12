# Reflection: FR-222 — Ruff flake8-bandit Security Rules

**Date:** 2026-04-12
**FR:** FR-222
**Scope:** Enable ruff `S` ruleset (flake8-bandit) at pre-commit and CI

## What was done

Added the flake8-bandit (`S`) ruleset to ruff's `select` list. Running
the check revealed 5 existing violations — all in code that was already
safe by reasoning (shlex.quote, controlled inputs, autoescape) but
lacked the explicit suppression that proves the reasoning was conscious.
Each violation was either fixed or documented in `docs/confessions.md`
with a CONF-XXX ID.

## Cognitive trap encountered

**`detection_without_enforcement`** — the security patterns were safe
before this FR, but "safe by inspection" is not the same as "safe by
gate". The gap between knowing a pattern is safe and having the linter
enforce it is exactly where the next contributor introduces a regression
without any warning. The FR converted advisory knowledge into a
blocking check.

## Heuristic

A `# noqa` with a confession is stronger than no check at all: it
records the deliberate decision. Silence records nothing.

## Seed

If bandit `S` catches 5 pre-existing patterns on first run, how many
new patterns would a full SAST scan (semgrep, CodeQL) surface that ruff
S misses? Is there a severity threshold at which a SAST gate should
block PR merge rather than just report?
