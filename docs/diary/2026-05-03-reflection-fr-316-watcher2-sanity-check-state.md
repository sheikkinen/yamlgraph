# Reflection: FR-316 watcher2 sanity_check state

**Date:** 2026-05-03
**FR:** FR-316 watcher2 post-validate sanity_check diary state

## Trap

`architecture_as_diagram`

## What Happened

The watcher2 pipeline had a validate and precommit split, but diary and post-validate quality review still lived in enforce-session instructions. The boundary existed in diagram form, not as an executable state transition.

## Root Cause

Review ownership was not enforced at the FSM boundary. Because there was no explicit sanity_check state, implementation and independent review stayed coupled in the same agent prompt.

## What Worked

Applying `spec_kill` and explicit boundary enforcement solved it: insert `sanity_check` between `validate` and `precommit_check`, route `WARN` as non-blocking, and move diary ownership to a dedicated sanity-check prompt that inspects proportionality, test quality, FR/code alignment, and pipeline log evidence.

## Seed

How can watcher2 automatically attach structured sanity-check evidence snippets (diff summary, pipeline log excerpt, FR criteria mapping) to each diary entry so reviewer quality remains consistent across models?
