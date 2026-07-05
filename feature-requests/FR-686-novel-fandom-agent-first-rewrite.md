# Feature Request: FR-686 — Novel Fandom Agent-First Rewrite

**Priority:** HIGH
**Type:** Feature
**Status:** Judged ✅ (consolidated; two judgement rounds folded into body)
**Effort:** 3–4 days
**Requested:** 2026-07-05
**Judged:** 2026-07-05 (v1 + v2 re-judgement + use-case review, consolidated)
**Depends:** FR-658 (graph-as-tool, enforced), FR-683 (ref_check graph-tool),
  FR-684 (semantic_dedup graph-tool)
**Supersedes:** FR-685 (genesis gate→route→fix — enforced in `e7b558de`,
  mechanism replaced by this FR)

> This document is the consolidated, judged spec. It absorbed two
> judgement rounds (v1 draft review, v2 after enforcement attempt 1 was
> rejected) and one use-case review (unnamed-entity twin minting). All
> amendments are folded into the body; the Judgement section records the
> decision history and rationale. The body is the frozen scope.

## Summary

Rewrite genesis and worldgen as agent nodes that create entities one at
a time via tool calls. Every `create_*` tool **is** a graph-tool
pipeline (FR-658): deterministic Pydantic validation gates the write, an
LLM node then judges semantic coherence against the origin document and
a canon digest. The agent sees a typed tool and a ≤2-line result; it
never knows a pipeline ran. This example is the primary showcase for
graph-as-tool.

## Problem

The current pipelines are **LLM-output-parsing machines**, not agents:

1. **Genesis**: LLM produces a monolithic `structured_world` JSON blob
   with all entities at once. A python tool validates, another persists.
   The LLM never sees the results of its own work. No self-correction at
   the entity level — only the FR-685 bulk fix loop that re-generates
   the entire blob.

2. **Worldgen**: Map nodes batch-process entities in parallel. The
   `deepen_events` agent has tools but works on a single assigned entity
   per map iteration — it never decides WHAT to work on, only HOW.

3. **FR-658 underused**: `type: graph` tools exist in worldgen's tool
   list but genesis bypasses them entirely. novel_fandom should be the
   **primary showcase** for graph-as-tool, not a python-tool hack with
   graph-tools on the side.

4. **Batch JSON fragility**: A single malformed entity in a 20-entity
   JSON blob invalidates the entire output. Agent tool calls are atomic
   — one entity per call, independent validation, immediate persistence.

5. **Identity errors are manufactured by the current gates** (use-case
   review): a synopsis that *implies* an unnamed entity (a father of one
   character, killed by another) defeats ID-existence checking. Each
   character's creation pass mints the implied entity from its own local
   context → two IDs for one person, each internally coherent, both
   passing every mechanical gate. Not hypothetical: canon history
   contains `ulf`/`ulfs`, `arnulf_rescue`/`arnulf_rescued`,
   `hildes_father`/`gunnars_father`/`fridas_grandmother`. The gate
   answered "does this ID exist" when the question was "does this
   *entity* exist" — an identity question, which is semantic.

## Design

### Architecture Overview

```
genesis.yaml:   load → synopsis (llm) → persist_synopsis (python)
                → genesis agent → final_gate (python) → END

worldgen.yaml:  reload → worldgen agent → final_gate (python) → END
```

Two parent graphs, one agent node each. No map nodes, no
select/split/batch orchestration — the agent decides work order (learned
from tool errors and its checklist), the tools enforce correctness.

### Creation Tools Are Graph-Tool Pipelines

Each `create_*` tool is a `type: graph` tool (FR-658). Five graph files
share one pipeline shape:

```
create_character.yaml:
  variables: {entity_type: character}
  nodes:
    persist   (python) → Pydantic-validate, write to canon/character/
                          hard fail → nothing persisted, error returned
    prefetch  (python) → build canon digest (1 line/entity: id, type,
                          summary) + full YAML of exactly the entities
                          the new entity references (parsed from its
                          declared fields: related_to, participants,
                          faction, members, affected_locations)
    check     (LLM)    → advisory semantic judgment: coherence with
                          referenced entities, fidelity to premise +
                          synopsis (self-loaded with canon), duplicate
                          suspicion
  output_key: result   → "Created character hilde. Refs coherent."
                          or "Created character hilde. Warning: ..."
```

**Frozen ordering — deterministic gates the write, LLM advises after:**
an LLM must not be a hard gate on persistence (a plausible wrong
"invalid" would nondeterministically block valid entities). Pydantic
failure means nothing is written. The LLM warning returns to the agent,
which repairs via subsequent tool calls. The deterministic final gate
(AC-10) is the backstop that cannot be sweet-talked.

**Token discipline — linear, not quadratic:** the check node never reads
the full canon (N creates × full-canon reads ≈ O(N²)). Digest gives
global context; ref prefetch gives local depth on the actual
relationships. One LLM call per create.

*Considered and rejected:* making the check an agent with a
`lookup_canon_page` tool. The refs are declared fields — what-to-read is
deterministically known, so an agent adds only model-cooperation
dependence and 2–3× the LLM calls. Pipeline decides, LLM judges.

### Origin Document as Ground Truth

Digest + prefetch test internal consistency only — twin entities minted
from different local contexts both pass. Only the origin document
reveals that "the father" and "the victim" are the same man. Therefore:

- The parent graph persists the **synopsis to canon** via a
  deterministic python node immediately after the synopsis LLM node
  (not an agent tool).
- Check nodes self-load canon and therefore receive premise + synopsis
  for free; the check prompt judges **fidelity to source**, not just
  internal coherence.

### Enumerate-Then-Create

The genesis agent's first obligation after reading the synopsis is to
emit its **entity checklist** — named AND implied entities, each with a
minted ID and a one-line context drawn from the synopsis — before the
first `create_*` call. Unnamed entities are minted once, at
global-context time, never coerced mid-create in local context. The
"referenced ID does not exist — create it first" error remains, but as
the safety net, not the design: an agent hitting it has already failed
its checklist. Enforced in `genesis_agent.yaml`.

### Identity Resolution: `dedup_check` in Both Agents

`dedup_check` (graph-tool → `semantic_dedup.yaml`, LLM comparison —
the second FR-658 showcase) is in **both** agents' tool lists. The child
graph self-loads canon; the agent passes only `candidate_id` +
`candidate_summary`. The agent prompt mandates: before minting any
entity NOT explicitly named in the synopsis, call `dedup_check`. Its
verdict is advisory — the skip-or-merge decision stays with the agent;
the backstop is the checklist plus the final gate.

### Genesis Agent

```yaml
nodes:
  genesis:
    type: agent
    prompt: genesis_agent
    tools:
      - load_premise        # python: read premise file
      - create_premise      # graph-tool: persist premise entity
      - create_character    # graph-tool: validate + persist + check
      - create_event        # graph-tool: validate + persist + check
      - create_faction      # graph-tool: validate + persist + check
      - create_location     # graph-tool: validate + persist + check
      - create_rule         # graph-tool: validate + persist + check
      - dedup_check         # graph-tool: semantic identity check
      - list_canon_ids      # python: see what exists
      - ref_check           # graph-tool: final audit before completion
    max_iterations: 50
    state_key: genesis_result
```

Synopsis is a separate `type: llm` node before the agent (one
deterministic call); the agent receives it via `variables`. There is no
`create_synopsis` tool.

### Worldgen Agent

```yaml
nodes:
  worldgen:
    type: agent
    prompt: worldgen_agent
    tools:
      - list_thin_entities  # python: find entities needing enrichment
      - deepen_entity       # python: validate + persist enriched entity
      - create_skeleton     # graph-tool: validate + persist + check
      - lookup_canon_page   # python: read an entity
      - list_canon_ids      # python: see what exists
      - dedup_check         # graph-tool: semantic identity check
      - ref_check           # graph-tool: final audit before completion
    max_iterations: 100
    state_key: worldgen_result
```

### Tool Design Principles

**Short descriptions, not data dumps.** Related artifacts are referenced
by ID + short description:

```
create_event(
  id="great_flood",
  year=0,
  scope="world",
  participants="hilde:survivor, erik:victim",   # ID:role pairs
  consequences="Destroyed Grauenbach;Split factions"
)
```

Bulk context (canon, synopsis) is **self-loaded inside child graphs** —
never passed as tool arguments, because agent tool arguments are
LLM-generated tokens. Normalize-at-the-boundary applied to token
economics.

*Scoped exemption:* `deepen_entity(id, updated_yaml)` accepts a full
YAML document — the agent authors new content there, not copies of
existing data.

**≤2-line tool returns.** "Created character hilde. Refs coherent." /
"Error: faction 'riverfolk' does not exist — create it first." Progress
is queried via `list_canon_ids`, never reconstructed from conversation
memory. If genesis needs more than `max_iterations: 50`, fail loudly —
do not raise the cap; the premise is too large for one run.

**No mechanical graph-tools in agent tool lists.** A graph-tool wrapping
a python set intersection is ID matching in a graph costume — it
showcases nothing (attempt-1 rejection). Every agent-facing graph-tool
contains an LLM judgment node; purely mechanical checks belong in
python tools or the deterministic final gate.

## Acceptance Criteria

1. **AC-1**: `genesis.yaml` = load → synopsis (`type: llm`) →
   persist_synopsis (python) → genesis agent (`type: agent`) →
   final_gate (python) → END. No other LLM nodes; no `create_synopsis`
   tool.

2. **AC-2**: Each `create_*` tool is a `type: graph` tool whose child
   graph: (a) Pydantic-validates and persists atomically — hard failure
   writes nothing and returns an error string; (b) runs an advisory LLM
   semantic check on digest + ref prefetch + origin document; (c)
   returns ≤2 lines.

3. **AC-3**: `ref_check` graph-tool is the agent's **final audit**,
   called over the full canon before the agent declares completion. It
   self-loads canon (no bulk args) and contains an LLM judgment node —
   or is dropped from agent tools entirely, leaving the audit to AC-10.
   A mechanical graph-tool in the agent's list is forbidden.

4. **AC-4**: `worldgen.yaml` has a single `type: agent` node. No map
   nodes for entity processing.

5. **AC-5**: `dedup_check` graph-tool is in **both** agents' tool lists;
   agent prompts mandate calling it before minting any entity not
   explicitly named in the synopsis. Interface: `candidate_id` +
   `candidate_summary` only; child graph self-loads canon.

6. **AC-6**: Creation tools use short-description parameters (ID +
   role/description), not full entity data. Scoped exemption:
   `deepen_entity`'s `updated_yaml`.

7. **AC-7**: Agent decides work order — no external select/split/batch
   orchestration in YAML edges. Genesis agent emits its
   enumerate-then-create checklist (named + implied entities, IDs minted
   at global-context time) before the first `create_*` call.

8. **AC-8**: Both graphs demonstrate FR-658 `type: graph` tools called
   from agent nodes; every agent-facing graph-tool contains LLM
   reasoning. This is the primary showcase for graph-as-tool.

9. **AC-9**: Tests with mock LLM: (a) genesis creates entities via tool
   calls; (b) worldgen deepens + creates via tool calls; (c) graph-tools
   invoked during creation; (d) error in one entity doesn't block
   others; (e) implied-entity premise — scripted sequence shows the
   checklist minting an unnamed entity once, with `dedup_check` called
   before its creation.

10. **AC-10**: After each agent node, a deterministic python `final_gate`
    runs referential-integrity checking over the canon directory and
    writes `gate_result` to state; the graph surfaces invalid results
    loudly (non-zero orphans in final output). No silent partial worlds.
    The agent's own completion claim is not trusted.

## Implementation Plan

**New graph-tools (6 YAML, each ~30 lines, shared pipeline shape):**
- `create_character.yaml` — input: id, name, role, faction, summary, related_to
- `create_event.yaml` — input: id, year, scope, participants, consequences, summary
- `create_faction.yaml` — input: id, name, description, members
- `create_location.yaml` — input: id, name, description, location_type
- `create_rule.yaml` — input: id, domain, title, description
- `create_premise.yaml` — input: id, text, genre_tags, era, themes, calendar_note

Each hardcodes `entity_type` via `variables:`; agent tool args arrive
via `input_mapping`.

**Shared components:**
- `nodes/creation_tools.py` — `persist_entity(state)` (Pydantic-gated
  write), `build_check_context(state)` (digest + ref prefetch),
  `final_gate(state)`, `persist_synopsis(state)`, `list_thin_entities`,
  `deepen_entity`. Delete `create_synopsis`.
- `prompts/ref_check_entity.yaml` — advisory semantic check: given the
  new entity, its referenced entities (full YAML), the canon digest, and
  premise + synopsis — judge reference coherence, fidelity to source,
  duplicate suspicion.
- `prompts/genesis_agent.yaml`, `prompts/worldgen_agent.yaml` —
  including enumerate-then-create checklist and dedup_check mandate.

**Reworked:**
- `semantic_dedup.yaml` — self-loads canon; id + summary interface.
- `ref_check.yaml` — LLM judgment node over digest, or removed from
  agent tool lists (implementer picks; AC-3).

**Kept as python tools (lookups, no LLM reasoning):**
- `list_canon_ids`, `lookup_canon_page`, `load_premise`,
  `nodes/reload_canon.py`.

**Retired — deleted, not stranded (grep for references, vulture must
pass, removals recorded in commit note):**
- Graphs/prompts: `generate_stubs.yaml`, `fix_genesis_refs.yaml`,
  `deepen_entity.yaml` prompt (if orphaned), map-node blocks.
- Python: `split_thin_by_type.py`, `select_thin.py`,
  `dedup_entities.py`, `apply_merge_map.py`, `collect_red_links.py`,
  and any worldgen-only nodes left unreferenced.
- Tests: delete FR-685 structure tests (mechanism replaced); rewrite
  FR-664/667/683 structure tests against this architecture. The suite
  is green in the same PR — the 15 currently failing structure tests
  belong to this FR, not to history.

## Constraints

- Agent nodes decide what to create; tools enforce correctness.
- One entity per tool call — atomic validation and persistence.
- Deterministic validation gates writes; LLM checks are advisory.
- Semantic checks always receive the origin document (premise +
  synopsis) — fidelity to source, not just internal coherence.
- Bulk context self-loaded in child graphs; agent passes IDs + short
  descriptions only.
- Check context is linear: digest + declared-ref prefetch, never the
  full canon per create.
- No mechanical (LLM-free) graph-tools in agent tool lists.
- Three-layer architecture: tools (Layer 3), graphs (Layer 2).

## Risks

- **Token cost**: ~25 creates × (1 tool-call turn + 1 embedded check
  call) far exceeds the old 2-call genesis. Accepted: this is the
  showcase cost; error recovery is per-entity, and check context is
  linear by design.
- **Agent wandering**: mitigated by the enumerate-then-create checklist
  and `list_canon_ids` progress queries; `max_iterations` fails loudly.
- **Ordering**: agent must create factions before members. Mitigated by
  checklist-first design; the "create it first" error is the safety net.
- **Advisory checks ignored**: an agent may ignore warnings. Backstop:
  deterministic AC-10 final gate reports orphans loudly.

## Related

- [FR-658](FR-658-graph-as-tool.md) — `type: graph` tool (core mechanism)
- [FR-683](FR-683-ref-integrity-graph-tool.md) — ref_check graph-tool
- [FR-684](FR-684-semantic-dedup-graph-tool.md) — semantic_dedup graph-tool
- [FR-685](FR-685-genesis-self-correcting-agent.md) — genesis fix loop (superseded)
- [FR-655](FR-655-genesis-graph.md) — original genesis pipeline
- [FR-657](FR-657-agentic-event-deepening.md) — worldgen agent pattern
- Diary: 2026-07-04 "The Boundary Collapses Inward" — missing docs
  enabled python-hack bypass of graph-tool
- Diary: 2026-07-05 "The Gate That Minted Twins" — deterministic gate on
  a semantic question manufactures compliant errors

---

## Judgement (consolidated — v1, v2, use-case review)

**Verdict: APPROVED — scope frozen as written in the body above. The
body absorbs all binding amendments from three review rounds; this
section records the decision history.**

### Round 1 (draft review)

1. **FR-685 reversal on the record.** FR-685's Judgement rejected a
   *batch* genesis agent (same blob output at 2× cost, control flow
   delegated to model cooperation, no compensating benefit). FR-686
   changes the unit of work: per-entity tool calls with atomic
   validation and persistence — different failure semantics, honestly
   priced. FR-685's cost arithmetic does not apply; its "genesis does
   not need an agent" evaluated only the batch variant. Reversal
   granted. *Record correction (round 2):* v1 claimed FR-685 was never
   enforced — wrong; commit `e7b558de` shipped it. The supersession
   replaces shipped behavior. Verify enforcement state from git log, not
   FR status lines.
2. **Data-dump contradiction (blocking).** Draft graph-tools took full
   canon JSON as tool arguments — LLM-generated tokens. Amended:
   self-loading child graphs, ID + summary interfaces (now Constraints).
3. **Per-entity ref_check demoted, then reconciled.** Optional-by-
   construction agent calls duplicate deterministic enforcement. v2
   moved the semantic check *inside* every `create_*` — enforced-by-
   construction — satisfying the objection. Standalone `ref_check` =
   final audit only (AC-3).
4. **Terminal gate added** (AC-10) — partial-world hazard from
   `max_iterations` exhaustion with immediate persistence.
5. **Context growth bounded** — ≤2-line tool returns, progress via
   `list_canon_ids`, hard iteration cap.
6. **Synopsis frozen** as a separate LLM node; `create_synopsis` cut.
7. **Dependencies corrected** — FR-683/684 added; FR-685 to Supersedes.
8. **Retirement completeness** — retired means deleted; vulture clean
   (partial_remediation trap).

### Round 2 (after enforcement attempt 1 rejected)

Attempt 1 shipped `ref_check.yaml` wrapping a python `set()`
intersection — mechanical ID matching in a graph costume
(`framework_costume`), zero LLM reasoning. Rejection ratified. Rulings:

1. **Persist-then-check ordering frozen** — Pydantic gates writes (hard);
   LLM checks advisory after persist. An LLM is never a hard gate on
   persistence.
2. **Quadratic token trap (blocking)** — full-canon reads per create ≈
   O(N²). Amended to digest + deterministic ref prefetch. The
   agent-with-lookup alternative was considered and rejected: refs are
   declared fields, what-to-read is known; pipeline decides, LLM judges.
3. **Red suite ownership** — 15 failing structure tests condemn
   structures this FR retires; they are this FR's to fix in the same PR.
   No "pre-existing failure".
4. **Tool inventory ruled** — `create_premise` accepted;
   `create_synopsis` deleted; `deepen_entity` YAML param recorded as
   scoped AC-6 exemption.

### Round 3 (use-case review: unnamed-entity twin minting)

Synopsis implies an unnamed third character (father of one, killed by
another). The "create it first" existence error *coerces* the agent into
minting the implied entity mid-create in local context — twice, from two
different contexts. Both twins pass every mechanical gate. Evidence in
canon history: `ulf`/`ulfs`, `arnulf_rescue`/`arnulf_rescued`, the
invented-relative stubs. The trap: `gate_checks_shape_not_substance` —
"does this ID exist" is not "does this *entity* exist"; identity is
semantic, and a deterministic gate on a semantic question manufactures
compliant errors (a gate is also a prompt). Rulings, all folded into the
body:

- **(a)** Origin document (premise + synopsis) is ground truth in every
  semantic check; synopsis persisted to canon deterministically.
- **(b)** `dedup_check` in both agents' tool lists (AC-5), mandated
  before minting entities not named in the synopsis.
- **(c)** Enumerate-then-create checklist (AC-7): implied entities
  minted once at global-context time; the existence error demoted to
  safety net. AC-9 gains the implied-entity test case (e).

### Effort

Frozen at 3–4 days: two graph rewrites, six create graph-tools, shared
check prompt + digest builder, two agent prompts, semantic_dedup rework,
tests (delete/rewrite/add), retirement.
