# Feature Request: DM v2 — Wider Per-Turn Character Performance

**Priority:** MEDIUM
**Type:** Enhancement (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** Judged (2026-06-14). **APPROVED, scope frozen** to the additive
widening of `character_intent` from `{thinking, intent}` to
`{thinking, intent, dialogue, expression}` as a **side-channel the arc never
reads**. OQ1 → minimal pair (`dialogue`, `expression`), no third field; OQ2 →
recap stays `intent`-only; OQ3 → `thinking` private, `expression` its only public
projection; OQ4 → empty performance legitimate; OQ5 → missing keys default `""`
(no raise). **Binds an extra guard the FR did not name:** the witness must show
`intent` quality did **not** degrade from the widened call (see *Judgement*).
Same J3 rules apply: **no CAP/REQ, no CI gate, no demo-log**.
**Requested:** 2026-06-14
**Continues:** FR-477 (the turn graph `intents` map), FR-479 (the per-character
`{thinking, intent}` side-channel and the director judgement). Same J3 rules
apply: **no CAP/REQ, no CI gate, no demo-log**; the walkthrough tests under
`examples/dungeon_master/tests/` are a visibility harness, not a gate.
**Feeds:** FR-487 (the full-text walkthrough) — this FR is the **capture** pass
whose output FR-487 **renders**. See *Value Statement* for why that ordering is
the real justification.

**Model under test:** `vertex` / `gemini-3.5-flash`.

## Summary

Each turn, a character currently commits to exactly two things —
`thinking` (private interior) and `intent` (one concrete physical action) — via
`prompts/character_intent.yaml`, persisted at
`doc["turns"][n-1]["intents"][cid] = {thinking, intent}`. This FR **widens** that
per-character output to a small performance bundle: keep `thinking` and `intent`,
and **add the outward, playable layer** — the line the character *says*
(`dialogue`), and the visible tell that *projects* their inner state
(`expression`: facial / bodily). The widening is purely **additive** and is a
side-channel: the director and the dry recap continue to read **only** `intent`,
so the arc logic (FR-481/482/483) and the two Final Cuts (FR-484/485) consume
exactly the same inputs they do today.

## Value Statement

The honest justification is **not** "a reader wants richer turns" — that is the
weak, speculative framing the FR-485 judgement would reject. The real driver is a
concrete downstream need: **FR-487's full-text walkthrough must write the spoken
and acted scene, and "compose, don't invent" forbids it from fabricating dialogue
and body language that no character ever committed to.** Without an authored
performance layer, the full text would have to invent every line and every
gesture. This FR exists so that what FR-487 renders is *authored, in-character
performance* — decided by the same private, point-of-view reasoning that already
produces each `intent` — not prose the finishing pass made up. The secondary
benefit (the DM can inspect and steer each character's spoken/expressed beat while
playing) is real but is the bonus, not the case.

## Problem

The play loop captures, per character per turn, only the *decision*: what they
privately think and the one physical thing they attempt. It captures nothing of
how that decision is **performed** — no spoken line, no facial or bodily tell. So:

1. **The performance is lost at capture time.** `intent` is "raise the lantern";
   it does not hold "*'Stay back,' she breathes, knuckles white on the haft*."
   That spoken-and-expressed layer is exactly what a full rendering needs, and it
   simply does not exist in the record — it is gone the moment the turn is played.

2. **A downstream finish would have to invent it.** FR-487 will write the full
   text of each turn. With only `{thinking, intent}` available, it must fabricate
   the dialogue and the body language — inventing character voice the player never
   authored, which is the precise "compose, don't invent" violation the DM
   prototype has fought to avoid (FR-484/485). The cheapest place to fix that is
   here, at capture, not downstream in the renderer.

3. **`thinking` is private and must stay private.** Today the only outward channel
   is `intent`. There is no field whose job is to be the *visible projection* of
   the private interior — the tell an observer would actually see. `expression`
   fills that gap (show, don't tell): the inner state becomes performable without
   ever exposing the raw interior monologue.

The arc seam must not move. The director judges the arc on `intent`
(FR-481/482/483); the dry recap consolidates `intent`s (FR-477); both Final Cuts
consume the recaps (FR-484/485). Widening the performance must therefore be a
**side-channel** that those readers never see — additive keys only.

## Proposed Solution

Widen one prompt's output schema and the persisted intent shape; touch nothing the
director or recap reads.

### The deterministic seam vs the generative seam (FR-482/483/484/485 law)

- **Deterministic (code, `turn_ops` + persistence):**
  - The persisted bundle grows from `{thinking, intent}` to
    `{thinking, intent, dialogue, expression}` — **additive keys**. Old turns and
    any partial model output normalize at the boundary: a missing key reads as
    `""` (a played turn from before this FR, and a silent character with no line,
    must both still render). This is a side-channel on a prototype, not an arc
    input, so the boundary default is `""`, not a raise (contrast FR-485's
    alignment validator, where a missing turn *is* a defect — here a missing
    `dialogue` is a silent character, which is legitimate).
  - `turn_intents(doc, chars, n)` extends its returned cards from
    `{name, thinking, intent}` to also carry `dialogue` and `expression`, so the
    turn card view (and, later, FR-487) can surface the performance.
- **Generative (prompt, `character_intent`):** the character now returns, still in
  first person and still committing to **one** decisive `intent`:
  - `thinking` — unchanged; private interior (one or two sentences).
  - `intent` — unchanged; the single concrete action that drives the arc.
  - **`dialogue`** — what the character *says* this turn, in their own voice;
    `""` when they say nothing (not everyone speaks every turn).
  - **`expression`** — the visible tell that *projects* the thinking: facial or
    bodily — the thing an observer would see (e.g. "jaw set, eyes flicking to the
    door"). The outward face of the interior, never the interior itself.

  Quality (does the expression actually convey the thinking? does the dialogue
  sound like the sheet?) has no clean deterministic witness — it is judged by a
  live run (as FR-484/485 OQ5).

### The artifact stays additive and the arc seam stays frozen

- `prompts/turn_direct.yaml` and `prompts/turn_recap.yaml` are **unchanged**: the
  director and narrator still receive only `intent` per character. A test asserts
  the director/recap inputs and behaviour are byte-for-byte what they are today —
  the wider fields must **not** leak into the arc judgement or the dry recap, so
  the FR-484/485 cuts are provably unaffected.
- `doc["turns"][n-1]["recap"]` keeps its `{text, reviewed}` shape; the performance
  lives only under `intents[cid]`.

### Explicitly out of scope

- **Rendering the full spoken/acted scene** — that is FR-487. This FR only
  *captures and surfaces* the performance; it does not weave it into prose.
- **Feeding dialogue into the dry recap** — rejected. The recap stays dry so the
  FR-484/485 cut inputs do not shift; the spoken scene is FR-487's artifact.
- **Exposing `thinking` to any rendered output** — `thinking` stays private; its
  only sanctioned public projection is `expression`.
- **A third/fourth performance field** (`manner`, `tone`, `body` …) — resist
  proliferation; `dialogue` + `expression` is the minimal pair that lets FR-487
  write a spoken, acted turn. More is OQ1, defended only by a live gap.

## Acceptance Criteria (draft — the Judge supersedes)

- [ ] `character_intent.yaml` returns `{thinking, intent, dialogue, expression}`;
      `dialogue` and `expression` may be `""` (silent / no overt tell).
- [ ] `turns[n-1].intents[cid]` persists all four keys additively; a turn played
      before this FR (missing the two new keys) still resolves via `""` defaults.
- [ ] `turn_intents` cards carry `dialogue` and `expression`; the turn card view
      surfaces them.
- [ ] The director (`turn_direct`) and recap (`turn_recap`) inputs and outputs are
      unchanged — existing turn/director/recap tests pass with no edits, proving
      the arc seam and the FR-484/485 cut inputs did not move.
- [ ] One live `vertex` witness: a turn where `expression` visibly projects
      `thinking` (the tell matches the private read) and `dialogue` is in the
      character's voice; recorded in the Implementation Status as structural facts.
- [ ] Tests added (the walkthrough visibility harness; no `@pytest.mark.req`).

## Open Questions (for the Judge)

- **OQ1 — field set.** Is `{dialogue, expression}` the right minimal pair, or is a
  third field (e.g. `manner`/`tone`) needed for FR-487 to render well? Lean:
  minimal pair; add only on a demonstrated live gap.
- **OQ2 — recap.** Keep the dry recap reading only `intent` (lean: yes — preserves
  FR-484/485 cut inputs), or let the recap begin to weave dialogue now? Lean: no;
  the spoken scene is FR-487.
- **OQ3 — `thinking` privacy.** Confirm `thinking` is never rendered downstream and
  `expression` is its only public projection (show, don't tell). Lean: yes.
- **OQ4 — empty performance.** Confirm `dialogue`/`expression` may be empty (silent
  character, blank face) and that empty is legitimate, not a defect. Lean: yes.
- **OQ5 — boundary default.** Confirm old turns / partial output default missing
  performance keys to `""` (not raise), because this is an additive side-channel,
  not an arc post-condition. Lean: yes — `""`.

## Alternatives Considered

- **Put the performance in the recap instead of per character.** Rejected: the
  recap is a single consolidated voice (the narrator), not per-character authored
  performance, and changing it shifts the FR-484/485 cut inputs. Per-character
  capture keeps each voice owned by its own point-of-view reasoning.
- **Let FR-487 invent dialogue at render time.** Rejected: that is the
  compose-don't-invent violation this FR exists to prevent. Authoring the
  performance at capture, by the character's own reasoning, is the structurally
  honest place.
- **A larger performance schema now** (tone, posture, props…). Rejected for a
  prototype: the minimal `dialogue` + `expression` pair is what FR-487 needs;
  proliferation is speculative extensibility (the FR-485 lesson).

## Related

- `examples/dungeon_master/prompts/character_intent.yaml` — the widened schema.
- `examples/dungeon_master/api/turn_ops.py` — `turn_intents`, persisted shape.
- `examples/dungeon_master/turn.yaml` — the `intents` map node (unchanged graph).
- FR-477, FR-479 — the turn graph and the `{thinking, intent}` side-channel.
- FR-487 — the full-text walkthrough that renders this performance.

## Judgement (2026-06-14)

**Verdict: APPROVED, scope frozen.** This is a small, additive, low-risk change
whose justification is honest *because* it refuses the speculative framing. I
examined it hardest at three seams: the stated value, the arc-seam claim, and a
risk the FR underweights.

### Red Hat — is the pain real?

The FR's own value statement disarms the trap that would have killed it. "A reader
wants richer turns" is the speculative-extensibility framing the FR-485 judgement
rejects, and the FR says so outright. The pain it stands on instead is concrete
and **downstream-forced**: FR-487 must render spoken, acted prose, and
"compose, don't invent" forbids it from fabricating a performance no character
ever authored. That is a real structural-honesty pain — *conditional on FR-487
proceeding.* Since I am also judging FR-487 (approved below), the condition holds:
the capture pass is the cheapest, most honest place to author the performance, at
the point of the character's own point-of-view reasoning. Approved on that basis,
not on the inspect-while-playing bonus (which the FR correctly demotes).

### The load-bearing claim: the arc seam does not move

Everything rests on the director (`turn_direct`) and the dry recap (`turn_recap`)
continuing to read **only `intent`**, so FR-481/482/483 and the FR-484/485 cuts
consume byte-for-byte identical inputs. The FR asserts this and proposes a test
for it. **I make that test mandatory and load-bearing:** the existing turn /
director / recap tests must pass *unedited*, and a test must assert the
director/recap variable bundles contain no `dialogue`/`expression`. If the wider
fields leak into the arc judgement, the change is rejected on sight — the whole
approval depends on the side-channel staying a side-channel.

### The risk the FR underweights — intent-quality dilution

The FR treats the widening as free. It is not quite. Asking one call to produce
`thinking + intent + dialogue + expression` instead of `thinking + intent` can
**dilute the model's focus on the single decisive `intent`** — and `intent` is the
field the entire arc logic reads. A degraded `intent` would silently weaken
FR-481/482/483 while every seam-freeze test still passes (the inputs are
structurally identical; only their *quality* dropped). This is the
`plausible_wrong_answer` trap at the performance boundary. **Binding:** the
required live `vertex` witness must show, on a real turn, that `intent` is still a
single concrete decisive action of the same calibre as today — not a hedge or a
sentence fragment crowded out by the new fields. The prompt must keep `intent`
first and explicitly singular. If the witness shows dilution, the fix is in the
prompt (order/instruction), not a schema retreat.

### Open questions — resolved

- **OQ1 (field set):** minimal pair `dialogue` + `expression`. No `manner`/`tone`.
  A third field is a *future* FR defended by a demonstrated FR-487 live gap.
- **OQ2 (recap):** the dry recap reads **only `intent`**. Binding (above).
- **OQ3 (privacy):** `thinking` is never rendered downstream; `expression` is its
  sole public projection. The prompt must say so (show, don't tell).
- **OQ4 (empty performance):** `dialogue`/`expression` may be `""`; a silent
  character with a blank face is legitimate, not a defect.
- **OQ5 (boundary default):** missing performance keys default to `""` — **not** a
  raise. This is the correct asymmetry against FR-485: an additive side-channel
  normalizes to a benign empty; an arc post-condition (alignment) raises. The two
  must not be confused.

### Binds on the enforcer

1. TDD: widen the persisted-shape / `turn_intents` behaviour with a failing test
   first (old turn missing keys → `""`; new turn carries all four).
2. Arc-seam freeze test is mandatory and must pass unedited (above).
3. The widened prompt keeps `intent` first and explicitly singular; `expression`
   defined as the *visible projection of `thinking`*, never the interior itself.
4. One live `vertex` witness recorded as structural facts: `expression` visibly
   tracks `thinking`, `dialogue` is in-voice, **and `intent` quality undegraded**.
5. Additive keys only; no new artifact; recap/director untouched; lints + graph
   lint clean.

**Authority granted** for the four-field side-channel and nothing more. The recap
weaving dialogue, a third performance field, and any rendering of `thinking` are
**out**.

## Implementation Status (2026-06-14) — DONE

Enforced under TDD. RED first: `test_turn_captures_wider_performance`,
`test_turn_intents_defaults_missing_performance_to_empty`,
`test_turn_card_surfaces_dialogue_and_expression` failed; the seam-freeze
sentinel `test_arc_seam_ignores_wider_performance` passed from RED (the new
fields are never referenced by `turn_direct`/`turn_recap`). GREEN: **37 passed**
(33 prior + 4 new), `ruff check` clean, `ruff format --check` clean (12 files),
`yamlgraph graph lint turn.yaml` clean.

**Changes (additive, no new artifact):**
- `prompts/character_intent.yaml` — system prompt returns four things, `intent`
  first and explicitly singular ("decide it first and keep it sharp; the other
  three serve it"); `expression` defined as the visible projection of `thinking`,
  never the interior; schema `required: [intent, thinking, dialogue, expression]`.
- `api/turn_ops.py` — `invoke_turn` persists 4 keys per cid; `turn_intents`
  cards now `{name, thinking, intent, dialogue, expression}` with new keys
  defaulting to `""` (benign side-channel, never raises — the FR-485 asymmetry).
- `api/templates/components/turn_card.html` — conditional "Says"/"Shows" rows.
- `api/session.py` — removed dead `_turn_intents` (stale 2-field duplicate,
  unused; entropy purge).

**Live vertex witness** (neutral flood-ledge arc, `gemini-3.5-flash`, structural
facts only): both `kara` and `tarek` returned all four fields non-empty;
`intent` a single decisive action (11 and 15–16 words, single-act check True) —
**undegraded** despite the widened call. Representative shape: `intent` 11 words,
`thinking` 24 words (private interior), `dialogue` 7 words (a spoken line),
`expression` 13 words (visible tell projecting the thinking). The Judge's
plausible-wrong-answer binding (intent must not dilute into a hedge) holds.

**Seam freeze proven:** `test_arc_seam_ignores_wider_performance` asserts
`dialogue`/`expression` appear in neither `turn_direct.yaml` nor `turn_recap.yaml`;
green throughout. The arc reads `intent` only, as before.
