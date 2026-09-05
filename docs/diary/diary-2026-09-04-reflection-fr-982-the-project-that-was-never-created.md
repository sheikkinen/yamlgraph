# The Project That Was Never Created

**Date:** 2026-09-04
**FR:** FR-982 the unit suite must not run with the operator's LangSmith tracer live
**Session:** enforcer, on the folded judgement (graph SPLIT overridden by the
operator; D-2 kept in scope)

## What happened

A test that stubs `subprocess.run` with a three-element list was red on my
machine and green in CI. The FR had already done the hard part — the stack
trace showing the LangSmith tracer's `get_runtime_environment()` shelling out
to `uname` and `file` underneath the stub, and the `list_runs` query showing
the unit suite posting fixture graphs to the operator's project. Enforcement
was two commits under `tests/` and one live witness.

Three things earned their place in the record.

**The judge found a cache I had not.** R-2 said the opt-in witness could not
pass because the fixture sets the highest-priority alias to `"false"` while
the witness flipped the lowest. Folding that, I read
`langsmith.utils.tracing_is_enabled` and found the lookup goes through
`get_env_var`, which is `@lru_cache(maxsize=100)`. So the first read of
`("TRACING_V2", default)` is frozen for the process. Without
`cache_clear()` the session fixture would have *appeared* to work on a cold
process and silently failed in any process where something had already
asked — e.g. a conftest import that constructs a `Client`. The judge's
finding was about precedence; the fix it forced surfaced a second, worse
defect in the same line. `does_the_platform_already_do_this` in its
inverse form: does the platform already *remember* this?

**The live witness returned the strongest possible zero.** AC-08 (R-3)
required an isolated `LANGSMITH_PROJECT` and zero root runs. The query did
not return an empty list. It returned `LangSmithNotFoundError: Project …
not found`. LangSmith creates a project on the first ingested run; a
project that does not exist has received no event of any kind — not a
root run, not a child span, not a failed flush. An empty list would have
said "nothing you asked about"; a missing project says "nothing at all".
The control (the operator's default project, same window, 0 root runs)
closed the other door. The right witness design produced a reading more
conclusive than the criterion demanded.

**I wrote a commit with the wrong message and did not notice for two
commits.** The RED commit's `&&` chain was `ruff check … && printf … >
tmp/msg.txt && git commit -F tmp/msg.txt`. Ruff failed on a dict
comprehension; the printf never ran; I fixed the lint and re-ran only
`git add && git commit -F tmp/msg.txt` — with the fold commit's message
still in the file. Then a `git log --grep 'RED witnesses'` to fill in the
SHA matched an FR-951 commit from another arc, and I pasted that SHA into
the FR. Two independent stale-state traps compounding: a file that held
yesterday's truth and a grep whose vocabulary was not unique. Repo memory
already holds `tmp-msg-txt-stale-state`; this is its second firing in my
hands. The `&&` chain is the culprit shape: it makes the message-write
conditional on unrelated checks, so a failure upstream leaves the file
stale for the retry.

## Heuristic

Write the commit message file **first**, in its own command, before any
check that can fail. And when a SHA must be transcribed, take it from
`git log -1` at the moment of the commit, never from a later `--grep`.

## Seed

**Seed:** The RED witness for a *helper that does not yet exist* can only fail with
`ImportError` — exactly the failure class AC-11 excludes as masking. The
substantive RED lived in a different test (AC-04's positional-stub failure).
Is there a witness shape for "this abstraction is missing" that fails on
behaviour rather than on import — e.g. asserting that the *existing* test's
stub survives an interleaved foreign call — so that RED and GREEN of a new
seam are measured by the same instrument?
