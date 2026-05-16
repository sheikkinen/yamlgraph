# FR-404: The Philosopher's Book

**Status:** Approved
**Priority:** Medium
**Effort:** Large

## Problem

The Knowledge Graph in `.github/copilot-instructions.md` contains 21 named cognitive traps —
failure modes discovered through hundreds of AI-assisted development diary entries. These traps
are currently only present as YAML data in the instructions file. They deserve a richer treatment:
a philosophical examination of each trap, using the diary itself as primary source material.

## Objective

Generate a 21-chapter philosophical book — one chapter per trap — where each chapter:
1. Uses real diary entries as primary sources (via `search_diary` tool)
2. Traces the trap back to the One Law (boundary violation)
3. Argues why the cure works
4. Reflects on what the trap reveals about thinking itself

The book arc deepens from mechanical traps (Part I) through architectural, cognitive, adversarial,
to existential traps (Part V).

## Acceptance Criteria

- [ ] `examples/demos/philosopher_book/` exists with `graph.yaml`, `tools.py`, `prompts/`
- [ ] `tools.py` exports: `load_trap_list`, `search_diary`, `read_file`, `assemble_book`
- [ ] `load_trap_list` returns all 21 traps with correct part assignments
- [ ] `search_diary` searches `docs/diary/*.md` case-insensitively, respects `max_results`
- [ ] `read_file` validates allowed path prefixes and truncates at 8000 chars
- [ ] `assemble_book` produces markdown with table of contents and part structure
- [ ] 10 unit tests pass (REQ-YG-404)
- [ ] `yamlgraph graph lint` passes

## Implementation Notes

Status updated to Approved. Implementation:
- `examples/demos/philosopher_book/` — full demo scaffold
- `tests/unit/test_philosopher_book.py` — 10 unit tests, all passing
- `capabilities/CAP-150-philosopher-book-demo.yaml` — capability registration
- REQ-YG-404 registered in ARCHITECTURE.md
- Changelog fragment at `changelog/unreleased/fr404-philosopher-book.md`

Key decisions:
- `tools.py` hardcodes the 21 traps (stable data) rather than parsing copilot-instructions dynamically
- `copilot` nodes with `backend: cli` follow the ebook pipeline pattern exactly
- `sequential: true` on map node to avoid rate limiting
- `read_file` validates path prefixes (docs/, .github/, feature-requests/) as security boundary

## Alternatives Considered

**Dynamic parsing of copilot-instructions.md** — rejected because it would add fragile parsing
logic that breaks if the comment format changes. The 21 traps are stable, well-defined data.

**Parallel map execution** — rejected to avoid API rate limiting over 21 sequential LLM calls.

## Part Assignments

- Part I (Mechanical): downstream_fix, symptom_patch, partial_remediation, regex_fourth_exclusion, false_duplicate, plausible_wrong_answer
- Part II (Architectural): framework_costume, working_system_inertia, architecture_as_diagram, gate_checks_shape_not_substance, audit_as_ritual
- Part III (Cognitive): continuation_bias, quick_confidence, intent_drift, recent_changes_blindness
- Part IV (Adversarial): instruction_boundary_uncrossed, vendor_default_as_help, model_as_trusted_peer, infrastructure_self_exempt
- Part V (Existential): workspace_is_not_boundary, identity_collapse
