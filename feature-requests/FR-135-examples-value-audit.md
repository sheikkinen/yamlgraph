# Feature Request: Examples & Demos Value Audit and Cleanup

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 2 days
**Requested:** 2026-03-08

## Summary

Audit all examples and demos for value, update the examples README to document 12 unlisted demos and 4 unlisted top-level examples, remove or archive low-value entries, and enforce a minimum quality bar (README + runnable graph) for inclusion.

## Value Statement

Contributors and newcomers find a curated, accurate examples index instead of discovering half the demos by accident, reducing onboarding friction and preventing drift between disk and documentation.

## Problem

The `examples/` directory contains 18 top-level examples and 31 demos, but the `examples/README.md` index is incomplete and stale:

1. **13 demos exist on disk but are missing from the Demos Index table:** `commit-delta-gate`, `innovation_matrix`, `interactive_tool`, `multi-turn`, `novel_generator`, `pipeline_audit`, `req-cross-check`, `safety-guards`, `session-continuation`, `session-test`, `tavily_rag`, `thinking`, `verified-search`.
2. **6 top-level examples are completely undocumented:** `copilot/`, `diary_digest/`, `ebook/`, `enforce/`, `openai_proxy/`, `rtm-hello/`.
3. **No quality gate** — there is no defined minimum bar for an example to be listed (some have full test suites, others are bare shell scripts).
4. **Category confusion** — `demos/` mixes learning demos (hello, router), utility scripts (run-analyzer, pipeline_audit, req-cross-check, commit-delta-gate), and FR validation tests (session-test, interrupt). These serve different audiences.

## Proposed Solution

### Phase 1: Classify and document (1 day)

Add every on-disk example/demo to `examples/README.md` with an accurate entry. Organize the Demos Index into three sections:

```markdown
## Demos Index

### Learning Demos
<!-- Ordered learning path + additional standalone demos that teach a single concept -->
| Demo | Node Types | Description |
|------|------------|-------------|
| hello | llm | Minimal example — start here |
| router | router | Conditional routing |
| ...existing + newly listed demos... |

### Utility Demos
<!-- Tools for codebase analysis — useful for maintainers, not for learning -->
| Demo | Description |
|------|-------------|
| pipeline_audit | Cross-pipeline structural analysis |
| req-cross-check | Architecture traceability audit |
| run-analyzer | Run output analysis utilities |
| commit-delta-gate | Inquisitor commit-delta gate logic |

### FR Validation Demos
<!-- Used primarily to validate specific feature requests -->
| Demo | FR | Description |
|------|-----|-------------|
| session-test | FR-105 | Copilot session continuation test |
| interrupt | — | Subgraph interrupt integration tests |
```

Add the 6 missing top-level examples to the Quick Reference table (`copilot/`, `diary_digest/`, `ebook/`, `enforce/`, `openai_proxy/`, `rtm-hello/`).

### Phase 2: Enforce minimum quality bar (0.5 day)

Define and document the minimum inclusion criteria at the top of `examples/README.md`:

```markdown
## Inclusion Criteria

Every listed example must have:
1. A `README.md` explaining what it does and how to run it
2. At least one runnable YAML graph (or a `demo.sh` for script-only demos)
3. A clear statement of which YAMLGraph feature it demonstrates
```

Audit each entry against these criteria. Examples that fail get either:
- **Fixed** (add missing README — trivial for most), or
- **Moved to `purgatory/`** if they provide no unique value

### Phase 3: Prune and archive (0.5 day)

Candidates for removal/archival (move to `purgatory/`):
- `demos/commit-delta-gate/` — shell script only, no YAML graph, demonstrates Inquisitor internals not YAMLGraph features
- `demos/session-test/` — redundant with `demos/session-continuation/`; pure FR-105 validation

No examples should be deleted — `purgatory/` preserves history.

## Acceptance Criteria

- [x] Every demo in `examples/demos/` has a corresponding entry in `examples/README.md`
- [x] Every top-level example in `examples/` has a corresponding entry in `examples/README.md`
- [x] Demos Index is split into Learning / Utility / FR Validation sections
- [x] Inclusion criteria documented at top of `examples/README.md`
- [x] Each listed entry meets the minimum quality bar (README + runnable artifact)
- [x] Low-value entries moved to `purgatory/` with a note in their original location
- [x] `yamlgraph graph lint examples/demos/hello/graph.yaml` still passes (smoke test)
- [x] No code changes — documentation and file moves only

## Alternatives Considered

1. **Automated staleness linter** — A lint rule checking README vs disk would catch future drift, but the immediate problem is classification and curation, not detection. A linter could be a follow-up FR.
2. **Separate `examples/internal/` directory** — Moving utility/FR-validation demos out of `demos/` would fix the category confusion at the filesystem level, but adds migration overhead. The README sectioning achieves the same goal with less churn.
3. **Delete low-value demos entirely** — Rejected; `purgatory/` preserves history per project convention. Some "low-value" demos may have educational value in their commit history.

## Related

- `examples/README.md` — the file to be updated
- FR-090 (docs-projects-vs-examples) — established the projects/ vs examples/ distinction; this FR addresses the _within-examples_ organization
- FR-096 (fr-template-demo-plan) — demo planning template
- `purgatory/` — archive for removed content

## Judgement

**Verdict: APPROVED** — Scope frozen. Authority granted to implement.

**Reviewed:** 2026-03-08

**Findings:**

1. **Scope is clear and minimal.** Documentation + file moves only, no code changes. The three-phase breakdown (classify → quality bar → prune) is well-sequenced.

2. **Factual corrections applied during review:**
   - Demo count: 13 missing (not 12) — the list was correct, the number was wrong.
   - Top-level examples: 6 missing (not 4) — `ebook/` was omitted from both the count and the list.

3. **Phase 2 is lighter than described.** Audit shows 31/32 demos already have both a README and runnable YAML. Only `commit-delta-gate` (shell-only, no README, no YAML) and `streaming` (no YAML) fail the quality bar. Phase 2 effort is ~0.25 day, not 0.5 day. The quality bar definition is still valuable as a documented gate for future additions.

4. **Acceptance criteria are measurable.** All 8 criteria are binary pass/fail. The lint smoke test anchors correctness.

5. **Architecture alignment confirmed.** Builds on FR-090 (projects vs examples) and FR-096 (demo plan template). Uses `purgatory/` convention. The three-category split (Learning / Utility / FR Validation) is a reasonable first cut; exact classification of each demo should be decided during implementation.

6. **No contradictions or ambiguities found.** The alternatives section is well-reasoned; the "README sectioning over filesystem restructure" decision is correct for minimizing churn.

**Scope freeze:** The FR covers `examples/README.md` updates, inclusion criteria documentation, and purgatory moves. No new scripts, no CI changes, no code modifications.
