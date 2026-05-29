# Audit Recommendations — Prioritized Action Plan

**Date**: 2026-05-29 | **Source**: Friendly Audit + IEC 62304 Assessment
**Priority**: P1 (do now) → P2 (next sprint) → P3 (backlog)

---

## P1 — Close Before Next Release

### REC-01: Add Missing CI Status Checks to Branch Protection

**Finding**: FINDING-001 — 7 of 10 documented required checks are not enforced at GitHub branch protection level.

**Action**: Run in GitHub Settings → Branches → `main` → Edit:

```
Add required status checks:
  ✅ commitlint          (already enforced)
  ✅ test (3.11)         (already enforced)
  ✅ test (3.12)         (already enforced)
  ☐ conflict-check       ← add
  ☐ copilot-trailer-gate ← add
  ☐ wip-gate             ← add
  ☐ changelog-gate       ← add
  ☐ changelog-req-gate   ← add
  ☐ demo-gate            ← add
  ☐ diary-gate           ← add
  ☐ security             ← add
```

**Minimum**: Add `security` and `copilot-trailer-gate`. The rest are process gates with pre-commit backstop.

**Risk if skipped**: A direct push or admin override bypasses CVE scanning and trailer injection detection.

---

### REC-02: Install pip-audit in Dev Environment

**Finding**: FINDING-002 — Security scanner missing locally.

**Action**:
```bash
pip install pip-audit
# Verify
pip-audit --desc
```

Also add to `pyproject.toml` `[dev]` extras so new contributors get it automatically.

---

### REC-03: Update CLAUDE.md Branch Protection Table

**Finding**: Documentation says `enforce_admins: true` but API shows `false`. Documentation lists `test` as single check but it's actually `test (3.11)` + `test (3.12)`.

**Action**: After REC-01, update the table in CLAUDE.md to match actual state. Or if some checks intentionally remain unenforced, document why.

---

## P2 — IEC 62304 Hardening

### REC-04: Add Safety Classification to Capability YAML

**Finding**: IEC 62304 Clause 5.2 — requirements lack per-item safety classification.

**Action**: Add `safety_class` field to capability schema:

```yaml
# capabilities/CAP-17-execution-safety-guards.yaml
requirements:
  - id: REQ-YG-055
    description: Map fan-out cap (max_items)
    safety_class: C          # ← NEW
    risk_control: true       # ← NEW
    modules:
      - map_compiler
```

Classification rules:
- **C**: Implements a risk control measure (loop limits, fan-out caps, timeout, injection prevention)
- **B**: Contributes to LLM output correctness (executor, graph loader, schema validation)
- **A**: Presentation, tooling, export (CLI, bench, codegen)

Extend `scripts/req_coverage.py` to report coverage grouped by safety class.

---

### REC-05: Coverage Gate Per Safety Class

**Finding**: IEC 62304 5.5.5 — verification rigor scales with safety class.

**Action**: Add tiered coverage thresholds to CI:

| Class | Current | Proposed Gate |
|-------|---------|---------------|
| C | 96.9% | ≥95% (fail build) |
| B | 95.9% | ≥90% (fail build) |
| A | 96.6% | ≥80% (warn) |
| Overall | 89.39% | ≥70% (existing) |

Implementation: extend `pytest` coverage config or add a post-step in CI that parses `coverage.json` by module group.

---

### REC-06: Guard Evaluator Coverage to 90%

**Finding**: `utils/guard_evaluator.py` at 73% — lowest-coverage module in Class B/C boundary.

**Action**: Add tests for the 35 uncovered lines (filter application, complex guard evaluation paths). This module evaluates safety expressions at runtime — it deserves Class C treatment.

---

### REC-07: Document SOUP Anomaly List

**Finding**: IEC 62304 5.3.3 — SOUP components identified but no known-anomaly register.

**Action**: Create `docs/soup-anomalies.md` listing known issues in critical dependencies:

```markdown
| Package | Known Issue | Impact on YAMLGraph | Mitigation |
|---------|------------|---------------------|------------|
| langgraph | ... | ... | ... |
| pydantic v2 | ... | ... | ... |
```

Review quarterly or on major version bumps.

---

## P3 — Future Hardening (Backlog)

### REC-08: Standalone Design Document for Safety Module

**Finding**: IEC 62304 Clause 5.4 — Class C modules warrant standalone detailed design beyond code.

**Action**: Create `docs/design/safety-guards.md` documenting:
- Guard evaluation algorithm
- Loop limit enforcement flow
- Fan-out cap decision tree
- Timeout signal handling (Unix-specific)
- Shell injection prevention strategy

This is the one module where "code is the design" is insufficient for a Class C argument.

---

### REC-09: Monitor Near-Boundary Modules

**Finding**: OBSERVATION-001 — Two files at 447/450 lines.

**Action**: No immediate action. Add to periodic review. If either grows past 450, pre-commit `file size gate` will block. Plan split strategy:
- `tools/agent.py` → extract `tools/agent_builder.py`
- `node_compiler.py` → extract by node type

---

### REC-10: A2A Module Integration Test Harness

**Finding**: `a2a_server.py` and `a2a_message.py` at 0% coverage.

**Action**: Create a lightweight test harness with mock A2A transport. These modules are server-only but should have at least message parsing and error path coverage. Target: 70%.

---

## Summary Matrix

| ID | Priority | Effort | IEC 62304 | Finding |
|----|----------|--------|-----------|---------|
| REC-01 | P1 | 10 min | Clause 8 | FINDING-001 |
| REC-02 | P1 | 2 min | — | FINDING-002 |
| REC-03 | P1 | 15 min | Clause 8 | Doc drift |
| REC-04 | P2 | 2h | Clause 5.2 | Safety class gap |
| REC-05 | P2 | 1h | Clause 5.5 | Tiered coverage |
| REC-06 | P2 | 2h | Clause 5.5 | Coverage gap |
| REC-07 | P2 | 1h | Clause 5.3 | SOUP register |
| REC-08 | P3 | 4h | Clause 5.4 | Design docs |
| REC-09 | P3 | — | — | Observation |
| REC-10 | P3 | 3h | Clause 5.5 | Coverage gap |

**Total estimated effort**: P1: ~30 min, P2: ~6h, P3: ~7h
