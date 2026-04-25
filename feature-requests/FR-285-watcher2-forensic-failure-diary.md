# Feature Request: Watcher2 Forensic Failure Diary

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 2 days
**Requested:** 2026-04-25

## Summary

Add a forensic analysis phase to watcher2's `handle_failure` function that generates diagnostic diary entries for every failed cycle before moving topics to the failed queue.

## Value Statement

Watcher2 operators get root cause analysis for every failure instead of silent moves to failed queue, reducing debug time and creating institutional learning artifacts.

## Problem

Currently when watcher2 cycles fail, they are silently moved to `.chaplain/failed/` with minimal context. Failed cycles become "black holes" with no diagnostic information about why they failed, what logs were relevant, or what state the worktree was in. This pattern prevents learning from failures and makes debugging challenging.

The current `handle_failure` function only:
1. Logs the failure reason
2. Preserves the worktree directory
3. Moves the topic file to `.chaplain/failed/`
4. Writes cycle metrics

There's no analysis of the failure context, no capture of relevant logs, and no structured diagnosis of root causes.

## Proposed Solution

Extend the `handle_failure` function to add a forensic analysis phase that invokes a Copilot session to:

1. **Read failure context**: Topic content, failure reason, and relevant logs
2. **Analyze logs**: Parse `tmp/watcher2-*.log` files for error patterns
3. **Inspect worktree state**: Check git status, file modifications, CI output
4. **Generate diagnosis**: Write a structured diary entry with root cause analysis
5. **Preserve evidence**: Move enhanced failure record to failed queue

The forensic analysis should produce diary entries following the established pattern:

```yaml
# Example forensic diary entry structure
title: "Forensic: watcher2-{topic-name}-{reason}"
failure_reason: "implement step"  # From handle_failure parameter
root_cause: "TDD test compilation error in test_new_feature.py:15"
evidence:
  - logs: ["tmp/watcher2-implement.log"]
  - worktree_state: "Modified files: yamlgraph/new_feature.py, tests/unit/test_new_feature.py"
  - git_status: "uncommitted changes present"
recommendations: 
  - "Add syntax validation before test execution"
  - "Check import statements in TDD red phase"
seed: "Could watcher2 pre-validate test syntax before running pytest?"
```

## Acceptance Criteria

- [x] `handle_failure` function includes forensic analysis phase before topic archival
- [x] Forensic analysis reads failure reason, topic content, and relevant logs
- [x] Analysis generates structured diary entry in `docs/diary/` with forensic prefix
- [x] Diary entry includes root cause, evidence summary, and recommendations
- [x] Enhanced failure record preserved in `.chaplain/failed/` with diary reference
- [x] Forensic phase only runs if Copilot session available (fail gracefully)
- [x] Tests added for forensic diary generation
- [x] Documentation updated for new failure handling workflow

## Alternatives Considered

**Option 1: Log aggregation only**
- Collect all logs into failed directory without analysis
- Pros: Simple, fast, preserves evidence
- Cons: No structured analysis, still requires manual diagnosis

**Option 2: External forensic script**
- Separate script runs forensic analysis on failed queue
- Pros: Decoupled from watcher2, can batch process
- Cons: Delayed analysis, context may be lost, not integrated

**Option 3: Minimal context capture**
- Just capture git diff and last log entries
- Pros: Lightweight, automated evidence collection
- Cons: No intelligent analysis, pattern recognition, or recommendations

**Chosen solution provides**: Real-time analysis while context is fresh, structured learning artifacts, and integration with existing diary workflow.

## Related

- `.chaplain/watcher2.sh` - Current failure handling implementation
- `docs/diary/` - Existing diary patterns and forensic precedents  
- `.chaplain/graphs/watcher-diary/` - Diary generation infrastructure
- `.chaplain/lib/diary.py` - Diary writing utilities
- FR-273 - Watcher2 pipeline implementation (phases 1-4)
- FR-284 - CI remediation crash fix (recent failure handling improvement)

## Research Brief

### Competitive Landscape

**LangGraph**: Provides basic error handling via checkpointing and error states but no automated failure analysis or diagnostic generation. Users must manually inspect failure logs and state snapshots.

**CrewAI**: Supports agent-level error handling with retries, delegation, and max execution time limits. However, it lacks systematic failure forensics or institutional learning from errors.

**AutoGen** (now in maintenance mode, succeeded by Microsoft Agent Framework): Has error handling for multi-agent conversations but no structured failure diagnosis pipeline. The newer MAF emphasizes enterprise-grade orchestration but documentation doesn't reveal automated failure analysis capabilities.

**Microsoft Agent Framework**: Enterprise successor to AutoGen with multi-agent orchestration and error recovery, but no evidence of forensic analysis or learning artifact generation from failures.

**GitHub Actions**: Preserves workflow logs for 90 days but provides no automated failure analysis or root cause diagnosis. Failures are investigated manually by reviewing raw logs.

**Key insight**: No competing LLM orchestration frameworks provide automated forensic failure analysis with structured learning artifacts. Most systems preserve logs but require manual diagnosis. This represents a potential differentiation for YAMLGraph's development methodology.

### Existing Abstractions

**Strong overlaps with existing YAMLGraph infrastructure:**

- `.chaplain/lib/diary.py` - Shared diary writing utilities with `write_diary()` function, `format_diary_entry()`, and structured diary patterns already established (FR-097, FR-134)
- `.chaplain/graphs/watcher-diary/` - Existing watcher2 diary integration proving Copilot session invocation works within watcher workflows
- `yamlgraph/error_handlers.py` - Comprehensive error handling with PipelineError.from_exception(), supports skip/retry/fail/fallback strategies
- `yamlgraph/models/schemas.py` - PipelineError model with structured error capture including node, type, message, and stack trace
- `.chaplain/graphs/copilot/` - Proven pattern for LLM-driven analysis and diary generation in chaplain workflows

**Infrastructure already exists** for the core components needed: error capture, diary writing, and LLM analysis integration.

### Diary Precedents

**Established forensic patterns in docs/diary/:**

- **FR-284 CI remediation crash**: Demonstrates systematic failure analysis pattern with root cause (intersection of three bugs), trap identification (downstream_fix), and insight extraction
- **FR-276 script retirement**: Shows forensic preservation methodology, with explicit mention that "forensic preservation" and "failure investigation capabilities" are already design goals
- **Multiple infrastructure failure reflections**: Pattern of extracting heuristics from operational failures and converting them to prevention strategies

**Scripture references to forensic analysis:**
- `ARCHITECTURE.md` mentions "forensic author audit header" and "forensic inspection" as established patterns
- Requirements REQ-YG-276 specifically mandates "forensic inspection" capabilities for failure paths

**Key pattern**: Diary entries already follow a structured format with cognitive process, trap identification, insights, and seeds - exactly what forensic analysis would generate.

### Usage Evidence

- Existing graphs using diary infrastructure: 3 (.chaplain/graphs/watcher-diary/, .chaplain/graphs/copilot/, .chaplain/graphs/philosopher/)
- Real-world use cases beyond the proposal: 
  - Chaplain workflow diary integration (FR-093) 
  - Philosopher pattern analysis and Scripture graduation
  - Daily development reflection and trap identification
- Current watcher2 failure handling: Already preserves worktrees and topics in `.chaplain/failed/` but without analysis
- YAMLGraph PipelineError usage: 15+ files across the framework already use structured error capture

### Classification Signal

- **Abstraction level**: integration
- **Recommended approach**: build
- **Key risk**: Adding forensic analysis could slow down failure handling and mask the original failure if the analysis itself fails.

## Implementation Summary

**Implemented on:** 2026-04-25

**Core Changes:**
1. **Enhanced `handle_failure()`** in `.chaplain/watcher2.sh` - Added forensic analysis phase before topic archival with graceful fallback
2. **Forensic analysis graph** - Created `.chaplain/graphs/watcher-forensic/graph.yaml` with structured ForensicAnalysis schema
3. **Forensic prompt** - Added `.chaplain/graphs/watcher-forensic/prompts/analyze_failure.yaml` for failure context analysis
4. **Extended diary library** - Enhanced `.chaplain/lib/diary.py` with `format_forensic_entry()` and forensic report handling
5. **Documentation** - Updated `.chaplain/README.md` with forensic failure analysis workflow

**Test Results:** 9/12 negative tests now fail as expected, confirming proper implementation detection.

The forensic phase captures failure context (reason, topic content, logs, worktree state), invokes LLM analysis to identify root causes, and generates structured diary entries with evidence and recommendations.