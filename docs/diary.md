# Development Diary

Metacognitive reflections on development process.

Previous: [diary-2026-02-22.md](diary-2026-02-22.md) — 12 entries from 2026-02-22.

---

## 2026-02-23: The Judge's Trap — Premature Requirement Allocation

**Context:** FR-075 audit revealed REQ-YG-078–082 (telco demo) were reserved in ARCHITECTURE.md capability table, but FR-075 originally proposed *releasing* them because outcaller uses `OC-XXX` numbering.

**Trap: Proposing Deletion Without Checking Dependencies.** The initial FR-075 draft said "release REQ-YG-078–082, remove CAP-27." But 34 tests are tagged with those requirement IDs:
```bash
grep -r "REQ-YG-07[89]\|REQ-YG-08[012]" tests/ --include="*.py" | wc -l
# 34 matches
```

If CAP-27 were removed from `req_coverage.py` while tests still reference those IDs, `--strict` would fail on "tagged tests reference unknown requirements."

**The Judge Protocol worked:** First instinct was to approve the "clean up" proposal. But the Judge must verify claims before granting authority. Running grep before signing off caught the issue. The FR was returned for amendment.

**Amended scope:** Reduced from "sync table + release reservation + add note" to just "sync table." The test coverage is real and valuable. The outcaller *application* uses `OC-XXX`, but the *framework integration tests* use `REQ-YG-XXX`. Both numbering schemes coexist correctly.

**Heuristic:** *Before approving deletion of any identifier (requirement ID, state key, function), grep for references first. The absence in one file doesn't mean absence everywhere.*

**Graduated pattern:** This extends "normalize at the boundary" — the deletion proposal was a *spec* normalized from what existed in the *code*. But the spec was wrong because it didn't consult the full truth (tests).

**Seed:** Should the Judge have a checklist? "Before approving deletion: grep codebase. Before approving rename: verify no external references. Before approving new ID: verify no collision." Formalize the verification steps that caught this issue.

---

## 2026-02-23: Documentation Drift as Entropy Signal

**Context:** ARCHITECTURE.md capability summary table was 5+ requirements behind `req_coverage.py`. Rows 3, 14, 17 were incomplete; row 28 didn't exist.

**Observation:** The *tests* were tagged correctly. The *script* (`req_coverage.py`) was correct. Only the *human-readable summary table* drifted. This pattern suggests: automated checks pass while documentation becomes stale.

**The entropy measure:** How far behind is the summary table?
- REQ-YG-050 (model override): missing from row 3
- REQ-YG-065 (native streaming): missing from row 14
- REQ-YG-059-062, 064 (safety guards): missing from row 17
- REQ-YG-083 (thinking budget): missing row 28

All these were added post-capability-table creation. The table was a snapshot, not a living document.

**Fix:** FR-075 — four table cell edits + one new row. 0.25 days. But the *detection* required an audit triggered by "disturbance in test tags."

**Heuristic:** *When tests pass but documentation feels stale, trust the tests. The stale doc is the trailing indicator of entropy, not its cause.*

**Seed:** Should there be a `docs/req_coverage.py --verify-architecture` mode that diffs the capability table against CAPABILITIES dict and reports mismatches? Automated detection of doc-code drift.

---

## 2026-02-23: World Digest — Observability & Agent Orchestration


**LangGraph ecosystem momentum:** Five LangGraph releases shipped this week (SDK 0.3.6–0.3.8, core 1.0.9, prebuilt 1.0.8), signaling active stabilization of the foundation YAMLGraph depends on. The SDK releases suggest refinement of deployment and runtime concerns.

**Agent observability as evaluation:** LangChain's recent focus on agent observability (multiple articles on tracing, behavior analysis, and evaluation frameworks) frames observability not as debugging overhead but as a first-class evaluation tool. This aligns with YAMLGraph's need to surface decision points and verify agent behavior—especially relevant to the seed on 'name the verification question' as a workflow gate.

**Memory and context patterns:** Articles on Agent Builder's memory system and context management for deep agents highlight that agent reliability depends on structured memory and context handling. YAMLGraph's YAML-first approach could formalize these patterns as declarative graph nodes, reducing silent fallbacks and invisible decisions.

**Tool registry and sandbox patterns:** New Agent Builder features (tool registry, file uploads) and the two-pattern analysis of agent-sandbox connections suggest the ecosystem is converging on explicit tool binding and execution isolation. This reinforces YAMLGraph's value: making these connections declarative rather than implicit in Python code.

**Evaluation at scale:** The monday.com + LangSmith case study demonstrates that evaluation strategy must be baked in from day one, not retrofitted. YAMLGraph's architecture should assume every node is observable and every edge is auditable—supporting the 'no-silent-fallback' lint rule seed.

**Connection to open seeds:** The observability focus directly supports the 'name the verification question' gate (agents need to state what they're verifying before acting). The memory and context articles suggest YAMLGraph should formalize 'invisible decisions' in memory handling (hardcoded defaults, deferred migrations) as a confession-style registry.

**Seed:** As agent observability becomes standard infrastructure, should YAMLGraph embed a mandatory 'trace annotation' layer — requiring every node to declare what observable state it expects and what it produces — making silent failures structurally impossible to hide?

---

## 2026-02-23: Git Report

## Repository Analysis: Last 3 Days Development Summary

Based on the git history, here's a **feature-level summary** of recent development:

### 🎯 Major Features Implemented

**1. FR-074: Outcall Probe-Recap (OC-005+) - APPROVED**
   - Voice callback system for probe recap operations
   - Redis session-lookup pattern for state management
   - ElevenLabs TTS integration path (Phase 1)
   - TTS completion tracking via Twilio marks
   - Tests for probe recap and outcaller TTS modules

**2. FR-071: Graph-Level Thinking Budget (REQ-YG-083)**
   - Extended thinking/reasoning support at graph node level
   - Schema validation (0 or ≥1024 tokens)
   - Automatic temperature=1 override for LLM calls
   - Linter warnings with 4 distinct codes (W071-1 through W071-4)
   - Full demo with configurable reasoning depth
   - 18 unit tests + 1 integration test
   - Complete requirement traceability

**3. FR-072: ElevenLabs STT Integration**
   - Streaming voice pipeline for outcaller
   - SDK-based Speech-To-Text integration tests
   - Raw bytes bug fixes and event name corrections
   - Twilio audio integration for voice modality

**4. FR-068: Chaplain Watch Loop**
   - Automated feature request workflow system
   - Plan → Judge → Amend cycle (max 3 iterations)
   - Inbox polling for topic files
   - Approved FRs auto-promote to feature-requests/
   - Dry-run mode for safe testing

### 🔧 Supporting Work

- **Code Refactoring**: FR-066/FR-067 CC distribution and edge compiler extraction
- **Template Improvements**: FR-064 Jinja2 AST migration for better variable extraction
- **Documentation**: Multiple diary entries capturing cognitive traps and architectural insights
- **Testing**: Comprehensive test coverage across telco, STT, thinking budget, and outcaller modules

### 📊 Development Statistics

- **Total commits analyzed**: 50+ recent commits
- **Files modified**: 60+ files
- **Key modules touched**: yamlgraph core, telco nodes, outcaller system, linter enhancements
- **Test cover
