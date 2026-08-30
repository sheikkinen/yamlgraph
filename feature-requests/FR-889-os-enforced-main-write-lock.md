# Feature Request: OS-Enforced Main-Write Lock — Delete the Grammar

**Priority:** HIGH
**Type:** Refactor
**Status:** ENFORCED 2026-08-30 (session lane ccd5fb52; RED 21608433, GREEN d0066cfb; PR pending — C-6 human review required before merge). Previously: Judged (APPROVED WITH REVISIONS 2026-08-25, R-1..R-6 folded); amended 2026-08-30 by operator direction — §4 scope additions (CLAUDE.md truth, terminal venv, FR-902 flag retirement, docs-PR auto-merge deadlock cure)
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

- `lock-main`: **owner-only `chmod -R u-w`** (R-1: preserves group/other
  and executable bits by construction — no manifest needed, no blanket
  widening possible on unlock via `u+w`) on
  `yamlgraph/ tests/ scripts/ capabilities/ .github/hooks/` in the main
  checkout — with two carve-outs kept writable: `.github/hooks/logs/`
  (audit trail) and `.github/hooks/state/` (lock metadata, sentinels).
- `unlock-main`: `chmod -R u+w` on the same roots, writes an audit row
  (`fr889-main-unlock`) and an unlock-age marker.
- **State contract (R-3):** marker `.github/hooks/state/main-lock.json`
  ({state: locked|unlocked, ts, by}) — survives `chmod -R` (carve-out);
  `lock-main` and `unlock-main` are idempotent; `sync` relocks in a
  trap/finally path on BOTH pull success and failure; `now.py` reads the
  marker read-only and flags stale unlocked state with age
  (flag-not-fix, orphan-board style).
- `sync`: `unlock-main` → `git pull --ff-only` → `lock-main` (trap
  guarantees relock) — the one legitimate route for main enforcement-tree
  updates. Release flow uses the same verb.
- **Lock-mutator fence (R-2, the ONLY terminal check this FR keeps):**
  raw `chmod`/`chflags`/`setfacl` targeting the five governed roots on
  the main checkout are denied with the cure
  `scripts/worktree.sh unlock-main` (audited route). Verbs-only over five
  fixed roots — mechanically prevented from growing into a write-shape
  grammar by the R-6 structural test. Without this fence the self-service
  `chmod` would silently bypass the audited unlock; with it, the escape
  hatch is the only door, as claimed.
  **Allowed escapes (operator decision, 2026-08-30): `git` and `sudo`.**
  `git` commands are never fenced (git manages tracked modes as data;
  actual writes are the kernel's problem), and `sudo`-prefixed forms
  pass — sudo requires the human's password, so a sudo permission
  change is human-authorized by construction.
- Worktrees: `git worktree add` produces writable trees naturally; no
  change.
- **Ergonomics under lock (R-4, smoke-witnessed):** Python import/pytest
  (with `PYTHONDONTWRITEBYTECODE=1` documented if required), hook test
  execution, `git status`/`git diff`, docs-lane `git add`, and
  `worktree.sh new` all function on locked main.

### 2. The deletion (the point)

- Remove the entire terminal write-grammar from Check 7 (redirects, tee,
  cp/mv, sed, wrappers, interpreter paths — all of it). Terminal writes
  are the kernel's problem now. **R-6: deletion is witnessed
  structurally** — a test fails if any terminal write-target analyzer
  (redirect/tee/cp/mv/sed-i/interpreter/direct-writer parsing) remains in
  `pre-command-guard.sh`; the R-2 lock-mutator fence is the sole
  permitted terminal check. FR-888's grammar tests are rewritten into
  OS-lock witnesses, never kept as parser tests.
- Keep the **edit-tool** path check (create_file / replace / apply_patch)
  solely for UX: its denial carries the executable worktree cure. Extract
  it from the heredoc into `.github/hooks/scripts/checks/main_write.py`
  (existing `python-checks.sh` dispatch pattern), lintable and
  size-gated.
- `FR888_ALLOW_MAIN=1` escape retires for terminal commands (use
  `unlock-main`, which is audited and board-visible); stays for edit
  tools.
- **Boundary (R-5):** FR-889 may update runbook text and add interface
  smoke tests proving `sync` is the main-update route; it must NOT alter
  release versioning, rollout-watch behavior, merge flow, branch
  protection, or FR-885 teardown logic unless a failing interface test
  proves the lock broke an approved contract.

### 3. The gate repair

- Widen the file-size pre-commit gate to `scripts/**`, `.github/**`
  and `*.sh` (post-mortem finding: enforcement infrastructure was
  self-exempt).

### 4. Scope additions (operator-directed, 2026-08-30, pre-enforcement)

Added after judgement by operator instruction; the judge re-confirms or
trims these at enforcement kickoff. All three ride the same subtraction
principle the verdict endorsed: observe at the boundary, delete the
predictions.

- **4a. CLAUDE.md truth update.** The "Branch Protection" section
  ("Default flow: single dev, push to main directly", verified
  2026-08-18) predates FR-888 and this FR. Rewrite it to the actual
  post-lock model: enforcement-class writes route worktree → PR →
  auto-squash-merge (required checks bind); docs-class and operator
  maintenance use `sync`/`unlock-main`. This is documentation truth,
  not a merge-flow change — R-5 boundary respected.
- **4b. Terminal venv activation.** Tool-spawned terminals get bare
  zsh; the shared venv is never on PATH (witnessed 2026-08-30: commit
  failed with `pre-commit not found`, forcing `PATH=…/.venv/bin`
  prefixes on every hook-bearing command). Lanes already symlink
  `.venv`/`.env` to the main checkout, so a static workspace setting is
  safe for all sessions: commit `.vscode/settings.json` with
  `terminal.integrated.env.osx` prefixing `${workspaceFolder}/.venv/bin`
  to PATH.
- **4c. Retire the FR-902 red-herring flags (evaluate, then delete).**
  Check 8's predictive heuristics rule on the hook payload `cwd`, which
  audit evidence shows is always the workspace folder — never the
  persistent terminal's actual cwd. False-positive classes witnessed
  across three sessions (FR-925 enforce session: 4 escapes; session
  6feda07b 2026-08-30: 5 firings incl. in-lane `git commit`, in-lane
  `rm`, and an escape genuinely set but denied by the position-0
  `FR902_ALLOW_OUTSIDE=1` regex). Candidates for deletion under the
  R-6 subtraction: the git-writes-land-at-cwd target heuristic, the
  `python3 -c`-writes-at-cwd heuristic, and the position-0 escape
  match (reuse the segment tokenizer that already strips env prefixes).
  Keep explicit-path lane checks (edit tools, resolvable command
  arguments). Observed cost of inaction: agents learn to prefix the
  escape reflexively — including on read-only commands — converting the
  OVERRIDE audit stream into noise.
- **4d. Cure the docs-PR auto-merge deadlock.** Witnessed on PR #501
  (2026-08-30): the docs-only path filter (`changes` job) skips the
  test matrix, but `test (3.11)`/`test (3.13)` are required contexts —
  skipped-by-filter jobs never report, so `gh pr merge --auto` waits
  forever and every docs-class PR through the FR-888 route needs an
  admin merge. That makes the sanctioned route silently degrade to the
  bypass. Cure (pick one at enforcement): (i) an always-reporting no-op
  `test (3.11)`/`test (3.13)` success job when the path filter skips
  the real matrix (GitHub's documented pattern for required checks +
  path filters), or (ii) drop the matrix contexts from required checks
  — defensible since `enforce_admins` is off and the single-dev flow
  bypasses them anyway. Option (i) preserves the gate for
  enforcement-class PRs and is the default choice.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: One terminal write witness to a governed path on locked main
      fails with filesystem permission denial, tree unchanged; test does
      not depend on the deleted grammar
- [ ] AC-02: `lock-main`/`unlock-main` idempotent; unlock audited
      (`fr889-main-unlock`); state under `.github/hooks/state/`; exec
      bits preserved; no group/world write bits added
- [ ] AC-03: `sync` = unlock → `git pull --ff-only` → relock; relocks on
      pull failure too; docs lane writable throughout
- [ ] AC-04: Edit-tool writes on locked main denied by the extracted
      lintable Python check with executable cure; identical writes in
      linked worktrees allowed
- [ ] AC-05: Raw permission-mutating commands (`chmod`/`chflags`/
      `setfacl`) targeting governed roots on main are denied by the
      narrow R-2 fence — tested; fence recognizes verbs, never write
      shapes; `git` and `sudo` forms pass (operator-decided escapes)
- [ ] AC-06: Old terminal write grammar removed; structural test fails if
      redirect/tee/cp/mv/sed-i/interpreter/direct-writer target parsing
      remains outside the R-2 fence
- [ ] AC-07: Hook suite green with grammar tests retired/rewritten;
      `pre-command-guard.sh` below the widened size gate; heredoc count
      decreases by ≥1
- [ ] AC-08: Locked-main smoke: Python import/pytest, hook tests,
      `git status`/`git diff`, docs-lane `git add`, `worktree.sh new` all
      function; bytecode suppression documented if used
- [ ] AC-09: `.github/hooks/logs/` and `.github/hooks/state/` writable
      under lock — audit and state writes tested
- [ ] AC-10: `now.py` reports unlocked main with age from the marker,
      read-only, never fixes
- [ ] AC-11: Widened size gate covers `scripts/**`, `.github/**`, `*.sh`
      with no hook-infrastructure exemption
- [ ] AC-12: Changelog fragment; diary reflection
- [ ] AC-13 (4a): CLAUDE.md Branch Protection section describes the
      post-FR-888/889 flow; no "push to main directly" default claim
      survives for enforcement-class work
- [ ] AC-14 (4b): `.vscode/settings.json` committed with venv PATH for
      tool-spawned terminals; a fresh terminal resolves `pre-commit`
      and `pytest` from the repo venv without manual prefixes
- [ ] AC-15 (4c): FR-902 Check 8 cwd-proxy heuristics dispositioned —
      each either deleted (with its false-positive class witnessed by a
      test that now passes) or retained with a written reason; the
      position-0 escape regex is replaced by tokenizer-based
      recognition; genuinely out-of-lane writes remain denied
- [ ] AC-16 (4d): a docs-only PR auto-merges without admin override —
      required `test (3.11)`/`test (3.13)` contexts report success (or
      are removed from the required set with the decision recorded);
      enforcement-class PRs still run the real matrix

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
3. (4c) Does the PreToolUse payload `cwd` follow the terminal's spawn
   cwd, or is it always the workspace folder? All evidence to date comes
   from terminals spawned at the root. One experiment — spawn a terminal
   in a lane, run a write, read the audit row — decides whether lane-cwd
   spawning could cure the false positives without touching the guard.

## Alternatives Considered

Beyond the tool-space table: **do nothing** (grammar is merged and green)
— rejected: the post-mortem shows maintenance cost compounds per bypass
found, and the witnessed git-index vector remains open. **Deny-by-default
verb allowlist** (post-mortem remediation #1) — strictly better than the
grammar but still a parser in the deny path; OS lock obsoletes it.

## Implementation Record (2026-08-30)

All ACs green: 70/70 FR-889 tests, full hook suite 251 passed, unit suite
6181 passed. Guard at exactly 450 lines, one heredoc remaining (FR-767).

**Decisions / deviations:**
- **R-2 operator amendment (2026-08-30):** lock-mutator fence escapes —
  `git` commands are NEVER fenced; `sudo`-prefixed segments pass
  (human-authorized). Env-prefixes (`FOO=1 chmod …`) are stripped and
  still fenced.
- **AC-11 as ratchet:** widened size gate shipped as
  `scripts/size_gate.py` with a shrink-only BASELINE dict for nine
  existing oversize files (guard itself NOT baselined — it must stay
  ≤450). Pre-commit `file-size-gate` entry now dispatches to it (py+sh).
- **§4d cure = option (i):** the required `test (3.11/3.13)` contexts now
  always report — job-level `if` removed, real steps gated per-step, a
  docs-only no-op step reports the conclusion. No branch-protection
  settings change needed.
- **AC-07 via extraction:** lockdown-status summary moved to
  `checks/audit_status.py` to fit the 450-line budget.
- **CONF-441:** S603 confession for the git plumbing extracted into
  `checks/main_write.py`.
- **Live-guard evidence:** six false-positive denials by the OLD grammar
  during this very enforcement, recorded in
  `docs/diary/2026-08-30-fr889-deleting-the-grammar.md` — the empirical
  case for the deletion.

**Post-merge rollout:** run `scripts/worktree.sh lock-main` on the real
main checkout after the squash merge lands.

## Related

- `docs/analysis-fr888-post-mortem-2026-08-25.md` (the condemnation)
- FR-888 (Completed — the mechanism this replaces/simplifies)
- FR-885 (watcher; unaffected — teardown interface unchanged)
- FR-902 / FR-925 (lane guard; §4c retires its cwd-proxy heuristics —
  the false-positive classes FR-925's judgement C-5 parked)
- `docs/diary/diary-2026-08-30-the-lane-the-guard-could-not-see.md`
  (payload-cwd evidence), `docs/diary/diary-2026-08-30-the-gate-that-guarded-a-different-number.md`
  (enforcement-ring overlap audit)
- Scripture: `regex_fourth_exclusion`, `two_strike_split`,
  `infrastructure_self_exempt`, `boring_enforcement`
