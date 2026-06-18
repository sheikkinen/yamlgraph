# Feature Request: FR-524 — DM v2: Synopsis/Summary Re-Weave at Chapter Close (Close the Outer Continuity Loop)

**Priority:** MEDIUM
**Type:** Bug (continuity defect, plan-vs-played drift authored at planning time)
**Status:** **SENT BACK TO PLAN (2026-06-18)** — Judgement REJECTED the framing: the
condemning `10024-BC` evidence is **misattributed**. It does not demonstrate
state-blind *future-summary* drift; it demonstrates an **in-chapter beat-coverage
gap** under the FR-501 16-turn cap (Ch3 played 16/16 turns, was force-closed having
realized only beat 1 of 5; `close_chapter` then *faithfully* recorded the partial
state). The real defect lives one boundary **upstream** of this FR. See Judgement
below. Do not enforce as drafted. A deterministic `beat_coverage_gap` witness must
condemn the real bug first (the FR-522→FR-523 rhythm).
**Effort:** ~1–2 days
**Requested:** 2026-06-18
**Depends on:** FR-523 (state-aware beat re-outline — the *inner* loop this completes)

## Judgement (2026-06-18) — SENT BACK TO PLAN

Examined against live code and the real `10024-BC` artifact (not just the reviewer's
prose). The draft is internally coherent and the "outer loop" intuition is plausible,
but the **condemning evidence does not prove the bug the FR proposes to fix**. A Judge
must not freeze scope on misattributed evidence (`symptom_patch`, `investigation_
before_fix`). Findings:

- **J1 — JQ2 resolves in the FR's favor, but it is moot.** The beat prompt
  (`prompts/chapter_reoutline.yaml`) does receive `prior_seam_packet` (with
  `open_threads`) yet is contractually pinned to the summary: *"Cover exactly the
  events the summary describes — no fewer, no more, nothing invented beyond it."* So a
  stronger FR-523 beat prompt genuinely cannot carry a thread the summary omits. That
  confirms the summary *would* be binding **if** the bug were future-summary drift.
  It is not (J2).

- **J2 — The condemning evidence indicts a different boundary.** Tracing the actual
  `10024-BC` data, not the reviewer's prose:
  - Ch3 `summary`/`beats` promise a 5-event arc: Arnulf swept away → grief → **returns
    alive** → **blames Gunnar / demands blood** → Hilde refuses.
  - Ch3 **played 16 turns** (`CHAPTER_TURN_CAP = 16`, FR-501) — a single continuous
    ledge scene that realizes only **beat 1** (T16: "Arnulf loses his footing… torn
    away downstream"). Beats 4–5 (return, feud) **never play**. The cap force-closes.
  - `close_chapter` then **faithfully** commits `Arnulf status='dead', location=
    'downstream'` and `open_threads` with **no** Arnulf-feud entry — correct for what
    *played*, contradicting what the chapter *promised*.
  - Ch4 (and its state-blind summary) correctly continue from "Arnulf dead." The
    reviewer's "Ch3 ends with Arnulf returned… Ch4 ignores it" is the gap between the
    chapter's **stated intent (summary/beats in story.md)** and its **16-turn play** —
    an *in-chapter plan-vs-play coverage* gap, **not** a cross-chapter summary drift.

- **J3 — FR-524's mechanism would not fix the cited symptom.** Re-weaving Ch4's
  summary reads the committed `played_memory`, in which Arnulf is *correctly* dead and
  the feud thread *correctly* absent (it never played). The re-weave would keep Arnulf
  gone — matching the ledger, still contradicting Ch3's over-promising summary. The FR
  treats a downstream symptom of an upstream coverage defect (`downstream_fix`).

- **J4 — The real defect (named, for the next Plan).** A chapter whose `summary`/
  `beats` enumerate more plot — especially a *reversal* (death **and** resurrection)
  than its 16-turn budget can play; the cap force-closes after the first beat; the
  unplayed beats become **phantom promises** in `story.md` that later chapters
  correctly ignore. Candidate boundaries (a **Plan** decision, not a Judge ruling):
  (a) the outliner must not pack an un-playable multi-reversal arc into one capped
  chapter (split death and return across chapters); (b) `close_chapter` must **detect
  and flag/reconcile** beats the play did not fulfill (committed `world_state`
  contradicts an enumerated beat — Arnulf `dead` vs beat "reappears alive"); (c) the
  turn budget must be beat-coverage-aware, not a flat 16.

- **J5 — Investigate before fixing (the FR-522 rhythm).** Per `investigation_before_
  fix`, the genuine "outer loop" gap (state-blind unplayed summaries) **may** still be
  real, but it is **unproven** by current evidence. The mandated next step is a
  deterministic witness, committed RED, that condemns the *actual* coverage bug:
  `witness_metrics.beat_coverage_gap(doc, cid)` — flag each enumerated beat of a closed
  chapter that no played recap realized, and/or each committed `world_state` lifecycle
  that contradicts that chapter's own later beats. Run it across the corpus
  (`scan_seam_gaps.py` sibling). Only once the witness fires deterministically on
  `10024-BC` Ch3 does a *fix* FR earn its scope.

**Verdict:** Returned to Plan. Re-open either as (i) a witness FR
(`beat_coverage_gap`, condemning the real plan-vs-play coverage bug) followed by a
fix FR at the boundary J4 names, or (ii) a re-scoped FR-524 whose condemning evidence
is a book that demonstrates *genuine* state-blind future-summary drift (a thread that
**did** play and commit to `open_threads`, yet a later unplayed summary ignores it).
The draft below is preserved as the original proposal; it is **not** authorized for
enforce.

### Investigation outcome (2026-06-18) — the witness now exists and condemns the real bug

Per J5 (`investigation_before_fix`), the deterministic witness was built FIRST:
`witness_metrics.beat_coverage_gap(doc, cid)` — pure, no LLM, no recap parsing. It
flags any beat that a chapter's OWN committed `world_state` contradicts: the ledger
records an actor terminal (dead/missing/lost) yet a beat of the same chapter promises
their return/presence. Condemning runs:

- **Fixture** (`tests/test_beat_coverage_gap.py`): the phantom-return beat fires
  (`gap_count == 1`); a removal-only chapter is the non-vacuous negative control
  (`gap_count == 0`); a living-ledger chapter with the same return beat is clean; a
  not-yet-closed chapter (legacy prose `world_state`) normalizes to no terminal.
- **Real artifact** `10024-BC` Ch3: fires exactly once —
  `Arnulf ledger='dead' beat[3]='Arnulf reappears alive with a downstream group of
  refugees'`.
- **Corpus** (`scripts/scan_beat_gaps.py` over `100*-BC`): **fires on `10024-BC`
  ALONE; clean on all 16 older books.** Precision corroborated — the older books
  *split* the death-and-return reversal across chapters (e.g. `10023-BC` defers
  Arnulf's return to ch6 via `seam_packet … reappear_from=6`), so no single capped
  chapter both commits him terminal and promises his return. `10024-BC`'s whole-book
  partitioner packed the entire reversal into Ch3's summary; FR-523's beat re-outline
  then faithfully reproduced all five beats (its contract is to *cover the summary*),
  making the phantom return beat explicit where the play could only reach beat 1.

**The real defect, now proven:** the **outliner packs a death-and-return reversal
into a single chapter** whose 16-turn budget (FR-501) cannot play both halves; the
cap force-closes after the removal; the return beat is a phantom promise. The fix
boundary is the **outliner/partitioner** (split reversals across chapters) and/or
`close_chapter` (flag a committed terminal status that the chapter's own later beats
contradict) — NOT a future-summary re-weave. A separate **fix FR** should now be
planned against that boundary, using this witness as its RED gate. FR-524 as drafted
stays rejected.

---

## Summary

FR-523 closed the **inner** continuity loop: at chapter close, the *next* chapter's
**beats** are re-outlined against the committed `world_state`/`seam_packet`, so a
lethal/exit beat is physically continuous with where the story left each actor. But
FR-523 deliberately **froze each chapter's `summary`** (J4) — the summary is the
dominant statement of chapter intent, authored once up-front by the **state-blind
whole-book partitioner** (`outline_chapters`), and never reconciled with what the
played chapters actually resolved or left open. The result is **plan-vs-played plot
drift**: a thread a chapter leaves open (an unresolved feud, a returning character,
a demand) is silently dropped by the next chapter, because that chapter's frozen
summary was written before the thread existed and the re-outline may only adjust
beats *within* that frozen intent. This FR closes the **outer** loop: re-weave the
**unplayed chapters' summaries** (and the synopsis thread-list) against the played
chapters' committed memory at chapter close — the same `the_one_law` move FR-523
applied to beats, lifted one level up to intent.

## Value Statement

A reader stops hitting "Chapter 3 ended with Arnulf back and demanding blood — why
does Chapter 4 open as if that never happened?" Open threads, unresolved
confrontations, and lifecycle changes carried by the played chapters become
obligations the *remaining plan* must address, instead of evaporating at the chapter
seam.

## Problem

### What is already closed (do not rebuild it)

Two forward-carry mechanisms already exist and must be respected, not duplicated:

- **`world_state`/`seam_packet`** — per-chapter committed physical state +
  `open_threads`/`must_carry_facts`/`character_lifecycle`, fed *into the next
  chapter's beats* by FR-523's `reoutline_chapter_beats`.
- **`live_synopsis`** (`doc_ops._update_live_synopsis`) — a **deterministic** rolling
  container (`summary`, `immutable_ledger`, `character_states`, `last_chapter_id`)
  updated at `apply_chapter_close` and forward-fed into the **director** (`turn_ops`
  reads `live_synopsis.character_states` for lower/higher position sources). This is
  the deterministic forward-memory loop — **already closed**.

### What is still open (the bug)

Neither mechanism re-authors the **unplayed chapter cards' `summary` fields**. Those
summaries are frozen at derivation by `expand_chapters` → `outline_chapters`, a
whole-book partition of the *original synopsis* with **no view of any committed
state**. FR-523 then re-outlines each unplayed chapter's **beats** against prior
state — but its J4 froze `summary` on purpose, because:

- `chapter_ops._planned_reappearance_chapter(doc, name)` scans each card's
  **title + summary + beats** for a `_RETURN_SIGNAL`, and
  `_clamp_lifecycle_reappearance_to_plan` uses that index to clamp when a
  presumed-dead character may reappear. The summary is **load-bearing** for the
  lifecycle clamp; rewriting it naively can move (or erase) a planned return and
  break FR-520/521 lifecycle continuity.

So the system has a hard tension: the summary is simultaneously (a) the place
plan-vs-played drift accumulates and (b) a deterministic input to the lifecycle
clamp. FR-523 resolved it by freezing the summary; this FR must resolve it by
re-weaving the summary **while preserving the clamp's invariant**.

### Condemning evidence (`10024-BC`, generated WITH FR-523 active)

`outputs/dungeon-master/10024-BC/review.md` — `book_reviewer` scored **Continuity
1/5** despite FR-523 closing the positional seam. The findings are summary-/thread-
level drift the inner loop cannot reach:

- **Dropped thread.** Ch3's played scene ends on an *active* feud: "Arnulf returned
  alive, confronting Gunnar and demanding blood while Hilde refuses to surrender
  him." Ch4's **frozen summary** opens on Reinmar arriving with a high-valley offer
  and **no mention of Arnulf** — the confrontation "completely absent … no
  resolution or explanation." The `seam_packet.open_threads` recorded the unresolved
  feud, but it reached only the *beats*; the *summary* (the dominant intent) never
  learned the thread existed.
- **Lifecycle whiplash surfaced as plan drift.** Arnulf is declared flood-dead
  (Ch3), grieved, then returns, then is *absent* (Ch4), then driven over a cliff
  (Ch6) — a trajectory no single chapter summary was re-woven to carry coherently.

This is **distinct from FR-523**: FR-523 fixed *physical position* at the seam (and
it held — the reviewer did **not** flag Arnulf being swept from an unreachable
position). The remaining breaks are *plot-thread* continuity in the frozen summaries.

> **Explicitly out of scope (a third, different surface):** *intra*-chapter
> turn-to-turn prose drift — Svala's position flickering within a chapter, the supply
> bundle teleporting between turns. That is a director/recap-memory problem, not a
> summary re-weave problem. This FR does **not** claim to fix it.

## Proposed Solution

Re-weave the **unplayed** chapters' summaries (and a synopsis thread-list) against
the committed memory of the chapters played so far, at chapter close — symmetric to
FR-523's beat re-outline, one level up.

### Boundary of the change (the One Law, applied to intent)

- **Layer:** logic/planning (`chapter_ops` + a new `synopsis_reweave` graph/prompt).
  No director/`running_scene`/turn-loop change (those stay innocent, as in FR-523).
- **Trigger:** at the end of `doc_ops.apply_chapter_close`, **after** FR-523's
  `reoutline_next_chapter`. Re-weave runs on the *remaining unplayed* chapters using
  the committed `world_state`/`seam_packet`/`chapter_memory` chain of all played
  chapters + the original synopsis. (Ordering: re-weave summaries **first**, then let
  FR-523 re-outline the immediate next chapter's beats against the freshly woven
  summary — so beats serve an up-to-date intent. The Judge must fix this ordering.)

### Graph / prompt change (NEW graph, not an extension — mirrors FR-523 J1)

`chapter_outline.yaml` is a whole-book partitioner; `chapter_reoutline.yaml`
(FR-523) is a single-chapter beat author. Neither re-weaves intent against played
history. Add a new `synopsis_reweave.yaml` graph + prompt whose contract is: given
the original synopsis, the committed memory of played chapters, and the *frozen*
summaries of unplayed chapters, **rewrite the unplayed summaries** so every recorded
open thread / lifecycle change is either advanced or deliberately resolved — and
**never silently dropped**. Inputs (shape TBD by Judgement):

```yaml
synopsis: { ... }              # original whole-book synopsis (source intent)
played_memory: { ... }         # committed world_state/seam_packet/open_threads chain
unplayed_chapters: [ {id, title, summary, beats}, ... ]   # the frozen plan tail
```

Output: updated `{id: summary}` for unplayed chapters only (and optionally a revised
synopsis thread-list). Titles MAY need to stay frozen (TBD — see Open Questions).

### `chapter_ops` change (pure; the adapter writes — mirrors FR-523 J2)

A pure `async reweave_unplayed_summaries(doc, cid) -> dict[str, str]` (or similar):
invokes `SYNOPSIS_REWEAVE_GRAPH`, returns the re-authored summaries, **never mutates
`doc`**. The `doc_ops` adapter writes them and re-runs the lifecycle-clamp
revalidation (see AC-3).

### Hook point (single write in the adapter — mirrors FR-523 J3)

In `doc_ops.apply_chapter_close`, after `reoutline_next_chapter`. Writes only the
unplayed cards' `summary` (and synopsis threads); guarded identically to FR-523:
no-op for any chapter that is `reviewed` or has played `turns`.

## Acceptance Criteria

> Same posture as FR-523: the **deterministic gate is the mocked-LLM unit**; the live
> regen is corroboration, not a gate (a fresh book is a fresh roll).

- [ ] **AC-1 (deterministic gate, mocked LLM).** With `SYNOPSIS_REWEAVE_GRAPH`
  stubbed: given a fixture where a played chapter committed an `open_thread`
  (e.g. "Arnulf's blood-demand unresolved") and the next unplayed chapter's frozen
  summary omits it, the adapter writes the stub's thread-carrying summary and a
  deterministic `thread_continuity` witness reports **0 dropped threads** for the
  unplayed tail. **Negative control (non-vacuous):** a stub omitting the thread leaves
  the witness reporting the dropped thread — proving the assertion measures thread
  carry, not plumbing.
- [ ] **AC-2 (deterministic dropped-thread witness, RED first).** A new pure
  `witness_metrics.dropped_thread_gap(doc)` (TDD RED, committed separately) flags
  `seam_packet.open_threads`/`character_lifecycle` entries from played chapters that
  appear in **no** subsequent unplayed chapter's summary or beats. It fires on the
  real `10024-BC` doc (Ch3 Arnulf feud thread dropped by Ch4). This is the FR's
  condemning evidence and the AC-1 gate's measure.
- [ ] **AC-3 (lifecycle-clamp invariant preserved — the hard one).**
  Re-weaving a summary MUST NOT silently move or erase a planned reappearance:
  `_planned_reappearance_chapter` for every presumed-dead character is **unchanged or
  later** after re-weave (never earlier), and `_clamp_lifecycle_reappearance_to_plan`
  is re-run/asserted post-write. A fixture proves a re-weave that would pull a return
  earlier is rejected (or the clamp re-applies). FR-520/521 lifecycle tests stay green.
- [ ] **AC-4 (purity + write split).** `reweave_unplayed_summaries` never mutates
  `doc` (deep-copy equality); the write happens only in `apply_chapter_close`; raises
  on empty (no silent fallback, Commandment 6).
- [ ] **AC-5 (guards / isolation).** No-op when there are no unplayed chapters.
  Played chapters, the closing chapter, and every `reviewed`/`turns`-bearing card are
  byte-identical after re-weave. `live_synopsis` (deterministic loop) is untouched.
- [ ] **AC-6 (no downstream change).** Director, `running_scene`, turn loop, FR-521
  roster-drop, FR-523 beat re-outline untouched; their tests stay green;
  `lint-imports` clean (no new cross-layer edge; the new graph is invoked via
  `get_app`/`tree.py` exactly like the others).
- [ ] **AC-7 (live corroboration, not a gate).** A regenerated Floodmark book: the
  Ch3→Ch4 Arnulf feud thread that the `10024-BC` reviewer flagged as "completely
  absent" is carried into Ch4's summary; `dropped_thread_gap` no longer flags it;
  `book_reviewer` Continuity score on summary-level thread drift improves. Intra-
  chapter prose drift is explicitly NOT expected to change.
- [ ] **AC-8 (regime).** Example tests REQ-exempt (FR-474 J3); no CAP/REQ minted;
  changelog fragment `type: fix, scope: examples`, no `req:`; commit subject carries
  `FR-524`; a diary entry accompanies the GREEN commit (diary-gate).
- [ ] `architecture.md` updated: the two-loop model documented (inner = beats vs
  state; outer = summaries/threads vs played memory) and the `dropped_thread_gap`
  witness described.

## Open Questions for Judgement

> This is a **draft**; these contradictions must be resolved and scope frozen before
> enforce (the FR-523 Judgement rite).

- **JQ1 — Summary vs the lifecycle clamp.** Re-weaving summaries collides head-on
  with FR-523 J4's freeze and `_planned_reappearance_chapter`'s title/summary scan.
  Options: (a) re-run the clamp after every re-weave and assert monotonicity (AC-3);
  (b) keep the `_RETURN_SIGNAL`-bearing sentence of a summary immutable and only
  re-weave the rest; (c) move the planned-return signal out of free-text summary into
  a structured field so re-weave can't disturb it. The Judge must pick one.
- **JQ2 — Is this beats or summary or both?** FR-523 already feeds `open_threads`
  into the *beats* via `prior_seam_packet`. Is the dropped-thread bug actually a
  *beat* gap that a stronger FR-523 prompt could close, making a separate summary
  re-weave unnecessary? Judge must confirm the summary is genuinely the binding
  constraint (evidence suggests yes: beats serve the frozen summary, which never
  mentions the thread).
- **JQ3 — Scope of re-weave: next chapter only, or the whole unplayed tail?**
  Re-weaving only `cid+1` is cheaper and mirrors FR-523, but a thread may need to land
  three chapters later. Re-weaving the whole tail every close is more correct but more
  expensive and more disruptive (a far chapter's summary churns every close).
- **JQ4 — Titles frozen or fluid?** `_planned_reappearance_chapter` scans titles too.
  Probably freeze titles (as FR-523 did) and re-weave only summaries — confirm.
- **JQ5 — Relationship to `live_synopsis`.** Should the deterministic `live_synopsis`
  feed the re-weave prompt (as committed memory), or stay purely a director input?
  Likely the former, read-only.

## Alternatives Considered

- **Stronger FR-523 beat prompt only (no summary re-weave).** Push harder on the
  beat re-outline to resurface dropped threads from `open_threads`. *Risk:* beats are
  constrained to serve the frozen summary; a thread the summary omits has no anchor.
  May reduce but not close the drift. (See JQ2 — the Judge should test this first; if
  it suffices, this FR collapses into an FR-523 prompt amendment and should be closed.)
- **Re-derive the whole synopsis each close (LLM rewrite of `live_synopsis.summary`
  into prose).** Maximal, but it discards the deterministic `live_synopsis` guarantee
  and risks unbounded drift of the original authorial intent. Rejected as too broad.
- **Do nothing — accept summary drift as inherent to up-front planning.** The cheapest
  option, and defensible if JQ2 shows beats can carry threads. Rejected pending the
  `10024-BC` evidence that beats alone did not.
- **Per-turn director thread-tracking (downstream fix).** Make the director resurface
  dropped threads at play time. Normalizes downstream — the boundary violation the One
  Law forbids; same rejection as FR-523's Fix D.

## Related

- FR-523 (state-aware beat re-outline) — the inner loop this completes; its J4 freeze
  of summaries is the precise constraint this FR must safely lift.
- FR-520 (positional working memory), FR-521 (forward-fed continuity), FR-522 (replay
  witness) — the continuity arc.
- `examples/dungeon_master/api/doc_ops.py` — `apply_chapter_close` (hook point),
  `_update_live_synopsis`/`_ensure_live_synopsis` (the deterministic loop already
  closed), `reoutline_next_chapter` (FR-523, runs just before this).
- `examples/dungeon_master/api/chapter_ops.py` — `outline_chapters` (state-blind
  summary author, the bug origin), `_planned_reappearance_chapter` /
  `_clamp_lifecycle_reappearance_to_plan` (the summary-scanning clamp — JQ1/AC-3).
- `examples/dungeon_master/api/witness_metrics.py` — home of the new
  `dropped_thread_gap` witness (AC-2).
- `outputs/dungeon-master/10024-BC/review.md` — Continuity 1/5 with FR-523 active;
  the condemning artifact (dropped Ch3→Ch4 Arnulf feud thread).
- Diary `docs/diary/diary-2026-06-18-the-director-was-blamed-for-the-planners-sin.md`
  — the **Seed** ("memory forward, intent backward … should the synopsis re-weave
  from the played chapters?") this FR answers.
- Scripture: `the_one_law`, `spec_kill`, `downstream_fix`, `boundary: state`.
