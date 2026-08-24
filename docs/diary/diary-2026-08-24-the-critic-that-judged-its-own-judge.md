# The Critic That Judged Its Own Judge — FR-879 enforcement

**Date:** 2026-08-24
**Arc:** FR-876 (train a tiny model) → FR-879 (make it a critic) — one
day from corpus to a production-shaped generate→score→filter→render
pipeline across two repos.

## The R-1 inversion

The judge applied `read_raw_output_first` against my own FR: a scorer
is measurement tooling, so authority required reading raw scorer output
BEFORE implementation. The 15-minute fixture run rewrote the spec three
times: the NLL band cannot detect memorization (a verbatim corpus row
scored in_band — 3.3 M params don't memorize sharply enough for a
likelihood floor), the tag register is systematically more predictable
than prose (single-band calibration would wrongly reject good tag
prompts → per-register calibration), and the model finds its own
generations MORE likely than real data (self-likelihood bias — never
calibrate on your own output). Every one of these was invisible in the
design and obvious in five JSONL rows. The gate is not ceremony; it is
the cheapest spec-review that exists.

## Trap: the guard that misfired on its own vocabulary

The pre-command guard blocks `pytest | head`; my commit command
contained `SKIP=pytest` and an unrelated `| head` — blocked. The
lesson generalizes: string-match guards fire on MENTIONS, not USES.
(Cure applied: keep commit commands pipe-free.)

## Trap: interleave, third form

Two new shared-repo race forms in one session: (1) pre-commit's
stash/restore cycle from a parallel session CLOBBERED my four unstaged
FR edits (stash taken before my edits, restored after — silent
overwrite, detected only by grep-after-commit); (2) `cannot lock ref
'HEAD'` — the parallel session moved HEAD during my 45 s hook run; the
staged files survived and a plain retry landed. The stash-restore form
is nastier than the swept-commit form because nothing fails: content
just reverts. Grep-verify after every commit in a shared repo
(`shared-git-index-race` memory updated).

## Insight: the demo refused to demo rejection

The witnessed run rejected nothing — 10/10 candidates in_band. A
frontier LLM given a corpus-adjacent style brief writes squarely
in-distribution; the filter's live value collapsed to ranking + spend
cap. The rejection behavior exists (fixture: business English and
random chars land far outside), but the flagship path doesn't exercise
it. A demo designed to show a mechanism should include one input that
TRIGGERS the mechanism — otherwise the table shows green rows and the
reader must trust the fixture. Same lesson as assert_path_not_
destination, in demo form.

## Heuristic

For any learned gate, ship the calibration probe set (in-style /
off-style / degenerate) as a permanent fixture — it is simultaneously
the R-1 evidence, the regression suite, and the demo of rejection the
happy path cannot provide.

**Seed:** the critic scores openings only (256-char context, all 10
candidates truncated). Is a "score the first N chars" critic actually
scoring STYLE, or scoring OPENINGS? A sliding-window mean vs
opening-window experiment on the val set would answer it in an hour —
and might justify (or kill) a block-512 retrain before anyone trusts
the ranking.
