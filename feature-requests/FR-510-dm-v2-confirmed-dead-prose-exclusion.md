# Feature Request: FR-510 - DM v2 Confirmed-Dead Character Prose Exclusion

**Priority:** HIGH
**Type:** Bugfix / Enforcement Hardening
**Status:** Judged - Granted
**Effort:** ~1-2 days
**Requested:** 2026-06-17

## Summary

Prevent `confirmed_dead` characters from appearing as active agents in
chapter-close final prose. The lifecycle gate (FR-507) and cast filter (FR-509)
enforce exclusion at intent generation time; neither enforces it at prose
synthesis time. This FR closes the remaining gap by adding lifecycle constraints
to `final_cut_context` and optionally validating the final text against them.

## Judgement

Decision: **Granted** (redraft resolves all four blockers).

**B1 resolved** — Active-role heuristic is now fully specified in Solution 3 and A6
test cases. N is fixed at 8 words. Passive exclusion patterns are enumerated
explicitly. The test cases are written before any implementation begins.

**B2 resolved** — A7 is removed from pass/fail evaluation criteria and reclassified
as a measurement target. This FR commits to log-and-warn only. Hardening to block
is explicitly deferred to a follow-up FR once false-positive rate is measured.

**B3 resolved** — `final_cut.yaml` is a Jinja2 template with no strict input schema.
Existing variables (`key_scene`, `beats`, `beat_groups`, `draft`, `instruction`)
are used directly as template identifiers. Adding `dead_characters` behind a
`{% if dead_characters %}` guard is fully backward-compatible: runs where no
characters are confirmed dead produce an empty string and the conditional block
silently omits the constraint. No graph schema file change required.

**B4 resolved** — Empty seam edge case (chapter 1, no prior seam packet) is now
explicitly listed as an A6 test case.

Grant scope notes:
- Blocking behavior is out of scope for this FR. Log-and-measure only.
- A7 is a measurement target, not a pass/fail gate.
- The Jinja2 guard is mandatory — the variable must always be injected;
  the conditional suppresses the prompt block, not the injection.

## Evidence

Run 10013, chapter 7: Alwina is correctly marked `confirmed_dead` in the chapter
6 seam packet, correctly excluded from chapter 7 intent generation (FR-509), and
correctly listed in chapter 6's `forbidden_regressions`. Despite this, chapter 7
final prose shows Alwina acting, speaking, and planting her ritual staff throughout
the entire chapter — as though she had never been killed in chapter 6.

Root cause: `final_cut_context` (in `turn_ops.py`) passes only arc/beats/summary
to the final-cut LLM. It does not pass lifecycle state or forbidden characters.
The model is handed the chapter's recaps (which can reference Alwina through
director prose) and asked to synthesize continuous text — with no boundary against
dead characters.

## Problem Decomposition

Three distinct paths let a confirmed-dead character appear in prose:

1. **Turn recap prose** — the director's `recap` field is free-form LLM text.
   The cast filter (FR-509) removes the character from the *intent map* but
   the director can still write the character into the *recap narration*.

2. **Final cut synthesis** — `invoke_final_cut` reads all turn recaps and
   synthesizes the chapter's final text. If recaps mention Alwina as active,
   the final cut model will include her.

3. **Final cut context gap** — `final_cut_context` explicitly omits lifecycle
   and forbidden-character data, so the final cut model has no source of truth
   to constrain against.

## Scope

In scope:
- Add `confirmed_dead` character names to `final_cut_context` as a hard exclusion list.
- Pass inherited seam lifecycle entries into the final cut prompt.
- Add post-generation validation of final prose text against `confirmed_dead` roster.
- Log typed violations; warn on confirmed-dead name appearing in active-role patterns.
- Witness rerun criteria for closure.

Out of scope:
- Validating each individual turn recap (scope for a future FR if needed).
- Resurrection semantics.
- Rewriting the final cut graph or its schema.

## Proposed Solution

### 1) Add lifecycle exclusion to `final_cut_context`

Extend `final_cut_context` to include a `dead_characters` field derived from the
inherited seam packet for chapter `cid`:

```python
dead = [
    item["name"]
    for item in inherited_seam_packet(doc, cid).get("character_lifecycle", [])
    if item.get("existence_state") == "confirmed_dead"
]
return {
    ...,
    "dead_characters": ", ".join(dead) if dead else "",
}
```

This gives the final-cut prompt authoritative knowledge of who cannot appear.

### 2) Update `final_cut.yaml` prompt to consume `dead_characters`

The final cut prompt already has a `key_scene` variable for the chapter plan.
Add a conditional block that, when `dead_characters` is non-empty, instructs
the LLM:

```
These characters are dead and must not appear, speak, or act in the narration:
{{ dead_characters }}
```

This is a soft LLM constraint — necessary but not sufficient. The validator
below is the hard enforcement.

### 3) Add deterministic post-prose validator at chapter close

After `invoke_final_cut` returns text, run a deterministic check:
- For each `confirmed_dead` character in the inherited seam packet, check whether
  the character's name appears in the prose in active-role context.
- Active-role detection rule (now fully specified):
  - Match: `<NAME>` followed by any finite verb (is/was/are/were excluded as
    weak copulas) within **8 words**, forward only.
  - Match: dialogue attribution pattern `"<NAME> <verb>"` where verb is one of
    said/asked/demanded/called/answered/ordered/snapped/drove/thrust/jabbed/lifted.
  - **Exclude** (passive/possessive/locative, no violation):
    - `<NAME>'s` (possessive) — e.g., "Alwina's staff", "Alwina's body"
    - `where <NAME> had/was/lay/stood` — locative past reference
    - `<NAME>'s` + noun phrase only (no subsequent active verb within 8 words)
- Log a typed warning if found:

```json
{
  "code": "DEAD_CHARACTER_PROSE_VIOLATION",
  "chapter_id": "7",
  "name": "Alwina",
  "pattern": "active_presence",
  "excerpt": "Alwina came forward with her ritual staff..."
}
```

- Do not block chapter close on this violation in this FR (witness metric only).
  A future FR can harden to block based on witness data.

### 4) Extend witness metrics to count prose violations

Add `dead_character_prose_violation_count` to `parse_generation_log_metrics` in
`witness_metrics.py`. Include in the FR-508 A5 evaluation as a new check:
`zero_dead_character_prose_violations`.

## Acceptance Criteria

- [ ] **A1 - Dead characters excluded from final cut context.**
- [x] **A1 - Dead characters excluded from final cut context.**
  `final_cut_context` includes `dead_characters` field derived from inherited
  seam packet `confirmed_dead` entries.

- [ ] **A2 - Final cut prompt consumes dead character list.**
- [x] **A2 - Final cut prompt consumes dead character list.**
  `final_cut.yaml` contains a conditional block that names dead characters as
  forbidden in narration when `dead_characters` is non-empty.

- [ ] **A3 - Post-prose validator exists and is deterministic.**
- [x] **A3 - Post-prose validator exists and is deterministic.**
  A pure validator checks final cut text for `confirmed_dead` character names in
  active-role patterns and returns typed violations.

- [ ] **A4 - Violations are logged with typed payload.**
- [x] **A4 - Violations are logged with typed payload.**
  `DEAD_CHARACTER_PROSE_VIOLATION` warnings appear in generation log when a dead
  character appears in prose.

- [ ] **A5 - Witness metric tracks prose violations.**
- [x] **A5 - Witness metric tracks prose violations.**
  `witness_continuity_metrics.py` reports `dead_character_prose_violation_count`.

- [ ] **A6 - Tests cover validator logic with specified heuristic.**
- [x] **A6 - Tests cover validator logic with specified heuristic.**
  Unit tests for dead-character detection using the exact rule from Solution 3:
  - `"Alwina came forward with her ritual staff"` → violation (name + verb ≤8 words)
  - `"Alwina drove her staff down"` → violation (name + verb ≤8 words)
  - `"Alwina demanded that he name his place"` → violation (dialogue attribution)
  - `"Alwina's staff lay on the ground"` → no violation (possessive, no active verb)
  - `"Alwina's body in the path"` → no violation (possessive noun phrase only)
  - `"where Alwina had stood"` → no violation (locative past pattern)
  - Empty inherited seam (chapter 1) → no dead characters, no violations (B4 edge case)

- [ ] **A7 - Witness run measurement recorded.**
  Fresh Floodmark 128-cap run is scored; `dead_character_prose_violation_count`
  is recorded in implementation status. This is a measurement target, not a
  pass/fail gate in this FR. Zero violations is the aspirational target;
  hardening to block is deferred to a follow-up FR once false-positive rate
  is established.

## Design Decisions

**Why not block chapter close?**
The validator is new and the pattern-match heuristic may produce false positives
(e.g., "Alwina's staff lay on the ground" — a passive reference to a dead
character's object, not active presence). Log-and-measure first; harden in a
follow-up FR once the false-positive rate is known.

**Why not validate individual turn recaps?**
Recap text is advisory context; final cut prose is the committed artifact. The
defect surface is the final committed text. Validating recaps would add noise
without reducing the root defect.

**Active-role detection heuristic (fully specified):**
- Match window: 8 words forward from name token.
- Weak copulas (is/was/are/were/be/been/being) do not count as active verbs.
- Dialogue attribution verbs (explicit enumeration in Solution 3) are matched
  directly on the `"<NAME> <verb>"` pattern regardless of the 8-word window.
- Exclusion patterns applied before any match: possessive (`<NAME>'s`),
  locative-past (`where/when/as <NAME> had/was/lay`).
- Regex prototype: `r'\b{name}\b(?!\')(?![^.!?]{{0,8}}\b(?:is|was|are|were)\b).{{0,40}}\b(came|drove|thrust|jabbed|lifted|demanded|called|stepped|moved|said|planted|struck|pressed|held|answered|snapped|ordered|pushed|walked|turned|stood|kept|raised|reached|pointed|pulled|shoved|forced|took|told|placed|stayed|brought|led|used|barred|pinned|seized|set)\b'`
  — this prototype is the starting point for TDD, not the final implementation.

**`final_cut.yaml` variable compatibility (B3):**
`final_cut.yaml` is a Jinja2 template. All variables are referenced by name only;
there is no declared input schema. The `dead_characters` variable is injected
always; when the value is an empty string the `{% if dead_characters %}` guard
suppresses the constraint block silently. No graph schema file requires updating.

## Enforce Sequence (TDD)

## Implementation Status

In progress — A7 witness measurement pending 10014 run completion.

Completed in this enforcement pass:
- `examples/dungeon_master/api/chapter_ops.py` — added `detect_dead_character_prose_violations(name, text)` with 8-word active-verb window, possessive/locative exclusion, and typed violation payloads.
- `examples/dungeon_master/api/chapter_ops.py` `close_chapter` — wired validator after `invoke_final_cut`; logs `DEAD_CHARACTER_PROSE_VIOLATION` warnings.
- `examples/dungeon_master/api/turn_ops.py` `final_cut_context` — added `dead_characters` field derived from inherited seam packet `confirmed_dead` entries.
- `examples/dungeon_master/prompts/final_cut.yaml` — added `{% if dead_characters %}` constraint block in system prompt.
- `examples/dungeon_master/api/witness_metrics.py` — added `_LOG_LINE_DEAD_PROSE` counter, `dead_character_prose_violation_count` to log metrics, `dead_character_prose_violation_count (measure)` to markdown table, and `_dead_prose_is_measurement_only` helper.
- `examples/dungeon_master/tests/test_dead_character_prose.py` — 10 unit/integration tests covering A6 cases.

Validation evidence:
- `python -m pytest examples/dungeon_master/tests/test_dead_character_prose.py --no-cov -q` → `10 passed`
- `python -m pytest examples/dungeon_master/tests --no-cov -q` → `154 passed`
- `python -m ruff check` on all changed files → clean.

Pending for full closure:
- A7: 10014 witness run in progress. Metrics will be recorded here on completion.

Acceptance criteria updated:

1. RED: add unit tests for active-role pattern detector:
   - `"Alwina came forward"` → violation
   - `"Alwina drove her staff"` → violation
   - `"Alwina's body"` → no violation
   - `"where Alwina had stood"` → no violation
2. RED: integration test that `final_cut_context` includes `dead_characters` for
   a chapter whose inherited seam has `confirmed_dead` entries.
3. GREEN: implement `dead_characters` field in `final_cut_context`.
4. GREEN: update `final_cut.yaml` with conditional dead-character block.
5. GREEN: implement post-prose validator in `chapter_ops.py` or `turn_ops.py`.
6. GREEN: wire validator into `close_chapter` after `invoke_final_cut`.
7. GREEN: extend `witness_metrics.py` with `dead_character_prose_violation_count`.
8. GREEN: run DM test suite.
9. WITNESS: rerun Floodmark 128-cap; score and record metrics.

## Risks & Mitigations

1. Risk: false positives from passive references.
   - Mitigation: test-drive the heuristic exhaustively before wiring; start with
     high-precision pattern (verb directly follows name).

2. Risk: prompt change degrades prose quality by over-restricting the LLM.
   - Mitigation: the constraint only names dead characters, not plot constraints;
     minimal surface area.

3. Risk: `final_cut.yaml` variable injection breaks existing graph.
   - Mitigation: use conditional Jinja2 (`{% if dead_characters %}`) so existing
     runs without dead characters are unaffected.

## Related

- FR-507 - lifecycle seam gate (chapter-open enforcement)
- FR-509 - cast filter (intent-map enforcement)
- FR-508 - layered memory contract
- Evidence: run 10013, chapter 7, Alwina active despite `confirmed_dead` in
  chapter 6 seam packet
- Diary: `docs/diary/diary-2026-06-17-boundary-at-admission-not-detection.md`
  (Seed: "Does chapter_memory's character_state_deltas need semantic validation
  at close time?")
