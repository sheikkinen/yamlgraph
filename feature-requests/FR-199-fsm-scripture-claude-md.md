# Feature Request: Upgrade FSM CLAUDE.md to Full YAMLGraph Doctrine

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-13

## Summary

Replace the FSM project's four-line principle summary (TDD/DRY/KISS/YAGNI) in `fsm/CLAUDE.md`
with the full YAMLGraph doctrine: The 10 Commandments, Sermon of the Chaplain, Rite of Correction,
Agents' prayer, and the Knowledge Graph of the Diary — adapted for FSM paths, package names,
and anti-patterns.

## Value Statement

FSM contributors get the same cognitive scaffolding and trap-awareness as YAMLGraph contributors,
eliminating doctrine drift between the two codebases that share CI, Scripture, and release flow.

## Problem

`fsm/CLAUDE.md` ends with:

```
## Project Principles

- **TDD**: Test-first development
- **DRY**: Variable interpolation at engine-level (not per-action)
- **KISS**: Actions return events, engine handles transitions
- **YAGNI**: Build minimal features, extend via custom actions
```

The four principles are true but incomplete. They omit:

- The 10 Commandments (research-first, TDD mandate, entropy control, etc.)
- Sermon of the Chaplain (Plan → Judge → Enforce → Purge → Submit → Distill lifecycle)
- Rite of Correction (Inspect → Amend → Escalate)
- Agents' prayer (callsite-fix heuristics)
- Knowledge Graph of the Diary (traps, cures, process patterns)
- Conventional Commits + FR reference enforcement
- noqa Confession requirement
- Anti-patterns table
- Requirement traceability (`@pytest.mark.req`) — if/when FSM adopts REQ-IDs

Agents operating only in `fsm/` receive doctrine-lite guidance and are likely to reproduce
traps already graduated to YAMLGraph Scripture (e.g., `downstream_fix`, `quick_confidence`,
`symptom_patch`).

## Proposed Solution

Rewrite `fsm/CLAUDE.md` to include all doctrinal sections from the root `CLAUDE.md` / custom
instructions, with the following FSM-specific adaptations:

| YAMLGraph | FSM equivalent |
|-----------|---------------|
| `yamlgraph/` Python package | `src/statemachine_engine/` |
| `graphs/*.yaml` | `config/*.yaml` / `examples/` |
| `prompts/*.yaml` | N/A (no LLM prompts) |
| `create_llm()` | `ActionLoader` / `BaseAction` |
| `execute_prompt()` | `BaseAction.execute(context)` |
| `PipelineError` | FSM error handling in `engine.py` |
| `state_key` | `context[key]` |
| `feature-requests/` | `../feature-requests/` (mono-repo root) |
| `changelog/unreleased/` | `../changelog/unreleased/` (mono-repo root) |
| `docs/diary/` | `../docs/diary/` (mono-repo root) |
| `.chaplain/inbox/` | `../.chaplain/inbox/` (mono-repo root) |

Sections to add verbatim (or near-verbatim where paths differ):

1. **The 10 Commandments** — unchanged; universal
2. **Sermon of the Chaplain** — unchanged; universal
3. **Rite of Correction** — unchanged; universal
4. **Agents' prayer** — unchanged; universal
5. **Knowledge Graph of the Diary** — unchanged; universal (traps are language/framework agnostic)
6. **Conventional Commits + FR enforcement** — note that FSM PRs follow root repo conventions
7. **Changelog fragments** — note shared `changelog/unreleased/` at mono-repo root
8. **noqa Confessions** — note shared `docs/confessions.md` at mono-repo root
9. **Anti-patterns table** — adapted for FSM idioms (see table above)
10. **Diary obligation** — final task on any list is a diary entry at `../docs/diary/`

The existing FSM-specific content (Architecture, Usage Patterns, Communication Architecture,
Troubleshooting, Development Commands) is preserved unchanged above the doctrine sections.

## Acceptance Criteria

- [ ] `fsm/CLAUDE.md` contains all 10 Commandments verbatim
- [ ] `fsm/CLAUDE.md` contains Sermon of the Chaplain verbatim
- [ ] `fsm/CLAUDE.md` contains Rite of Correction verbatim
- [ ] `fsm/CLAUDE.md` contains Agents' prayer verbatim
- [ ] `fsm/CLAUDE.md` contains the Knowledge Graph of the Diary verbatim
- [ ] Path/package adaptation table is present and accurate for FSM project layout
- [ ] Anti-patterns table is present with FSM-specific wrong/correct pairs
- [ ] All existing FSM-specific sections (Architecture, Usage, Troubleshooting) are preserved intact
- [ ] The four-line YAGNI/TDD/DRY/KISS block is replaced, not duplicated
- [ ] Diary entry written in `docs/diary/` after implementation
- [ ] No new Python code, tests, or CI changes required (documentation-only change)

## Alternatives Considered

1. **Symlink `fsm/CLAUDE.md` → root `CLAUDE.md`**: Rejected — FSM-specific architecture,
   usage patterns, and troubleshooting content would be lost; agents need project-local context
   interleaved with doctrine.

2. **Include directive / shared fragment**: Rejected — CLAUDE.md is consumed by AI agents as
   plain markdown; no include mechanism exists in the reading pipeline.

3. **Keep minimal and rely on root CLAUDE.md being in context**: Rejected — agents scoped to
   `fsm/` may not receive the root file; doctrine must travel with the project.

4. **Single shared `.github/CLAUDE.md`**: Rejected — not a standard path; agents look for
   `CLAUDE.md` at the working directory root.

## Related

- `fsm/CLAUDE.md` — current file to be upgraded
- `CLAUDE.md` — root YAMLGraph doctrine (canonical source)
- `feature-requests/FR-198-fsm-chaplain-pipeline.md` — added Chaplain pipeline to FSM
- `feature-requests/FR-193-mass-graduation-scripture-patterns.md` — mass graduation of traps
- `docs/diary/` — destination for post-implementation reflection
