# Reflection: FR-902 Session Worktree Lifecycle — the guard that guards the guard-writer

**FR:** FR-902 · **Branch:** feat/fr902-session-worktree-lifecycle · **Tests:** 55 new, 225 hooks suite green

## The recursion was the test fixture

Mid-enforcement, the FR-888 main-write guard denied my own `chmod +x` on the
hook scripts I was writing — inside the FR worktree, because the relative path
resolved against the payload cwd. The system under construction policed its
constructor. This is not an anecdote; it is the strongest evidence the
mechanism works: enforcement that cannot inconvenience its own author is
advisory (`detection_without_enforcement`). I fixed my command, not the guard.

## Trap encountered: `growth_as_default` at the guard boundary

Check 8 made `pre-command-guard.sh` 714 lines with three python heredocs that
each re-implement the same shell-command parser. I added the third copy
*knowingly* — extraction-ready, env-parameterized — because the judgement froze
scope to D-1..D-9. The operator flagged the bloat within minutes. The lesson is
not "should have refactored" (that would be scope creep past a frozen
judgement); it is that **the third duplicate is the graduation moment** — the
same rule as `regex_fourth_exclusion`, one exclusion earlier. The refactoring
plan now lives in the FR (dispatcher + `checks/guard_common.py`), disposition:
follow-up FR via inbox. Duplication acknowledged in writing beats duplication
denied.

## Insight: ship mechanism, arm policy separately

AC-13 demanded human review *before the policy is live*, but the PR gauntlet
demands the code merge. The live-flag file (`.github/hooks/fr902.live`,
untracked) dissolves the contradiction: merge ships inert mechanism; the
operator arms policy by touching a file after reviewing the diff. This
generalizes — any hook whose blast radius is "every future session" should
separate its merge boundary from its activation boundary. The flag is the
`enforcement_at_merge_boundary` complement: *activation at the operator
boundary*.

## Insight: a hang that wasn't

"Test seemed to hang" → no stray processes, last log truncated at [100%] with
no summary. Diagnosis: the suite is just slow (2m32s — every FR-902 test builds
real repos, worktrees, and bare remotes). The cheapest diagnostic was `pgrep` +
reading the log tail, not re-instrumenting (`read_raw_output_first`, applied to
test output). Subprocess-real fixtures are the right cost here: the feature IS
git behavior; a mocked git is a unit test with extra steps (`mock_escape_hatch`).

**Seed:** the checkpoint trailers now give every tree delta a request-level
cost. When GC classifies a lane "merged", the credits spent in that lane are
joinable to the squash commit on main — should `worktree.sh gc` emit a
cost-per-lane line (credits from the ledger, lines from the diff) so the
retirement of a lane doubles as its accounting close?
