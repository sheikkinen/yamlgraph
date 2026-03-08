## 2026-03-08: FR-164 — Verification Gate Pattern

**Context:** Added an optional `verification` field to node definitions that requires the LLM to state a falsifiable prediction before acting, then compares the prediction against the actual output at runtime. This surfaces silent failures — nodes that produce plausible but wrong results — by turning invisible drift into observable discrepancies. Implementation spans schema (`VerificationConfig` in `graph_schema.py`), runtime (`verification.py` with `VerificationResult`), LLM node integration, linter checks, and a demo example.

**Trap:** plausible_wrong_answer — The entire feature exists because of this trap. LLM outputs pass type validation (correct shape) while containing wrong content. Without explicit expectations stated *before* execution, there is no reference point to detect drift. The verification gate forces the LLM to commit to a prediction, creating an observable contract that can be checked post-hoc. The deeper insight: validation checks *structure*, verification checks *intent*.

**Heuristic:** When a system produces structured output that always passes schema validation, add a prediction layer — force the producer to declare what it expects before it acts. The gap between prediction and reality is where silent failures live. This is the boundary normalization law applied to *semantic* boundaries: normalize not just the type, but the intent at the boundary where the LLM commits to an answer.

**Seed:** Could verification gates compose across subgraphs — where a parent graph's verification references the verification results of child nodes — creating a hierarchical chain of falsifiable predictions that surfaces exactly which layer of a multi-agent pipeline drifted?
