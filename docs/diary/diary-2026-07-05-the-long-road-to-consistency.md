# The Long Road to Consistency

**Date:** 2026-07-05
**Arc:** FR-637 → FR-689 (55 FRs, 82 commits, 31 diary entries, 10 days)
**Subject:** Reflection on the novel_fandom canon consistency journey

## The Arc

What started as "let's give the NPC example a proper canon schema" (FR-637, July 2) became a 55-FR arc spanning the full distance from hand-written seed YAML through LLM-generated pipelines to agent-orchestrated creation with mechanical dedup gates.

### Phase 1: The Seed (FR-637 → FR-654)
**The Ignored Floor.** Twelve FRs to take manually authored canon pages from flat YAML to typed, schema-validated, lane-annotated entities. Each FR tightened a boundary: the prompt is the asset (FR-655), the template is the boundary (FR-656). The recurring pattern: the LLM produced plausible output that failed Pydantic validation because the *prompt* didn't constrain what the *schema* required. The fix was always upstream — in the prompt, not in post-processing.

### Phase 2: The Agent (FR-655 → FR-667)
**The Tool Is the Boundary.** Genesis pipeline: premise → synopsis → agent creates entities. Worldgen: agent deepens thin entities. The shift from batch-processing to agentic creation exposed a new class of problems. The agent could *plan* but it couldn't *remember* what it had already created. FR-664 added referential integrity checking. FR-665 added semantic dedup. FR-667 wired them into a stub pipeline. Each was a standalone tool the agent was *told* to call.

### Phase 3: The Integration Trilogy (FR-683 → FR-686)
**The Boundary Collapses Inward.** FR-658 introduced graph-as-tool — a YAML graph callable by an agent as a tool. FR-683/684/685 converted ref_check and dedup_check into graph-tools. FR-686 rewrote genesis and worldgen as agent-first architectures where each `create_*` tool IS a sub-pipeline. The agent plans, the pipeline enforces. The boundary between "what the agent decides" and "what the system guarantees" became mechanical.

### Phase 4: Consistency (FR-689)
**The Dict That Ate the Twin.** LangSmith traces revealed: dedup_check worked correctly — the agent ignored it. The fix wasn't better prompting. It was integrating the gate INTO the create pipeline so the agent never gets a choice. The agent calls `create_character(id="hilde")` → dedup_pre_check runs → if exists, return "Refused" → agent never writes a file.

The variables injection bug was the last surprise: `entity_type: character` was declared in the YAML but never reached the state dict when running as a graph-tool. One line — `default_variables=child_config.raw_config.get("variables") or None` — fixed the root cause of every "unknown entity_type ''" error.

## What the Arc Taught

### 1. Advisory gates become mandatory gates
Every dedup mechanism started as "the agent should check." Every one was converted to "the pipeline checks, the agent receives the result." The pattern repeated across FR-664, FR-665, FR-684, FR-689. Advisory → mechanical is not an improvement; it's the only design that works.

### 2. The bug is always at the boundary
- FR-655: LLM output ↔ Pydantic schema (prompt didn't match schema)
- FR-664: Agent plan ↔ filesystem state (no ref check after creation)
- FR-689: Graph YAML ↔ graph-tool runtime (variables not injected)
- FR-689: Python dict ↔ filesystem truth (dict consumed collision evidence)

Zero bugs in LLM logic. Zero bugs in business logic. Every bug was at the seam between two systems that each worked correctly in isolation.

### 3. Prompting is cheaper than code, but code is cheaper than trust
Phase 1 tried to fix LLM output with prompt engineering. Phase 2 tried to fix agent behavior with instructions ("DEDUP MANDATE: always call dedup_check before creating"). Phase 3 stopped asking and started enforcing. The cost curve: a prompt change costs one minute but buys probabilistic compliance; a pipeline gate costs one hour but buys deterministic compliance. For anything that must be true, the hour is cheaper.

### 4. The container consumed the evidence
The most subtle bug: `_load_canon()` returns a dict keyed by `id`. When two files have the same ID in different type directories, the dict keeps only one. The collision detection code that iterates the dict can never see collisions — they were consumed by the data structure before the detector arrived. Never detect anomalies using a container that silently normalizes them.

### 5. Scale of the journey
55 FRs is not 55 features. It's 55 boundary discoveries. The system didn't get 55 new capabilities — it got 55 fewer places where reality could diverge from intent. The canon is consistent not because we added things, but because we closed gaps.

## The Numbers

| Metric | Value |
|---|---|
| FRs in arc | 55 (FR-637 → FR-689) |
| Commits | 82 in 10 days |
| Diary entries | 31 |
| Entity types | 7 (character, event, faction, location, rule, premise, synopsis) |
| Create pipelines | 6 (each a graph-tool sub-pipeline) |
| Genesis result | 47 entities, 46 unique create calls, 0 duplicates |
| Worldgen result | 50 deepen calls, 0 create calls, 0 duplicates |
| Final gate | PASS — no orphans, no violations, no collisions |

## Heuristic

**Consistency is not a feature — it's the absence of boundaries where truth diverges from intent.** Each FR in this arc didn't add something new. It closed a gap where two correct systems produced an incorrect result because they met at an unguarded seam.

## Seed

The canon is now consistent for a single genesis+worldgen pass. What happens when the pipeline runs incrementally — adding to existing canon, deepening entities across sessions, handling schema evolution? The dedup gate prevents duplicate IDs, but does it prevent duplicate *concepts*? Semantic dedup (FR-684's LLM check node) was retained in the pipeline but never triggered in this clean run. The real test is a second worldgen pass on the same canon — do the 5 entities that were deepened twice get deepened a third time? Does the system converge or diverge?
