# Feature Request: FR-278 Remove FR-277 Watcher2 Baseline Dead Code

**Priority:** MEDIUM
**Type:** Cleanup
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-04-25
**Judged:** 2026-04-25
**Verdict:** APPROVED (2026-04-25 08:44)

## Summary

Remove incomplete and non-functional FR-277 watcher2 baseline checkpointing code that was merged via PR #211 but never properly implemented.

## Value Statement

Developers get a cleaner codebase with no broken imports or dead code paths, reducing confusion and maintenance overhead.

## Problem

FR-277 was implemented partially and merged via PR #211, leaving behind non-functional code that creates several issues:

1. **Broken imports**: `.chaplain/graphs/baseline/graph.yaml` references `yamlgraph.chaplain.nodes` which doesn't exist
2. **Non-existent file references**: `watcher2.sh` contains `--import-state .chaplain/baseline/latest.json` pointing to a file that doesn't exist
3. **Dead code modules**: Several Python modules with no working functionality or integration
4. **Phantom test coverage**: Test file exists but tests non-functional code
5. **Stale documentation**: References to baseline functionality in README that doesn't work

The implementation was incomplete:
- No manifest file exists
- No baseline directory structure
- No working node implementations  
- No actual integration with watcher2 pipeline

This creates confusion for developers and wastes CI resources running tests for non-functional code.

## Proposed Solution

Perform a complete removal of all FR-277 baseline checkpointing code and references:

### Files to Remove
- `yamlgraph/chaplain/baseline.py`
- `yamlgraph/chaplain/__init__.py`
- `yamlgraph/models/baseline.py`
- `.chaplain/graphs/baseline/graph.yaml`
- `tests/unit/test_fr277_watcher2_baseline_checkpointing.py`
- `capabilities/CAP-129-watcher2-baseline-checkpointing.yaml`

### Files to Edit
- `.chaplain/watcher2.sh`: Remove `--import-state .chaplain/baseline/latest.json` line
- `ARCHITECTURE.md`: Remove REQ-YG-279 requirement entry
- `.chaplain/README.md`: Remove baseline checkpointing documentation sections

### Feature Request Status
- Mark `feature-requests/FR-277-watcher2-baseline-checkpointing.md` as rejected/removed

### Clean Implementation Path
If baseline checkpointing is needed in the future, it should be re-implemented from scratch with:
- Complete design specification
- Working manifest system
- Proper integration testing
- Full documentation

## Acceptance Criteria

- [x] All baseline-related Python modules removed (`yamlgraph/chaplain/baseline.py`, `yamlgraph/models/baseline.py`)
- [x] Chaplain package init file removed (`yamlgraph/chaplain/__init__.py`)
- [x] Baseline graph YAML file removed (`.chaplain/graphs/baseline/graph.yaml`)
- [x] Baseline test file removed (`tests/unit/test_fr277_watcher2_baseline_checkpointing.py`)
- [x] Capability registration removed (`capabilities/CAP-129-watcher2-baseline-checkpointing.yaml`)
- [x] Import state line removed from watcher2.sh
- [x] REQ-YG-279 requirement removed from ARCHITECTURE.md
- [x] Baseline documentation removed from `.chaplain/README.md`
- [x] FR-277 marked as rejected in feature requests
- [x] No import errors when running existing tests
- [x] No references to baseline functionality in grep search across codebase
- [x] All tests pass after removal
- [x] Linting passes (no dead imports or references)

## Alternatives Considered

1. **Complete the FR-277 implementation**
   - Rejected: Would require significant effort (4+ days) to properly implement the missing pieces
   - Original FR-277 was already complex and this removal task is about cleaning up incomplete work

2. **Leave the code and mark as "work in progress"**
   - Rejected: Dead code with broken imports creates maintenance debt and confusion
   - Tests for non-functional code waste CI resources

3. **Partial cleanup (remove only obviously broken parts)**
   - Rejected: Incomplete removal would leave other dead code paths and confusion about what works

## Related

- FR-277: Original watcher2 baseline checkpointing feature (to be marked rejected)
- PR #211: Pull request that merged incomplete implementation
- REQ-YG-279: Requirement to be removed from architecture
- CAP-129: Capability to be removed from registry

## Research Brief

### Competitive Landscape

**LangChain** does not expose specific cleanup utilities in their contributing docs, but GitHub search reveals a common industry pattern: incomplete implementations are typically removed entirely rather than left as dead code. Python's own AST module documentation demonstrates clear practices for deprecating and removing features with proper migration paths.

**GitHub Issues Analysis**: Search results for "remove incomplete implementation" show this is a common maintenance task across projects. Standard approaches include:
- Complete removal of non-functional code (preferred over partial fixes)
- Clear documentation of what was removed and why  
- Preservation of the original design in case of future re-implementation

No competing frameworks provide specific tooling for baseline checkpointing as described in FR-277, confirming it was a novel approach.

### Existing Abstractions

**Vulture Dead Code Detection** (`vulture_whitelist.py`, `.pre-commit-config.yaml`): YAMLGraph already has established patterns for dead code cleanup via FR-162. Key abstractions:
- `vulture_whitelist.py` for suppressing false positives
- Pre-commit hooks with vulture integration
- Systematic removal of modules with zero production callers
- Documentation requirements for `# noqa` suppressions in `docs/confessions.md`

**Feature Request Rejection Pattern** (`feature-requests/REJECTED-fix-philosopher-copilot-nodes.md`): Established precedent for marking FRs as rejected with clear reasoning, cross-references to duplicates/alternatives, and preservation of context for future reference.

**Requirement Traceability System** (`scripts/req_coverage.py`, `ARCHITECTURE.md`): Well-defined process for removing requirements with tests that verify coverage gaps.

### Diary Precedents

**`partial_remediation` trap** (2026-03-19): Key pattern where "each cleanup path cleared *some* state but not all." This FR explicitly addresses this by ensuring complete removal rather than partial cleanup of baseline functionality.

**Vulture cleanup patterns** (FR-162, 2026-03-08): Established successful precedent for dead code removal with:
- Clear identification of false positives vs. genuine dead code
- Systematic approach to module/test deletion  
- Lowered detection thresholds after cleanup
- Documentation of suppressions

**Infrastructure self-exemption trap** (2026-04-12): Pattern where "infrastructure exempts itself from cleanup rules" - the baseline implementation exemplifies this by being merged incomplete but never held to the same standards as complete features.

### Usage Evidence

- Existing graphs using baseline abstractions: **1** (`.chaplain/graphs/baseline/graph.yaml` - non-functional)
- Real-world use cases beyond the proposal: **None** (no imports of `yamlgraph.chaplain` modules found in examples)
- References to baseline functionality: **3 files** (graph.yaml, capability registration, test file - all dead code)
- watcher2.sh references: **1 line** (`--import-state .chaplain/baseline/latest.json` - points to non-existent file)

### Classification Signal

- **Abstraction level**: cleanup (removing failed integration attempt)
- **Recommended approach**: build (complete removal as specified)  
- **Key risk**: Incomplete removal leaving orphaned references that cause future import errors or confusion

---

## Judgement

**Verdict: APPROVED. Scope frozen. Implementation authority granted.**

### Critical Review (2026-04-25 08:44)

All 8 evaluation criteria PASSED:

1. ✅ **Scope**: Clear and minimal - complete removal of non-functional FR-277 baseline checkpointing code
2. ✅ **Consistency**: No contradictions. Clear list of files to remove vs. edit, with specific line references
3. ✅ **Measurability**: 12 acceptance criteria are precisely testable with clear pass/fail conditions
4. ✅ **Feasibility**: Simple file deletions and line removals. Well within stated 1-day effort estimate
5. ✅ **Architecture**: Follows established dead code cleanup patterns from FR-162. No framework changes required
6. ✅ **Single Responsibility**: Focused solely on removing incomplete code - no bundled concerns
7. ✅ **Classification**: Cleanup task with clear business value (remove maintenance debt and confusion)
8. ✅ **Tests**: 18 acceptance tests compile correctly and fail for the right reasons (files exist that should be removed)

**Research validated**: Competitive analysis confirms this follows industry standard practice for removing incomplete implementations. Existing YAMLGraph patterns (FR-162 vulture cleanup) provide proven precedent.

**Test validation**: Acceptance tests properly fail because target files still exist. Sample test shows clear assertion: "Dead code module still exists: .../baseline.py" - this is the correct failure for a removal task.

### Implementation Scope

**In Scope:**
- Complete removal of all FR-277 baseline artifacts (Python modules, YAML configs, tests, docs, capability registration)
- Cleanup of references in watcher2.sh, ARCHITECTURE.md, and README files
- Marking FR-277 as rejected for historical clarity
- Verification that removal causes no import errors or test failures

**Out of Scope:**
- Any new baseline checkpointing implementation
- Changes to watcher2 pipeline functionality beyond removing broken baseline import
- Modifications to requirement traceability system beyond removing REQ-YG-279

**Success Criteria:**
- All 18 acceptance tests pass
- No grep results for baseline references in codebase
- All existing tests continue to pass after cleanup
- Linting passes with no import-related errors

This cleanup directly addresses the `partial_remediation` trap identified in diary precedents by ensuring complete removal rather than leaving orphaned references.
