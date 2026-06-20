# Feature Request: DM v2 Fact-Reversal Subject-Binding (Locative False Positive)

**Priority:** MEDIUM (witness false-positive; erodes trust in the fact_reversal number)
**Type:** Bug (fix-by-redesign)
**Status:** Enforced (RED 6c92e9b1 roster -> re-aimed RED 3278deb3 entities -> GREEN 5f004a25) -- live 10032-BC gap 1 -> 0
**Effort:** ~0.5 day
**Requested:** 2026-06-20

## Summary

The FR-542 `fact_reversal_gap` detector reports a **false positive** when two unrelated
resolved facts about **different subjects** share an incidental **locative/scene token**. In
10032-BC it flagged a "reversal" between *"Reinmar arrived at the flood zone by the salt road"*
(Ch4) and *"Arnulf is still missing in the flood zone and unconfirmed dead"* (Ch5) — two facts
about two different people that merely both mention **"flood zone."** The subject-token matcher
binds on *any* shared significant word, including the shared *place*, so a present-subject fact
and an absent-subject fact about distinct entities compose a phantom `present↔absent` reversal.

## Value Statement

The `fact_reversal` witness stops crying wolf on coincidental scene/location overlap, so its
`gap_count` reflects only genuine same-fact reversals — and a clean book (10032-BC: reviewer
0 breaks, 5/5) reads `gap_count == 0` on this rail instead of a spurious 1.

## Problem

`_antonym_reversals` ([fact_reversal.py](examples/dungeon_master/api/fact_reversal.py)) requires
the prior and later lines to *share at least one subject token*, intending "same subject ⇒ real
reversal." But `_subject_tokens` returns **every** word ≥4 chars that is not a stopword or
antonym token — which includes **locative and scene nouns** (`flood`, `zone`, `ledge`, `river`,
`ridge`, `valley`). Two facts set in the same place therefore "share a subject" even when their
*actual* subjects (the entities the fact is about) differ.

The 10032-BC collision, exactly:

- Prior (Ch4 resolved): `"Reinmar arrived at the flood zone by the salt road."` → asserts
  `arrived` (pair 1 `present`, side 0). Subject tokens include `reinmar, flood, zone, salt, road`.
- Later (Ch5): `"Arnulf is still missing in the flood zone and unconfirmed dead."` → asserts
  `missing` (pair 1 `absent`, side 1). Subject tokens include `arnulf, flood, zone, unconfirmed, dead`.
- Shared subject tokens: `{flood, zone}` → non-empty → **gap fired**, `subject="flood"`.

The true subjects — **Reinmar** vs **Arnulf** — are *different*, so there is no reversal. The LLM
reviewer, reading prose, correctly reported **0 continuity breaks** on this book. This is the
mirror image of the FR-543 seam-entrance defect: there a semantically-inverted token caused a
false *negative*; here a semantically-irrelevant (locative) token causes a false *positive*.
Both are `gate_checks_shape_not_substance` — the matcher checks token overlap, not whether the
two lines are *about the same thing*.

A genuine reversal that this fix must still catch (the 10029-BC motivating case, FR-542): a
*food bundle* `secured` in Ch3 then `unclaimed` in Ch4 — both lines share the real subject
`bundle`/`food`, and that is an *object/possession* subject, not a location. The fix must
distinguish "shared **entity/object** subject" (real) from "shared **place** subject" (spurious).

## Proposed Solution (re-planned per Judgement)

The invariant: *two lines describe the same fact only if they are about the same entity.* A shared
*place* token (`flood`, `zone`) does not make two facts about different people the same fact. The
judged mechanism is a single **negative guard** — premise-independent, never strips a subject, and
cannot blind the detector to reversals about places:

> **Suppress a fact-reversal when the prior line and the later line each name a roster character
> and they name DIFFERENT roster characters.**

This kills the verified 10032-BC case (`Reinmar` ≠ `Arnulf`) without any scene vocabulary; it
preserves the genuine bundle case (neither line names a *different* roster member — the subject is
the object `bundle`/`food`); and it preserves the `ford` `closed↔reopened` reversal (neither line
names a roster character at all → no suppression).

**Rejected from the original plan (do not implement):**

- **Tactic 1 `_LOCATIVE_STOPWORDS`** — premise-fragile (scene nouns are open-ended and tuned to
  the floodmark-saga; useless on a desert/city/starship premise) AND it re-introduces an
  FR-543-style false *negative*: the `closed/sealed ↔ reopened/unsealed` antonym pair is
  *inherently about places*, so stripping `ford`/`road` empties `_subject_tokens` and silently
  drops the real `"The ford was sealed" → "The ford was reopened"` reversal. No place-noun
  stopword set is added.

**Plumbing (the original plan omitted this).** `fact_reversal_gap(prev_card, card)` cannot see the
roster — it takes only the two cards. Thread the roster as an optional, defaulted parameter:

- `fact_reversal_gap(prev_card, card, roster: set[str] | None = None)` — `roster` defaults to
  empty/`None`, so an empty roster ⇒ no suppression ⇒ today's behavior (the four existing
  `fact_reversal_gap(prev, card)` unit tests stay green unchanged).
- Inside `_antonym_reversals`, after the shared-subject check, build the per-line named-character
  sets (intersection of the line's lowercased tokens with `roster`); if both lines name ≥1 roster
  character and the two sets are **disjoint**, suppress that reversal.
- `fact_reversal_summary(story_doc)` builds the roster name set from
  `story_doc["characters"]["roster"]` → `story_doc["characters"]["cards"][id]["name"]` (mirroring
  `allegiance_ledger._roster_name_set`, normalized via the same `_norm_token` discipline) and
  passes it into each `fact_reversal_gap` call.

Keep the frozen antonym set, the leaf-module boundary, and the visibility-not-gate posture
untouched. A residual where two un-rostered place facts collide escalates to the deferred Phase-2
LLM tier (`regex_fourth_exclusion` discipline) — never widen heuristics indefinitely.

## Acceptance Criteria

- [ ] RED test (committed separately, `SKIP=pytest`) reproducing the 10032-BC collision: prior
      `"Reinmar arrived at the flood zone by the salt road."` + later `"Arnulf is still missing
      in the flood zone and unconfirmed dead."`, with `roster={reinmar, arnulf, …}` →
      `gap_count == 0` (currently 1).
- [ ] **Ford guard** (standing guard against the rejected Tactic 1): prior `"The ford was sealed"`
      → later `"The ford was reopened"` (no roster characters named) **stays** `gap_count == 1`.
      This is the false-negative Tactic 1 would have caused, now a permanent regression test.
- [ ] **Same-entity reversal is NOT suppressed**: prior and later both name the *same* roster
      character on opposite antonym sides (e.g. `"Arnulf arrived at the ridge"` →
      `"Arnulf is missing"`) with that character in `roster` → `gap_count == 1` (a same-entity
      reversal is still a reversal; suppression must require *distinct* named entities).
- [ ] Regression: the FR-542 genuine bundle case (`secured` Ch3 → `unclaimed` Ch4, object subject,
      no distinct roster characters) still fires `gap_count == 1`.
- [ ] **(C1) Multi-token name RED**: a roster character whose name is two tokens (e.g.
      `"Old Reinmar"`) is still recognized as named — a line is deemed to *name* character `C` iff
      **any** name-token of `C` with length ≥ 4 appears in the line's lowercased token set; the
      roster is passed as a set of per-character token-sets (or a `name_token → char_id` map), not
      full-name strings. RED: `"Old Reinmar arrived…"` vs `"Arnulf is missing…"` → suppressed → 0.
- [ ] **(C2)** Roster name-tokens are lowercased and tokenized through the same `[a-z0-9]+`
      grammar the line matcher uses (`_TOKEN_RE`), so names carrying punctuation/casing match.
- [ ] **(C3)** The roster token structure is built in `fact_reversal_summary` and passed in;
      `fact_reversal.py` stays a leaf (imports only `re`) — no import of the private
      `allegiance_ledger._roster_name_set` into the leaf.
- [ ] `fact_reversal_gap` gains an optional `roster` parameter defaulting to empty/`None`;
      empty roster ⇒ identical behavior to today.
- [ ] `fact_reversal_summary` builds the roster token structure from
      `story_doc["characters"]["roster"]` → `["cards"][id]["name"]` and threads it down.
- [ ] All existing FR-542 `test_fact_reversal_gap.py` tests (which call with two args) stay green.
- [ ] 10032-BC witness re-run reports `fact_reversal.gap_count == 0`; prior clean cases unchanged.
- [ ] `fact_reversal.py` stays a leaf and under the 450-line ceiling.
- [ ] Changelog fragment (`type: fix`, `scope: examples`, no `req:` — example-exempt).
- [ ] Distill diary entry (`place_is_not_subject` seed).

## Alternatives Considered

- **Tactic 1 `_LOCATIVE_STOPWORDS` (the original primary fix)**: rejected by Judgement —
  premise-fragile and re-introduces an FR-543 false-negative on the inherently-locative
  `closed↔reopened` antonym pair (the `ford` reversal). See Proposed Solution and Judgement.
- **Require subject tokens to be roster/object names only** (positive requirement): too strict —
  it would miss legitimate reversals about un-rostered nouns (a *gate*, a *route*, a *ford*). The
  chosen rule is a *negative* guard (suppress on entity-disagreement), which leaves un-rostered
  subjects untouched.
- **Drop the shared-subject requirement entirely and match only on antonym sides**: rejected —
  that maximizes false positives (any present fact + any absent fact anywhere reverses).
- **LLM-judged same-fact identity**: the deferred Phase-2 tier; overkill for a collision the
  deterministic roster-disagreement guard resolves cheaply.

## Related

- `examples/dungeon_master/api/fact_reversal.py` — `_subject_tokens`, `_antonym_reversals`, `_SUBJECT_STOPWORDS`
- `feature-requests/FR-542-dm-v2-seam-fact-reversal-gate.md` (the detector this corrects)
- `feature-requests/FR-543-dm-v2-seam-entrance-arrival-scan-false-clear.md` (mirror defect: token false-negative)
- Evidence: `outputs/dungeon-master/10032-BC/continuity_witness.json` (the spurious gap), `review.md` (0 breaks)
- Memory: `/memories/repo/seam-entrance-roster-vs-nonroster.md`

## Judgement (2026-06-20) — Pain APPROVED; mechanism REJECTED as specified, return to Plan

**The pain is real and verified against the cited run.** I confirmed
`10032-BC/continuity_witness.json` directly: `fact_reversal.gap_count == 1`, the single gap is
`subject: "flood"` binding `"Reinmar arrived at the flood zone by the salt road."` against
`"Arnulf is still missing in the flood zone and unconfirmed dead."`, while the reviewer scored
`5/5` with `break_count: 0`. The mechanism is exactly as described: `_subject_tokens`
([fact_reversal.py](examples/dungeon_master/api/fact_reversal.py) L88) keeps every ≥4-char
non-stopword/non-antonym token, so the *place* `flood`/`zone` binds two facts about **different
people**. This is a genuine `gate_checks_shape_not_substance` false positive worth fixing.

**But the primary proposed fix — Tactic 1, `_LOCATIVE_STOPWORDS` — is the wrong mechanism, and
it introduces a false NEGATIVE in the same family FR-543 just repaired.** Two disqualifying
findings:

1. **It guts the `closed↔reopened` antonym pair, whose subjects ARE locatives.** That third
   frozen pair (`closed/sealed ↔ reopened/unsealed`) is *semantically about passages and places*
   — fords, roads, gates, banks. The existing FR-542 regression test
   `test_forbidden_regression_violation_is_flagged` is literally a **ford** going
   `closed → reopened`, and the FR's own proposed locative set lists `ford`, `road`, `bank`. A
   minimal genuine reversal — `"The ford was sealed"` → `"The ford was reopened"` — shares only
   the subject `ford`; strip it as locative and `_subject_tokens` is empty on both sides → the
   **real** reversal is silently missed. That is the precise FR-543 false-clear defect
   (a semantically-load-bearing token discarded), re-introduced on the fact-reversal rail. The
   existing test survives today only incidentally, because its card also happens to contain the
   word `clan`. The fix must not make a detector blind to reversals about places.

2. **The locative vocabulary is premise-fragile and unbounded.** `{flood, zone, ledge, river,
   ridge, valley, slope, water, road, crest, ford, bank, …}` is tuned to the floodmark-saga
   premise. A desert, a city, or a starship premise has an entirely different scene vocabulary,
   none of it in the set. Unlike the antonym set — closed because antonymy is *universal* — place
   nouns are open-ended and story-specific, so this set is whack-a-mole that silently rots on the
   next premise. It fails the closed-set posture it claims to honor.

**The correct fix is Tactic 2, reframed from "optional requirement" to the SOLE mechanism, and
phrased as a suppression, not a requirement.** The real invariant: *two facts are the same fact
only if they are about the same entity.* The premise-independent, precisely-targeted rule is:

> **Suppress a reversal when the prior and later lines each name a roster character and they name
> DIFFERENT roster characters.**

This kills the verified case (`Reinmar ≠ Arnulf`) without any place vocabulary; it preserves the
genuine bundle case (neither line names a *different* roster character — the subject is the object
`bundle`/`food`); it preserves the ford case (neither line names a roster character at all → no
suppression); and it cannot cause the false negatives Tactic 1 does, because it never strips a
subject — it only vetoes a match when two *named, distinct* entities are present. Note the
phrasing is deliberately a **negative guard** (suppress on entity-disagreement), not the FR's
alternative "require subject ∈ entities" (which the FR itself correctly rejects as too strict,
since legitimate subjects like a *gate* or *route* are un-rostered).

**Plumbing condition (the plan omits it):** `fact_reversal_gap(prev_card, card)` cannot see the
roster — it takes only the two cards (L169), and the sole production caller `fact_reversal_summary`
holds the `story_doc` but does not pass the roster down. The redesign must thread the roster:
`fact_reversal_gap(prev_card, card, roster=...)` with `roster` defaulting to empty so the four
existing `fact_reversal_gap(prev, card)` unit tests keep passing unchanged (empty roster ⇒ no
suppression ⇒ today's behavior), and `fact_reversal_summary` passing
`story_doc["characters"]["roster"]` + name cards through. State this in the ACs.

**Required changes before enforce:**
- Drop Tactic 1 (`_LOCATIVE_STOPWORDS`) entirely. Do not add a place-noun stopword set.
- Make the roster-entity-disagreement **suppression** the sole mechanism.
- Thread the roster into `fact_reversal_gap` (defaulted) and through `fact_reversal_summary`.
- ACs: keep the 10032-BC RED (`gap_count: 1 → 0`) and the bundle regression (`stays 1`); **add** a
  RED guarding the locative antonym pair — `"The ford was sealed"` → `"The ford was reopened"`
  must **stay** `gap_count == 1` (the false-negative Tactic 1 would have caused, now a standing
  guard); add a case where the *same* roster character appears on both sides (present→absent about
  one person) and is **not** suppressed (a same-entity reversal is still a reversal).
- Update Type to reflect a bug-fix-by-redesign; Effort holds ~0.5d.

**Verdict.** The defect is real and worth fixing; the locative-stopword mechanism is rejected
because it is premise-fragile and re-introduces the FR-543 false-clear on the inherently-locative
`closed↔reopened` pair. Return to Plan: rebuild around roster-entity-disagreement suppression with
the roster threaded into the detector, and add the ford-reversal guard test. Keep the frozen
antonym set and the visibility-not-gate posture untouched.

**Diary seed:** `place_is_not_subject` — a scene/location token names *where* a fact holds, not
*what* it is about; binding fact-identity on shared place is the locative twin of FR-543's
borrowed-edge token. The cure is to anchor identity on the named entity (and veto on
entity-disagreement), never to enumerate the open-ended vocabulary of places.

## Judgement v2 (2026-06-20) — APPROVED with conditions; freeze scope

The re-plan adopts the judged mechanism faithfully. I traced the single negative guard
(*suppress when both lines name distinct roster characters*) against the live
`_antonym_reversals` ([fact_reversal.py](examples/dungeon_master/api/fact_reversal.py) L100) and
all four discriminating cases resolve correctly:

| Case | prior named-set | later named-set | guard | result |
|------|-----------------|-----------------|-------|--------|
| 10032-BC (`Reinmar`/`Arnulf`, shared `flood/zone`) | `{reinmar}` | `{arnulf}` | both named, disjoint → suppress | `1 → 0` ✓ |
| Ford `sealed`→`reopened` (no chars) | `{}` | `{}` | neither named → keep | stays `1` ✓ |
| Same-entity `Arnulf arrived`→`Arnulf missing` | `{arnulf}` | `{arnulf}` | intersect non-empty → keep | stays `1` ✓ |
| Bundle `secured`→`unclaimed` (object subject) | `{}` | `{}` | neither named → keep | stays `1` ✓ |

The guard is premise-independent, never strips a subject (so it cannot cause the FR-543-class
false negative the rejected Tactic 1 would have), and the defaulted `roster` keeps the four
existing 2-arg `fact_reversal_gap` unit tests green. The plumbing source is verified correct:
`story_doc["characters"]["roster"]` → `["cards"][id]["name"]` is exactly what the FR-545 sibling
`allegiance_ledger._roster_name_set` reads.

**One gap to close before enforce (conditions):**

- **(C1) Define "names a roster character" for multi-token names.** `_roster_name_set` returns
  `_norm_token(name)` — a *possibly multi-word string* (`"old reinmar"`), whereas a ledger line is
  tokenized into single words by `_TOKEN_RE`. A naive `line_tokens & roster_name_set` intersection
  silently fails on any multi-word name → the guard would never suppress and the 10032-BC RED
  would not go green for such rosters. Specify the match explicitly: a line **names** character `C`
  iff **any** name-token of `C` (length ≥ 4, to avoid matching connectives like *the*/*of* inside
  a name) appears in the line's lowercased token set. Build the roster as a *set of token-sets*
  (or a flat `name_token → char_id` map), not a set of full-name strings, and match per character.
  Add a RED with a two-token roster name (e.g. `"Old Reinmar"`) proving the suppression still fires.

- **(C2) Normalize the roster tokens the same way the line is tokenized.** Lines are matched via
  `_TOKEN_RE.findall(line.lower())`; the roster name-tokens passed into `fact_reversal_gap` must be
  lowercased and run through the same `[a-z0-9]+` tokenization so a name like `"Reinmar-the-Elder"`
  or one carrying punctuation matches. State the normalization in the AC, mirroring the
  `_norm_token` discipline but reduced to the per-token grain the matcher needs.

- **(C3) Keep the roster-set construction out of the leaf.** `fact_reversal.py` imports only `re`
  and must stay a leaf. Build the roster token structure in `fact_reversal_summary`
  (emit_continuity_witness.py, which already imports the sibling modules) and pass the prepared
  structure into `fact_reversal_gap`. Do **not** import `allegiance_ledger._roster_name_set`
  (a private cross-module symbol) into the leaf — if a shared helper is wanted, that is a separate
  refactor FR, out of scope here.

**Scope frozen** to: the optional `roster` parameter on `fact_reversal_gap`, the disjoint-named-set
suppression inside `_antonym_reversals`, the roster construction + threading in
`fact_reversal_summary`, and the four/five RED+regression tests named in the ACs (10032-BC,
ford-guard, same-entity, bundle, multi-token-name). No locative stopword set. No entity/object
tracking beyond the roster. Residual non-roster locative collisions remain Phase-2 (deferred).

**Verdict: APPROVED — authority granted to enforce** once C1–C3 are folded into the ACs. Write the
RED first (`SKIP=pytest`), then the GREEN with the changelog fragment and the `place_is_not_subject`
diary entry.

## Enforcement Deviation (2026-06-20) — BLOCKED: the roster-disagreement premise is false on the real run

Enforcement proceeded RED → GREEN cleanly at the **unit** level: RED committed (`6c92e9b1`,
`SKIP=pytest`) with the five discriminating tests; the leaf gained an optional `roster`
(name_token → char_id) parameter and the disjoint-named-set veto in `_antonym_reversals`;
`fact_reversal_summary` builds the roster token map from `story_doc["characters"]["roster"]` →
`["cards"][id]["name"]` via the new leaf helper `name_tokens`. **All 12 `test_fact_reversal_gap.py`
tests pass; all 17 witness + allegiance sibling tests pass.**

**But the live-witness AC FAILS.** Re-emitting `10032-BC` still reports
`fact_reversal.gap_count == 1` on the *exact* gap the fix targets. Root cause, measured directly
from `outputs/dungeon-master/10032-BC/story.json`:

- `characters.roster == ["hilde", "gunnar", "reinmar", "alva"]`, and `characters.reviewed == False`.
- **`Arnulf` is NOT in the roster** — yet the string `Arnulf` appears **434 times** in the doc.
  He is a major off-roster (antagonist/offscreen) character.

So the verified collision — `"Reinmar arrived at the flood zone…"` vs
`"Arnulf is still missing in the flood zone…"` — has `prior_chars == {reinmar}` but
`later_chars == {}` (Arnulf unrostered). The veto requires **both** sides to name a roster
character, so it does not fire, and the false positive stands. **The Judgement-v2 table line
"`{reinmar}` / `{arnulf}` → disjoint → suppress" was wrong: it assumed Arnulf is rostered. He is
not.** This is the same class as the FR-545 baseline=0 catch — a plan premise falsified only by
measuring the live artifact.

**Why I did not force it green.** Two dishonest paths were available and rejected: (a) editing a
test fixture to make Arnulf rostered would make the suite lie about the live behavior
(`plausible_wrong_answer`); (b) silently swapping to a proper-noun mechanism the Judge never
evaluated would violate the frozen scope. The unit code is correct and retained on `main`
(`6c92e9b1` RED is committed; GREEN code is staged-but-uncommitted), but the FR cannot close.

**Proposed re-plan (for the next Judge pass).** Keep the judged *invariant* — "two facts about
different named entities are not the same fact" — but fix the **entity source**, which the roster
under-covers. Candidate: derive the named-entity set per line from **capitalized proper-noun
tokens** (case-preserving, dropping a sentence-initial token only when it is a known function word
like *The/A/After/Still*), **unioned with** the roster. Then `{Reinmar}` vs `{Arnulf}` are disjoint
proper nouns → suppressed, with no dependence on roster completeness; the ford/bundle cases stay
`{}` (their lead token is a dropped function word) → still flagged; same-entity stays non-disjoint.
This is premise-independent (proper-noun capitalization is a property of English prose, not of the
floodmark vocabulary) but introduces a new boundary risk — a capitalized sentence-initial *common*
noun (e.g. `"Floodwater rose"`) misread as a proper noun — which must be condemned by an added RED
before it is trusted. Alternatively, defer to the Phase-2 LLM same-fact-identity tier.

**Status:** returned to Judge. Do not close. The RED commit stands as the standing condemnation.

## Re-plan v2 (2026-06-20) — corpus proper-noun entity source supersedes roster-only

The invariant is unchanged (*two facts about different named entities are not the same fact*); the
**entity source** is replaced. The roster is incomplete (it omits major off-page characters like
Arnulf and Aschenwulf), so the entity set is derived from the prose itself:

**Proper-noun lexicon `L` (built once per doc):** a token is a proper noun iff it appears
**capitalized in a non-sentence-initial position at least twice** across the committed chapter
prose (`chapters.cards[*].text`), with length ≥ 4 and lowercased; **unioned** with the roster
name-tokens (belt-and-suspenders for a rostered member rarely in prose). Sentence boundaries split
on `[.!?]+`. This is premise-independent: capitalization-mid-sentence is a property of English
prose, not of the floodmark vocabulary.

**Per-line named entities:** `named(line) = _subject_tokens(line) ∩ L` — reusing `_subject_tokens`
(which already strips `_SUBJECT_STOPWORDS`, antonym tokens, and < 4-char tokens) so function words
like *this* never enter.

**Suppression (unchanged shape):** suppress a reversal when `named(prior)` and `named(later)` are
both non-empty and **disjoint**.

### Measured evidence (10032-BC, the cited run)

The prose lexicon (cap mid-sentence, ≥ 4 chars) is
`{gunnar:63, hilde:29, alva:29, arnulf:20, reinmar:19, aschenwulf:7, keep:3, this:2, mark:1, here:1}`:

- **All six named characters are present — including off-roster `arnulf` (20×) and `aschenwulf`
  (7×).** The roster-blindness that blocked v2 is gone, with no dependence on roster completeness.
- **No locative poisons the lexicon:** `flood, zone, ford, road, ledge, bundle, water, salt` are
  all absent (they are never capitalized mid-sentence), so `{reinmar}` vs `{arnulf}` stays
  disjoint and the suppression fires. *(This was the catastrophic risk — had `Flood` been a
  capitalized event-name in prose, both lines would share `{flood}` and the fix would silently
  fail. Verified empirically absent.)*
- **Residuals** `keep/this/mark/here` are dialogue-capitalized common words: the ≥ 2 frequency
  threshold drops `mark`/`here`; `_SUBJECT_STOPWORDS` drops `this`; `keep` (3×) is the bounded
  residual — a rare residual that escalates to the deferred Phase-2 LLM tier, consistent with the
  visibility-not-gate posture (a rare over-suppression of one reversal never gates the run).

### Revised Acceptance Criteria (supersede the roster-only ACs above)

- [ ] **Signature:** generalize the leaf parameter from `roster: dict` to `entities: set[str] |
      None`, defaulting `None` ⇒ no suppression ⇒ today's two-argument behavior (the four existing
      FR-542 `fact_reversal_gap(prev, card)` unit tests stay green). The session's committed RED
      tests (which pass `roster=<dict>`) are rewritten to pass `entities=<set>`.
- [ ] **Off-roster RED (the live failure):** prior `"Reinmar arrived at the flood zone by the salt
      road."` + later `"Arnulf is still missing in the flood zone and unconfirmed dead."` with
      `entities={reinmar, arnulf, …}` (Arnulf present though **not** rostered) → `gap_count == 0`.
- [ ] **Lexicon-builder unit:** a helper in `fact_reversal_summary`'s module builds `L` from
      `chapters.cards[*].text` (cap-mid-sentence ≥ 2, len ≥ 4) ∪ roster tokens; a RED asserts a
      locative that is lowercase in prose (`flood`) is **absent** from `L` and a character cap'd
      mid-sentence (`arnulf`) is **present**.
- [ ] **Common-noun-risk RED (the new boundary):** a line led by a capitalized common noun absent
      from `L` (e.g. `"Floodwater secured the ledge"`) must **not** treat `floodwater` as an
      entity → a genuine reversal about it is **not** suppressed (`gap_count` stays `1`).
- [ ] **Ford guard:** `"The ford was sealed"` → `"The ford was reopened"` (no entity in either
      line) **stays** `gap_count == 1`.
- [ ] **Same-entity reversal:** `"Arnulf arrived…"` → `"Arnulf is missing…"` (same entity both
      sides) **stays** `gap_count == 1`.
- [ ] **Bundle regression:** FR-542 `secured` Ch3 → `unclaimed` Ch4 (object subject, no entity)
      **stays** `gap_count == 1`.
- [ ] `fact_reversal_summary` threads `L` into each `fact_reversal_gap` call.
- [ ] **End-to-end:** re-emitting the 10032-BC witness reports `fact_reversal.gap_count == 0`
      (the AC that failed under v2), proven by a committed synthetic story-doc fixture (outputs/
      is gitignored) plus a manual witness re-run noted in the Implementation section.
- [ ] `fact_reversal.py` stays a leaf (imports only `re`) under the 450-line ceiling; the lexicon
      builder lives in `emit_continuity_witness.py`, not the leaf.
- [ ] Changelog fragment (`type: fix`, `scope: examples`, no `req:` — example-exempt) + diary.

## Judgement v3 (2026-06-20) — APPROVED; authority to re-enforce

The v2 block was a true premise failure (roster ≠ cast), caught only by measuring the live
artifact — the third recurrence of the off-roster-Arnulf class (FR-538 twice, now here). The v2
fix is rejected as insufficient. The corpus proper-noun entity source is **APPROVED**, on three
verified grounds:

1. **It closes the live AC.** Arnulf and Aschenwulf are in the prose lexicon though absent from the
   roster, so the disjoint-entity veto fires on the exact 10032-BC gap → `1 → 0`. No dependence on
   roster completeness.
2. **The catastrophic poisoning risk is empirically absent.** I checked directly: no locative
   (`flood/zone/ford/road/ledge/bundle/water/salt`) is capitalized mid-sentence in the prose, so
   the lexicon cannot collapse the discriminator. This is the one failure mode that would have
   silently re-broken the fix, and it is verified, not assumed.
3. **The new false-positive-name boundary is bounded and condemned.** Dialogue-capitalized common
   words (`keep/mark/here/this`) are the residual; the ≥ 2 threshold + `_SUBJECT_STOPWORDS` reuse
   contain them, and the **common-noun-risk RED** makes the boundary a standing test rather than a
   hope. The irreducible residual (a frequent dialogue word capitalized ≥ 2×) escalates to
   Phase-2 — acceptable under the visibility-not-gate posture, since the worst case is a rare
   *missed* reversal in a measurement-only witness, never a gated run.

**Conditions:**
- (D1) The lexicon threshold is **≥ 2** mid-sentence capitalizations; state it as a named constant
  with a comment citing the `keep/mark/here` residual, so the trade-off is legible and tunable.
- (D2) Reuse `_subject_tokens` for `named(line)` — do **not** add a parallel tokenizer; the entity
  match must inherit the same stopword/antonym/length discipline the subject match already uses.
- (D3) Keep the leaf pure: the lexicon builder reads `chapters.cards[*].text` in
  `emit_continuity_witness.py`; `fact_reversal.py` receives only the finished `entities` set.
- (D4) The end-to-end AC is pinned by a **committed synthetic fixture** whose prose contains the
  off-roster name capitalized mid-sentence (outputs/ is gitignored — the baseline must not depend
  on a real output file).

**Scope frozen** to: the `entities: set[str]` parameter, the corpus lexicon builder (cap-mid ≥ 2 ∪
roster), the disjoint-entity suppression, the threading, and the RED+regression suite named in the
revised ACs. No locative stopword set. No NLP POS tagger. Residual frequent-dialogue-word
collisions remain Phase-2.

**Verdict: APPROVED — re-enforce.** The session's RED (`6c92e9b1`) is amended to the
`entities`-set shape (still a RED commit, `SKIP=pytest`), then GREEN with the lexicon builder,
changelog fragment, and the `place_is_not_subject` diary entry. The uncommitted roster-dict GREEN
code in the working tree is superseded — replace it, do not commit it as-is.

## Implementation (2026-06-20) — Enforced

- **RED** `3278deb3` (`SKIP=pytest`) re-aimed the condemnation from the superseded roster-dict
  shape (`6c92e9b1`) to the judged `entities`-set mechanism: off-roster collision, ford guard,
  same-entity, capitalized-common-noun boundary, lexicon-builder, and an end-to-end off-roster
  fixture. Verified RED against HEAD production (ImportError on `_proper_noun_entities` +
  `entities=` kwarg absent).
- **GREEN** replaced the roster-dict working-tree code (never committed, per the deviation):
  `fact_reversal.py` — `fact_reversal_gap(prev, card, entities: set[str] | None = None)`;
  `_named_entities(line, entities) = _subject_tokens(line) & entities` (D2 reuse, no parallel
  tokenizer); `_antonym_reversals` vetoes a reversal when both lines' entity sets are non-empty and
  disjoint. `emit_continuity_witness.py` — `_proper_noun_entities(story_doc)` builds the lexicon
  from `chapters.cards[*].text` (cap non-sentence-initial ≥ `_PROPER_NOUN_MIN_CAPS == 2`, len ≥ 4)
  ∪ roster name-tokens (D1 named constant, D3 builder outside the leaf); `fact_reversal_summary`
  threads it.
- **Acceptance:** all ACs met. Unit `test_fact_reversal_gap.py` 14/14; siblings
  `test_emit_continuity_witness.py` + `test_allegiance_ledger.py` 17/17. Live re-run of the cited
  book reports `fact_reversal.gap_count == 0` (the v2-failing AC), pinned in-suite by the committed
  synthetic fixture `test_summary_suppresses_offroster_locative_collision` (outputs/ is gitignored).
  `fact_reversal.py` 243 lines / `emit_continuity_witness.py` 295 lines — both under the 450 ceiling.
- **Distill:** changelog `changelog/unreleased/fr547-fact-reversal-entity-disagreement.md`; diary
  `docs/diary/diary-2026-06-20-the-roster-is-not-the-cast.md` (heuristic `roster_is_not_cast`;
  green-fixtures-cannot-falsify-the-plan-they-encode). Repo memory
  `seam-entrance-roster-vs-nonroster.md` updated with the third recurrence.
- **Deviation from D-conditions:** none material. The diary seed graduated from
  `place_is_not_subject` to `roster_is_not_cast` — the place-token symptom was real, but the deeper
  boundary the enforcement exposed is that the *roster under-covers the named cast*; the entity
  source, not a locative exclusion, is the cure.
