# Diary 2026-08-19 — FR-822: The Gate That Knew the Repo Better Than I Did

## Arc

Proposal (chaplain inbox) → desk research (DA API docs) → FR-822 spike →
live API publish of tmp/da.png — one sitting, first-attempt 200s on all four
calls. Deviation: <https://www.deviantart.com/sheikkinen/art/API-Spike-Veil-and-Vow-1370448491>.

## Trap: greenfield assumption, corrected by machinery

I wrote the pipeline proposal with a fresh `examples/deviant_publish/` Phase 1
— description generation from scratch. The prior-art pre-commit gate refused
the FR commit and surfaced FR-781: the WatchPaths-triggered DeviantArt MD
generator, ENFORCED two weeks ago, already using FR-769's vision tool. Phase 1
was largely shipped and I didn't know. The human didn't catch it either — the
gate did. This is `ask_before_generate` mechanized: the question "who solved
this before?" fired as a blocking hook, not as discipline I remembered to
apply. The proposal was corrected from "build Phase 1" to "Phase 1 delta
only" before any code existed — spec_kill at the cheapest rung, executed by
infrastructure.

## Trap: one_session_one_repo, fourth strike

`git add <file> && git commit` swept six diary files another session had
staged. I knew the ritual (staged-check empty before add) and skipped it
because the commit felt small. Split into two clean commits before push, but
the lesson is that the ritual exists precisely for commits that feel too
small to check.

## Boundary find: vendor form text vs vendor behavior

DA's registration form warns http redirect URIs "must be secure (https)" —
yet accepted `http://localhost:8721/cb` without complaint. The docs are a
lossy summary of the vendor's intent (Scripture:
does_the_platform_already_do_this); the form's validation text is a lossy
summary of the form's validator. Try the cheap input before building the
workaround (I had a manual-code-paste fallback designed; never needed).

## Spike-first payoff

Three unknowns (ToS error codes, paragraph rendering, refresh rotation) each
died to one observation of a real system: no `agree_*` params needed;
`\n\n` renders as paragraphs; refresh tokens rotate and must be re-persisted.
Every one would have been a guess embedded in Phase-2 code. Cost: ~150 lines
of condemned-at-birth script, one test deviation the operator can delete.

**Seed:** the prior-art gate matched on nouns (deviantart, publish) — it found
FR-781 because the FR titles shared vocabulary. What about semantic overlap
with disjoint vocabulary — an FR that reimplements `utils/fsm` but calls it
"workflow engine"? Noun matching is the cheap tier; is an embedding-space
prior-art sweep the graduation of this gate, and would it have fired anywhere
noun matching stayed silent in the last quarter?
