# The Half-Threaded Invariant

*2026-06-19 — Distill, FR-534 (DM v2 protected-character projection)*

## What happened

FR-533's spike found the bug: DM v2 already enforces lifecycle precedence
(`chapter_memory > live_synopsis > seam_packet`) at chapter open — it will refuse
to commit a turn whose memory layers disagree about who is alive. But that same
precedence was never handed to the prose generators. The turn director and the
final-cut composer narrated chapter 7's Witta dying; the ledger, holding the plan
that says Witta lives, then refused to record it. The reader sees a death the
canon erases next chapter: a resurrection.

The fix was not "add a guard." The guard existed. The fix was to finish wiring a
guard that was only half-threaded: the gate consumed the precedence, the prose
did not.

## The trap: the invariant enforced at one boundary, assumed at the others

DM v2 has three places lifecycle truth crosses into behaviour: the open-gate, the
turn director, the final-cut composer. FR-519 had already taught the composer
about *dead* characters (`dead_within_chapter`). But "must stay dead" and "must
stay alive" are the same invariant viewed from opposite ends, and only one end was
wired. The asymmetry was invisible because each half worked in isolation — the
gate's tests passed, the composer's tests passed. The defect lived in the *policy
connecting* two correct components, not in either component. (This is the
`composition_bug` from Scripture, in its quiet form: not a crash, a silent
narrative contradiction.)

## What I did right

I refused to add the protection logic where the symptom showed (the composer). The
gate already owned the precedence; duplicating it in the composer would have
created two sources of truth that drift. Instead I extracted the precedence into
`lifecycle_resolver.py` and made *both* the gate and the prose side import the
*same* functions — and I wrote a test that asserts function *identity*
(`turn_ops._state_map_from_memory is lifecycle_resolver._state_map_from_memory`),
not just equal behaviour. An identity assertion is a structural guarantee that the
two boundaries can never diverge, where a behavioural assertion would silently pass
the day someone forks the logic. That is `name_the_seam` applied to a shared
dependency: the test names the seam (one resolver, two consumers) so a future
split shows up as a failure, not as drift.

## The smaller trap: lint as a contract carrier

Refactoring the extractors out of `turn_ops` left them imported-but-"unused" — yet
the identity test *requires* `turn_ops` to re-export them. Ruff's F401 wanted them
gone; the contract wanted them kept. The redundant-alias form (`import x as x`) is
the idiomatic way to tell the linter "this is a deliberate re-export," and it kept
the fix local instead of reaching for a repo-wide `__all__` or a noqa confession.
The lesson: when a linter and a test disagree, the linter is usually right about
*mechanism* and the test is right about *intent* — find the construct that
satisfies both rather than suppressing either.

## Seed

The protected-character constraint now lives in a prompt — a probabilistic gate. The
novel_generator comparison (folded into FR-534) showed an LLM review-gate alone is
too soft for a hard invariant, which is why FR-535 will add a deterministic
post-compose backstop. **Seed:** when an invariant is enforced at a hard boundary
(the gate raises) but only *requested* at a soft one (the prompt asks), what is the
general pattern for proving the soft request is sufficient before paying for the
hard backstop — and should every prompt-level constraint carry an automatic,
cheap, deterministic assertion of the thing it asks for, the way every gate
carries a raise?
