# Feature Request: FR-664 — Genesis Referential Integrity Gate

**Priority:** HIGH
**Type:** Fix
**Status:** Enforced
**Effort:** 0.5 day
**Requested:** 2026-07-03
**Judged:** 2026-07-03

## Summary

Add a referential integrity validation gate to `persist_genesis` so that every
ID appearing in any `to:`, `participants:`, `references:`, `members:`, or
`affected_locations:` field is defined as a full entity in the same output.
Prevents orphan IDs from being born — the root cause of the parallel-invention
duplicate explosion documented in the 2026-07-03 diary entry.

This gate applies regardless of genesis shape — it guards the current
full-character pipeline and the future stub-only pipeline (FR-667) equally.
FR-667 reduces the orphan surface (stubs have fewer cross-references), but
the gate ensures whatever genesis produces is internally consistent.

## Problem

Genesis `structure_world` produces a single JSON object with all seed entities.
The LLM creates relationship references to entities it never instantiates:

```yaml
# hilde.yaml (genesis output)
relationships:
  - to: aldric        # ← never created as a page
    kind: father
    valence: love and grief

# ruedeger.yaml (genesis output)
relationships:
  - to: hermann       # ← never created as a page
    kind: enemy killed
  - to: alric         # ← never created as a page
    kind: brother (deceased)
```

These orphan IDs are the birth defect. When worldgen's `deepen` map node
encounters "Hilde's father" in backstory prose, each parallel slot invents a
different name (bjorn, egil, leif, aldric, father_of_hilde_and_arnulf, hermann)
because the canonical ID was never instantiated. 30 genesis files → 60 after
one worldgen run, half ghosts.

### Root Cause Chain

```
synopsis says "her father" (unnamed)
  → genesis_roster extracts 2-4 principals (father excluded — dead before story)
  → structure_world invents "aldric" in relationship.to but never creates aldric.yaml
  → worldgen deepen × 10 slots each re-invent the father independently
  → collect_red_links dedup by ID → bjorn ≠ egil ≠ leif → all pass
  → create_skeletons → 6 ghost files for 1 person
```

The fix is at the genesis boundary — normalize where identity enters the system.

## Acceptance Criteria

1. **AC-1**: `structure_world.yaml` prompt includes explicit rule: "Every ID
   in any `to`, `participants`, `references`, `members`, or
   `affected_locations` field MUST appear as a fully defined entity in your
   output. If you mention a dead parent or historical figure, include a minimal
   character entry with `status: dead` and a one-line summary."

2. **AC-2**: New Python function `validate_referential_integrity(pages)` in
   `persist_genesis.py` that scans all pages for cross-reference integrity.
   Returns `{"valid": bool, "orphan_ids": list[str], "violations": list[str]}`.

3. **AC-3**: `persist_genesis` calls `validate_referential_integrity` before
   writing. If orphan IDs found, logs warnings with the full violation list.
   Does NOT block writing (genesis is expensive to re-run) — but the output
   is visible for debugging.

4. **AC-4**: Unit tests covering: valid canon passes, orphan `to:` target
   detected, orphan participant detected, orphan reference detected, orphan
   member detected, orphan `affected_locations` detected.

5. **AC-5**: Re-run genesis with the updated prompt and verify the output has
   zero orphan IDs. Log the validation result.

## Implementation Approach

### 1. Prompt constraint (AC-1)

Add to `structure_world.yaml` system prompt:

```
- REFERENTIAL INTEGRITY: Every ID appearing in any `to`, `participants`,
  `references`, `members`, or `affected_locations` field MUST be defined
  as a full entity in this output. If you reference a dead character
  (e.g. a killed parent), include them as a character with status: "dead"
  and a summary. No dangling IDs — every cross-reference must resolve.
```

### 2. Validation function (AC-2)

```python
def validate_referential_integrity(
    pages: list[dict],
) -> dict[str, Any]:
    defined_ids = {p["id"] for p in pages if "id" in p}
    orphans = set()

    for page in pages:
        # relationships.to
        for rel in page.get("relationships", []):
            to = rel.get("to", "") if isinstance(rel, dict) else ""
            if to and to not in defined_ids:
                orphans.add(to)

        # participants, references, members, affected_locations
        for field in ("participants", "references", "members",
                      "affected_locations"):
            for ref in page.get(field, []):
                ref_id = ref if isinstance(ref, str) else ref.get("id", "")
                if ref_id and ref_id not in defined_ids:
                    orphans.add(ref_id)

    violations = [f"orphan ID '{oid}' referenced but never defined"
                  for oid in sorted(orphans)]
    return {
        "valid": len(orphans) == 0,
        "orphan_ids": sorted(orphans),
        "violations": violations,
    }
```

### 3. Integration in persist_genesis (AC-3)

Call `validate_referential_integrity` on the flattened pages list before
passing to `_persist_impl`. Log violations as warnings.

## Constraints

- No new graph nodes — this is a prompt edit + validation in existing persist.
- Validation is warn-only, not blocking (genesis is expensive).
- No LLM involved in validation — purely deterministic.
- Does not change worldgen — that's FR-665.

## Related

- [Diary: 2026-07-03 Parallel Invention Trap](../docs/diary/2026-07-03-parallel-invention-trap.md) — root cause analysis
- [FR-655](FR-655-genesis-graph.md) — genesis pipeline
- [FR-656](FR-656-tighten-genesis-prompt.md) — previous prompt tightening
- [FR-657](FR-657-agentic-event-deepening.md) — agent tools that exposed the problem
- [FR-665](FR-665-worldgen-semantic-dedup.md) — downstream dedup (addresses multiplication)

## Judgement

**Verdict: APPROVED — enforce as written.**

### Assessment

Clean, minimal, correctly scoped. The validation function is deterministic,
the prompt constraint is explicit, and warn-only is pragmatic for an expensive
pipeline. No over-engineering — a Python function and a prompt edit.

### Dependency Note

AC-1 targets `structure_world.yaml`. FR-667 deletes that prompt. This is
correct — FR-664 lands first, guards the current genesis shape. FR-667 AC-3
explicitly carries the referential integrity constraint forward into
`generate_stubs.yaml`. The gate function (AC-2) survives both genesis shapes.

### Enforcement Sequence

Land first. FR-667 and FR-665 depend on this gate existing.
- [FR-667](FR-667-genesis-stub-pipeline.md) — genesis streamlining (reduces orphan surface)
