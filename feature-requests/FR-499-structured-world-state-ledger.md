# Feature Request: FR-499 — Structured world-state ledger + enforced continuity gate

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged — Phase A frozen, Phase B gated (2026-06-16); see Judgement
**Effort:** 2–3 days
**Requested:** 2026-06-16

## Summary

Replace the DM v2 prose `world_state` ledger with a **typed, structured** running
state — `character → {faction, status, location, inventory[]}` and
`object → {holder|location}` — carried forward between chapters as data, not lossy
prose; and upgrade the chapter director from an *advisory* continuity flagger into
an **enforced gate** that rejects a chapter event contradicting a standing ledger
fact.

This is the **root-cause** fix for the cross-chapter continuity breaks the
`book_reviewer` (FR-497) found in the *Floodmark Saga*: the generator already
*passed every per-chapter gate* yet the book fails, because continuity is a
*between*-chapter, fact-level property no node enforces (Scripture:
`composition_bug` — every component passes its unit test; the defect is in the
policy connecting them).

## Value Statement

Continuity stops *entering* the next chapter at all: a structured ledger preserves
inventory and position that terse prose drops, and a director that checks each
chapter event against the ledger turns "who is alive/where/holding what" from an
unverified narrative aside into an enforced constraint at the seam where the next
chapter is generated — converting four reviewer-found break classes (barrier
overturned, phantom weapons, teleporting objects, status drift) into impossibilities
rather than after-the-fact findings.

## Problem

The forward-carry ledger exists today
([prompts/chapter_close.yaml](examples/dungeon_master/prompts/chapter_close.yaml),
FR-491 J7) — but it is **prose** ("a few terse sentences or bullet lines"), and the
director ([prompts/turn_direct.yaml](examples/dungeon_master/prompts/turn_direct.yaml))
only flags *actors not in the roster*. That leaves three holes, and the FR-497
review of `outputs/dungeon-master/10000-BC/review.md` found exactly the breaks they
let through:

| Reviewer finding | Hole |
|---|---|
| Arnulf stranded **below** a wedged slab (Ch2) → **above** it (Ch3) | Ledger fact silently overturned without the "say so plainly" acknowledgment the prompt asks for |
| Phantom **hand-axe** / reappearing knife | Inventory not a tracked field; terse prose drops "what they hold" |
| Valda's staff **seized & planted** (Ch3) → wielded again (Ch4, Ch6) | Object holder/location not tracked |
| Status/position drift between chapters | Prose ledger is unverifiable; director never checks an event against it |

Prose is lossy at the carry-forward boundary and unenforceable at the generate
boundary. The fix must **normalize at both**.

## Proposed Solution

**1. Typed ledger (carry-forward boundary).** Replace the single `world_state`
string with a Pydantic-backed structure produced by `chapter_close` and threaded
into the next chapter's STARTING WORLD STATE:

```yaml
# chapter_close.yaml output_schema (replacing the single world_state string)
world_state:
  characters:        # keyed by name
    - name: str
      faction: str   # carried from roster (FR-498)
      status: str    # alive | dead | wounded | missing | …
      location: str
      inventory: [str]
  objects:
    - name: str
      holder: str    # character name, or "" if unheld
      location: str
  facts: [str]       # irreversible standing facts not captured above
```

The next chapter inherits this as data; `chapter_close` updates it (carry still-true
entries, overturn only with an explicit changed-status note, drop what is no longer
true) — the same J7 discipline, now machine-checkable.

**2. Enforced continuity gate (generate boundary).** Give the director the typed
ledger and have it reject (not merely flag) a turn whose intent contradicts a
standing fact — e.g. an actor acting from a location/status the ledger forbids, or
wielding an object the ledger says another holds. Reuse the existing `continuity`
field for surfacing, but add a blocking signal the play loop honors (steer/retry the
turn), mirroring the J5 "raise rather than emit something wrong" stance the
headless generator already takes.

This is a **prototype-scope** change under the FR-474 J3 regime: it touches only
`examples/dungeon_master/` (prompts + the session/ledger plumbing in `api/`), adds
**no** CAP file and **no** `@pytest.mark.req` markers, and is committed with an
honest `feat(dungeon-master): FR-499 …` plus the `FR-474 J3` trailer.

## Acceptance Criteria

- [ ] `chapter_close` emits the typed `world_state` structure (characters, objects,
      facts); validated by Pydantic, persisted via the adapter.
- [ ] Next-chapter STARTING WORLD STATE is built from the structure, not prose.
- [ ] Carry-forward preserves inventory and location across at least 3 chapters in a
      witness run (no silent drops).
- [ ] Director rejects/steers a turn that contradicts a standing ledger fact;
      demonstrated by a targeted witness.
- [ ] A regenerated multi-chapter book, re-reviewed by `book_reviewer`, shows a
      materially improved continuity score vs. the FR-497 baseline (1/5), captured
      to a log.
- [ ] Diary reflection + changelog fragment added.

## Alternatives Considered

- **Keep prose, just instruct harder.** Already tried implicitly (the prompt asks
  for precision); prose remains lossy and unenforceable. Rejected.
- **Editor-only repair (FR-500).** Fixes symptoms downstream and re-runs forever;
  does not stop drift from entering. Complementary, not a substitute.
- **Full symbolic world model / rules engine.** Over-engineered for a prototype;
  a typed ledger + director check is the minimal sufficient normalization.

## Related

- FR-491 J7 — the prose `world_state` ledger this FR upgrades
- FR-498 — roster `faction`/`inventory` (the front-boundary half; supplies the
  ledger's initial values)
- FR-497 — `book_reviewer` (the located evidence and the regression oracle)
- `examples/dungeon_master/prompts/chapter_close.yaml`, `turn_direct.yaml`,
  `api/session.py`
- `outputs/dungeon-master/10000-BC/review.md` (live evidence)

## Judgement — 2026-06-16 (scope frozen with amendments)

**Status:** Judged — scope frozen, **split into two phases**. Verified the plumbing
before ruling.

**Red Hat — is the pain real?** Yes, and it is the root cause: every chapter passed
its director gate yet the book scored continuity **1/5**. This is the
`composition_bug` — correct parts, broken connecting policy. Authorized.

**Plumbing verified (premise holds).** `world_state` is a single `str` threaded
end-to-end: written by `chapter_close`, stored on the chapter card
([api/session.py](examples/dungeon_master/api/session.py) `world_state: str`),
inherited via [api/turn_ops.py](examples/dungeon_master/api/turn_ops.py)
`inherited_world_state(doc, cid)` → `cards[order[i-1]]["world_state"]`, applied in
`doc_ops.apply_chapter_close`. A structured replacement has exactly these four
touch-points. The Proposed schema is sound.

- **J1 (split — BLOCKING).** This FR bundles two changes of very different risk:
  (a) **typed ledger** (a serialization change — bounded, testable, low risk) and
  (b) **enforced/blocking director gate** (changes the play loop's control flow —
  high risk of false-positive stalls, interacts with `scene_complete`, `turn_cap`,
  and retry). Ruling: **Phase A = typed ledger only** (carry-forward boundary).
  **Phase B = director continuity *enforcement*** (generate boundary), gated on
  Phase A landing and on a witness proving the false-positive rate is acceptable.
  Freeze Phase A now; Phase B stays Proposed until Phase A's witness exists.
- **J2 (the `objects` ledger is the highest-value field).** Three of four reviewer
  findings (hand-axe, knife, staff) are *object* breaks; one (barrier) is location.
  The `objects: [{name, holder, location}]` block is non-negotiable in Phase A —
  it is where the prose ledger leaks most.
- **J3 (carry-forward must be lossless, J7 discipline preserved).** Phase A keeps
  FR-491 J7's rules (carry still-true entries, overturn only with an explicit
  changed-status note, drop what is no longer true) — now machine-checkable per
  field instead of asserted in prose.
- **J4 (no blocking in Phase A).** Phase A may *populate* `continuity` flags from
  ledger diffs (advisory, complementing FR-498 J4) but MUST NOT alter the play
  loop. Blocking is Phase B only. This prevents control-flow risk riding in on a
  serialization change.
- **J5 (render stays clean).** The structured ledger is **plumbing**, never
  rendered ([api/render.py](examples/dungeon_master/api/render.py) already excludes
  `world_state`). The structure must not leak into `story.md` — same no-stored-book
  discipline (FR-492).
- **J6 (regime).** Prototype-only. FR-474 J3 applies: no CAP, no `@pytest.mark.req`,
  honest `feat(dungeon-master): FR-499 …` + `FR-474 J3` trailer. Phases A and B are
  separate commits.
- **J7 (regression oracle).** Success = a regenerated multi-chapter book's
  `book_reviewer` continuity score **materially beats the 1/5 baseline**. That is
  the only acceptance proof that matters; assert it on a captured witness log.

**Frozen — Phase A acceptance** (Phase B deferred):
1. `chapter_close` emits typed `world_state` {characters[], objects[], facts[]};
   Pydantic-validated, persisted via adapter; the four touch-points updated.
2. Next-chapter STARTING WORLD STATE built from the structure, not prose.
3. Carry-forward preserves inventory + location across ≥3 chapters (witness, no
   silent drops).
4. Structure never appears in `story.md` (render-purity witness).
5. Regenerated Floodmark-class book re-reviewed by `book_reviewer` shows improved
   continuity vs. 1/5 baseline (witness log).
6. Diary + changelog fragment.

**Phase B (Proposed, gated on Phase A):** director *rejects/steers* a turn
contradicting a standing ledger fact; acceptance includes a false-positive witness
(a legitimately surprising-but-valid turn is NOT blocked).

## Implementation Status — Phase A Enforced

- **Typed ledger (AC1).** New `api/world_state.py`: Pydantic `WorldState`
  (`characters[]{name, faction, status, location, inventory[]}`,
  `objects[]{name, holder, location}`, `facts[]`), `parse_world_state` (validates
  + tolerates legacy str/None/junk → empty ledger at the boundary), and a
  deterministic `format_world_state` (dict → terse prompt text, "" when empty).
  `prompts/chapter_close.yaml` rewritten to emit the structured object;
  `chapter_ops.close_chapter` validates the result with `parse_world_state`.
- **Four touch-points threaded.** `turn_ops.inherited_world_state` now returns the
  structured dict (`{}` for first chapter); `running_scene` formats it into
  STARTING WORLD STATE (AC2); `chapter_ops.close_chapter` formats the inherited
  ledger into `previous_world_state` and stores the validated structure;
  `session.py` renders the chapter card's ledger via `format_world_state`.
- **Render purity (AC4).** `test_render_never_leaks_structured_world_state` proves
  the dict never reaches `story.md` (no object names, no dict repr).
- **Carry-forward (AC3).** `test_inherited_world_state_returns_previous_structured_ledger`
  + `test_running_scene_formats_structured_ledger_into_prompt_text` prove inventory
  + location survive the chapter boundary as formatted text, not a raw repr.
- **Tests.** New `tests/test_world_state.py` (12 tests: parse/format/carry-forward/
  render-purity); migrated `test_chapters.py` + `test_turn_prototype.py` fixtures
  from `str` to structured ledgers (the forward-carry seam tests went RED on the
  type change — the plumbing assertion held). Full DM suite: **107 passed**.
  `chapter_close.yaml` lints clean; ruff + import-linter clean.
- **Detection only (J4).** No blocking added; the ledger informs continuity
  advisorily. Phase B (blocking gate) remains deferred.
- **Regime (J6).** `feat(dungeon-master): FR-499 …` + `FR-474 J3` trailer; no CAP,
  no `@pytest.mark.req`. Separate commit from FR-498. Changelog fragment + diary.

**Status: Phase A Enforced** (AC5 live-witness: see combined Floodmark-v2 regen +
review). Phase B remains Proposed/gated.

## Implementation Status — Phase A live-run hardening (2026-06-16)

Two boundary defects surfaced only under real generation (the green unit suite
proved plumbing but not *render* or *budget*):

- **Prompt-brace KeyError.** `format_prompt` renders each message independently and
  falls to `str.format()` when a message has no Jinja markers; the rewritten
  `chapter_close` prompt's literal `{"world_state": …}` JSON braces were read as
  format fields → `KeyError('"world_state"')`. Fixed by describing the JSON shape in
  **prose** (matching `chapter_outline.yaml` house style). Pinned by
  `test_chapter_close_prompt_messages_render_without_keyerror` (RED→GREEN), which
  renders every prompt message through the real `format_prompt` with real vars.
- **Reasoning starves the ledger.** gemini-3.5-flash spends hidden thinking tokens
  from the *completion* budget before emitting JSON; a `max_tokens: 2000` cap was
  consumed entirely by reasoning (~1921 tok observed in LangSmith), leaving
  `text: ""` → an empty ledger silently rendered as no characters/objects. Fixed at
  the config boundary in `chapter_close.yaml` defaults: `max_tokens` 2000→8000 **and**
  `thinking_budget: 512` to bound reasoning so the JSON always has room. The
  threshold is kept **below 1024** deliberately — `create_llm()` rejects
  `thinking_budget >= 1024` on non-thinking providers, so a sub-threshold value
  bounds Gemini reasoning on vertex yet is silently ignored on inception/mercury
  (used for fast test runs), keeping the graph provider-portable. Pinned by
  `test_chapter_close_reasoning_budget_cannot_starve_the_ledger`. Live witness:
  ledger populates (Hilde/Gunnar/Arnulf/Torstein, Gunnar's axe, 4 facts); completion
  bounded 1996→1351 tok. Full DM suite: **109 passed**.
