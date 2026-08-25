# Judgement: FR-888 Main-Write Guard - Worktree as the Only Enforcement Write Path

**Prior art:** dispositioned in the FR (supersedes FR-750; July coordinator plan Q1/Q4; FR-767 mechanism; FR-885/886 census siblings fenced by R-5).

**Verdict:** APPROVED WITH REVISIONS - the main-write guard is a sound and strategically necessary enforcement primitive, but implementation authority activates only after the FR fixes the executable worktree command contract, freezes the cross-FR teardown boundary, and makes the guard's worktree/write grammar mechanically testable.

**Reviewed against:** `feature-requests/FR-888-main-write-guard-worktree-route.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-750-worktree-pilot.md`; `docs-planning/plan-interactive-finalize-coordinator.md`; `feature-requests/FR-767-graph-authoring-sole-route.md`; `feature-requests/FR-767-graph-authoring-sole-route.judgement.md`; `feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md`; `feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.judgement.md`; `docs/FR-884-session-task-shapes.md`; `docs/FR-884-raw-read-log.md`; `feature-requests/FR-885-deploy-watch-outside-session.md`; `feature-requests/FR-886-judge-route-adoption-nudge.md`; `scripts/worktree.sh`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/hooks/scripts/checks/common.sh`; `.github/hooks/tests/test_authoring_guard.py`; `.github/hooks/tests/test_pre_command_guard.py`; `feature-requests/FR-241-complete-worktree-teardown-self-heal.md`; `capabilities/CAP-102-complete-worktree-teardown-self-heal.yaml`; `feature-requests/FR-311-watcher2-git-commit-hook-fix-retry.md`.

## What is sound

The problem is real. Repo doctrine records the shared-index hazard as repeated staged-file, working-tree, and environment corruption across parallel sessions, with an explicit ritual only "when sharing is unavoidable" (`.github/copilot-instructions.md:163`). FR-888 correctly moves that risk from remembered choreography to a boundary guard: it names the first consumer and first event (`feature-requests/FR-888-main-write-guard-worktree-route.md:8-10`), states that voluntary routing failed (`feature-requests/FR-888-main-write-guard-worktree-route.md:49-53`), and cites the exact doctrine cure of delivering instructions at denial time (`feature-requests/FR-888-main-write-guard-worktree-route.md:54-58`).

The strategic direction is aligned with prior decisions. The July coordinator plan froze Q1 as branch/PR/CI/merge parity and Q4 as "hook DENIES writes to main - worktree becomes the only write path" for enforcement arcs (`docs-planning/plan-interactive-finalize-coordinator.md:258-261`). FR-750's own status now records that its voluntary pilot had zero subjects in five weeks and was superseded by FR-888's deny-mode main-write guard (`feature-requests/FR-750-worktree-pilot.md:5-9`), so the FR is not prematurely skipping an active pilot; it is correcting a circular sequencing failure.

The proposed mechanism has a strong local precedent. FR-767 already hardened a sole route by adding a PreToolUse denial over file-write tools and terminal write shapes, with path-based bright lines and sentinel protection (`feature-requests/FR-767-graph-authoring-sole-route.md:119-156`). The implemented guard proves the hook can inspect `create_file`, `replace_string_in_file`, `multi_replace_string_in_file`, `apply_patch`, `run_in_terminal`, and `send_to_terminal` (`.github/hooks/scripts/pre-command-guard.sh:171-300`), and its tests prove deny/allow behavior for file tools, terminal redirects, copy/move, and ambiguous write shapes (`.github/hooks/tests/test_authoring_guard.py:85-228`). Reusing this family for enforcement writes is feasible.

The `.env` addition is tightly coupled to the worktree route, not an unrelated convenience. Current `scripts/worktree.sh` symlinks `.venv` into new worktrees (`scripts/worktree.sh:150-153`) but has no `.env` handling in the creation path (`scripts/worktree.sh:146-169`). FR-888 identifies the resulting failure mode: fresh worktrees can lack credentials and fail late during graph runs or integration tests (`feature-requests/FR-888-main-write-guard-worktree-route.md:59-63`). Completing the setup command is necessary if the denial message is to be a real cure rather than an RTFM loop.

Strategic classification: **Framework/process enforcement primitive**. The FR protects multiple recurring enforcement arcs, reuses existing hook and worktree infrastructure, and has no adequate advisory substitute. It is broader than pattern documentation because the failure mode is already priced and repeated; it is narrower than a general workflow rewrite because it touches only the main-checkout write boundary and worktree setup/runbook surfaces.

## Required revisions

### R-1: Align the denial cure with the actual `scripts/worktree.sh` interface

Replace every `scripts/worktree.sh create fr-<nnn>` / `scripts/worktree.sh create fr-<nnn> && cd <printed-path>` contract with an executable command that exists today, or explicitly authorize a tested CLI change. The current script supports `new`, `spike`, `rm`, and `list`, not `create` (`scripts/worktree.sh:12-19`, `scripts/worktree.sh:293-310`). FR-888's denial message currently quotes `scripts/worktree.sh create fr-<nnn>` (`feature-requests/FR-888-main-write-guard-worktree-route.md:95-100`), so the first denied agent would receive a broken cure.

Fold one of these mechanically into the FR:

1. Prefer existing interface: denial message uses `scripts/worktree.sh new fr-<nnn>` and the FR requires the command to print an unambiguous final `cd <path>` line.
2. Or, if `create` is intentionally desired, the FR must authorize adding `create` as the canonical verb, updating `scripts/worktree.sh` usage, tests, and all denial/runbook text in the same change.

Do not leave the enforcer to infer an alias.

### R-2: Freeze the worktree detection predicate and fixture shape

The FR correctly rejects path heuristics and requires git plumbing: compare `git rev-parse --git-common-dir` with `--git-dir` (`feature-requests/FR-888-main-write-guard-worktree-route.md:81-87`). That is directionally right but not yet implementable enough for a guard that must decide before writes happen. Fold into the FR the exact predicate and tests:

- main checkout = `git rev-parse --path-format=absolute --git-common-dir` resolves to the same directory as `git rev-parse --path-format=absolute --git-dir`, after normalizing symlinks with `pwd -P` or equivalent;
- linked worktree = the two resolved paths differ;
- non-git or parse-error contexts fail closed only when an enforcement-class write target is present, with an audit row explaining the parse failure;
- nested Git repositories under the checkout are fixture-tested so a foreign repo is not misclassified as the main checkout.

This preserves the FR's `workspace_is_not_boundary` concern while keeping the hook mechanical (`.github/copilot-instructions.md:87`, `feature-requests/FR-888-main-write-guard-worktree-route.md:153-155`).

### R-3: Narrow and enumerate terminal write grammar without relying on CI as the safety net

FR-888 says unrecognized command shapes are allowed with audit because a false deny is worse than a rare miss and "the CI/PR ring catches escapes" (`feature-requests/FR-888-main-write-guard-worktree-route.md:102-105`). That sentence conflicts with the stated objective: the shared-index hazard happens at local main write/stage time, before CI or PR checks can help (`feature-requests/FR-888-main-write-guard-worktree-route.md:41-45`). Revise the claim.

Fold this into the FR: the guard may allow **read-only or non-write** unrecognized shapes with audit, but when a terminal command both mentions an enforcement-class path and contains an unclassified write signal (`>`, `>>`, `tee`, `cp`, `mv`, `rsync`, `install`, `sed -i`, `python/perl/ruby -c/-e` with `open`/`write`, `dd`, `truncate`), it must deny with the worktree cure unless `FR888_ALLOW_MAIN=1` is present. Add fixture tests for at least: direct redirect, quoted path redirect, `tee`, `cp` to file, directory copy materializing a governed path, `sed -i`, env-prefixed command, `time`-prefixed read-only command allowed, and `time`-prefixed write command denied or explicitly classified.

### R-4: Make the escape hatch auditable and constrained

`FR888_ALLOW_MAIN=1` is a necessary operator escape hatch, but the FR currently allows it with only "audited to audit.jsonl" (`feature-requests/FR-888-main-write-guard-worktree-route.md:106-108`). Because this changes enforcement infrastructure, strengthen the contract: the audit row must include `session_id`, `tool_use_id` when available, cwd, normalized target path(s), command/tool name, and reason `fr888-main-write-override`. Tests must prove the escape allows the denied write class and emits that row. The escape hatch must not disable unrelated guards such as Co-authored-by, `--no-verify`, branch creation, or FR-767 authoring-route denial (`.github/hooks/scripts/pre-command-guard.sh:321-369`, `.github/hooks/scripts/pre-command-guard.sh:171-300`).

### R-5: Decouple FR-888 authority from unapproved FR-885 implementation

The merged-path teardown in FR-888 is assigned to the FR-885 watcher terminal step (`feature-requests/FR-888-main-write-guard-worktree-route.md:125-129`), and FR-885 likewise says it executes FR-888 merged-FR teardown (`feature-requests/FR-885-deploy-watch-outside-session.md:74-85`, `feature-requests/FR-885-deploy-watch-outside-session.md:113-117`). But FR-885 is still Proposed (`feature-requests/FR-885-deploy-watch-outside-session.md:3-7`). FR-888 cannot require a live witness of a separate unapproved feature as a condition of its own completion.

Fold this boundary into the FR: FR-888 may define the teardown interface and board/orphan detection requirements, but it must not implement FR-885's watcher or require a live FR-885 merged-path teardown witness unless FR-885 has separately received authority. For FR-888 itself, merged-path teardown acceptance may be satisfied by a fixture or stubbed hook contract proving "merged + zero untracked -> worktree.sh rm/remove; untracked -> flag, never delete"; the live watcher execution remains FR-885's acceptance. Rejected-path teardown and orphan-board detection may stay in FR-888 if they are tested without implementing the watcher.

### R-6: Reconcile worktree removal wording with the actual script and the untracked-file invariant

FR-888 says all automatic teardown paths must verify zero untracked files before removal (`feature-requests/FR-888-main-write-guard-worktree-route.md:131-134`), but the current `scripts/worktree.sh rm` removes with `git worktree remove --force` and deletes the branch (`scripts/worktree.sh:252-255`). That existing behavior is not safe enough for a future automatic pruner. Fold into the FR whether this FR changes `scripts/worktree.sh rm` globally or adds a narrower safe removal mode used by the guard/watcher path. The revised acceptance criteria must require fixture tests proving untracked files block automatic removal and produce a board/flag artifact instead of deletion.

### R-7: Add the mandatory human-review gate for enforcement-infrastructure changes

Judge doctrine requires enforcement-infrastructure changes such as hooks and CI to be treated as adversarial input and reviewed by a human (`.github/skills/judge-fr/doctrine.md:96-101`). FR-767 carried that as a GATE for hook/doctrine changes (`feature-requests/FR-767-graph-authoring-sole-route.judgement.md:81-90`). FR-888 changes a PreToolUse denial path over core write surfaces (`feature-requests/FR-888-main-write-guard-worktree-route.md:77-108`), so add the same explicit gate: human review is mandatory before the hook is considered merged policy.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-888-main-write-guard-worktree-route.md`: fold R-1 through R-7, implementation status, decisions, and deviations. |
| D-2 | `.github/hooks/scripts/pre-command-guard.sh` and shared hook helpers only as needed: add the main-checkout enforcement-write guard, worktree detection, denial message, escape-hatch audit, and allowed/audited cases. |
| D-3 | `.github/hooks/tests/`: fixture tests for main checkout denial, linked worktree allowance, docs-lane allowance, nested repo detection, terminal command grammar, escape-hatch audit, and no regression to existing guards. |
| D-4 | `scripts/worktree.sh`: add `.env` symlink/provisioning and final stdout `cd <path>` output; optionally add the canonical `create` verb only if R-1 chooses that path. |
| D-5 | `scripts/worktree.sh` tests or hook fixture tests proving readable `.env`, importable `.venv`, and safe removal behavior chosen by R-6. |
| D-6 | `scripts/vscode/now.py` or its existing board surface only if needed for orphan-tree detection in AC-10; no broad board redesign. |
| D-7 | `.github/hooks/README.md` or adjacent runbook documentation: denial contract, worktree command, escape hatch, dependency-change warning, and cleanup ownership. |
| D-8 | `feature-requests/FR-750-worktree-pilot.md`: mark superseded with pointer to FR-888 if not already complete. |
| D-9 | Changelog fragment and `docs/diary/` reflection required by existing repository gates. |

Not authorized: implementing the FR-885 rollout watcher; implementing FR-886 adoption nudges; changing judge/author/review route doctrine; changing YAMLGraph runtime primitives; changing branch protection or GitHub repository settings; adding a daemon/FSM runtime; migrating docs-lane writes off main; broad global hook bypasses; deleting worktrees with untracked files; suppressing or bypassing existing PreToolUse guards.

## Revised acceptance criteria

- [ ] AC-01: A PreToolUse hook denies an unsentineled edit-tool write to an enforcement-class path (`yamlgraph/**`, `tests/**`, `scripts/**`, `capabilities/**`, `.github/hooks/**`) when the hook cwd is the main checkout, and allows the byte-identical write in a linked git worktree; both are proven by fixture tests, not live repo mutation.
- [ ] AC-02: Docs-lane writes (`docs/**`, `feature-requests/**`, `changelog/**`, `research/**`, `tmp/**`, `logs/**`) on main are allowed and tested.
- [ ] AC-03: Worktree detection uses normalized git plumbing (`--path-format=absolute --git-common-dir` and `--git-dir`) and is tested for main checkout, linked worktree, nested repository, and parse-error cases.
- [ ] AC-04: The denial message's first line is the verdict, its body contains one executable worktree cure using the canonical `scripts/worktree.sh` verb chosen by R-1 plus a concrete `cd` target, and its last line points to FR-888/doctrine.
- [ ] AC-05: `scripts/worktree.sh` creates a worktree whose `.env` is readable when the main checkout has `.env`, whose `.venv` is importable when the main checkout has `.venv`, and whose final stdout line is the `cd` command or path consumed by the denial cure.
- [ ] AC-06: Terminal write grammar is tested for redirect, quoted redirect, `tee`, `cp`/`mv`, directory copy materializing an enforcement-class path, `sed -i`, env-prefixed command, `time`-prefixed read-only allowance, and `time`-prefixed write denial or explicit classification.
- [ ] AC-07: `FR888_ALLOW_MAIN=1` allows only the FR-888 main-write denial class, emits an audit row with session/tool/cwd/target detail and reason `fr888-main-write-override`, and does not bypass existing Co-authored-by, `--no-verify`, branch creation, or FR-767 authoring guards.
- [ ] AC-08: Unrecognized non-write command shapes are allowed with audit; unrecognized write-shaped commands targeting enforcement-class paths are denied unless the escape hatch is present.
- [ ] AC-09: FR-750 is marked Superseded with a pointer to FR-888; changelog fragment and diary reflection are included.
- [ ] AC-10: Orphan-tree detection surfaces a worktree whose branch has no open PR and no live pipeline on the `now.py` board, including age and untracked-file count, using fixtures; auto-deletion is explicitly absent.
- [ ] AC-11: Safe teardown ownership is witnessed without depending on unapproved FR-885: rejected-path teardown and a merged-path stub/fixture both verify branch state and zero untracked files before removal, and both flag rather than remove when untracked files exist. A live FR-885 watcher teardown remains out of scope unless FR-885 is separately approved.
- [ ] AC-12: Existing hook suites, including FR-767 authoring guard tests and pre-command guard tests, continue to pass; no existing guard is weakened.
- [ ] AC-13: Human review of the hook/worktree enforcement change is recorded before it is treated as merged policy.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-7 into FR-888 before implementation authority activates. | GATE |
| C-2 | The denial cure must be executable as written against the committed `scripts/worktree.sh` interface. | GATE |
| C-3 | The guard must decide main checkout vs linked worktree by git plumbing, not path names. | GATE |
| C-4 | False-deny avoidance may not reopen the shared-index hazard for write-shaped commands targeting enforcement-class paths. | GATE |
| C-5 | `FR888_ALLOW_MAIN=1` must be narrow, audited, and unable to bypass unrelated guards. | GATE |
| C-6 | Do not implement or depend on FR-885 watcher behavior under FR-888 unless FR-885 has separately received authority; fixture/stub contracts may define the interface. | GATE |
| C-7 | Automatic worktree removal must never remove a tree with untracked files; it must flag instead. | GATE |
| C-8 | Human review is mandatory before merge because this FR changes enforcement infrastructure and hook denial policy. | GATE |

Authority granted: after R-1 through R-7 are folded into the FR, the enforcer may implement the main-checkout enforcement-write guard, complete `scripts/worktree.sh` setup output and `.env` provisioning, add fixture-tested safe teardown/orphan detection contracts, and update documentation/tests within the frozen surfaces above.
