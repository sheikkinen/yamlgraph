# Reflection: FR-1170 — the witness that only runs where the extra is installed

**Date:** 2026-11-19
**FR:** [FR-1170](../../feature-requests/FR-1170-azure-thinking-off.md)

## What happened

The judged ACs asked for witnesses on the real Azure SDK request payload. The
precedent (FR-1056, DeepSeek) did exactly that, and it was right there:
`langchain-openai` is a core dependency. `langchain-azure-ai` is the optional
`azure` extra, and neither CI leg installs it. Written as the precedent was,
every FR-1170 payload test would have needed `importorskip` and would have been
skipped in CI. The PR would have shown green CI without any FR-1170 test running.

The fix was a second, SDK-free layer: a fake `langchain_azure_ai` module and
an assertion on the constructor kwargs. It is weaker than the payload, but it
runs in CI and fails if someone removes the mapping. The payload tests stay as
the local, stronger witness.

## Trap: a skipped witness reads as a passing one

Copying a precedent's test shape also copies its environment assumption. A
skip is not a failure, so CI turns green without testing anything, and nothing
flags that.

## Heuristic

Before writing a witness, check that CI installs everything it imports. If it
needs an optional extra, add a layer that pins the contract below the SDK, so
CI can still fail when the contract breaks.

## Seed:

Could `req_coverage --strict` count a REQ as covered only when one of its tests
can run under CI's extras, so a REQ witnessed only by skipped tests shows as
uncovered?
