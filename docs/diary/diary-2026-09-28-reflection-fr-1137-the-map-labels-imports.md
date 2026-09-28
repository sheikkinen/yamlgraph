# Reflection: FR-1137 — the map labels what a test imports, not what it guards

**Date:** 2026-09-28
**FR:** FR-1137 (test corpus map: description, target, type per test)

## What happened

The map ran over 6,891 tests in 546 calls to mercury-2.5 and was accepted
on the second full run. The first full run found two defects, and neither
was in the classification.

1. **The rejection path had never seen a real failure.** Unit tests fed
   `publish_map` failures as dicts. The live map returns typed
   `MapFailure` objects (FR-1073), so the first real failure crashed the
   code that was meant to report it. The fake failures had the wrong
   type, and they were the only failures the path had ever seen.
2. **3 of 545 calls returned a bare array.** Mercury sent `[...]` where
   the schema asked for `{"records": [...]}`. The data was correct but
   the wrapper was missing. The operator's answer was three layers: a
   prompt line, a retry with feedback, and a 5% allowance for failed
   partitions. The accepted run needed only the retry: both retries were
   the same bare-array shape, and both recovered. The structural fix is
   FR-1140, at the structured-output boundary, where every graph gets it.

The raw read before the aggregates found the real finding. The model
labels a test by the code it *imports*, not the artifact it *guards*.
Tests of pre-commit config, of the copilot-instructions text, and of this
demo's own `tools.py` all come out `core`. The aggregate reads "67% core".
Read raw first, the same aggregate reads "at most 67% core".

## Trap

`fake_failure_shape`: a failure path tested only with hand-built failures
tests the author's idea of a failure, not the one the system produces.
The crash was in the code written to report failures, and it fired on the
first real one.

## Heuristic

For every rejection or error-report path, build at least one test fixture
from the producer's real type (`MapFailure(...)`, not `{"error": ...}`).
If the producer's type is a Pydantic model, the fixture is an instance of
it.

## Seed

**Seed:** Should the taxonomy ask "what breaks if this test is deleted?"
instead of "what does this test target?" The first question has a single
answer that points at an artifact. The second invites the import graph to
answer.
