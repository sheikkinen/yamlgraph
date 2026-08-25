# Post-mortem: FR-888 — the 601-line guard that took three hours

**Date:** 2026-08-25
**Arc:** FR-888 main-write guard, PR #476, 16 commits, ~2.5–3 h wall time,
5 sequential review rounds, merged by operator override.
**Prompted by:** operator damage report — "worktrees were supposed to make
git processes easier and cheaper; you changed one shell script and its
docs, and pushed it to a bloated 500+ lines, flagged by nothing."

## Outcome vs cost

| Metric | Value |
|---|---|
| Files materially changed | `pre-command-guard.sh`, `worktree.sh`, tests, docs |
| `pre-command-guard.sh` size after | **601 lines** (bash + 2 embedded Python heredocs) |
| Commits on the arc | 16 |
| Review rounds (sole route, gpt-5.5) | 5, all "Not approved" until operator merge |
| Defect classes fixed from reviewer probes | 14 |
| Wall time | ~2.5–3 h |
| Gates that flagged the bloat | **none** |

## Verdicts on the four questions

### Was the planning bad? — Yes: scope.

One arc bundled the guard, a terminal write-grammar, `worktree.sh`
completion (.env, cd line), `rm-safe` with two safety modes, orphan-board
detection, a runbook, and an escape hatch — 13 ACs, plus 7 judge
revisions. A v1 of **edit-tool denial only** would have shipped in ~30
minutes and covered the way agents perform ~95% of writes. The terminal
grammar — the entire time sink — could have been its own FR, or nothing.

### Was the implementation lacking? — Yes: wrong substrate.

Python-embedded-in-bash-heredoc is invisible to every quality gate: no
ruff, no radon, no vulture, no size gate, testable only through
subprocess. Every review fix was string surgery inside a heredoc. The
repo already has the correct pattern (`python-checks.sh` dispatching to
real Python modules); it was not used.

### Was the review too strict? — No, but the spec made it unbounded.

Every reviewer probe was a genuine bypass (`rm-safe` would have deleted
unmerged committed work; `cp -r` materialization; `Move to:` hunks;
`time`/whitespace wrappers; direct writers; interpreter one-liners). The
defect was upstream: AC-06 said *enumerate write shapes*, which turned
review into an adversarial fuzzer against a regex grammar — a game where
the fuzzer has unbounded ammunition and each round costs a full
review+fix cycle. The reviewer won the same argument five times; the spec
invited it.

### Wrong tool for the task? — Yes: the core failure.

Scripture names this twice, and both entries were ignored in the moment:

- `regex_fourth_exclusion`: "fourth special case → switch to proper
  parser." Round 2 (`time` prefix) was the fourth special case. Seven
  more grammar rewrites followed.
- `two_strike_split`: "same guard fires twice after a reword → the
  abstraction level belongs in code; stop rewording."

The correct round-2 move was to **invert the grammar**: deny-by-default
any terminal command that touches an enforcement path with a
non-allowlisted verb. Allowlists converge; denylists never do.

## The two findings that hurt most

1. **The guard misses the witnessed vector.** Every recorded
   shared-index incident (FR-748 ×2, the `commit -a` sweep) was a **git
   index operation** — `git add -A`, `git commit -a` on main. The
   601-line grammar denies redirects, `tee`, `cp`, `sed -i`, `touch`,
   and interpreter one-liners — and allows `git add -A` unexamined. We
   armored hypothetical vectors and left open the door the burglars
   actually used.
2. **`infrastructure_self_exempt`, verbatim.** The file-size gate runs
   `find yamlgraph -name "*.py"` — wrong tree AND wrong extension. The
   enforcement layer is exempt from every entropy gate it enforces:
   601 lines, heredoc Python, zero flags. The trap is already in
   Scripture; the gate config never caught up with it.

## What was NOT the problem

**The worktree.** Creation was one command; isolation held (parallel
main-lane commits landed during the arc with zero collisions); teardown
was one command (`rm-safe --merged-confirmed`, dogfooded). The relative
path friction was cosmetic. The hours went into the grammar war, which
would have been identical on main. The worktree hypothesis is not
falsified by this arc — the substrate hypothesis is.

## Remediation queue (each independently small)

1. **Invert the terminal grammar** — deny-by-default on
   enforcement-path mention + non-allowlisted verb. Kills the fuzzing
   game structurally; covers `git add`/`commit -a` for free.
2. **Extract the heredocs** into `.github/hooks/scripts/checks/*.py`
   modules (existing `python-checks.sh` pattern); bash becomes a thin
   dispatcher; the Python becomes lintable, size-gated, unit-testable.
3. **Widen the size gate** to `scripts/**`, `.github/hooks/**`, and
   `*.sh` — one line of pre-commit config.
4. **Review-loop circuit breaker** (process): two consecutive
   Not-approved rounds on the same defect *class* → stop fixing, split
   the abstraction (two_strike_split applied to review rounds, not just
   prompts).

## Heuristic to graduate

**Enumerative security grammar is scope creep with momentum.** When an
acceptance criterion says "enumerate the dangerous shapes," the review
loop becomes a fuzzer with unbounded ammunition and the artifact grows
one special case per round. The cure is decided at spec time, not fix
time: default-deny with a curated allowlist, or don't build the grammar
at all.

**Seed:** the guard's real adversary is not a malicious agent but an
honest one holding a shell — should enforcement-path terminal writes on
main simply be denied wholesale (no grammar, no verbs), with the
audited escape hatch as the only door, and would anyone actually be
inconvenienced?
