# Feature Request: DM v2 — Two-Tier Roster with a Declared Supporting Cast

**Priority:** HIGH (coherence lever — attacks the single most recurring defect class across the arc)
**Type:** Feature
**Status:** Approved with conditions (fold C1-C4; enforce after FR-550)
**Effort:** ~2 days
**Requested:** 2026-06-20

## Summary

Add a **supporting-cast tier** to the roster: after the main cast is named (`expand_roster`,
FR-475), a second side-effect stage derives the **supporting characters** the synopsis requires —
the guides, antagonists, lost companions, and clan figures the story leans on — each declared with
a one-line **role** and a **lifecycle slot** and **reconciled into the roster**. This makes
non-roster NPCs *first-class, tracked* characters instead of ad-hoc prose inventions, closing the
single most recurring defect class in the whole DM arc.

## Value Statement

The play loop stops inventing untracked NPCs in chapter prose — every supporting character a chapter
names is a declared roster member with a lifecycle the seam-entrance (FR-538), allegiance (FR-545),
and overlay (FR-544) witnesses can already see — directly attacking the non-roster break class that
the witnesses are structurally blind to today.

## Problem

**Non-roster named NPCs are the single most recurring defect across the entire arc:**

| Book | Non-roster NPC defect |
|------|------------------------|
| 10028-BC | Arnulf (appears Ch3, drowns, no establishment), Eirik (returns alive Ch6) |
| 10030-BC | Arnulf (acts Ch3 "already with them", absent Ch1/2) |
| 10034-BC | Reinmar (guide Ch3) → Wenda (Ch4) role-swap, no transition |

The roster is **one flat tier** of ~4 main characters (`expand_roster` → `split_roster` →
one card per name). A multi-chapter survival saga *structurally* needs more people than its
protagonists — guides, antagonists, the drowned companion, the rival clan's envoy. With no slot for
them, the generator invents them ad hoc in chapter prose at 0.7 temperature: **no establishment, no
lifecycle, no roster identity.** The witnesses are roster-scoped by design (FR-538 chose roster-only
explicitly), so these NPCs are invisible to every deterministic rail — they surface only when the
LLM reviewer flags them, after the fact.

FR-538's worked example documented non-roster NPCs as *out of scope* precisely because there was no
mechanism to track them. This FR builds that mechanism. It is also what makes the FR-548 character
leak (`Reinmar` named outside the roster) impossible *by construction*: a supporting character is a
roster member, not loose world prose.

## Proposed Solution

A new side-effect stage `expand_supporting_cast`, mirroring `expand_roster`'s pattern, plus a
two-tier roster shape. **Declaration, pre-action** — the safe quadrant (cheap, constraining), never
prose.

**Stage:** `examples/dungeon_master/supporting_cast.yaml` + `prompts/supporting_cast.yaml`. Given the
accepted synopsis **and the already-named main roster**, name the supporting characters the story
requires, each as `name | role | lifecycle` — e.g. `Reinmar | a Bärenschädel guide who leads the
survivors over the high country | introduced Ch3, lost in the flood`. Parse with the
`split_roster`-style line parser (names-only precedent, FR-475), extended to three pipe-delimited
fields. **No prose** — a role is one clause, not a paragraph.

**Two-tier roster shape (additive — `roster` semantics unchanged):**

```json
"characters": {
  "roster": ["hilde", "gunnar", "arnulf", "wenda"],          // main tier (unchanged)
  "supporting": ["reinmar", "eirik"],                         // NEW supporting tier
  "cards": {
    "reinmar": {"name": "Reinmar", "tier": "supporting",
                "role": "a Bärenschädel guide …", "lifecycle": "introduced Ch3, lost in the flood",
                "text": "", "reviewed": false}
  }
}
```

Supporting cards carry `tier: "supporting"` and the declared `role`/`lifecycle`; main-tier cards are
untouched (or gain `tier: "main"` for symmetry — Judge's choice). Supporting cards are **not**
drafted into full origin sheets by `character.yaml` (that is main-tier depth) — the one-line role is
their establishment.

**Roster reconciliation (the key contract):** the supporting tier feeds every roster-scoped
consumer:
- `_normalize_chapter_cast` ([doc_ops.py L60](examples/dungeon_master/api/doc_ops.py#L60)) resolves
  chapter cast names against **both tiers**, so a chapter naming `Reinmar` keeps him (today it drops
  him as an unknown name).
- The FR-538 seam-entrance witness reads the roster directly — **(C2, verified)** there is no
  `acting_in()` function; `seam_entrance_gap()` builds its roster from `chars.get("roster")` at
  [seam_entrance.py L154-159](examples/dungeon_master/api/seam_entrance.py#L154). Extend that roster
  construction to also read `chars.get("supporting")` so a supporting NPC acting unestablished becomes
  visible to the witness. (FR-545 allegiance ledger and FR-544 overlay are out of scope for v1 — name
  only the seam actually touched.)

**Sequencing (C1, verified):** on synopsis-accept, after `expand_roster`. Both expansions live in
**`session.accept()`'s `stage.name == "synopsis"` branch** ([session.py L287-293](examples/dungeon_master/api/session.py#L287)),
**not** in `weave()` and **not** in `scripts/generate.py` — `generate.py` reaches them through
`session.accept()`, so a **single insertion** after `expand_roster` in that branch covers both the API
and the script paths: `expand_roster` → **`expand_supporting_cast`**. (This is the slot FR-548's
`expand_codex` vacates per FR-550.)

## Acceptance Criteria

- [ ] **(deterministic RED, the gate)** committed separately, `SKIP=pytest`:
      `expand_supporting_cast` on a doc with an accepted main roster persists a `characters.supporting`
      list and one `tier: "supporting"` card per name with `role` and `lifecycle` populated; a
      duplicate of a main-tier name is **not** re-added to either tier (dedup across tiers); a
      malformed line (missing role/lifecycle fields) defaults the missing fields to `""` and is kept
      iff it has a name (boundary normalization, `the_one_law`).
- [ ] **(deterministic RED)** `_normalize_chapter_cast` resolves a supporting-tier name to its
      display name instead of dropping it as unknown — the regression that lets `Reinmar` survive a
      chapter cast list.
- [ ] **(deterministic RED)** the FR-538 seam-entrance witness includes supporting-tier names —
      extend the roster construction in `seam_entrance_gap()` ([seam_entrance.py L154-159](examples/dungeon_master/api/seam_entrance.py#L154))
      to read `chars.get("supporting")` in addition to `chars.get("roster")`, so a supporting NPC
      acting unestablished is now *visible* to the witness (closes the FR-538 documented out-of-scope
      gap). **(C2 — there is no `acting_in()` symbol; do not chase one.)**
- [ ] `supporting_cast.yaml` graph (`parse_json: false`, three-field line parser) + `supporting_cast`
      prompt; lints clean.
- [ ] `expand_supporting_cast(doc, story_dir)` sequenced on synopsis-accept after `expand_roster`
      **as a single insertion in `session.accept()`'s `stage.name == "synopsis"` branch** ([session.py L287-293](examples/dungeon_master/api/session.py#L287)).
      **(C1 — do NOT edit `scripts/generate.py`; it reaches this through `session.accept()`. The
      "and `scripts/generate.py`" / "`session.weave`" claims were false against live code.)**
- [ ] **(visibility evidence, NOT a blocking test)** `demo-output.log` records a fresh book where a
      previously-untracked NPC (e.g. a guide) now appears in `characters.supporting` and is caught by
      the seam-entrance witness if unestablished.
- [ ] Example-exempt: NO `@pytest.mark.req`, NO capability YAML; changelog fragment `type: feat`,
      `scope: examples`, no `req:`.
- [ ] Distill diary entry.
- [ ] **(C3 — hard gate, not advice)** New modules/prompts under the 450-line ceiling. `doc_ops.py`
      is already large — if the new boundary pushes it over 450, split the cast-expansion cluster into
      a `cast_ops` leaf (mirroring `turn_ops`/`chapter_ops`); do **not** inflate `doc_ops`.

## Alternatives Considered

- **Keep one flat roster, just let chapter cast names widen it**: rejected — silently widening the
  animated roster from prose is exactly the ad-hoc invention that produces unestablished NPCs; the
  tier must be *declared up front* so it has a lifecycle and the witnesses can scope it.
- **Draft supporting characters into full `character.yaml` origin sheets**: rejected for v1 — that is
  main-tier depth and bloats outline-time cost for characters who may appear in one chapter; the
  one-line role/lifecycle is sufficient establishment. Promotion to full sheets is a later FR if
  needed.
- **Mutable supporting tier (add members mid-play when a chapter names someone new)**: deferred —
  v1 derives the supporting cast once from the synopsis (like the main roster). Mid-play promotion of
  a newly-named NPC is a follow-up once the declared-tier mechanism is proven.
- **Fold supporting cast into the world bible (FR-552)**: rejected — `false_duplicate`. Cast is
  *characters with lifecycle* (coherence axis); the world bible is *factions/locations* (depth axis).
  Conflating them is what produced the FR-548 leak.

## Related

- `examples/dungeon_master/character_roster.yaml` + `api/doc_ops.py` `expand_roster` — the pattern to mirror
- `examples/dungeon_master/api/doc_ops.py` `_normalize_chapter_cast` (L60) — the cast resolver to extend to both tiers
- `examples/dungeon_master/api/session.py` — `weave` synopsis-accept branch (sequence point, L289)
- `examples/dungeon_master/api/seam_entrance.py` — FR-538 witness whose `acting_in` gains the supporting tier
- `feature-requests/FR-538-dm-v2-seam-entrance-arrival-scan-false-clear.md` — documented non-roster NPCs out of scope; this FR scopes them in
- `feature-requests/FR-550-dm-v2-rollback-world-codex.md` — vacates the synopsis-accept slot this stage fills
- `/memories/repo/seam-entrance-roster-vs-nonroster.md` — the roster-lens-misses-non-roster-NPC analysis
- Evidence: Arnulf/Eirik (10028), Arnulf (10030), Reinmar→Wenda (10034) — the recurring non-roster break class

## Judgement (2026-06-20) — APPROVE WITH CONDITIONS

**Verdict: APPROVE WITH CONDITIONS.** The idea is sound and attacks a verified recurring defect class;
two mechanism claims are false against live code and must be corrected in the spec before enforce
(`judge_as_junior_pr` — the same `false_duplicate`/`intent_drift` traps that condition-folded FR-548).

**Sound and confirmed:**
- The defect class is real and recurring (Arnulf/Eirik 10028, Arnulf 10030, Reinmar 10034). The
  10034-BC `story.json` confirms `roster == [hilde,gunnar,arnulf,wenda]` while Reinmar acts as a guide
  — a non-roster NPC the roster-scoped witnesses are structurally blind to.
- `_normalize_chapter_cast(doc, authored)` exists at `doc_ops.py` L60 and is the correct resolver to
  extend to both tiers (today it drops unknown names). Verified.
- The declared-pre-action-tier approach (cheap, constraining, never prose) is the safe quadrant and is
  the structural fix that makes the FR-548 leak impossible by construction. The `false_duplicate`
  rejection of "fold cast into the world bible" is correct: cast = lifecycle (coherence axis), bible =
  factions/locations (depth axis).

**Conditions (blocking — amend Proposed Solution + ACs before enforce):**
- **C1 (blocking) — the `scripts/generate.py` sequence point does not exist.** Verified: `generate.py`
  calls `session.weave()` + `session.accept()` (L59-85); it never calls `expand_roster`/`expand_codex`
  directly. Both expansions live in **`session.accept()`'s `stage.name == "synopsis"` branch**
  (L287-293), **not** in `weave()`. Correct the AC and Proposed Solution: sequence
  `expand_supporting_cast` in `session.accept()`'s synopsis branch immediately after `expand_roster` —
  a **single insertion** that covers both the API and `generate.py` paths (generate.py reaches it
  through `accept()`). Delete "and `scripts/generate.py`" and the "`session.weave`" attribution. This
  is the exact C4 false-duplicate trap from FR-548; do not repeat it.
- **C2 (blocking) — `acting_in(cid)` is a fictional symbol.** `seam_entrance.py` has no `acting_in`
  function (its functions are `_name_tokens`, `_contains_token_run`, `_name_has_arrival_signal`,
  `seam_entrance_gap`). The witness builds its roster from `chars.get("roster")` at L156 inside
  `seam_entrance_gap`. Name the real seam: extend the roster construction at
  `seam_entrance.py` L154-159 to also read `chars.get("supporting")`. The mechanism is sound; the
  named symbol is invented — fix the reference so the enforcer does not chase a function that is not
  there.
- **C3 — Module-size discipline is a condition, not advice.** `doc_ops.py` is already large. If the
  new boundary pushes it over 450, split the cast-expansion cluster into a `cast_ops` leaf (mirroring
  `turn_ops`/`chapter_ops`) — do **not** inflate `doc_ops`. The FR already states this; promote it to
  a hard gate.
- **C4 — Dedup-across-tiers is the load-bearing invariant; keep it as a deterministic RED.** A name
  already in the main roster must not be re-added to the supporting tier. This and the
  `_normalize_chapter_cast` two-tier resolution are the real gates (the demo-log NPC-appearance claim
  stays visibility-only, correctly).

**Ordering/dependency:** enforce after FR-550 (it fills the synopsis-accept slot FR-550 vacates).
With C1-C4 folded, no re-judge required. Status -> **Approved with conditions (fold C1-C4, then
authority to enforce).**
