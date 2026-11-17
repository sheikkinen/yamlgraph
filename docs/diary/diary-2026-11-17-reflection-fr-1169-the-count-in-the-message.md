# Reflection: FR-1169 — the count in the message

**Date:** 2026-11-17
**FR:** [FR-1169](../../feature-requests/FR-1169-haiku-5-5-default.md)

## What happened

The task arrived with a count: 83 files name `claude-haiku-4-5`. A wider search
found 254, most of them records (diaries, census runs, demo logs, proofs) that
must keep the id they ran on. The live set was 58 files, of which 19 were
graph or prompt YAML. My first RED commit message said 13, a number I had
estimated from the list rather than counted; the witness itself listed 19.

## Trap: a stated count is a claim, not a measurement

A number written into a brief or a commit message looks like evidence, and the
next reader repeats it. Both counts here were estimates that read like
measurements. The witness's own list was the only count that had been checked.

## Heuristic

When a message states how many files, take the number from the command that
produced the list, in the same step, and never from memory of the list.

## Seed:

Could a RED commit message quote the witness's failing output directly, so
its numbers can never drift from what the test saw?
