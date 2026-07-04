# Feature Request: FR-684 — Semantic Dedup as Graph-Tool

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged ✅
**Effort:** 1.5 days
**Requested:** 2026-07-04
**Judged:** 2026-07-04
**Depends:** FR-658 (graph-as-tool, enforced), FR-665 (deterministic dedup, enforced)

## Summary

Replace the stub LLM dedup pass in `dedup_entities.py` with a graph-tool
(`semantic_dedup.yaml`) that uses an LLM to cluster semantically identical
entities. Also give the `deepen_events` agent a `dedup_check` tool so it
can ask "does this entity already exist under a different name?" before
inventing new IDs — prevention at the source.

## Starting Point

FR-665 delivered deterministic dedup between `collect` and `create_skeletons`
in worldgen. Three merge rules: possessive stripping (`ulfs → ulf`), article
variants (`the_X → X`), stop-word prefix matches. The LLM dedup pass is
stubbed with a TODO:

```python
# LLM dedup would be invoked here via graph-tool (FR-658)
# TODO: Wire dedup_check graph-tool (FR-665 AC-3)
```

Verified results (2026-07-04):
- Deterministic dedup merged 3 entities across 3 worldgen iterations
- False positive: `ulfs → ulf` collapsed two distinct characters
- Surviving parallel invention: `gunnars_father` (Uwe) and `ulfs` (Ulf) both
  claim to be "Gunnar's father" — different IDs, no lexical overlap, invisible
  to string matching

The false positive and the surviving parallel invention are both problems
that only an LLM semantic comparison can solve.

FR-658 (`type: graph` tool) is enforced and provides the composition mechanism.

## Problem

1. **Deterministic dedup has false positives**: Possessive stripping merged
   `ulfs` (Gunnar's father, war-leader) with `ulf` (Frida's husband, trapper).
   Different characters, similar IDs. An LLM pass would compare summaries and
   keep them separate.

2. **Deterministic dedup misses semantic duplicates**: `gunnars_father` and
   `ulfs` both describe "Gunnar's father" but share no lexical ID overlap.
   Only a summary comparison or relationship-graph analysis can detect this.

3. **Agent creates duplicates at source**: `deepen_events` agent invents new
   entity IDs in `new_entities` without checking if the role already exists in
   canon. Dedup runs after the fact. A `dedup_check` tool would let the agent
   ask "does 'Gunnar's father' already exist?" before inventing a new ID.

## Acceptance Criteria

1. **AC-1**: New graph `examples/novel_fandom/semantic_dedup.yaml` — takes
   `candidates` and `canon_pages` (JSON strings or lists — graph-tool args
   arrive as `str`, JSON-parse at the entry node before the LLM prompt),
   uses an LLM to identify semantic duplicates (same narrative role,
   different IDs). Returns merge decisions.

2. **AC-2**: `semantic_dedup` registered as `type: graph` tool in
   `worldgen.yaml`:
   ```yaml
   semantic_dedup:
     type: graph
     path: semantic_dedup.yaml
     description: "Compare entities semantically. Returns merge map for duplicates."
     input_mapping:
       candidates: candidates
       canon_pages: canon_pages
     output_key: merge_map
   ```

3. **AC-3**: LLM pass wired at the **graph level**, not inside
   `dedup_entities.py` (a Layer-3 python tool cannot invoke graph-tools —
   no registry access, import-linter boundary). In `worldgen.yaml`:
   `dedup` (python, deterministic — unchanged) → router on
   `len(survivors) > threshold` → `semantic_dedup` as `type: tool_call` node
   → new python node `apply_merge_map` folds merge decisions into entities →
   `create_skeletons`. Below threshold, route straight to `create_skeletons`.
   Delete the TODO stub and `_LLM_DEDUP_THRESHOLD` from `dedup_entities.py`;
   the threshold lives in the router condition.

4. **AC-4**: `dedup_check` for the `deepen_events` agent is the **same**
   `semantic_dedup` graph — no second graph, no second prompt. The agent
   invokes it with a single-candidate list. If a distinct tool name aids the
   agent, register the same graph twice with different descriptions.
   Registered in `deepen_events` tools list.

5. **AC-5**: The LLM prompt in `semantic_dedup.yaml` compares entity summaries,
   relationships, and types — not just IDs. Groups entities by narrative role.
   Handles `len(candidates) == 1` (compare one entity against canon roles).
   Returns `{merge_map: {dropped_id: surviving_id}, reasoning: str}`.

6. **AC-6**: False positive guard — the prompt instructs: omit uncertain
   pairs from `merge_map` entirely (no numeric confidence field). The prompt
   includes the `ulf`/`ulfs` false positive as a negative example: "Two
   characters named Ulf with different roles are NOT duplicates."

7. **AC-7**: Tests split by determinism:
   - Unit (mock LLM, CI): router threshold routing, `apply_merge_map`
     application, JSON normalization, prompt contains the negative example.
   - Integration (API-key-gated, not CI-blocking): LLM merges
     `gunnars_father`/`ulfs` (same role, different IDs); keeps `ulf`/`ulfs`
     separate (same name, different roles). Plus fixture-based prompt
     regression (golden transcript).
   - Agent calls `dedup_check` before creating (mock LLM).

## Implementation Approach

1. Write `semantic_dedup.yaml` — JSON-normalize entry node + prompt + LLM node
2. Write `prompts/semantic_dedup.yaml` — structured prompt with negative
   examples, single-candidate handling
3. Register as `type: graph` tool in `worldgen.yaml`
4. Rewire `worldgen.yaml`: router after `dedup` → `tool_call` node →
   `apply_merge_map` (new python node) → `create_skeletons`
5. Remove TODO stub + `_LLM_DEDUP_THRESHOLD` from `dedup_entities.py`
6. Add `dedup_check` (same graph) to `deepen_events` agent tools
7. Tests with mock LLM; API-key-gated integration tests

## Constraints

- Deterministic dedup stays as first pass — cheap and fast for obvious cases.
- LLM dedup is second pass, gated on entity count threshold (router condition
  in YAML, not Python).
- `dedup_check` for agent is the same graph invoked with a single-candidate
  list — not a separate graph.
- The LLM prompt must include negative examples to prevent false positives.
- Graph-tool returns structured text, not raw Pydantic — agent parses it.
- Three-layer boundary: `nodes/*.py` never invokes graph machinery.

## Risks

- **LLM cost**: Each dedup call is an LLM invocation. Mitigated: threshold
  gate, batch comparison (not per-entity), and deterministic first pass
  handles the easy cases.
- **False negatives**: LLM might miss duplicates. Mitigated: deterministic
  pass catches lexical variants, LLM catches semantic ones. Together they
  cover more ground than either alone.

## Related

- [FR-658](FR-658-graph-as-tool.md) — enables `type: graph` tool
- [FR-665](FR-665-worldgen-semantic-dedup.md) — deterministic dedup (current)
- [FR-683](FR-683-ref-integrity-graph-tool.md) — ref integrity graph-tool
- Diary: 2026-07-04 "The Stub Kills the Hydra" — documents the false positive
  and surviving parallel invention

## Judgement

**Verdict: APPROVED — scope frozen with amendments below.**

### Assessment

Raw-output evidence is concrete and could not be fabricated: `ulfs → ulf`
false-positive merge (two distinct characters), `gunnars_father`/`ulfs`
parallel invention with zero lexical overlap. The TODO stub is verified at
`dedup_entities.py:162–165` with `_LLM_DEDUP_THRESHOLD = 5`. This is exactly
the class of problem doctrine assigns to LLM over regex. Substance gate passes.

### Issues Found & Required Amendments

1. **AC-3 violates the three-layer architecture.** "`dedup_entities.py` wires
   the LLM pass — invoke the `semantic_dedup` graph-tool" is impossible from
   a Layer-3 Python tool: node functions receive only `state`, have no access
   to `callable_registry`, and importing graph machinery into `nodes/` breaks
   the import-linter boundary. The wiring belongs in YAML (Logic layer).

   **Amendment:** Replace AC-3 with graph-level composition in
   `worldgen.yaml`: `dedup` (python, deterministic — unchanged) → router on
   `len(survivors) > threshold` → `semantic_dedup` as `type: tool_call` node
   (graph-tool via callable_registry, per FR-658) → new small python node
   `apply_merge_map` folds merge decisions into entities → `create_skeletons`.
   Below threshold, route straight to `create_skeletons`. Delete the TODO
   stub and `_LLM_DEDUP_THRESHOLD` from `dedup_entities.py`; the threshold
   lives in the router condition.

2. **Graph-tool args are strings.** Same as FR-683 amendment 2:
   `input_mapping` fields are `str`-typed. `semantic_dedup.yaml` must
   JSON-parse `candidates` and `canon_pages` at its entry node before the
   LLM prompt. Add to AC-1.

3. **AC-4 ambiguity resolved — no second graph.** `dedup_check` for the agent
   is the SAME `semantic_dedup` graph-tool registration, invoked by the agent
   with a single-candidate list. Do not build a second "lighter" graph or
   prompt. The prompt must handle `len(candidates) == 1` (compare one entity
   against canon roles) — add one line to the prompt spec in AC-5. If a
   distinct tool name aids the agent, register the same graph twice with
   different descriptions; zero new YAML.

4. **AC-7 test claim overreaches.** "LLM dedup correctly merges
   `gunnars_father`/`ulfs`" is a live-LLM assertion — flaky in CI. Split:
   unit tests with mock LLM assert the plumbing (router threshold, merge_map
   application, JSON normalization, prompt contains negative example);
   the `gunnars_father`/`ulfs` and `ulf`/`ulfs` cases become an integration
   test marked for API-key-gated runs, plus fixture-based prompt regression
   (golden transcript). CI must not depend on live-LLM judgement calls.

5. **Confidence field.** AC-6 says "only merges when confidence is high" but
   AC-5's schema has no confidence signal. Freeze schema as
   `{merge_map: {dropped_id: surviving_id}, reasoning: str}` where the prompt
   instructs: omit uncertain pairs from merge_map entirely. No numeric
   confidence field — a plausible number would be theatre.

### Frozen Scope

ACs 1–7 as amended — **amendments folded into the AC, Implementation, and
Constraints sections above**. Enforce after FR-683 (shares the
JSON-normalization pattern). Effort estimate holds at 1.5 days.
