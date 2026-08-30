# 2026-08-30 — FR-889: Deleting the Grammar It Was Standing On

## The work

Enforced FR-889: replaced the FR-888 shell-command grammar (a growing
regex taxonomy of "things that might write") with an OS lock —
`chmod -R u-w` on governed roots of the main checkout. The kernel does
not need a grammar. Check 7 shrank to two duties the filesystem cannot
cover: edit-tool classification (editors bypass permissions via the
extension host) and a lock-mutator fence (deny bare `chmod` on governed
roots; the cure is `worktree.sh unlock-main`, which leaves a marker and
an audit row).

## The trap: guard_polices_its_own_replacement

The session enforcing the grammar's deletion was policed, throughout, by
the *live installed copy of the grammar being deleted*. Six false-positive
witnesses in one session:

1–2. `grep` commands denied because the *pattern argument* contained
   writer tokens (`tee`, `sed`) — the grammar cannot tell mention from use.
3. `tee logs/…` with a relative path denied in-lane — the FR-902
   cwd-proxy guessed the wrong working directory.
4. A `grep` mentioning "pytest" piped to `head` tripped Check 4's
   pytest-pipe rule — again mention, not use.
5. In-lane `git add` with relative paths denied by the cwd proxy.
6. A read-only `python3 -c "ast.parse(...)"` denied because the code
   string *mentioned* `scripts/` — worked around with `python3 -m
   py_compile`.

Every witness is the same defect class: **textual analysis of commands is
a lossy simulation of the filesystem**. The grammar guessed what a command
would write; the kernel knows. The fix was never a better regex — it was
moving enforcement to the boundary where writes actually happen
(`the_one_law`: normalize at the boundary). The six denials are not
anecdotes; they are the empirical justification of the FR they obstructed.

## Insight: the escape hatch is the telemetry

`FR902_ALLOW_OUTSIDE=1` was used ~a dozen times this session, each row
audited. A guard whose escape hatch is used more often than its denials
are correct has inverted its own purpose — the audit log of overrides is
the failing test suite of the guard itself. FR-889 §4c retired the
cwd-proxy heuristics precisely because the override rows proved the
heuristic wrong more often than right.

## Also

- Second confirmed witness of `two_strike_split` at the guard level: two
  FRs of prompt/grammar patching (FR-888 iterations) fell to one boundary
  (`chmod`). The Scripture's cure generalizes from LLM outputs to shell
  grammars: any textual simulation of a mechanizable check loses to the
  mechanism.
- Confession-anchor coupling: adding 19 lines to `now.py` broke six
  existing CONF entries because the noqa-confession hook binds to *line
  numbers*. Presence-check by line anchor is `gate_checks_shape_not_substance`
  in miniature — the anchor drifts, the substance didn't.

**Seed:** The live-hook self-policing problem is structural: any FR that
modifies the guard is enforced under the *old* guard. Should
`worktree.sh new` snapshot the hooks into the lane and point the session
at the snapshot, so guard changes are testable against themselves before
install — a staging ring for the enforcement ring?

## Addendum (same day): the exception died in five words

"docs exception removed. agent should not have any business writing to
main." — the operator deleted a whole lane class the original FR had
carefully preserved. The docs lane existed because *I* found it
convenient (FR status updates, diary pushes straight to main). Its
removal is the `additive_default` cure applied to *permissions*: the
convenience of the author is not a design justification. Two hours after
merge I had already used the docs lane to push an FR status edit to main
— exactly the write class the operator then closed.

Bonus witness: the size-gate ratchet I shipped in the morning blocked my
own afternoon commit (guard test 687 > baseline 666) and forced the
overdue split of the OS-lock suite into test_main_lock.py. The gate
worked on its author first — `infrastructure_self_exempt` refuted by
construction.

**Seed:** changelog/ remains the last agent-writable committed path on
main. Fragments are born in lanes anyway — should the runtime-lane list
shrink to tmp/ and logs/ only, making "committed = via PR" true without
exception?
