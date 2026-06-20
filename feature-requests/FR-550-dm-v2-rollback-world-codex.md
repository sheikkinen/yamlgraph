# Feature Request: DM v2 — Roll Back the Synopsis-Derived World Codex (FR-548)

**Priority:** HIGH (active multi-source-drift hazard; remove before the `doc["codex"]` schema ossifies into saved stories)
**Type:** Removal
**Status:** Enforced (RED 91eda6fe condemns the live symbols -> GREEN this commit) — `tests/test_no_world_codex.py` is the permanent guard; codex grep returns zero; final_cut.yaml lints clean; 388 DM tests green
**Effort:** ~0.5 day
**Requested:** 2026-06-20

## Summary

Remove the FR-548 **World Codex** stage in full — the `world_codex.yaml` graph, its prompt,
the `expand_codex`/`_normalize_codex` boundary, the `WORLD_CODEX_GRAPH` declaration and its
synopsis-accept sequencing, the `final_cut` weave, and the `doc["codex"]` persistence. The codex
is a *placement defect*, not a tunable: it authors **prose, before the action exists, from the
synopsis**, and every failure observed in 10034-BC follows mechanically from that placement. The
length/depth goal it served is re-earned from sound sources by FR-551 (supporting-cast tier) and
FR-552 (world bible), which share almost no code with synopsis-derived prose. This is a judged
`removal`, not a raw `git revert` — doctrine: *"If it is not required and not tested, it shall not
exist."*

## Value Statement

The codebase sheds a stage that leaks characters into immutable world texture and creates an
un-precedenced character-state source the continuity witnesses cannot track — removing a known
multi-source-drift hazard (the exact failure FR-534's three-source precedence exists to forbid)
while it is still cheap to remove, before the `codex` key hardens into persisted `story.json` files.

## Problem

FR-548 shipped on the hypothesis that faction/location backstory is *additive, ~zero continuity
cost*. The 10034-BC causal check falsified that hypothesis **by mechanism**:

- **Roster = `[hilde, gunnar, arnulf, wenda]`, but the codex names `Reinmar`** — a character not in
  the roster. The codex invented a person.
- **`factions` included "Wenda's people" and "the combined survivors"** — plot-derived groupings
  that embed characters, not stable institutions.
- **Every breaking character (Arnulf, Reinmar, Wenda) appears in the codex text** — world texture
  meant to be character-free became a second, unbridged character-state source.

The root cause is **placement, not content**, so a name-blocklist in `expand_codex` would treat the
symptom and leave the cause:

1. **The synopsis IS plot.** Asking a plot summary for "factions and locations" pulls plot in,
   because plot is all it contains — there is no clean world/plot seam to extract at that boundary.
   "Wenda's people" and the Reinmar leak are the inevitable result, not a one-off.
2. **Prose authored before its action is speculative.** It describes a world the chapters have not
   realized yet, so it can drift from — or contradict — the text that follows.

The +1,400-word length gain was therefore **contaminated** (partly leaked codex prose), not a clean
win worth defending. None of the 10034-BC reviewer breaks is a codex-content contradiction; the
codex did not *directly* cause the 1/5 score (10031-BC scored the same with no codex), but it is an
active drift hazard regardless of this run's score.

## Proposed Solution

> **Amended per Judgement J1-J4 (2026-06-20).** Excise by **symbol name, not line number** —
> `doc_ops.py` was reformatted after this FR was drafted, so every cited line below is advisory only.
> `scripts/generate.py` has **no** codex call to remove (J2, verified). Keep the guard test permanently
> (J3).

Remove every FR-548 artifact and touch-point. Inventory (excise by symbol; line numbers advisory):

**Delete (whole files):**
- `examples/dungeon_master/world_codex.yaml` (the graph)
- `examples/dungeon_master/prompts/world_codex.yaml` (the prompt)
- `examples/dungeon_master/tests/test_world_codex.py` (the FR-548 tests, **except** the one-line
  re-introduction guard — see J3 below; relocate that guard to a surviving test module)

**Excise (in-file, by symbol):**
- `api/doc_ops.py`: `expand_codex`, `_normalize_codex`, `_codex_entries`,
  `_CODEX_FACTION_FIELDS`, `_CODEX_LOCATION_FIELDS`, and the `WORLD_CODEX_GRAPH` import.
- `api/tree.py`: the `WORLD_CODEX_GRAPH` constant and its comment block.
- `api/session.py`: the `await doc_ops.expand_codex(doc, story_dir)` call and its comment in the
  `stage.name == "synopsis"` branch. `expand_roster` stays.
- `api/final_cut.py`: `_format_world_codex` and the `"world_codex": _format_world_codex(doc)`
  context entry.
- `final_cut.yaml`: the `world_codex: str` state key and the `world_codex: "{state.world_codex}"`
  variable binding.
- `prompts/final_cut.yaml`: the `{% if world_codex %}WORLD CODEX … {{ world_codex }}{% endif %}`
  block.
- `scripts/generate.py`: **nothing to remove (J2).** Verified — `generate.py` drives
  `session.weave()` + `session.accept()`; the `expand_codex` call lives only in `session.accept()`'s
  synopsis branch, which the excision above already covers. Do not invent a removal here.

**Verify clean:** after removal, `grep -ri 'codex' examples/dungeon_master/` returns zero matches
(except the one-line re-introduction guard test, J3); `yamlgraph graph lint
examples/dungeon_master/final_cut.yaml` passes; the full DM suite is green; a fresh generation
produces a `story.json` with **no** `codex` key.

## Acceptance Criteria

- [ ] **(RED, committed separately, `SKIP=pytest`)** A guard test asserting the post-removal
      invariant: `expand_codex` no longer exists on `doc_ops` (`not hasattr(doc_ops, "expand_codex")`),
      and a fresh generated doc has no `"codex"` key — RED before removal (the symbol still exists),
      GREEN after. **(J3 — decision made) KEEP this as a permanent one-line regression guard against
      re-introduction**; relocate it into a surviving test module (e.g. `test_doc_ops.py`) rather than
      deleting it with `test_world_codex.py`.
- [ ] All FR-548 files deleted; all in-file touch-points excised **by symbol name** per the inventory
      above (J1 — do not trust the line numbers; the file was reformatted).
- [ ] `grep -ri 'codex' examples/dungeon_master/` returns zero matches **except** the relocated
      re-introduction guard test (no orphaned references, comments, or doc strings elsewhere).
- [ ] `final_cut.yaml` + every DM graph lints clean; full DM test suite green.
- [ ] A fresh `generate_and_review.sh` run produces a `story.json` with no `codex` key and the
      `final_cut` prompt is byte-identical to the pre-FR-548 template (the guarded block is gone, not
      merely empty).
- [ ] FR-548 markdown updated: Status → **Reverted (superseded by FR-550)** with a one-line pointer
      to FR-551/FR-552 as the sound re-approach.
- [ ] Example-exempt: NO `@pytest.mark.req`, NO capability YAML; changelog fragment `type: removal`,
      `scope: examples`, no `req:`.
- [ ] Distill diary entry (the placement-defect lesson: speculate only on declarations; make prose
      either ground-truth input or post-action grounded).
- [ ] Modules touched stay under the 450-line ceiling (removal only shrinks them).

## Alternatives Considered

- **Name-blocklist patch in `expand_codex`** (drop/warn on entries naming roster members): rejected —
  treats the symptom (`gate_checks_shape_not_substance`). The cause is a speculative pre-action prose
  stage derived from plot; a blocklist leaves that stage in place and still maintained.
- **Keep the codex, move it post-action**: rejected here, owned by FR-552 — that is a *different*
  stage (grounded from played chapters, not synopsis-derived) sharing no code with FR-548. Removing
  FR-548 first keeps the tree clean for FR-552's design.
- **Leave FR-548 shipped, attribute the 1/5 to noise**: rejected — `working_system_inertia`. The
  score is noise, but the character-leak mechanism is a real defect independent of the score, and the
  stage is non-load-bearing, so removal cost only grows with time.
- **`git revert` the FR-548 commits directly**: rejected — doctrine requires a judged FR for the
  removal so the rationale is recorded; a raw revert loses the placement-defect lesson.

## Related

- `feature-requests/FR-548-dm-v2-world-codex-backstory-stage.md` — the stage being removed
- `feature-requests/FR-551-dm-v2-supporting-cast-tier.md` — the coherence-lever re-approach (cast)
- `feature-requests/FR-552-dm-v2-world-bible.md` — the length/depth re-approach (world texture)
- `examples/dungeon_master/api/doc_ops.py` — `expand_codex`/`_normalize_codex` to excise
- `examples/dungeon_master/api/session.py` — `weave` synopsis-accept branch (L289–293)
- `examples/dungeon_master/api/final_cut.py` — `_format_world_codex` (L314) to excise
- FR-534 three-source character-state precedence — the contract the codex's character leak violated
- Evidence: 10034-BC causal check (roster=[hilde,gunnar,arnulf,wenda]; codex named Reinmar; factions
  "Wenda's people"/"the combined survivors")

## Judgement (2026-06-20) — APPROVE

**Verdict: APPROVE.** The central premise was verified against live data, not taken on the FR's word.

**Evidence is real (Red Hat "is the pain real?" check passed).** Read directly from
`outputs/dungeon-master/10034-BC/story.json`:
- `characters.roster == ["hilde","gunnar","arnulf","wenda"]` — **Reinmar is absent**, yet `codex` text
  names him. A non-roster character leaked into immutable world texture.
- `codex.factions == ["Aschenwulf","Bärenschädel","Wenda's people","the combined survivors"]` — the
  last two are plot-derived groupings that embed characters, exactly as the FR claims.
- `Wenda`, `Arnulf`, `Reinmar` all appear in the codex JSON. The FR-548 "additive, ~zero continuity
  cost" hypothesis is **falsified by live data.** The placement defect (plot synopsis IN, character-
  bearing world prose OUT) is genuine, not a tuning issue. A name-blocklist would treat the symptom
  (`gate_checks_shape_not_substance`) and leave a speculative-pre-action-prose stage in place.

**This is a judged removal, correctly framed.** Doctrine "if it is not required and not tested, it
  shall not exist" applies; FR-548 is non-load-bearing (10031-BC scored the same with no codex), so
  removal cost only grows as `codex` hardens into saved `story.json` files. Forward removal, not a
  history rewrite — correct (the FR-548 commits are already on `origin/main`; this FR removes the
  artifact going forward).

**Conditions (minor, do not require re-judge):**
- **J1 — Inventory by symbol, not line.** `doc_ops.py` was reformatted after the FR was written
  (`expand_codex` is now L277, not the cited L289-range; `session.py` synopsis branch is L287-293).
  Excise by symbol name (`expand_codex`, `_normalize_codex`, `_codex_entries`, `_CODEX_FACTION_FIELDS`,
  `_CODEX_LOCATION_FIELDS`, `WORLD_CODEX_GRAPH`, `_format_world_codex`); treat every cited line number
  as advisory.
- **J2 — `scripts/generate.py` has no codex call to remove.** Verified: `generate.py` drives
  `session.weave()` + `session.accept()`; the `expand_codex` call lives only in `session.accept()`'s
  synopsis branch (L293). The FR already hedges this ("verify and remove") — the verify returns zero,
  so there is nothing to excise there. Do not invent a removal.
- **J3 — Keep the guard test (resolve the FR's "Judge's choice").** Keep a one-line permanent
  regression guard: `not hasattr(doc_ops, "expand_codex")` + a fresh doc has no `"codex"` key. Cheap
  insurance against re-introduction; do not delete it in the GREEN commit.
- **J4 — The `grep -ri 'codex'` zero-match AC is substantive, keep it** (it checks absence of orphaned
  references, not mere file deletion). Good gate.

**Ordering:** FR-550 first (clean tree), then FR-551 (fills the vacated synopsis-accept slot), then
FR-552 (depends on FR-551's tracked roster for its leak-check). Proceed to RED-first enforce under the
existing example-exempt discipline. Status -> **Approved (authority to enforce).**
