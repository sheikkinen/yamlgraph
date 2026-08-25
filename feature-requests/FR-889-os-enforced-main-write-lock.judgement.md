# Judgement: FR-889 OS-Enforced Main-Write Lock — Delete the Grammar

**Prior art:** dispositioned in the FR (FR-888 post-mortem remediation; operator-proposed mechanism; tool-space table incl. rejected chown/uchg/LLM/CP candidates).

**Verdict:** APPROVED WITH REVISIONS — replacing the terminal write grammar with an OS permission boundary is the right remediation, but authority activates only after the FR defines reversible permissions, closes the raw-`chmod` escape, and proves the lock/unlock/sync state machine without expanding into unrelated workflow policy.

**Reviewed against:** `feature-requests/FR-889-os-enforced-main-write-lock.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `docs/analysis-fr888-post-mortem-2026-08-25.md`; `feature-requests/FR-888-main-write-guard-worktree-route.md`; `feature-requests/FR-888-main-write-guard-worktree-route.judgement.md`; `feature-requests/FR-885-deploy-watch-outside-session.md`; `feature-requests/FR-885-deploy-watch-outside-session.judgement.md`; `scripts/worktree.sh`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/hooks/tests/test_main_write_guard.py`; `.pre-commit-config.yaml`; `scripts/vscode/now.py`; `.github/hooks/README.md`.

## What is sound

The problem is real and priced. The FR-888 post-mortem records a 601-line bash/heredoc guard, 5 review rounds, 14 defect classes, and no bloat gate catching it (`docs/analysis-fr888-post-mortem-2026-08-25.md:12-20`). It also identifies the root failure as an unbounded write-shape grammar where every reviewer probe was a genuine bypass (`docs/analysis-fr888-post-mortem-2026-08-25.md:41-50`) and notes that the grammar missed the actually witnessed git-index vector (`docs/analysis-fr888-post-mortem-2026-08-25.md:66-79`).

The proposed strategic move matches repo doctrine: the FR moves enforcement to the write boundary instead of downstream prediction (`feature-requests/FR-889-os-enforced-main-write-lock.md:24-36`), which aligns with `downstream_fix`, `regex_fourth_exclusion`, `two_strike_split`, and `infrastructure_self_exempt` in Scripture (`.github/copilot-instructions.md:71-81`, `.github/copilot-instructions.md:115-116`). It is also subtractive: deleting the terminal grammar and extracting the edit-tool check into lintable Python directly addresses the post-mortem finding that Python-in-bash heredocs are invisible to quality gates (`docs/analysis-fr888-post-mortem-2026-08-25.md:33-39`; `feature-requests/FR-889-os-enforced-main-write-lock.md:93-105`).

The solution builds on already-live worktree and hook surfaces instead of inventing a parallel system. FR-888 is completed and records the worktree route as live on main (`feature-requests/FR-888-main-write-guard-worktree-route.md:3-5`); `scripts/worktree.sh` already has the `new`, `rm`, and `rm-safe` verbs, `.env` symlink, final `cd` output, and safe removal path (`scripts/worktree.sh:12-19`, `scripts/worktree.sh:155-182`, `scripts/worktree.sh:297-358`); the existing test suite already names the grammar tests to retire and lock/worktree witnesses to preserve (`.github/hooks/tests/test_main_write_guard.py:178-356`, `.github/hooks/tests/test_main_write_guard.py:461-527`).

Strategic classification: **process/enforcement primitive**. This is not product functionality and not pattern documentation; it changes the local enforcement boundary for every future enforcement-class edit on the main checkout. The scope is appropriately one concern: replace a brittle predictive grammar with a filesystem lock, keep only edit-tool UX denial, and bring enforcement infrastructure under normal size/lint gates.

## Required revisions

### R-1: Define reversible permission semantics without widening modes

Replace "unlock-main reverses it" with a mechanical contract for how modes are restored. `chmod -R a-w` is precise on lock, but a naive reverse such as `chmod -R a+w` would make files and directories world-writable and silently widen committed file modes. Fold in one of these contracts:

1. `lock-main` records a mode manifest for every governed path before removing write bits, and `unlock-main` restores from that manifest; or
2. the lock uses owner-only mutations (`u-w` / `u+w`) and explicitly preserves group/other bits and executable bits.

The acceptance tests must assert that `sync` and `unlock-main` do not change executable bits on scripts or introduce group/world write bits on files that did not already have them. This matters because the FR's lock targets `scripts/` and `.github/hooks/` (`feature-requests/FR-889-os-enforced-main-write-lock.md:77-87`), where execute permissions are functional contract.

### R-2: Close or explicitly fence raw permission-change bypasses

State the threat model and enforcement rule for direct terminal commands that alter the lock itself. The FR says terminal writes become "the kernel's problem" and the grammar is deleted (`feature-requests/FR-889-os-enforced-main-write-lock.md:93-105`), but the selected mechanism is same-owner `chmod`, and the FR explicitly rejects `chown` because `chmod` remains self-service (`feature-requests/FR-889-os-enforced-main-write-lock.md:71-72`). That means an agent can bypass the audited `unlock-main` path with a raw `chmod +w` followed by a write unless this is fenced.

Fold this into the FR: raw `chmod`, `chflags`, `setfacl`, or equivalent permission-changing commands targeting governed lock roots on the main checkout are denied by a small non-write grammar, or the FR must downgrade its claims from "unfuzzable" and "audited escape hatch as the only door" to "soft lock for accidental writes." If the former is chosen, tests must prove the permission-change denial does not recreate the deleted terminal write grammar; it should recognize only lock-mutating verbs over the five governed roots, not enumerate write shapes.

### R-3: Specify lock state files, carve-outs, and stale-state recovery

Define exactly where the lock manifest/unlocked flag lives, how it survives `chmod -R`, and how stale state is handled. The FR reserves `.github/hooks/logs/` and `.github/hooks/state/` as writable carve-outs (`feature-requests/FR-889-os-enforced-main-write-lock.md:79-84`), but does not define the filenames, JSON shape, or recovery behavior if a command dies after `unlock-main` and before `lock-main`.

Fold in a state contract: audited rows stay under `.github/hooks/logs/`; lock metadata and unlock-age marker stay under `.github/hooks/state/`; `lock-main` is idempotent; `unlock-main` is idempotent; `sync` relocks in a trap/finally path after a failed `git pull --ff-only`; and `now.py` reports stale unlocked state from the marker. `scripts/vscode/now.py` already has an orphan-worktree board pattern that flags instead of fixing (`scripts/vscode/now.py:41-107`), so the unlocked-state line should follow that read-only board style.

### R-4: Preserve git and developer ergonomics under the lock with explicit smoke witnesses

Add concrete witnesses for ordinary read-only development commands under the locked main checkout. AC-06 currently says one full unit run on locked main proves no `__pycache__` write is needed (`feature-requests/FR-889-os-enforced-main-write-lock.md:129-130`), but the lock covers `yamlgraph/`, `tests/`, and `scripts/` (`feature-requests/FR-889-os-enforced-main-write-lock.md:77-80`), while repo doctrine requires tests and tooling to continue as operational truth (`.github/copilot-instructions.md:221-225`). Fold in explicit smoke checks for:

- Python import/pytest under locked main;
- hook test execution under locked main;
- `git status`, `git diff`, and `git add` of docs-lane files under locked main;
- `scripts/worktree.sh new` under locked main.

The enforcer may set `PYTHONDONTWRITEBYTECODE=1` for the locked-main smoke if needed, but the FR must say so rather than leaving the runtime assumption implicit.

### R-5: Keep FR-885/release integration as interface tests, not implementation authority

The FR says release flow and FR-885 are affected or retained (`feature-requests/FR-889-os-enforced-main-write-lock.md:85-90`, `feature-requests/FR-889-os-enforced-main-write-lock.md:139-140`, `feature-requests/FR-889-os-enforced-main-write-lock.md:165-165`). FR-885 is judged and fenced so teardown only executes under separately granted FR-888 authority (`feature-requests/FR-885-deploy-watch-outside-session.md:103-107`, `feature-requests/FR-885-deploy-watch-outside-session.judgement.md:63-72`). FR-889 must not become a release-system or watcher implementation.

Fold in this boundary: FR-889 may update runbook text and add interface smoke tests proving `sync` is the route for main updates, but it may not alter release versioning, rollout-watch behavior, GitHub merge flow, branch protection, or FR-885 watcher teardown logic unless a failing interface test demonstrates the lock broke those already-approved contracts.

### R-6: Update acceptance criteria to test the absence of the deleted grammar

AC-05 says the hook suite is green "with the grammar deleted" and heredoc count decreases (`feature-requests/FR-889-os-enforced-main-write-lock.md:126-128`), but it does not mechanically prevent a future enforcer from replacing the old grammar with a smaller new grammar. Add a structural assertion: `pre-command-guard.sh` must contain no terminal write-target analyzer for redirects, `tee`, `cp/mv`, `sed -i`, interpreter one-liners, direct writers, or path-materialization. The only allowed terminal check related to this FR is the narrow permission-mutator fence chosen in R-2, if any. Existing FR-888 grammar tests in `.github/hooks/tests/test_main_write_guard.py:178-356` must be deleted or rewritten into OS-lock witnesses, not kept as parser tests.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-889-os-enforced-main-write-lock.md`: fold R-1 through R-6, implementation status, decisions, and deviations. |
| D-2 | `scripts/worktree.sh`: add `lock-main`, `unlock-main`, and `sync` verbs; implement idempotent lock/unlock, audit, state marker, and safe relock semantics. |
| D-3 | `.github/hooks/scripts/pre-command-guard.sh`: remove the FR-888 terminal write grammar; keep only non-terminal existing guards plus any narrow lock-mutator denial authorized by R-2. |
| D-4 | `.github/hooks/scripts/checks/main_write.py` or equivalent lintable Python module: edit-tool main-checkout enforcement-path denial and friendly worktree cure. |
| D-5 | `.github/hooks/tests/`: replace FR-888 grammar tests with OS-permission lock, edit-tool denial, worktree allowance, unlock audit, sync relock, permission-preservation, carve-out, and stale-unlock board tests. |
| D-6 | `.pre-commit-config.yaml` and related hook docs: widen file-size/quality gates to enforcement infrastructure as specified. |
| D-7 | `scripts/vscode/now.py`: add read-only unlocked-main status line using `.github/hooks/state/` metadata only. |
| D-8 | `.github/hooks/README.md` or adjacent runbook: document the lock model, sync route, unlock audit, carve-outs, and allowed docs lane. |
| D-9 | Changelog fragment and `docs/diary/` reflection. |

Not authorized: changing YAMLGraph runtime behavior; changing graph-authoring/judge/review doctrine; adding daemon processes; changing branch protection or GitHub repository settings; implementing rollout watcher behavior; changing release versioning semantics; moving docs/feature-request/changelog work off main; adding broad shell parsing beyond the lock-mutator fence chosen in R-2; weakening existing Co-authored-by, `--no-verify`, multiline commit, pytest pipe, branch-creation, or graph-authoring guards.

## Revised acceptance criteria

- [ ] AC-01: With main locked, one terminal write witness to a governed enforcement path fails with filesystem permission denial and leaves the target tree unchanged; the test does not depend on the old terminal write grammar.
- [ ] AC-02: `scripts/worktree.sh lock-main` and `unlock-main` are idempotent, audit unlocks with reason `fr889-main-unlock`, store state under `.github/hooks/state/`, preserve executable bits, and do not add group/world write bits that were absent before locking.
- [ ] AC-03: `scripts/worktree.sh sync` performs `unlock-main` -> `git pull --ff-only` -> `lock-main`, relocks even when pull fails, and leaves docs-lane paths (`docs/`, `feature-requests/`, `changelog/`) writable.
- [ ] AC-04: Edit-tool writes on locked main to governed enforcement paths are denied by the extracted lintable Python check with an executable worktree cure; byte-identical writes in linked worktrees are allowed.
- [ ] AC-05: Raw permission-mutating terminal commands targeting governed lock roots on main are either denied by the narrow R-2 fence and tested, or the FR text explicitly classifies the lock as accidental-write protection rather than an audited-only escape boundary.
- [ ] AC-06: The old FR-888 terminal write grammar is removed from `pre-command-guard.sh`; structural tests fail if redirect/`tee`/`cp`/`mv`/`sed -i`/interpreter/direct-writer target parsing remains except for the R-2 lock-mutator fence.
- [ ] AC-07: Hook suite passes with grammar tests retired or rewritten; `pre-command-guard.sh` is below the widened size gate; heredoc Python count decreases by at least one.
- [ ] AC-08: Locked-main smoke proves Python import/pytest, hook tests, `git status`, `git diff`, docs-lane `git add`, and `scripts/worktree.sh new` still function; if bytecode suppression is required, the command and rationale are documented.
- [ ] AC-09: `.github/hooks/logs/` and `.github/hooks/state/` remain writable while the rest of `.github/hooks/` is locked; tests prove audit and state writes work under lock.
- [ ] AC-10: `scripts/vscode/now.py` reports unlocked main with age from the state marker and never attempts to fix it.
- [ ] AC-11: Widened file-size gate covers `scripts/**`, `.github/**`, and `*.sh` without exempting hook infrastructure.
- [ ] AC-12: Changelog fragment and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-6 into FR-889 before implementation authority activates. | GATE |
| C-2 | Lock/unlock must preserve existing file modes; no blanket permission widening is allowed. | GATE |
| C-3 | The audited unlock path must not be silently bypassable by raw permission-mutating terminal commands unless the FR explicitly narrows its threat model to accidental-write protection. | GATE |
| C-4 | `sync` must relock on both success and failure paths. | GATE |
| C-5 | The terminal write grammar must be deleted rather than renamed or reimplemented in a smaller form. | GATE |
| C-6 | Enforcement-infrastructure changes require human review before being treated as merged policy. | GATE |
| C-7 | Existing unrelated PreToolUse guards must not be weakened. | GATE |

Authority granted: after R-1 through R-6 are folded into the FR, the enforcer may replace the FR-888 terminal write grammar with an OS permission lock for main, keep a lintable edit-tool UX denial, add lock/unlock/sync worktree verbs and board visibility, widen enforcement-infrastructure size gates, and update tests/docs within the frozen surfaces above.
