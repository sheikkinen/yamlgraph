# 2026-08-25 — The guard is built inside the cage it builds

FR-888 enforced from inside its own worktree — the first arc to live in
the container it mandates. The dogfood caught what no fixture would have:
the cure command in my judged FR quoted a verb (`create`) that doesn't
exist, the tree was born without `.env`, and the script never printed the
`cd` line its own denial message promises. Three defects in the *cure
path*, found by drinking the medicine before prescribing it.

## Traps

**The budget I didn't know I was spending.** My Check 7 added a fourth
python invocation to every clean terminal call — and an FR-442 test I had
never read failed. Someone else's discipline (a pinned invocation budget)
caught my regression the way my guard is meant to catch theirs. Guards
compose: every new check inherits every old check's constraints, and the
suite is the only place that knowledge lives.

**Mention-grammar vs target-grammar.** My first write-signal regex denied
commands that merely *mentioned* enforcement paths — `pytest scripts/x |
tee logs/y` would have been denied for reading. The fix (extract write
TARGETS: redirect destinations, tee/cp/mv last args, sed -i operands)
is the same lesson as FR-884's micro-turn tax read in reverse: precision
about which token is the object, not which words appear.

**The clean tree that wasn't.** `rm-safe` refused its own fixture: the
setup's `.env`/`.venv` symlinks and `.gitignore` append are untracked
files. Safety invariants need an ontology of dirt — reproducible setup
artifacts are not unlanded work. Excluding them by name is honest;
excluding by pattern would eventually eat someone's draft.

**Line-pinned confessions rot under insertion** (second time today), and
my perl one-liner corrupted a confession header while re-pinning —
repairing the repair. Anchoring confessions to line numbers is a
`substance_over_presence` violation waiting for every insert above L60.

## Insight

The denial-as-guideline thesis survived contact: building the guard
required reading nothing about the hooks — the existing suite's failures
taught me the constraints (budget, parse conventions, audit shape) at
exactly the moments I violated them. The enforcement infrastructure
onboarded its own extender by denying him, which is precisely the
mechanism FR-888 ships for everyone else.

**Seed:** confessions pinned to line numbers rot on every insertion above
them — today needed two re-pins and one corrupted header. Should the
noqa checker match on (file, code, nearest-def) instead of (file, line),
making confessions insertion-stable?
