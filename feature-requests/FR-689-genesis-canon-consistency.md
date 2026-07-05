# Feature Request: FR-689 — Genesis Canon Consistency — Integrated Dedup Gate

**Priority:** HIGH
**Type:** Bug
**Status:** Judged ✅ (consolidated — amendments folded into body; Judgement retained as decision history)
**Effort:** 1–2 days
**Requested:** 2026-07-05
**Judged:** 2026-07-05
**Depends:** FR-686 (agent-first rewrite — amends its Finding 1 ruling and AC-5)

## Summary

Genesis produces duplicate entities because dedup is advisory (separate tool the agent can ignore). Integrate the dedup LLM into each `create_*` pipeline so it's a mechanical gate that blocks writes.

## Value Statement

Genesis produces a clean, duplicate-free canon on first run. Dedup enforcement is structural, not dependent on agent judgment.

## Problem

LangSmith trace `019f32f8-aa56-7780-90d8-83dd27cd5476` shows three bugs:

1. **Agent ignores dedup results**: `dedup_check` correctly returned `merge_map: {"ulf_asche": "hildes_father"}`. Agent acknowledged it (LLM #11: "Many of my candidates are duplicates"), then later created `ragnar` anyway because `ref_check` flagged a broken reference in event `death_of_ragnar`. Agent reasoned (LLM #15): "The event `death_of_ragnar` references 'Ragnar' but no character entity exists with that ID" — and created a duplicate to "fix" the reference. The dedup detection worked; the enforcement was missing.

2. **Dual synopsis**: `persist_synopsis` writes without clearing existing synopses. Canon ends up with two conflicting synopses (one names "Runa," the other "Frida" for the same keeper-of-rites role).

3. **Cross-type ID collision**: `survival_truce` exists as both `event/` and `rule/`. `final_gate` doesn't detect this.

## Root Cause

Dedup is a separate advisory tool. The agent calls `dedup_check`, gets a correct answer, then independently calls `create_character` which writes to disk immediately. Nothing in the `create_*` pipeline prevents the write. The agent can bypass dedup entirely — which is exactly what happened when ref_check pressure overrode prior dedup knowledge.

```
Current flow (advisory):
  Agent → dedup_check → merge_map (agent ignores) → create_character → written to disk ✗

Required flow (mechanical):
  Agent → create_character → [dedup LLM gate] → refuse/persist
```

## Rejected Approaches

1. **Prompt-level fix** ("honor merge_map"): Agent can ignore it. The traced failure proves agents override correct tool results under pressure from other tools. Prompt instructions are not enforcement.

2. **String matching in persist_entity**: Regex and name/summary comparison won't catch semantic near-misses. The dedup problem is inherently semantic — "Hilde's father" and "Ragnar" are the same person with no string overlap.

## Proposed Solution

### Fix 1: Integrate dedup into creation pipelines (genesis + worldgen)

Change each `create_*.yaml` (six genesis tools + worldgen `create_skeleton.yaml`) from:
```
persist → prefetch → check → END
```
to:
```
pre-check (python) → [route] → dedup gate (LLM) → [route] → persist → prefetch → check → END
       ↓ (exact-ID / cross-type collision)      ↓ (duplicate found)
      END → refusal                            END → "Refused: duplicate of {surviving_id}. Use update_refs to repoint existing references."
```

**Deterministic checks first, at the write boundary.** Exact-ID existence
and cross-type ID collision are deterministic — a python pre-check node
short-circuits before any LLM call. The dedup LLM judges only the
semantic near-miss it alone can see.

**Dedup gate (LLM).** Reuse `semantic_dedup.yaml` logic (LLM compare at
temp 0.1), but input is the **canon digest**, not full canon (FR-686
Finding 2 quadratic trap). If the candidate duplicates an existing
entity, short-circuit to END with the refusal message — the agent cannot
write. Gate prompt bias: refuse only on high-confidence identity (same
referent, not same archetype — ulf/ulfs negative example from FR-684);
when uncertain, permit. A leaked duplicate is caught by final audit or
worldgen dedup; a false merge is silent and unrecoverable — bias toward
the recoverable error.

Two LLM calls per create (gate + advisory check), priced and accepted —
supersedes FR-686's one-call-per-create accounting.

Remove `dedup_check` from both agents' standalone tool lists — it's now
built into every creation tool (supersedes FR-686 AC-5; record in FR-686
at enforcement).

### Fix 2: `update_refs` repair tool (deadlock prevention)

A refusal without a repair path is a deadlock, not a gate: in the traced
scenario the agent created `ragnar` precisely to repair a dangling
reference — refusing the create while the dangling ref remains traps the
agent between the dedup gate and the final gate. Add a deterministic
python tool to the genesis agent:

```
update_refs(old_id="ragnar", new_id="hildes_father")
```

Rewrites reference fields (participants, related_to, members, faction,
affected_locations) across canon from one ID to another. The refusal
message names this tool as the repair action.

### Fix 3: `persist_synopsis` — clear before write

```python
def persist_synopsis(state: dict[str, Any]) -> dict[str, Any]:
    canon = _canon_path()
    synopsis_dir = canon / "synopsis"
    if synopsis_dir.exists():
        for f in synopsis_dir.glob("*.yaml"):
            f.unlink()
    # ... existing write logic
```

### Fix 4: Cross-type ID collision detection

Primary check lives in the write-boundary pre-check (Fix 1);
`final_gate` keeps the same check as backstop audit (the gate that
cannot be sweet-talked):

```python
from collections import defaultdict
id_types = defaultdict(list)
for page in all_pages:
    id_types[page["id"]].append(page["type"])
collisions = {k: v for k, v in id_types.items() if len(v) > 1}
if collisions:
    result["valid"] = False
    result["id_collisions"] = collisions
```

### TDD (Type: Bug — no fix before condemnation)

RED commit: (a) mock-LLM test replaying the traced scenario — dedup
returns a merge_map, agent issues create anyway, current pipeline writes
the duplicate; (b) dual-synopsis test; (c) cross-type collision test.
GREEN commit: the fixes. The regen run ("nuke canon, regenerate") is the
demo, not the test — canon is generated data, deletion approved.

## Acceptance Criteria

- [ ] All six genesis `create_*.yaml` + worldgen `create_skeleton.yaml` run deterministic pre-checks (exact-ID, cross-type collision) then dedup LLM gate before persist — duplicates refused
- [ ] Dedup gate input is the canon digest, not full canon
- [ ] Refusal message names surviving entity ID and `update_refs` as the repair path
- [ ] Gate prompt: high-confidence refusal bias; uncertain → permit; ulf/ulfs negative example
- [ ] `update_refs` python tool in genesis agent rewrites reference fields old_id → new_id
- [ ] `dedup_check` removed from both agents' standalone tool lists
- [ ] `persist_synopsis` clears synopsis dir before writing
- [ ] `final_gate` detects cross-type ID collisions as backstop
- [ ] Full genesis+worldgen on clean canon produces zero duplicates
- [ ] Tests RED→GREEN: traced-scenario replay, dedup gate refuses duplicate, dedup gate permits unique, synopsis clearing, ID collision detection, update_refs rewrite
- [ ] Nuke existing canon, regenerate, verify; demo with `demo-output.log`

## Related

- FR-686: Agent-first genesis rewrite (current architecture)
- FR-684: Semantic dedup graph-tool (dedup LLM logic to reuse)
- FR-658: Graph-as-tool pattern (create_* pipelines)
- LangSmith genesis trace: `019f32f8-aa56-7780-90d8-83dd27cd5476`
- LangSmith worldgen trace: `019f32fd-e38a-73e2-97cc-1b540655ab41`

---

## Judgement (decision history — amendments folded into body above)

**Verdict: APPROVED — scope frozen with the binding amendments below.
Finding 2 is blocking: the FR as drafted deadlocks the agent.**

### Assessment

The evidence is exactly what Commandment 9 demands: cited traces showing
the advisory mechanism failing in production. LLM #11 acknowledged the
merge_map; LLM #15 overrode it under ref_check pressure. That is the
`model_as_trusted_peer` trap caught red-handed — FR-686's advisory
design assumed the agent would honor correct tool results, and the trace
proves it does not when two tools apply conflicting pressure. The
Rejected Approaches section is correct on both counts: prompt fixes are
not enforcement, and identity is semantic, beyond string matching.

Fixes 2 and 3 are trivial, deterministic, and approved with one
boundary relocation (Finding 3).

### Findings & Binding Amendments

1. **Prior-ruling conflict — scoped reversal, on the record.** FR-686
   Judgement v2 Finding 1 froze: "An LLM must NOT be a hard gate on
   persistence." This FR proposes exactly that. The reversal is granted,
   **scoped to the identity question only**, for two reasons. (a) The
   trace proves the advisory alternative fails — the premise of FR-686's
   ruling (agent repairs on advisory warnings) is empirically dead.
   (b) Failure asymmetry: a false refusal surfaces immediately to the
   agent as text and is recoverable in-loop; a false pass writes a
   duplicate to disk, invisible until the final gate. The coherence
   check stays advisory — FR-686 Finding 1 stands for every question
   except identity. FR-686 AC-5 (standalone `dedup_check` in agent tool
   lists, mandated by prompt) is superseded by the built-in gate; note
   this in FR-686 at enforcement time.

2. **Refusal deadlock — BLOCKING.** Walk the traced scenario under the
   proposed design: event `death_of_ragnar` references `ragnar`;
   `create_character(ragnar)` is refused ("duplicate of
   hildes_father"); the dangling reference remains; genesis has **no
   update/repair tool** (verified: only `create_*` in the tool list —
   worldgen's `deepen_entity` does not exist in genesis). The agent is
   trapped between the dedup gate (cannot create) and the final gate
   (dangling ref) — an unsatisfiable state. The trace shows the agent
   created the duplicate precisely to repair a broken reference; the
   gate removes its only repair path. **Amendment:** add an
   `update_refs` tool to the genesis agent — deterministic python,
   rewrites reference fields (participants, related_to, members,
   faction, affected_locations) from one ID to another:
   `update_refs(old_id="ragnar", new_id="hildes_father")`. The refusal
   message must name the action: "Refused: duplicate of hildes_father.
   Use update_refs to repoint existing references." A refusal without a
   repair path is a deadlock, not a gate.

3. **Deterministic checks run before the LLM, at the write boundary.**
   The pipeline must short-circuit cheaply: (a) exact-ID existence and
   (b) cross-type ID collision (Fix 3) are deterministic — check them in
   `persist_entity`/gate entry BEFORE invoking the dedup LLM. The LLM
   judges only the semantic near-miss it alone can see. Fix 3 therefore
   moves to the write boundary (`normalize at the boundary`);
   `final_gate` keeps the collision check as backstop audit, per AC-10
   doctrine (the gate that cannot be sweet-talked).

4. **False-refusal risk priced and biased.** The gate inherits
   nondeterminism — a wrong "duplicate" verdict silently merges two
   distinct people, which is the same corruption class the FR fights.
   **Amendment:** the dedup gate prompt instructs refuse only on
   high-confidence identity (same referent, not same archetype — the
   ulf/ulfs negative example from FR-684 carries over); when uncertain,
   permit. Rationale: a leaked duplicate is caught later by final audit
   or worldgen dedup; a false merge is silent and unrecoverable. Bias
   the gate toward the recoverable error.

5. **Pipeline shape frozen.** `create_*.yaml` becomes:
   deterministic pre-checks (python: exact-ID, cross-type) → dedup gate
   (LLM, digest input, pre-persist, refusing) → persist (python,
   Pydantic) → prefetch → check (LLM, advisory, post-persist). Two LLM
   calls per create, priced and accepted — this supersedes FR-686's
   one-call-per-create accounting. Dedup gate input is the canon digest
   — not full canon (FR-686 Finding 2 quadratic trap applies here too).

6. **Worldgen included.** `create_skeleton` gets the same gate; the
   traced worldgen run is cited but the fix list only names genesis
   tools. AC list extended: both pipelines' creation tools carry the
   gate; `dedup_check` removed from both agents' standalone lists.

7. **TDD — this is Type: Bug.** No fix before condemnation. RED commit:
   (a) mock-LLM test replaying the traced scenario — dedup returns a
   merge_map, agent issues create anyway, current pipeline writes the
   duplicate; (b) dual-synopsis test; (c) cross-type collision test.
   GREEN commit: the three fixes. The regen run ("nuke canon,
   regenerate") is the demo, not the test — canon is generated data,
   deletion approved.

### Scope Freeze

- Dedup LLM gate inlined pre-persist in all six genesis `create_*.yaml`
  + worldgen `create_skeleton.yaml`; refusal short-circuits with
  surviving ID + repair instruction.
- Deterministic exact-ID + cross-type checks before the LLM, at the
  write boundary; `final_gate` collision backstop (Fix 3).
- New `update_refs` python tool in genesis agent (Finding 2).
- `persist_synopsis` clears synopsis dir before write (Fix 2).
- `dedup_check` removed from both agents' tool lists; FR-686 AC-5
  superseded — record in FR-686 at enforcement.
- Gate prompt: high-confidence refusal bias, ulf/ulfs negative example.
- Tests RED→GREEN per Finding 7; regen demo with `demo-output.log`.
- Effort frozen at 1–2 days (update_refs + worldgen coverage added).
