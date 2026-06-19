# DM v2 Continuity — Projection Plan (synthesis of three story engines)

**Status:** Design note (not yet a Feature Request). Distilled 2026-06-18 from the
10026-BC calibration run and a three-way comparison of the repo's story engines.
**Audience:** whoever picks up the FR-507/509/510 cluster next.
**Thesis:** DM v2's continuity defects are architectural, not gate-deep. The cure is to
move a few load-bearing plot facts from *reconstructed* (inferred from prose at chapter
close) to *projected* (authored up front, prose generated from them). This document
combines the best practice of three working engines in this repo into one target shape.

---

## 1. The evidence that forced this plan

`10026-BC` (generated 2026-06-18 under the FR-532-recalibrated reviewer) scored continuity
1/5 with **6 reader-real breaks, zero micro-state noise**. With the noise gone, every
remaining break is one structural defect class:

| Break | Class | Mechanism (from `story.json` seam cards) |
|---|---|---|
| Witta dies ch7 -> argues ch8 | lifecycle resurrection | ch7 prose: "she vanished into the flood... the valley swallowed the judgment". ch7 `character_lifecycle`: `existence_state: "alive"`, `resolved_events: "she survived the chapter"`. **The close-time extractor mis-read a death it had just narrated.** |
| Arnulf swept away ch3 -> alive ch4 | lifecycle resurrection (early) | ch3: `missing_presumed_dead`, `allowed_reappearance_from_chapter: 6`. FR-510 excludes only `confirmed_dead` from prose, so `missing_presumed_dead` leaked into ch4 -- 2 chapters before the floor -- AND the planned ch6 return still fired (double return). |
| ch5 standoff replays in ch6 | scene/plot replay | FR-523 reoutlines next-chapter *beats* but freezes title/summary. Frozen ch6 summary "Arnulf Returns" + synopsis feud beats re-injected a conflict ch5 already resolved. |

**Tell:** every `character_lifecycle` entry's `source_chapter` equals the chapter it was
*extracted from*. There is no plot fact in DM v2 that is authored ahead of the prose that
realizes it. Lifecycle is an inference over the generator's own output -- and inferences
can lie.

---

## 2. The three engines in this repo (the design space)

| Engine | Plot model | Prose direction | Cross-unit state | Parallel-safe? | Continuity failure mode |
|---|---|---|---|---|---|
| `examples/ebook` | none | written per chapter, independent | none | **yes** (9 chapters at once) | cannot fail -- and cannot continue (no shared world) |
| `examples/demos/novel_generator` | beats authored **once**, up front | **projected from the plan** (`type: map` fan-out) | none -- beats independent | **yes** (parallel prose) | drift *between* beats: the plan is too thin to carry lifecycle |
| `examples/dungeon_master` (v2) | outline up front, but **lifecycle/world state reconstructed from prose at close** | turn-by-turn (excellent), then plot inferred backward | rich `seam_packet` threaded serially | **no** -- chapter N+1 must read N's prose-derived state | resurrection + replay: inherits extraction lies |

### The litmus test this comparison exposes

> **Parallel-safety is the test for true projection.** `novel_generator` can fan prose
> across all beats simultaneously *because* plot truth lives in the authored plan, not in
> the prose. `ebook` parallelizes by having no shared state. DM v2 **must serialize**
> chapters -- and that forced ordering is the architectural symptom of reconstruction:
> each chapter waits to read the previous chapter's prose-derived state. If a fact must be
> read back out of prose, it cannot be projected, and the engine cannot parallelize on it.

Each engine is right about one thing and wrong about another:
- **ebook** is right that a *judge -> amend* gate belongs on every generated artifact; wrong
  that continuity can be skipped.
- **novel_generator** is right that prose should be *projected from* an authored plan;
  wrong that the plan can be `summary|characters|importance` (too thin for a death).
- **DM v2** is right that the seam needs a rich typed world model and that turn-by-turn
  play produces the best prose; wrong that the world model's load-bearing facts should be
  *reconstructed from* the prose it just generated.

---

## 3. The combined target shape

Keep DM v2's turn generator (its genuine strength). Change only the *direction of truth*
for the small set of facts that cause reader-visible breaks: **lifecycle (alive/dead/
return floor) and resolved-conflict identity.**

```
                 +-------------------- AUTHORED ONCE (projection, novel_generator) --------------------+
                 |                                                                                     |
synopsis -> cast -> chapter outline  -> LIFECYCLE LEDGER (write-once, monotonic)                       |
                    (title/summary/beats)   per character: existence_state timeline + reappearance floor
                                            per conflict:   resolved-at-chapter id
                 |                                                                                     |
                 +------------------------------------------+------------------------------------------+
                                                            |
            per chapter, in order (DM v2 turn engine kept): |
                                                            v
   running_scene  <-- PROJECTS from the ledger (not inherited prose-state)
        |               cast = ledger.alive_at(chapter); excluded = ledger.not_yet_returnable(chapter)
        v
   turns (map -> director -> recap)     [unchanged: this is DM's strength]
        |
        v
   chapter_close  -- proposes a lifecycle DELTA (death narrated? return? )
        |
        v
   JUDGE -> AMEND gate (ebook)  -- validate the proposed delta AGAINST the prose:
        |    "prose contains death markers for X => existence_state may not stay 'alive'"
        |    "ledger says X dead with floor=N => prose at <N must not feature X"
        v
   COMMIT to ledger  -- WRITE-ONCE / MONOTONIC: once dead, the close step may not flip to alive;
                        it may only set/advance a reappearance floor (FR-526 intent, enforced)
```

### What changes, concretely
1. **Author a lifecycle ledger up front** (novel_generator projection), rich enough to
   carry `existence_state` transitions + `allowed_reappearance_from_chapter` -- the thing
   novel_generator's `characters|importance` could not express.
2. **Project the chapter cast and the prose-exclusion set from the ledger**, for *all*
   non-alive states (closes the FR-510 `confirmed_dead`-only gap that leaked Arnulf), and
   bind **final-cut + beats**, not only the roster filter, to the floor.
3. **Replace `chapter_close`'s prose->state extraction with a judge->amend gate** (ebook)
   that validates a *proposed delta* against the prose and the existing ledger, rather than
   re-deriving state from scratch. Make the ledger **write-once monotonic**: a death may
   never be downgraded to alive by a later extraction (kills the Witta class at the source
   boundary, per the Scripture's "normalize where data enters").
4. **Let the reoutline revise the frozen summary, or gate the frozen summary against the
   ledger's resolved-conflict set** (kills the replay class).

### Acceptance litmus (borrowed from the comparison)
The lifecycle ledger is *truly projected* iff two chapters' prose could, in principle, be
generated against it **without one reading the other's prose**. If a chapter still needs
the prior chapter's *prose* (not its authored ledger delta) to know who is alive, the fact
is still reconstructed, not projected.

---

## 4. Staging (smallest reversible steps first)

1. **Witness FR (investigation):** build a deterministic test over `10026-BC`'s
   `story.json` seam cards proving the three causal chains (prose-death vs `alive`
   extraction; `missing_presumed_dead` prose leak; frozen-summary replay). The evidence
   already exists on disk -- the RED test is cheap. (`investigation_before_fix` cure.)
2. **Cheap fix (ebook gate):** add a judge->amend cross-check after `chapter_close` --
   death markers in prose forbid `existence_state: alive`. Kills the Witta class without
   re-architecture.
3. **Projection fix (novel_generator):** author the write-once lifecycle ledger up front;
   project cast + prose-exclusion from it for all non-alive states; bind final-cut/beats to
   the floor. Kills the Arnulf class.
4. **Replay fix:** gate or revise the frozen summary against the ledger's resolved set.
5. **Acceptance:** re-run a Floodmark book; expect the lifecycle breaks to fall to zero in
   the recalibrated reviewer; record before/after like FR-532.

---

## 5. Why this is not just "more gates"

The FR-506->532 arc has been hardening *gates* and *extraction inputs* -- fighting the
symptom of a reconstruction architecture at the boundary where it *manifests* (chapter
open). This plan moves the fix to the boundary where the bad data is *born* (chapter
close / up-front authoring). It is the `downstream_fix` -> boundary-normalization cure
applied at architectural scale. The deterministic gates already written are correct; they
will simply consult a projected ledger that cannot lie, instead of a reconstruction that
can.

---

## 6. FR-533 spike verdict (2026-06-19) — the premise was half-inverted

The FR-533 spike (`tmp/fr533_projection_spike.py`, throwaway) tried to hand-author the
"truthful" projection for the ch7->ch8 Witta seam — edit ch7's `seam_packet` Witta to
`confirmed_dead`/`absent` and re-play ch8 via the FR-522 single-chapter harness. **The
deterministic precedence gate (`_enforce_memory_precedence_gate`,
`ContinuityMemoryConflictError`) refused the re-play, pre-LLM**, with
`alive conflicts with confirmed_dead`. That refusal is the load-bearing finding, and it
corrects this plan's own §1 Cause-A framing:

1. **The "lie" is a plan-vs-prose conflict, not a careless misread.** Reading the actual
   `10026-BC` data: ch7's composed `text` *does* kill Witta ("She vanished into the flood
   as it seized her, and the valley swallowed the judgment"). But the per-turn recaps are
   **non-monotonic** — turn 7 sweeps her off, turns 8–16 have her alive, present, and
   physically restrained by Reinmar (a textbook FR-501 no-progress tail, one beat replayed
   ~6×). The chapter's *final-cut composition* chose a dramatic death; its *turn ledger*
   and **six** structured sources chose alive.

2. **Six sources unanimously keep Witta alive — and the plan pulled them there.**
   `world_state.status`, `chapter_memory.character_state_deltas`,
   `irreversible_facts` ("Witta is alive at the end of the chapter, not dead or swept
   away"), `forbidden_regressions` ("FORBID: Witta is dead"), `seam_packet`, **and**
   `live_synopsis.character_states` (`Witta -> alive`). Witta is the plan-critical
   ritual-keeper antagonist the synopsis needs for the rest of the arc. The state path was
   *plan-faithful*; the prose path was *plan-violating*.

3. **The precedence gate already enforces plan-over-prose — for bookkeeping.** Precedence
   `chapter_memory > live_synopsis > seam_packet`. Injecting the death at the lowest source
   is exactly what the gate exists to refuse. So the architecture is *not* missing
   plan-over-prose; it is missing it **at prose-generation time**. Nothing stopped the
   turn engine / final-cut from narrating the death of a protected character in the first
   place.

### What this changes in the plan

- The §3 step "replace close-time extraction with a judge that forbids `alive` when prose
  says dead" is **inverted for plan-protected characters**. Ratifying the prose death into
  the ledger would contradict the synopsis and break the remaining arc. The death is the
  *error to prevent*, not the *truth to record*.
- The true projection is **plan → prose at generation**: feed the protected-character set
  (and any authored reappearance floor) into the turn director **and** the final-cut, so a
  plan-protected character can never be killed on the page. Then there is no conflict for
  any gate or extractor to reconcile.
- The vividness/orthogonality question (FR-533 J1) is **unanswerable via Witta**: her
  correct projected state is *alive*, which the baseline bookkeeping already holds, so
  there is no "projected death prose" to read for flatness. Testing whether projection
  flattens prose needs a character the **plan authors as dying** — which this architecture
  never produces. That absence is itself the point: there is no authored-death channel.

### Verdict on refactor-vs-rewrite

The spike **strengthens the refactor call** (FR-533 decision rule, fourth branch). The
expensive asset — a typed ledger with working plan-over-prose precedence — already exists
and already works. The gap is one missing edge: the same precedence must reach prose
generation. That is an additive constraint on the turn engine, not an engine rewrite.
A `novel_generator` rewrite remains the wrong move; it would re-pay for precedence the gate
already provides.
