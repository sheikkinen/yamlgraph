# FR-281 Watcher2 Remediation Loop Enhancement

**Date:** 2026-04-25
**Context:** Implementing progressive ruff fixing to prevent watcher2 pipeline crashes on SIM117 (nested with statements) violations

**Trap:** quick_confidence — Initially felt confident the solution was "just add --unsafe-fixes flag everywhere" without understanding the progressive strategy needed. The Scripture warns: "When I feel certain → Judge instead."

**Discovery:** The real insight came from recognizing this was a **boundary normalization** problem. The FR evidence showed SIM117 violations appearing in *generated* code (from copilot nodes), not authored code. The boundary where external AI-generated content enters our pipeline needed better handling.

**Heuristic:** **Progressive remediation normalizes at capability boundaries** — When external systems (like AI code generation) produce content that doesn't meet our standards, apply progressive fixing: safe transformations first, then unsafe transformations, then escalate to intelligent remediation. This prevents both false positives (rejecting fixable code) and false negatives (silently accepting poor code).

**Implementation Pattern:**
```bash
# Boundary normalization for AI-generated content
ruff check --fix         # Safe automatic fixes
ruff check --fix --unsafe-fixes  # Unsafe but deterministic fixes
# Only then escalate to copilot for complex cases
```

**Testing Insight:** The TDD approach was crucial — writing tests that expected specific command sequences in watcher2.sh forced me to think through the *exact* progressive strategy rather than hand-waving "make it work somehow."

**Demonstration Value:** Creating `examples/demos/watcher2-remediation/demo-script.sh` that shows before/after SIM117 transformations was more valuable than unit tests alone. Seeing actual nested `with` statements get combined proves the feature works in practice.

**Seed:** How can we apply this progressive remediation pattern to other AI code generation boundaries? Could we create a general "AI output normalization" pipeline that handles multiple linter rules, formatting standards, and even semantic improvements in progressive stages?

**Related Scripture:** This reinforces the "normalize at the boundary" principle — the watcher2 finalize step is exactly the boundary where generated content enters our quality gates.
