# Feature Request: Shared-Repo Write Discipline — Skill Doctrine + Hermetic Adapter + Guard

**Status:** Proposed — judged APPROVED WITH REVISIONS 2026-08-23; R-1..R-5 folded 2026-08-23, awaiting human review of hook/doctrine changes (gate C-2) before enforcement
**Date:** 2026-08-23
**Author:** agent session (operator-directed reflection)

**Prior art:** `.github/skills/session-introspection/SKILL.md` (read-side situation awareness; names `one_session_one_repo` but prescribes no write rituals — this FR adds its write-side doctrine rather than a rival skill); `.github/skills/judge-fr/` + `.github/skills/review-pr/` (the doctrine + adapter + mechanical-guard pattern this FR instantiates); Scripture `one_session_one_repo` process entry (names the ritual but at summary altitude); FR-852 (sixth shape), FR-859/FR-860 (worktree-airlock regen, verified twice); ~~FR-784~~ CORRECTED per judgement R-1: `feature-requests/FR-784-playwright-network-sniff-utility.md` is a Playwright utility, not an interleave cure — the fourth-shape incident has no committed FR and is evidenced in the taxonomy table below; FR-767 (sentinel-armed PreToolUse guard precedent); FR-858 (Proposed — retires the committed fr-board, deleting the most contended generated artifact; this FR is complementary: it governs the *class* of shared-tree writes, not one artifact, and its doctrine must not assume the board survives); diary 2026-08-23-the-worktree-is-the-airlock.md (the reflection that motivated this FR). Disposition: no existing artifact provides repo-visible, enforceable write discipline for parallel sessions — the six-shape taxonomy lived only in per-machine agent memory, invisible to the chaplain, CI, other machines, and non-Copilot agents; it is graduated into this FR below (judgement R-1, C-6).

## Ideal Result

Any agent (human-driven session, chaplain, watcher2, a fresh machine with zero
local memory) that writes to this shared repo discovers the parallel-session
write rituals from the repo itself, runs hook-input-divergent generators
through one hermetic route, and is mechanically denied the operations that
caused all six recorded interleave incidents.

## Problem

Six named interleave shapes (foreign staged sweep, stash-pop clobber,
hook-input divergence, branch switch underfoot, mid-cycle sweep + phantom
drift, pathspec-vs-staged board drift) were diagnosed and cured across
FR-852/859/860 and undocumented incidents recorded in the taxonomy below —
but the cures lived in `/memories/repo/hook-lessons.md`,
which is **local agent memory**: per-machine, per-tool, uncommitted. The
chaplain, CI, sibling projects, and any agent without that memory file will
re-derive each shape by incident. Repo-scoped operating knowledge stored
outside the repo violates the boundary the Scripture itself names
(`workspace_is_not_boundary` corollary: memory visibility ≠ repo truth).

## Interleave-Shape Taxonomy (folded per judgement R-1)

This table is the committed evidence record. Shapes marked † had NO
committed evidence before this FR — the incident detail recorded here is
the primary source (judgement R-1 escape clause; C-6 satisfied by this
graduation).

| # | Shape | Failure mode | Committed evidence | Cure | Enforcing surface |
|---|-------|--------------|--------------------|------|-------------------|
| 1 | Foreign untracked sweep into pathspec commit | A sibling session concurrently staged its untracked file (a diary dated 2026-08-23); a hooks-vs-index race carried it into this session's `git commit --only` commit; repaired by `git reset --soft HEAD~1` + recommit | `docs/diary/2026-08-22-the-gate-that-audited-its-own-courtroom.md` (§ one_session_one_repo, strike again) | Post-commit `git show --stat` audit; structurally: private index per session | Guard D-5 (primary-checkout commit denial); doctrine commit ritual |
| 2† | Foreign stash-pop clobber | During the shape-6 incident (2026-08-22), a diagnostic `git stash --keep-index` was a silent no-op (nothing unstaged remained after the sibling's sweep), so the subsequent bare `git stash pop` popped a YEARS-OLD foreign stash (FR-643-era WIP) into the tree with UU conflicts, clobbering the index view | † recorded here; aftermath context in `docs/diary/diary-2026-08-22-fr852-preserve-the-briefs.md` | Never bare `git stash pop/apply`; push with a unique token, pop by exact `stash@{n}` after `git stash list`; never stash-diagnose — simulate in a worktree | Guard D-5 (explicit-stash-ref rule) |
| 3† | Hook-input divergence via stash | pre-commit stashes unstaged changes before hooks run; `fr-board-check` regenerates the board from that hook-time tree, so a sibling's UNSTAGED FR edits make working-tree regen ≠ hook-time regen — drift unfixable from inside the session (first hit ≈ 2026-08-07; staged-sibling variant = shape 5) | † recorded here; cure narrative in `docs/diary/2026-08-23-the-worktree-is-the-airlock.md` | Hermetic regen: HEAD worktree + explicit overlay | `scripts/hermetic.sh` (D-3) |
| 4† | Branch switch underfoot | A parallel session checked out `fix/fr-763-*` in the shared checkout; this session's `git commit && git push` intended for `main` landed and pushed on the foreign branch (≈ 2026-08-05..08) | † recorded here (no committed narrative exists) | `git branch --show-current` before every commit; structurally: linked worktrees have independent HEADs | Doctrine commit ritual; guard D-5 (primary-checkout denial removes the shared HEAD) |
| 5 | Pathspec board drift with staged sibling edits | Under `git commit --only <paths>`, hook-time tree = HEAD + pathspec files + untracked files (staged-but-unnamed sibling files revert to HEAD in the stash) — working-tree `--check` passing predicts nothing | Worktree-airlock cure executed and verified during FR-859 and FR-860 filings (2026-08-22); `docs/diary/2026-08-23-the-worktree-is-the-airlock.md` | Worktree airlock: regen inside `git worktree add /tmp/<view> HEAD` + overlay pathspec files | `scripts/hermetic.sh` (D-3) |
| 6 | Mid-cycle sweep + phantom drift | While this session looped on a "board drift" hook failure, a sibling committed the session's ENTIRE staged FR-852 work inside their FR-853/854 commit (`fc655173`) and pushed — the "drift" was HEAD moving underfoot, not a bad regen; cascaded into shape 2 | `feature-requests/FR-852-preserve-authoring-briefs.md`; `docs/diary/diary-2026-08-22-fr852-preserve-the-briefs.md` | On a repeated hook failure after a correct fix, run `git log --oneline -3` FIRST; structurally: private index per session | Doctrine diagnostic ritual; guard D-5 |

## Proposed Solution

Instantiate the judge/review pattern for shared-repo writes, homed in the
existing skill (Commandment 4 — conform before extending):

1. **Doctrine** — `.github/skills/session-introspection/doctrine.md`:
   the write-side contract. Contents graduated from local memory:
   - Commit ritual: `git branch --show-current` before every commit;
     pathspec commits (`git commit --only <paths>`) — scoped as a
     worktree/private-index ritual, since the primary checkout denies agent
     commits outright; unique repo-local message files
     (`./tmp/msg-<topic>.txt`, never a shared `./tmp/msg.txt`);
     `git show --stat` audit after; `git fetch` before every push.
     Doctrine reconciliation (judgement R-4): the Scripture convention
     line mandating shared `./tmp/msg.txt` is updated by D-7 to the
     unique-file rule — repo-local under `tmp/` (not `/tmp/`) so message
     provenance stays inside the workspace; no committed doctrine may
     require both forms.
   - Stash prohibition: never bare `git stash pop` in a shared tree; push
     with a unique token, pop by exact `stash@{n}` ref after `git stash list`
     verification; never stash-diagnose — simulate in a worktree.
   - The airlock procedure: any generator whose pre-commit hook regenerates
     from the working tree runs inside `git worktree add /tmp/<view> HEAD`
     + explicit overlay of the commit's pathspec files (the verified
     FR-859/860 recipe).
   - The six-shape taxonomy as an incident appendix (condensed, one
     paragraph per shape, cure cross-referenced to the rules above).
   - SKILL.md description updated so the trigger list includes write
     rituals, not just introspection.
2. **Adapter** — `scripts/hermetic.sh`: hermetic generator runner with a
   frozen interface (judgement R-2):

   ```
   scripts/hermetic.sh [--in <repo-rel-path>]... --out <repo-rel-path> [--out ...] -- <cmd> [args...]
   ```

   Contract (documented verbatim in `--help`, AC-04):
   - **Airlock**: `git worktree add --detach <tmpdir> HEAD` under
     `${TMPDIR:-/tmp}/hermetic-<pid>`; removed via EXIT trap
     (`git worktree remove --force`), success or failure.
   - **Input overlay**: (a) all currently staged files, discovered via
     `git diff --cached --name-only -z`, materialized from the INDEX
     (`git checkout-index`), plus (b) each `--in` path copied from the
     main working tree. Paths must be repo-relative; absolute paths and
     `..` escapes are rejected; a nonexistent `--in` is an error.
   - **Interpreter**: `PATH` prefixed with `<main-repo>/.venv/bin` so
     `python` resolves to the main repo's venv (FR-174/FR-199 worktree
     trap cure).
   - **On command failure** (nonzero exit): nothing is copied back; the
     main working tree is untouched; hermetic.sh exits with the command's
     code (C-5).
   - **On success**: ONLY `--out` paths are copied back. A declared
     output missing from the airlock is an error and aborts all copyback.
     Undeclared dirty airlock files (`git status --porcelain` minus
     declared outputs) are listed to stderr as a diagnostic and NEVER
     copied (C-4) — silent copyback would recreate the shared-tree hazard.
   - Sole sanctioned route for hook-input-divergent generators
     (`fr_board.py` while it exists per C-7, `aggregate_capabilities.py`,
     changelog aggregation), mirroring how `judge.sh`/`review.sh` are sole
     routes.
3. **Guard** — extend `.github/hooks/scripts/pre-command-guard.sh`,
   boundary-first (operator revision 2026-08-23: "should it start sooner —
   write to main prohibited"):
   - **Primary rule: agent commits in the primary checkout are denied.**
     Target resolution is explicit and FAIL-CLOSED (judgement R-3): the
     guard resolves which worktree a command targets by parsing plain
     `git commit`, `git -C <path> commit`, and `cd <path> && git commit`
     forms against the command's working directory. The resolved root's
     `.git` decides: directory → primary → DENY; file → linked worktree →
     ALLOW. Any shape the parser cannot resolve (variable paths, nested
     subshells, multiple `cd`) → DENY with an ambiguous-target reason and
     a message routing to `scripts/worktree.sh` — never approve on parse
     failure (C-3). Audit-logged with stable reason codes:
     `primary_commit_deny`, `ambiguous_commit_target`, `stash_bare_deny`,
     `linked_commit_allow`. This makes shapes 1, 4, 5,
     and 6 structurally impossible instead of individually parried;
     PreToolUse binds agents only, so the operator's push-to-main flow is
     untouched.
   - Defense-in-depth (still reachable inside a private worktree): bare
     `git stash pop` / `git stash apply` without an explicit `stash@{n}`
     ref remains denied.
   - Index-sweep rules (`git add -A/.`, `git commit -a`) are DROPPED —
     they were choreography around the shared index the primary rule
     removes.
   - Known residual (named, not solved here): file EDITS still land in
     the shared tree while sessions are anchored to the main folder; the
     commit denial forces worktree adoption over time but cannot see
     edits. Doctrine mandates opening writing sessions in worktrees;
     mechanical edit-guarding is out of scope.
4. **Rollout gate (judgement R-5)** — the commit denial does NOT activate
   on merge. Sequence: (1) land the guard in WARN mode — would-deny
   decisions audit-logged to `.github/hooks/logs/audit.jsonl` without
   denying; (2) run at least one chaplain/watcher cycle (or a replay of
   their recorded command logs) and record findings in this FR; any
   legitimate primary-checkout automation is moved to worktrees or
   explicitly recorded as out of scope; (3) human reviews the hook +
   doctrine diff (C-2) — result recorded in Implementation Status; only
   then flip WARN to DENY.
5. **Memory disposition (subtraction)** — after the doctrine lands, the
   interleave content of local `hook-lessons.md` is superseded; the memory
   file shrinks to a one-line pointer at the doctrine. Repo is truth,
   memory is cache.

## Non-Goals / Out of Scope

- Retiring the fr-board (FR-858 owns that; this FR's doctrine and adapter
  must work whether or not the board survives).
- Session-locking or preventing parallel sessions (the operator runs them
  deliberately; the goal is safe interleaving, not exclusion).
- Guarding `git push`/`git fetch` ordering (advisory in doctrine only —
  push races serialize at origin, where git fails loudly; the silent
  failure class is the shared index/tree, which the primary rule removes).
- Mechanically guarding file edits in the primary checkout (PostToolUse
  edit-warning is a candidate follow-up FR once worktree-per-session is
  the observed norm).

## Deliverables (frozen by judgement)

- D-1: `.github/skills/session-introspection/doctrine.md` — committed
  write-side doctrine including the six-shape taxonomy and cures (R-1 folded)
- D-2: `.github/skills/session-introspection/SKILL.md` — trigger/description
  update advertising write rituals as well as read-side awareness
- D-3: `scripts/hermetic.sh` — one hermetic generator runner with the frozen
  R-2 contract
- D-4: hermetic.sh tests (existing script-test pattern): worktree creation,
  explicit overlay, declared-output copyback, undeclared-file refusal,
  failure isolation, cleanup, surviving-generator witness
- D-5: `.github/hooks/scripts/pre-command-guard.sh` — primary-checkout
  commit denial (fail-closed target resolution) and explicit-stash-ref rules
  only, audit-logged, denial messages naming `scripts/worktree.sh` and the
  doctrine path
- D-6: hook tests (existing harness): primary vs linked commit,
  target-resolution ambiguity, bare vs explicit stash
- D-7: `.github/copilot-instructions.md` — minimal msg-file reconciliation
  (R-4) + `one_session_one_repo` pointer to the doctrine
- D-8: this FR — folded revisions, implementation status, decisions,
  validation record, local-memory disposition note
- D-9: `changelog/unreleased/` fragment and `docs/diary/` entry as required
  by existing gates for the final commit type

## Acceptance Criteria (revised by judgement)

- [ ] AC-01: FR-861 contains a six-shape taxonomy table with committed
  evidence source, failure mode, cure, and enforcing surface per shape; the
  FR-784 citation is corrected. *(folded above)*
- [ ] AC-02: `doctrine.md` contains the folded write-side contract:
  worktree-first rule, commit ritual, explicit-stash-ref rule,
  hermetic-generator rule, six-shape appendix.
- [ ] AC-03: SKILL.md description and body advertise write rituals, not
  only read-side introspection.
- [ ] AC-04: `scripts/hermetic.sh --help` documents the frozen interface:
  command, input overlay, declared outputs, output-copy policy, failure
  behavior, cleanup, main-repo venv resolution.
- [ ] AC-05: Hermetic tests prove: HEAD worktree created; staged +
  explicit inputs overlaid; declared outputs copied back; undeclared dirty
  airlock files NOT copied; failure leaves main-tree non-output files
  unchanged; worktree removed.
- [ ] AC-06: Hermetic witness uses a current generator: `docs/fr-board.md`
  only while FR-858 has not retired it, else the successor or
  `scripts/aggregate_capabilities.py`.
- [ ] AC-07: In the primary checkout, agent `git commit` is denied naming
  `scripts/worktree.sh` and the doctrine path; identical command in a
  linked worktree is allowed.
- [ ] AC-08: Guard tests cover plain `git commit`, `git -C <path> commit`,
  `cd <path> && git commit`, linked-worktree allow, primary deny,
  ambiguous-target deny.
- [ ] AC-09: Guard tests cover stash: bare `pop`/`apply` denied; explicit
  `stash@{n}` allowed.
- [ ] AC-10: Guard decisions audit-logged with stable reason codes
  (`primary_commit_deny`, `ambiguous_commit_target`, `stash_bare_deny`,
  `linked_commit_allow`).
- [ ] AC-11: Msg-file rule reconciled with `.github/copilot-instructions.md`;
  no committed doctrine requires both shared and unique message files.
- [ ] AC-12: No new required CI checks; no judge/review/graph-authoring
  route, graph/prompt artifact, push/fetch guard, session lock, or
  primary-checkout edit guard changed.
- [ ] AC-13: New/changed tests carry valid `@pytest.mark.req` coverage with
  any capability registry update included.
- [ ] AC-14: Implementation status records the human-review gate result,
  warn-mode findings for chaplain/watcher commit paths, validations run,
  and the local-memory disposition (no private memory content committed).

## Risks

- Worktree friction for small docs/diary commits — mitigation:
  `scripts/worktree.sh` provisioning already exists; doctrine includes a
  short-lived "commit worktree" recipe (add, commit, push, remove) whose
  cost is comparable to the airlock ritual it replaces.
- Worktree venv/symlink traps are known prior incidents (FR-174 venv
  corruption, FR-199 CLAUDE.md symlink) — mitigation: doctrine cites both
  cures; hermetic.sh and worktree.sh use the main repo's venv python
  explicitly.
- Chaplain/watcher automation committing in the primary checkout would be
  denied — mitigation: they already operate in worktrees (FR-241
  teardown lineage); verify with an audit-log dry run before enabling the
  deny (guard supports warn-then-deny rollout via its audit trail).
- Doctrine drift vs Scripture summary — mitigation: Scripture
  `one_session_one_repo` entry gains a pointer to the doctrine as its
  canonical expansion (one-line edit, within scope).
