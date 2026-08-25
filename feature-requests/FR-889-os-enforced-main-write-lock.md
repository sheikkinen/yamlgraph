# Feature Request: OS-Enforced Main-Write Lock — Delete the Grammar

**Priority:** HIGH
**Type:** Refactor
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-25
**First consumer / first event:** the next terminal command that would
write an enforcement path on main — it fails at the syscall with EACCES
instead of being parsed by a 250-line grammar.

**Prior art:** FR-888 (Completed 2026-08-25) built the current guard; its
post-mortem (`docs/analysis-fr888-post-mortem-2026-08-25.md`) condemns the
enumerative terminal grammar (5 review rounds, 14 bypass classes, 601-line
hook, `regex_fourth_exclusion` ignored at round 2) and this FR is its
remediation queue items 1–3 unified under a stronger mechanism. The
operator proposed the winning candidate ("simply changing the owner for
the folder"). FR-888's edit-tool denial, worktree lifecycle (`new`,
`rm-safe`), escape-hatch audit shape, and 181-test suite are retained.
No graveyard hit proposes OS-permission enforcement.

## Summary

Stop *predicting* writes by parsing shell; make the OS *refuse* them.
Enforcement-class directories on the main checkout become unwritable
(`chmod -w` on directories); worktrees are fresh checkouts and stay fully
writable. The 250-line terminal write-grammar is deleted. The PreToolUse
guard shrinks to the edit-tool path check (kept only for its friendly
denial message — the cure delivery), extracted from bash heredoc into a
real Python module.

## Value Statement

The guard becomes unfuzzable: enforcement moves from a grammar over an
undecidable language (shell) to the boundary where every write actually
happens (the syscall). Review loops over write shapes end permanently.

## Problem

The FR-888 post-mortem, condensed:

1. Parsing shell commands to predict writes is a losing game — every
   review round found a new shape (`time` prefix, whitespace, `Move to:`
   hunks, `touch`/`mkdir`, interpreter one-liners), and the grammar can
   never be complete because the language is not statically analyzable.
2. The witnessed incident vector — `git add -A` / `commit -a` sweeping
   files another session wrote — is **not covered** by the grammar at all.
   With read-only trees it is covered *transitively*: files that cannot be
   written cannot be swept.
3. The 601-line bash+heredoc hook is exempt from every quality gate.

## Ideal Result

`echo x > yamlgraph/f.py` on main: **Permission denied** — from the
kernel, zero hook lines involved. An edit-tool write on main: denied by a
30-line Python check whose message carries the worktree cure. `git pull`
on main: works via one sync verb. A worktree: everything writable, no
ceremony. The hook file count of lines goes down by ~300 and everything
that remains is lintable Python.

## Tool-Space Analysis (operator-requested, honest verdicts)

| Candidate | Verdict | Why |
|---|---|---|
| Shell regex grammar (status quo) | ☠ condemned | Post-mortem: undecidable prediction, unbounded fuzz surface |
| Python rewrite of the grammar | ✗ | Better substrate, same undecidable problem — language change doesn't fix the game |
| Constraint programming | ✗ | There is no constraint model of "what a shell command writes" short of executing it; static analysis of shell is the same trap in a fancier costume |
| LLM classifier per tool call | ✗ | ~1s latency on every command, nondeterministic enforcement (`plausible_wrong_answer` in a guard), model-in-enforcement is doctrinally adversarial |
| Trained tiny GPT | ✗ | Training corpus = the fuzz corpus we failed to enumerate; probabilistic denial; absurd ops burden for a hook |
| Power Apps / quantum | ✗ | Filed under morale |
| **OS permissions (dir `chmod -w`)** | ✅ **selected** | Enforcement at the write boundary itself; covers every shape by construction incl. git index sweeps; zero parse cost; standard, auditable, reversible |
| Separate owner (`chown` + sudo) | ✗ (fallback) | Stronger but needs sudo for every unlock; `chmod` by the same owner is self-service and sufficient — upgrade path if chmod proves too soft |
| `chflags uchg` | ✗ | macOS-only, blocks even the audited unlock path ergonomics; overkill |

## Proposed Solution

### 1. The lock (`scripts/worktree.sh` verbs, ~40 lines)

- `lock-main`: `chmod -R a-w` **directories and files** under
  `yamlgraph/ tests/ scripts/ capabilities/ .github/hooks/` in the main
  checkout — with two carve-outs kept writable: `.github/hooks/logs/`
  (audit trail) and `.github/hooks/state/` (sentinels).
- `unlock-main`: reverses it, writes an audit row
  (`fr889-main-unlock`), and flags the unlocked state.
- `sync`: `unlock-main` → `git pull --ff-only` → `lock-main` — the one
  legitimate reason main's enforcement tree changes. Release flow uses
  the same verb.
- `now.py` board line when main is unlocked (age of unlock) — same
  flag-not-fix pattern as the orphan board.
- Worktrees: `git worktree add` produces writable trees naturally; no
  change.

### 2. The deletion (the point)

- Remove the entire terminal write-grammar from Check 7 (redirects, tee,
  cp/mv, sed, wrappers, interpreter paths — all of it). Terminal writes
  are the kernel's problem now.
- Keep the **edit-tool** path check (create_file / replace / apply_patch)
  solely for UX: its denial carries the executable worktree cure. Extract
  it from the heredoc into `.github/hooks/scripts/checks/main_write.py`
  (existing `python-checks.sh` dispatch pattern), lintable and
  size-gated.
- `FR888_ALLOW_MAIN=1` escape retires for terminal commands (use
  `unlock-main`, which is audited and board-visible); stays for edit
  tools.

### 3. The gate repair

- Widen the file-size pre-commit gate to `scripts/**`, `.github/**`
  and `*.sh` (post-mortem finding: enforcement infrastructure was
  self-exempt).

## Acceptance Criteria (non-enumerative — the post-mortem lesson)

- [ ] AC-01: With main locked, ONE witness terminal write to a locked
      path fails with EACCES and the tree is unchanged — no hook
      involvement asserted (the shape doesn't matter; that's the design)
- [ ] AC-02: `sync` updates main from origin and leaves it locked;
      the docs lane (docs/, feature-requests/, changelog/) remains
      writable throughout
- [ ] AC-03: Edit-tool write on locked main is denied by the extracted
      Python check with the executable cure; the same write in a worktree
      is allowed (existing witnesses keep passing)
- [ ] AC-04: `unlock-main` audits and the board flags unlocked state with
      age; `lock-main` clears the flag
- [ ] AC-05: Hook suite green with the grammar deleted; the guard shell
      shrinks below the (now widened) size gate; heredoc Python count in
      `pre-command-guard.sh` decreases by at least one
- [ ] AC-06: pytest/imports on locked main still function (no `__pycache__`
      write needed — witnessed by one full unit run on locked main)
- [ ] AC-07: Changelog fragment; diary reflection

## Blast Radius

`scripts/worktree.sh`, `.github/hooks/scripts/pre-command-guard.sh`
(shrinks), new `.github/hooks/scripts/checks/main_write.py`, hook tests
(grammar tests retire, lock tests arrive), `.pre-commit-config.yaml`
(size gate), `scripts/vscode/now.py` (one board line), hooks README
runbook section (rewrites to the lock model). Release flow: verify
`scripts/release.sh`-class operations work under `sync`.

## Open Questions (judge input wanted)

1. Does any legitimate main-lane automation write enforcement paths
   outside `sync`? (fr-board regen writes docs/ — unaffected; changelog
   freeze writes changelog/ — unaffected; release version-bump writes
   `pyproject.toml` — root file, currently OUTSIDE the locked set: keep
   it out or lock it?)
2. Lock granularity: `-R` on the five roots vs directories-only (files
   inherit protection from unwritable dirs for create/delete but not for
   in-place edits — `-R` both is safer, chosen by default).

## Alternatives Considered

Beyond the tool-space table: **do nothing** (grammar is merged and green)
— rejected: the post-mortem shows maintenance cost compounds per bypass
found, and the witnessed git-index vector remains open. **Deny-by-default
verb allowlist** (post-mortem remediation #1) — strictly better than the
grammar but still a parser in the deny path; OS lock obsoletes it.

## Related

- `docs/analysis-fr888-post-mortem-2026-08-25.md` (the condemnation)
- FR-888 (Completed — the mechanism this replaces/simplifies)
- FR-885 (watcher; unaffected — teardown interface unchanged)
- Scripture: `regex_fourth_exclusion`, `two_strike_split`,
  `infrastructure_self_exempt`, `boring_enforcement`
