# Diary: 2026-07-01 — Streaming Triptych

**Date:** 2026-07-01
**FRs:** FR-633, FR-634, FR-635
**Duration:** ~20 min (3-FR enforcement chain)

## Observation

Three FRs (add CLI flag, rewrite demo, delete dead code) formed a clean dependency chain where each one's existence justified the next. The deletion of dead code (FR-635) was only safe *because* FR-633 proved the replacement works, and FR-634 proved no demo relied on the old path.

## Trap: framework_costume

`create_streaming_node()` survived for months as dead code because it *looked* like a feature — it had a factory function, tests, documentation, and a README reference. But its output type (async generator) was architecturally incompatible with its consumer (`app.invoke()` expects dicts). The code was a **costume**: it had the shape of a working feature without the substance.

The cure was not fixing it but recognizing that graph-level streaming (`astream(stream_mode="messages")`) had already solved the problem from a different angle. The node-level code was never needed — it was a false start that calcified into "feature."

## Heuristic

**Dead code survives dressed as features.** If code has tests and docs but zero consumers in production graphs, the tests are testing the costume, not the system. The litmus: grep for real usage (`.yaml` files, production scripts, integration tests that actually run graphs). Zero hits = dead regardless of test count.

## Seed

Could the linter detect nodes with `stream: true` and warn that it's a no-op? More generally: can static analysis detect YAML keys that *look* valid but have no runtime consumer in the framework?
