# Feature Request: FR-665 — Worldgen Semantic Entity Dedup

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced
**Effort:** 1 day
**Requested:** 2026-07-03
**Judged:** 2026-07-03

## Summary

Add a semantic deduplication node to the worldgen pipeline that merges
`new_entities` referring to the same narrative role before skeleton creation.
Prevents parallel map slots from creating multiple canon pages for one person.

This is the second line of defense. FR-664 prevents orphan IDs at genesis.
FR-667 reduces the orphan surface by making genesis produce stubs only. This
FR catches the duplicates that worldgen itself creates during parallel
deepening — a problem that persists regardless of genesis quality because
map slots independently invent names for unnamed roles in backstory prose.

## Problem

Even with FR-664's genesis referential integrity gate, worldgen's `deepen`
map node can still produce semantic duplicates:

1. **Map parallelism**: 10 parallel slots (5 agent, 5 LLM) each enrich an
   entity independently. Each slot's `new_entities` output invents names for
   unnamed roles referenced in backstory prose.

2. **ID-only dedup**: `collect_red_links` deduplicates by exact ID. Since
   slot 1 says `bjorn` and slot 2 says `egil` for "Hilde's father", both
   pass as unique.

3. **Materialization**: `create_skeletons` writes a skeleton page for each
   red link. Ghosts become real canon. Next loop loads them as truth.

### Evidence (worldgen-657c.log)

```
red_links after collect (22 items, at least 10 phantoms):
  egils_wife + astrid + egil_wife        → 3 IDs, 1 person
  death_of_berengar_wife + wasting_fever → 2 IDs, 1 event
  ulf_death_bear_hunt + ulf_death_in_bear_hunt → 2 IDs, 1 event
  ulfgars_wife + ulfgar_wife             → 2 IDs, 1 person
```

FR-664 fixes the genesis birth defect. This FR fixes the worldgen
multiplication. Both are needed — genesis prevents orphan IDs, this FR
prevents parallel invention of new IDs.

## Acceptance Criteria

1. **AC-1**: New Python node `dedup_entities` inserted between `collect` and
   `create_skeletons` in `worldgen.yaml`. Takes `state.red_links` (list of
   entity dicts) and `state.canon_pages`, returns deduplicated
   `state.red_links` and `state.red_link_count`.

2. **AC-2**: Dedup strategy — deterministic first pass:
   - Exact suffix match: `egil_wife` and `egils_wife` → merge (keep shorter ID)
   - Prefix match: `ulf_death_bear_hunt` and `ulf_death_in_bear_hunt` → merge
   - `the_X` / `X` variants already caught by `validate_draft`

3. **AC-3**: Dedup strategy — LLM second pass (graph-tool via FR-658),
   gated on `red_link_count > 5` (constant in `dedup_entities.py`).
   Below that threshold, deterministic dedup is sufficient.
   A `dedup_check.yaml` graph registered as `type: graph` tool. Takes the
   surviving red_links list and returns clusters of IDs that refer to the
   same narrative role. The dedup node merges each cluster into one entity
   (keeps the first ID, drops the rest).

4. **AC-4**: Merged entities update `references` in the `deepened` results —
   any `updated_page` that referenced a dropped ID gets the reference
   rewritten to the surviving ID.

5. **AC-5**: Unit tests covering: exact suffix dedup, prefix dedup, LLM
   cluster merge, reference rewriting in deepened pages.

6. **AC-6**: Re-run worldgen with dedup enabled. Verify red_link_count
   decreases and no duplicate-cluster pages appear in canon after persist.

## Implementation Approach

### 1. Deterministic dedup pass (AC-2)

```python
def _deterministic_dedup(red_links: list[dict]) -> list[dict]:
    """Merge obvious duplicates without LLM."""
    by_id = {e["id"]: e for e in red_links}
    merged = set()

    for eid in list(by_id.keys()):
        if eid in merged:
            continue
        # Check the_X / X
        alt = f"the_{eid}" if not eid.startswith("the_") else eid[4:]
        if alt in by_id and alt not in merged:
            merged.add(alt)

        # Check possessive variants: egils_wife / egil_wife
        for other in list(by_id.keys()):
            if other == eid or other in merged:
                continue
            # Strip trailing s from first segment only
            def _strip_possessive(s: str) -> str:
                parts = s.split("_", 1)
                if parts[0].endswith("s"):
                    parts[0] = parts[0][:-1]
                return "_".join(parts)

            if _strip_possessive(other) == _strip_possessive(eid) and other != eid:
                merged.add(other)

    return [e for e in red_links if e["id"] not in merged]
```

### 2. LLM dedup pass (AC-3)

A `dedup_check.yaml` graph with one LLM node:

```yaml
# prompts/dedup_check.yaml
system: |
  Given a list of proposed new entities, identify clusters that refer to
  the same narrative role. Return clusters as a list of lists of IDs.
  Two entities are duplicates if they describe the same person, event,
  or place under different names.

schema:
  name: DedupResult
  fields:
    clusters:
      type: list[list[str]]
      description: "Each inner list contains IDs that are the same entity"
```

Registered as `type: graph` tool in worldgen via FR-658:

```yaml
tools:
  dedup_check:
    type: graph
    path: dedup_check.yaml
    input_mapping:
      entities: red_links_text
    output_key: clusters
```

### 3. Reference rewriting (AC-4)

After merging, scan all `deepened` results. For each `updated_page`, rewrite
any reference to a dropped ID → surviving ID. Fields to scan: `references`,
`participants`, `relationships.to`, `affected_locations`, `members`.

### 4. Graph edge insertion (AC-1)

```yaml
edges:
  - from: collect
    to: dedup_entities    # ← NEW

  - from: dedup_entities  # ← was: from: collect
    to: create_skeletons
    condition: red_link_count > 0
```

## Constraints

- Deterministic pass runs first (fast, no LLM cost). LLM pass only for
  remaining ambiguous cases.
- Does not change deepen prompts — this is a post-deepen cleanup.
- Does not block pipeline on dedup failure — falls through to create_skeletons
  with whatever survived.
- FR-658 (`type: graph` tool) must be landed first for AC-3.

## Alternatives Considered

| Approach | Verdict |
|----------|---------|
| Pre-assignment name registry | Requires anticipating all roles — brittle |
| Sequential map (kill parallelism) | 5x slower, defeats map purpose |
| Prohibit `new_entities` in deepen | Breaks red-link expansion entirely |
| Dedup only in `collect_red_links` | Can't do semantic dedup without LLM |

## Related

- [Diary: 2026-07-03 Parallel Invention Trap](../docs/diary/2026-07-03-parallel-invention-trap.md) — root cause analysis
- [FR-658](FR-658-graph-as-tool.md) — graph-as-tool infrastructure (enabler for AC-3)
- [FR-664](FR-664-genesis-referential-integrity.md) — genesis gate (prevents orphan ID birth)
- [FR-657](FR-657-agentic-event-deepening.md) — agent tools that exposed the problem
- [FR-667](FR-667-genesis-stub-pipeline.md) — genesis streamlining (reduces but doesn't eliminate the problem)

## Judgement

**Verdict: APPROVED with amendments.**

### Assessment

Architecturally sound — the two-pass strategy (deterministic then LLM) is
the right shape. The insertion point between `collect` and `create_skeletons`
is correct. The reference rewriting (AC-4) is essential and correctly scoped.

### Amendment 1: Harden deterministic dedup (AC-2)

The `replace("s_", "_")` possessive matching replaces ALL occurrences of `s_`
in a string, not just the possessive suffix. `crisis_management` → `crii_management`
is harmless (no false match), but the pattern is semantically wrong.

**Required change:** Replace the blanket `str.replace("s_", "_")` with a
targeted check: strip trailing `s` from the segment before the FIRST `_` only.
Implementation sketch: `eid.split("_", 1)` → strip `s` from segment 0 → rejoin.
This correctly matches `egils_wife` → `egil_wife` without touching interior
segments.

### Amendment 2: LLM pass cost control (AC-3)

The LLM dedup pass runs every worldgen iteration. With FR-664 + FR-667
reducing orphan birth, most iterations will have few red links — burning an
LLM call on 2-3 entities is waste.

**Required change:** Gate the LLM pass on `red_link_count > 5`. Below that
threshold, deterministic dedup is sufficient. Above it, the probability of
semantic duplicates justifies the cost. The threshold is a constant in
`dedup_entities.py`, not a graph variable.

### Enforcement Sequence

Land last. Depends on FR-658 (landed), FR-664 (gate), FR-667 (stubs reduce
surface). Can be enforced independently of FR-667 but benefits from it.
