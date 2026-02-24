# Feature Request: Document projects/ vs examples/ Distinction

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-24

## Summary

Add documentation to ARCHITECTURE.md explaining the distinction between `projects/` and `examples/`, including graduation criteria and requirement traceability differences.

## Value Statement

Contributors understand where new work belongs and when an example should graduate to a project, preventing requirement-tracking confusion and directory misplacement.

## Problem

ARCHITECTURE.md references `projects/outcaller` with project-scoped requirements (OC-XXX, IC-XXX) and documents the relocation of REQ-YG-078–086 to project-specific tags (§27, line 545). However, no documentation explains:

1. **What `projects/` is for** — its purpose is implicit, never stated.
2. **How it differs from `examples/`** — both contain standalone applications using YAMLGraph; the boundary is undocumented.
3. **When an example graduates to a project** — no criteria exist for the transition.
4. **How requirement traceability works differently** — projects use project-scoped tags (OC-XXX) excluded from `req_coverage.py`, but this is never explained as a deliberate design choice.

This gap causes friction for contributors deciding where to place new work and understanding why some requirements are tracked differently.

## Proposed Solution

Add a `### projects/ vs examples/` subsection to ARCHITECTURE.md after the "Application Layer Pattern" section (after line 84), with a comparison table and graduation criteria.

```markdown
### projects/ vs examples/

| Aspect | `examples/` | `projects/` |
|--------|-------------|-------------|
| **Purpose** | Demonstrate YAMLGraph patterns and capabilities | Standalone applications with domain-specific goals |
| **Requirements** | Framework-scoped (REQ-YG-XXX) | Project-scoped (OC-XXX, IC-XXX, etc.) |
| **Traceability** | Tracked by `scripts/req_coverage.py` | Own traceability, excluded from framework coverage |
| **Tests** | Optional for demos, required for complex examples | Required |
| **Scope** | Illustrate framework features | May diverge from framework patterns for domain reasons |

**Graduation criteria** — An example becomes a project when:
1. It accumulates domain-specific requirements worth tracking independently
2. It needs dedicated test coverage beyond framework validation
3. Its requirements would pollute the framework requirement namespace (see §27 Telco relocation)
```

## Acceptance Criteria

- [x] `### projects/ vs examples/` section added to ARCHITECTURE.md after "Production Example: NPC Encounter" section (~line 142)
- [x] Table covers: purpose, requirements, traceability, tests, scope
- [x] Graduation criteria list with ≥3 concrete criteria
- [x] Cross-reference to §27 Telco relocation as a worked example of graduation
- [x] No changes to code or tooling — documentation only
- [x] `yamlgraph graph lint examples/demos/hello/graph.yaml` still passes (smoke test)

## Alternatives Considered

1. **Separate CONTRIBUTING.md section** — Rejected; the distinction is architectural, not procedural. ARCHITECTURE.md is the canonical source for structural decisions.
2. **README in projects/ directory** — Could supplement but doesn't replace the architectural documentation. A `projects/README.md` may be added separately.
3. **Merge projects/ back into examples/** — Rejected; the requirement relocation (FR-078, OC-008) established a clear precedent for separation.

## Related

- ARCHITECTURE.md §27 "Telco Voice Call Demo" (line 541) — documents the OC-XXX/IC-XXX relocation
- `scripts/req_coverage.py` — framework-level requirement traceability (excludes projects/)
- `projects/outcaller` — first graduated project, exemplifying the pattern
- `examples/npc/architecture.md` — complex example that could be a graduation candidate
