# Diary 2026-09-26 — The context line

**Context:** FR-1104 — retire `core-test`, move the CI ceiling to 3.14,
SPLIT verdict overruled by the operator.

The CI question ("are we running the same tests three times?") had a
cheap answer: two jobs ran `tests/unit` on the same interpreter, and one
was a 70% subset of the other. The judge split the FR because retiring
`core-test` also retires FR-756's separate `not process` CI run. That
was a real loss, and the operator accepted it by name rather than by
silence. The FR now carries the accepted loss in one sentence, which is
cheaper than a second FR that exists only to hold a sentence.

Three gates fired on the way, and each taught something different.
The prior-art gate matched the FR against its own judgement — a
self-match, satisfied honestly by a line saying so. The REQ collision
test caught me claiming REQ-YG-277 in a fragment when CAP-127 owns it;
FR-918 had already solved the same case by omitting `req:`, and the
precedent was one `ls` away. The changelog release-sync gate was the
only one that was wrong: it searched the whole diff for
`version = "`, and unified diff context put the unchanged version line
next to `requires-python`. The operator authorized a skip; the defect
has its own FR (FR-1107) rather than a "deferred" bullet.

The stash was the quiet hazard. `git stash -- tests/` stashed staged
FR files too, and a commit made during the probe collided with the pop.
Nothing was lost because the committed copy was a strict superset, but
I learned that from a diff, not from the command's promise.

**Heuristic:** a text-search gate over a diff must look at `+`/`-`
lines only; context lines are the old file wearing the diff's clothes.

**Seed:** which other hooks grep whole `git diff --cached` output, and
would a single "changed lines only" helper retire the class?
