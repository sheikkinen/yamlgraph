# The Dict That Ate the Twin

**Date:** 2026-07-05
**FR:** FR-689 (Genesis Canon Consistency — Integrated Dedup Gate)
**Trap:** downstream_fix → normalize at entry boundary

## Situation

FR-689 integrated dedup checks into the create_* pipelines as a mechanical gate. The final piece was cross-type ID collision detection in `final_gate` — detecting when two canon entities in different type directories share the same `id`.

## Trap

`final_gate` used `_load_canon()` which returns a dict keyed by `id`. The Python dict contract is simple: last write wins. When `event/survival_truce.yaml` and `rule/survival_truce.yaml` both exist, the dict keeps only one. The collision detection loop then sees exactly one type per ID, and `len(types) > 1` is never true.

The test was correctly RED — it set up two files with the same ID in different type dirs and expected `valid=False`. The production code saw `valid=True` because the collision was consumed by the data structure before the detection code could observe it.

## Insight

**The container consumed the evidence before the detective arrived.** A dict keyed by the field you're checking for duplicates is the worst possible data structure for detecting duplicates of that field. The `dedup_pre_check` function already did this correctly — it scanned the filesystem directly, never loading into a dict.

This is the `downstream_fix` trap inverted: we weren't fixing downstream, we were *observing* downstream — after the dict had already deduplicated the very thing we wanted to count.

## Cure

Replace the dict iteration with a direct filesystem scan:

```python
for type_dir in canon.iterdir():
    for f in type_dir.glob("*.yaml"):
        page = yaml.safe_load(f)
        id_types[page["id"]].append(dir_type)
```

Now the detection happens at the source — the filesystem — before any container can eat the evidence.

## Collateral

Three old tests (FR-684, FR-664) still asserted `dedup_check in agent["tools"]`. FR-689 removed standalone dedup_check from agents (replaced by built-in gate in create_* pipelines). Updated these to assert the new contract: `update_refs in agent["tools"]` and `dedup_check not in tools`.

## Heuristic

**Never detect duplicates using a container that deduplicates.** If the data structure you're reading into cannot represent the anomaly you're looking for, the anomaly is invisible by construction. Scan the raw source.

## Seed

Could `_load_canon()` itself be made collision-aware — returning a list of collisions alongside the dict — so that every downstream consumer gets both the canonical view and the collision report? Or is the filesystem scan the correct boundary for this class of check?
