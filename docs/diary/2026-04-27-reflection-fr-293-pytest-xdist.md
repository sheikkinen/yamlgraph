# Reflection: FR-293 pytest-xdist parallel tests

**Date:** 2026-04-27
**FR:** FR-293
**Trap encountered:** downstream_fix — surrogate Unicode in source file only manifested under xdist serialization

## What happened

Adding pytest-xdist for parallel test execution revealed a lurking bug: `image_node.py` contained surrogate-pair escape sequences (`\ud83d\uddbc\ufe0f`) in logger calls instead of proper Unicode emoji. These are valid Python string literals but invalid UTF-8 — they can't be serialized by execnet across worker boundaries.

The fix was at the boundary (the source file), not downstream (suppressing the xdist error).

## Insight

**The One Law applied:** The surrogate data entered at the source code boundary. Normalizing there (replacing escape sequences with real emoji) fixed all downstream consumers — xdist, log output, CI, everything.

**Benchmark-first worked:** Implementation Step 0 (benchmark before committing) caught the crash immediately and validated the 21s target before any other changes.

## Metrics

- Sequential (no slow): 42s
- Parallel `-n auto` (12 cores): 21.8s
- Speedup: 1.93x (I/O-bound tests don't parallelize as well as CPU-bound)
- Worker startup overhead: ~3s (acceptable for 3700+ tests)

## Seed

**When should xdist be extended to CI?** Coverage + xdist requires `pytest-cov` distributed mode. The 2-4 core CI runners may not benefit. Is there a threshold (core count × test count) below which xdist overhead exceeds sequential execution?
