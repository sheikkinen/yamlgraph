# Process: Continuity Incident Analysis, Review, and Reflection

## Purpose

This document captures the actual process used in this repository to diagnose,
fix, review, and reflect on continuity incidents in Dungeon Master v2.

It is anchored to the live implementation from FR-509, FR-510, and FR-513, not a
generic template.

## Actual Implementation Map

### Runtime boundaries

1. Chapter turn runtime and cast admission live in:
   - examples/dungeon_master/api/turn_ops.py
2. Chapter close and final prose validation live in:
   - examples/dungeon_master/api/chapter_ops.py
3. Witness scoring logic lives in:
   - examples/dungeon_master/api/witness_metrics.py
4. Final prose prompt contract lives in:
   - examples/dungeon_master/prompts/final_cut.yaml
5. Forward-carry world ledger (characters, objects, facts, relationships) lives in:
   - examples/dungeon_master/api/world_state.py
6. Chapter-close ledger extraction contract lives in:
   - examples/dungeon_master/prompts/chapter_close.yaml

### What is enforced now

1. Memory precedence gate at chapter open:
   - _enforce_memory_precedence_gate
2. Lifecycle gate at chapter open:
   - _enforce_lifecycle_gate
3. Lifecycle roster pre-filter before cast assembly:
   - _filter_roster_for_lifecycle
4. Final-cut context includes dead_characters:
   - final_cut_context
5. Post-prose dead-character validator logs violations:
   - detect_dead_character_prose_violations
   - close_chapter logs DEAD_CHARACTER_PROSE_VIOLATION payloads
6. Relationship grounding gate at the close boundary (FR-513):
   - parse_world_state drops any relationship lacking recap_citations or naming
     fewer than two parties (refinements 1 + 4) — an ungrounded bond never enters
     the ledger or the next chapter's turn context.
7. Relationship turn-context pruning (FR-513):
   - running_scene renders inherited relationships with relationships="active";
     format_world_state excludes dormant/archived rows so stale tensions are not
     reinvoked in play (refinements 2 + 3). The close carry-forward uses the
     default relationships="all" so dormant bonds survive for revival.

### What is measured but not fail-gated now

1. dead_character_prose_violation_count is parsed in witness metrics.
2. evaluate_fr508_a5 does not include dead_character_prose_violation_count in
   pass checks.

Implication:

- A run can pass witness checks while still containing dead-character prose
  contradictions if they are not represented in fail criteria.
- Emotional continuity (relationships persisting across chapters) is now grounded
  and carried at the boundary, but is not yet a witness fail criterion: a run can
  pass while a relationship the recaps established still fails to surface in the
  next chapter's prose.

## Inputs for Incident Analysis

Required artifacts:

1. logs/gen-<run>-azure.log
2. outputs/dungeon-master/<run>/story/story.json
3. outputs/dungeon-master/<run>/story.md when present
4. FR status docs for active incident

Note:

- Some runs may not emit story.md in output root; verify actual artifact layout
  under outputs/dungeon-master/<run>/ first.

## Full Process

### Step 1: Freeze evidence

1. Record run id and command (premise, turn cap, output path).
2. Save witness JSON output for that exact run.
3. Preserve story evidence with line numbers when story.md exists.
4. Verify seam lifecycle state in story.json for the affected character.

Exit criteria:

- Defect is reproducible from immutable artifacts.

### Step 2: Identify escaping boundary

1. Check if defect is blocked at cast admission (_filter_roster_for_lifecycle).
2. Check if defect is blocked at lifecycle gate (_enforce_lifecycle_gate).
3. Check if defect appears only after final prose synthesis.
4. Check whether witness pass criteria include this defect class.

Decision rule:

- If defect survives upstream but appears in final prose, add or strengthen
  final prose boundary controls.

### Step 3: Plan and judge in FR

1. Define exact defect class and target boundary.
2. Specify deterministic heuristic and explicit exclusions.
3. Decide measure-only vs fail-gate policy.
4. List edge cases, including chapter 1 empty prior seam.

Do not code until judge blockers are resolved.

### Step 4: Enforce with TDD

1. RED tests first.
2. GREEN implementation with minimal boundary changes.
3. Keep existing gates strict; do not mute typed errors.
4. Add structured warning payloads for measurable violations.
5. Extend witness parsing only if log signal exists.

Actual FR-510 implementation path:

1. Add dead_characters in final_cut_context.
2. Update final_cut.yaml to include dead-character exclusion instruction.
3. Add detect_dead_character_prose_violations in chapter_ops.
4. Log DEAD_CHARACTER_PROSE_VIOLATION during close_chapter.
5. Add tests in examples/dungeon_master/tests/test_dead_character_prose.py.

### Step 5: Validate code and behavior

1. Run targeted test file for the new detector.
2. Run full DM tests.
3. Run ruff on changed files.
4. Score witness on new run.
5. Compare with baseline run metrics.

### Step 6: Review (mandatory)

Review in severity order.

1. Critical defects still present in output artifacts.
2. Gate/metric mismatch risks.
3. Regressions introduced by fix.
4. Missing tests for accepted edge cases.

#### Review Results from this cycle

Run 10013:

1. Critical finding: contradiction present in prose (Alwina dead in chapter 6,
   active in chapter 7).
2. Witness output: pass true.
3. Root cause: pass checks in evaluate_fr508_a5 do not include dead prose
   violation count.

Run 10014:

1. Witness output: pass false.
2. Failure cause: completed_equals_planned false and
   book_gate_opened_before_turn_cap false.
3. Metrics showed dead_character_prose_violation_count 0, but artifact review is
   limited because story.md was not emitted in output root for this run.

### Step 7: Reflect (mandatory)

Reflection must answer:

1. Which signal was over-trusted?
2. Which boundary was missing or weaker than expected?
3. Where did measurement diverge from enforcement?
4. What process or gate change prevents recurrence?

#### Reflection from this cycle

1. Witness pass was over-trusted as narrative truth.
2. Final prose boundary was initially under-constrained relative to lifecycle
   source-of-truth.
3. Measurement-only dead prose metric created confidence without enforcement.
4. Process change: always review final prose artifacts when available, even when
   witness passes.

Seed:

- Should dead_character_prose_violation_count become a fail gate in
  evaluate_fr508_a5 once false positive rate is characterized?

### Step 8: Close loop

1. Update FR implementation status with objective metrics.
2. Record review findings and residual risks explicitly.
3. Add diary reflection with seed question.
4. Update this process doc when enforcement policy changes.

## Command Checklist

### Witness scoring

```bash
PYTHONPATH="$PWD" .venv/bin/python \
  examples/dungeon_master/scripts/witness_continuity_metrics.py \
  --log logs/gen-<run>-azure.log \
  --story outputs/dungeon-master/<run>/story/story.json \
  --json
```

### Targeted tests

```bash
.venv/bin/python -m pytest \
  examples/dungeon_master/tests/test_dead_character_prose.py \
  --no-cov -q
```

### Full DM tests

```bash
.venv/bin/python -m pytest examples/dungeon_master/tests --no-cov -q
```

### Lint changed files

```bash
.venv/bin/python -m ruff check \
  examples/dungeon_master/api/chapter_ops.py \
  examples/dungeon_master/api/turn_ops.py \
  examples/dungeon_master/api/witness_metrics.py \
  examples/dungeon_master/tests/test_dead_character_prose.py
```

### Quick artifact inventory before review

```bash
ls -la outputs/dungeon-master/<run>
ls -la outputs/dungeon-master/<run>/story
```

## Definition of Done

Incident closure requires all of the following:

1. Defect path is documented from artifact evidence to code boundary.
2. Tests and lint are green.
3. Witness result is interpreted against actual fail criteria, not assumptions.
4. Review findings are recorded in severity order with residual risk.
5. Reflection and seed question are recorded.
