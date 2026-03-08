## 2026-03-08: FR-166 — Verification Count Range Pydantic Model

**Context:** Replaced loose `int` locals in the `count_range` verification evaluator with a `CountRangeClaim` Pydantic model. The evaluator previously extracted `min_count` and `max_count` from a regex match into bare variables with no validation — an inverted range like "10-3 items" was silently parsed and created an impossible check. The Pydantic model validates `min_count <= max_count` at construction, and its structured fields are now exposed in `VerificationViolation.details` for programmatic inspection.

**Trap:** downstream_fix — The inverted-range bug could have been caught with a post-hoc `if min_count > max_count` guard inside the evaluator logic. But that fixes the symptom downstream. The real boundary is where external data (the regex match) enters structured form. By normalizing at the boundary — a Pydantic validator on construction — every consumer inherits the guarantee. This is The One Law in action: validate where data enters, not where it manifests.

**Heuristic:** When a regex match feeds into multiple downstream checks, wrap the extracted groups in a Pydantic model immediately. The model becomes both the validator and the documentation of what the regex is expected to produce. Bare locals from `match.group()` are untyped dicts in disguise.

**Seed:** Could the verification evaluator registry itself be driven by Pydantic discriminated unions — where each evaluator type (exact, contains, count_range, regex) is a tagged model variant — eliminating the string-dispatch `if/elif` chain and letting the type system enforce exhaustiveness?
