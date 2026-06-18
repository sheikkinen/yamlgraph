# Feature Request: FR-516 - DM v2 Ranked Top-K Ledger Retrieval

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced (2026-06-17) — code + tests green (depends on FR-514)
**Effort:** ~0.5 day
**Requested:** 2026-06-17
**Plan:** [docs/plan-ledger-memory.md](../docs/plan-ledger-memory.md) §4.4, §6 (item 3)
**Depends on:** FR-514 (edge `valid_from` ordinal for recency). Soft: FR-515
(`valid_to` exclusion is a no-op until FR-515 lands — see Judgement).

## Judgement

The plan labelled this "independent of 1–2," but the ranking reads `valid_from`
(recency) and excludes `valid_to`-set edges — both edge-temporal fields. Resolved:

- **Hard dependency on FR-514**, which introduces the integer `valid_from` stamp
  (J2). Recency = `valid_from` ordinal, not the free-string `last_interaction`.
- **Graceful without FR-515:** before FR-515 no edge is ever closed, so the
  `valid_to is None` filter is a harmless no-op; FR-516 needs no FR-515 code.
- Inherits **J1** keying for cast-overlap matching.

**Verdict:** Approved, MEDIUM. Independent of FR-515/517 for scheduling; only the
`valid_from` stamp from FR-514 is required.

## Summary

Turn-1 context currently injects **all** active relationships. Replace this with
**ranked top-K** retrieval: select the relationships most relevant to the turn's
on-stage cast, scored by relevance × importance × recency, and inject only those.

## Value Statement

Long stories keep turn context bounded and on-point — a 40-chapter saga does not
drag thirty stale bonds into every turn's prompt.

## Problem

`running_scene` renders every active relationship from the inherited ledger into
turn-1 context (`format_world_state(..., relationships="active")`). For short
stories this is fine; for long ones it is unbounded context growth, diluting the
turn's actual cast with bonds whose parties are not on stage. This is exactly the
paging problem MemGPT (arXiv:2310.08560) and the salience-ranked retrieval of
Generative Agents (arXiv:2304.03442) exist to solve.

## Proposed Solution

### Ranking function (pure, deterministic where possible)

```python
def rank_relationships(rels, *, cast_names, k):
    # relevance: a party of the edge is on stage this turn (hard filter first)
    on_stage = [r for r in rels if set(r["between"]) & set(cast_names)]
    # importance: tension count (proxy for salience); recency: valid_from chapter
    on_stage.sort(key=lambda r: (len(r.get("tensions", [])),
                                 r.get("valid_from", "")), reverse=True)
    return on_stage[:k]
```

`running_scene` passes the current turn's `cast_names` and a configured `k` (e.g.
6) so turn context contains at most K cast-relevant relationships. Off-stage,
dormant, archived, and closed (FR-515 `valid_to` set) edges are excluded.

### Configuration

`k` lives in the graph defaults (a small integer), not hardcoded, so long-form vs
short-form runs can tune the budget.

## Acceptance Criteria

- [x] **A1 - Cast relevance filter.** A relationship with no on-stage party is
  excluded from turn context. Test: `test_offstage_relationship_excluded`.
- [x] **A2 - Bounded to K.** A ledger with >K cast-relevant relationships yields at
  most K rows in turn context. Test: `test_turn_context_bounded_to_k`.
- [x] **A3 - Salience ordering.** Among cast-relevant edges, higher-tension /
  more-recent rank first. Test: `test_ranking_prefers_salient_relationships`.
- [x] **A4 - Short-story parity.** With ≤K active relationships all on stage, none
  are dropped (interpreted as set-preservation, not exact input order, since
  ranking reorders by salience). Test:
  `test_short_story_ranking_keeps_all_relevant_edges`.

## Implementation

`world_state.rank_relationships(rels, cast_names, k)` (pure) hard-filters to
current + active + on-stage edges, sorts by (tension count, `valid_from`), and
keeps top-K. `turn_ops._retrieve_turn_ledger` ranks the inherited ledger using
`build_allowed_scene_cast` and `RETRIEVAL_TOPK` before `running_scene` formats it;
an empty allowed cast falls back to the full inherited ledger (bounds, never
blanks).

## Alternatives Considered

1. **Embedding-similarity retrieval (true Generative Agents relevance).** Deferred:
   adds an embedding dependency and I/O to a currently-pure path; cast-membership is
   a strong, free relevance signal for this domain. Revisit if cast-overlap proves
   insufficient.
2. **Let the LLM pick which relationships matter.** Rejected: pushes a deterministic
   bounding decision into the model; retrieval budgeting is a code concern.

## Related

- [docs/plan-ledger-memory.md](../docs/plan-ledger-memory.md) — north-star (§4.4).
- Generative Agents (arXiv:2304.03442), MemGPT (arXiv:2310.08560).
- [turn_ops.py](../examples/dungeon_master/api/turn_ops.py) — `running_scene`.
- [world_state.py](../examples/dungeon_master/api/world_state.py) — `format_world_state`.
