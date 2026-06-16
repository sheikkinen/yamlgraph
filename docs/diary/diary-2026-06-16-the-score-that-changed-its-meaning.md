# The Score That Changed Its Meaning

*Diary — 2026-06-16 — DM v2 × book_reviewer, the 10003-BC mercury witness*

## What happened

The full FR-499 arc was built to lift the *Floodmark Saga* off its **1/5 continuity**
baseline: the structured world-state ledger (FR-499), the roster/faction/inventory
authority (FR-498), the per-chapter turn budget (FR-501). I regenerated the saga
end-to-end on `inception`/`mercury` — nine chapters, 6174 words, the book gate open
— and ran `examples/book_reviewer` over it. The verdict came back **overall 2/5,
continuity still 1/5.** The naive read: the ledger didn't move the needle.

The naive read was wrong, and the reason it was wrong is the whole lesson.

## The trap: reading the number as the verdict

`1/5` is the same digit it was at the FR-497 baseline, so the reflex is "no
improvement." But the reviewer does not *only* emit a number — by design (its whole
anti-almighty-prompt thesis) it emits **located findings**, and the findings show
the 1/5 now condemns a *completely different class of break*. The baseline 1/5 was
faction flips and phantom items — characters changing clans, objects appearing from
nowhere. Those are **gone**. Not one finding in 30+ flags a clan flip or an
un-owned actor. The ledger did exactly its job.

What the new 1/5 flags is **prop-position thrash**: the axe migrates from ridge to
valley floor "with no action explaining the relocation"; the ceremonial dagger
"appears without prior establishment" then is pulled, placed, and driven into stone
in contradictory order; chapter 4 jumps to "hours earlier" than chapter 3. Same
score, orthogonal cause. A number is a symptom; only the located finding is a
diagnosis — and trusting the digit over the finding would have sent me to fix the
ledger, which is already correct.

## The diagnosis the reviewer found on its own

The reviewer independently named the generator's real limiter — the one I had only
suspected from reading the prose: *"nearly every paragraph follows the pattern
'Hilde [action], Gunnar [action], Reinmar [action], Einar [action],' which deadens
engagement."* That round-robin is structural: the director asks **every** rostered
character to act **every** turn, so every turn re-grabs and re-plants the same five
props, and *that churn* is what reads as continuity breakage at each chapter seam.
The ledger tracks object state faithfully; mercury's prose simply won't let an
object stay put. The bottleneck moved from *state tracking* (solved) to *prose
subordination* (a provider/director limit), and the score stayed flat while the
underlying failure mode changed entirely.

## The Seed that got an answer

The FR-501 diary planted: *should a force-close mark a chapter as degraded — a
quality flag the book_reviewer reads?* The witness answered empirically. Chapters 6
and 7 — the two the turn budget force-closed at 16 turns with `scene_complete=False`
— scored **engagement 1/5**, the reviewer noting "the shelter is described as
completed at least four separate times" and "characters testing things they've
already tested." The degradation a budget-cap produces is **independently
detectable** by the reviewer with no new metadata. So the cheapest "is this a
natural close or a cap?" signal may already exist downstream — but the generator
still emits no *explicit* flag, so the confound (low score = weak chapter vs. low
score = capped chapter) is only resolvable by cross-referencing turn counts by hand.

## Heuristic

When an evaluation score is unchanged but the system underneath it changed, do not
conclude "no progress" — read the *located findings*, not the digit. A decomposed
reviewer's value is that the same number can hide a completely different cause: the
ledger can fully eliminate one break class while a provider-level limit keeps the
score pinned. A flat score across a real fix is a provider confound, not a failed
fix; the only honest verdict compares findings, and only on a like-for-like
provider. This 2/5 is a **mercury floor**, not a **ledger verdict**.

**Seed:** The reviewer can *detect* a force-capped chapter's degradation from prose
alone, but the generator knows the ground truth (it set the cap) and stays silent.
Should `apply_chapter_close` persist a `closed_by: "budget" | "scene_complete"`
field so a future reviser can target exactly the capped chapters — and so the
reviewer's per-chapter score can be read against the generator's own admission of
which chapters it cut short? Detection downstream and confession upstream should
agree; when they disagree, which one is the bug?
