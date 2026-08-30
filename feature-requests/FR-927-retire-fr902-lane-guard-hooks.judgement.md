# Judgement: FR-927 Retire the FR-902 Lane-Guard Hook Machinery

**Verdict:** APPROVED WITH REVISIONS -- the subtraction direction is sound, but authority activates only after the FR adds mandatory research evidence, supplies the missing RED structural test it already claims, and tightens the full-hook-retirement/status mechanics.

**Prior art:** `FR-927-retire-fr902-lane-guard-hooks.md` [Judged] — the FR this judgement rules on. `FR-902-session-worktree-lifecycle.md` [Enforced] — the retirement subject; dispositioned in the FR's own Prior art line. `FR-925-lane-delivery-agent-context.md` + judgement + research [Approved] — superseded by FR-927 per R-4 (history preserved). All hits reviewed as input closure, none competing.

**Reviewed against:** `feature-requests/FR-927-retire-fr902-lane-guard-hooks.md`; `feature-requests/FR-902-session-worktree-lifecycle.md`; `feature-requests/FR-902-session-worktree-lifecycle.judgement.md`; `feature-requests/FR-925-lane-delivery-agent-context.md`; `feature-requests/FR-925-lane-delivery-agent-context.judgement.md`; `feature-requests/FR-925.research.md`; `feature-requests/FR-889-os-enforced-main-write-lock.md`; `feature-requests/FR-888-main-write-guard-worktree-route.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `feature-requests/TEMPLATE.md`; `.github/copilot-instructions.md`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/hooks/scripts/checks/lane_guard.py`; `.github/hooks/session-probe.json`; `capabilities/CAP-254-session-worktree-lifecycle.yaml`; `tests/unit/test_session_worktree_lifecycle.py`; `.github/hooks/tests/test_fr902_lane_guard.py`; `.github/hooks/tests/test_fr902_session_worktree.py`; `.github/hooks/tests/test_fr902_checkpoint.py`; `.github/hooks/tests/test_fr902_gc_join.py`; `.github/hooks/tests/fr902_fixtures.py`; tracked-file inventory for `feature-requests/*927*research*`, `feature-requests/research-briefs/*927*`, and `.github/hooks/tests/test_fr902_retired.py` (no committed artifacts present).

## What is sound

The problem is real and supported by committed precedent. FR-927 identifies Check 8 as the live FR-902 session-lane ownership guard behind `fr902.live` (`feature-requests/FR-927-retire-fr902-lane-guard-hooks.md:38-40`), and the current hook confirms that Check 8 still contains a write-shaped tool-name case and shell grep alternation (`.github/hooks/scripts/pre-command-guard.sh:309-334`). FR-889 already records the same defect family: the hook payload `cwd` is the workspace folder rather than the persistent terminal cwd, false positives were witnessed across sessions, and reflexive escapes turn the OVERRIDE stream into noise (`feature-requests/FR-889-os-enforced-main-write-lock.md:168-182`).

The proposed deletion matches the repo's subtraction doctrine better than another parser patch. FR-889 deliberately moved main-checkout enforcement from terminal grammar to an OS write lock (`feature-requests/FR-889-os-enforced-main-write-lock.md:199-216`), while repo doctrine names both `growth_as_default` and `infrastructure_self_exempt` as traps for mature enforcement systems (`.github/copilot-instructions.md:82`, `.github/copilot-instructions.md:95`). FR-927's ideal result -- no hook-level lane arbitration and no bash write-shape grammar in the hook chain -- is therefore architecturally aligned (`feature-requests/FR-927-retire-fr902-lane-guard-hooks.md:20-26`).

The delete/keep boundary is mostly crisp. The FR deletes Check 8, `lane_guard.py`, SessionStart/Stop hook wrappers, hook registrations, FR-902 hook tests, `fr902.live` references, and `FR902_ALLOW_OUTSIDE` guidance (`feature-requests/FR-927-retire-fr902-lane-guard-hooks.md:72-89`), while explicitly retaining `scripts/worktree.sh session`/`gc`, read-only lane observability, historical join tooling, and existing lanes/branches (`feature-requests/FR-927-retire-fr902-lane-guard-hooks.md:91-98`). That preserves the reusable substrate while retiring the automatic hook machinery.

The acceptance shape is testable once the missing test exists. Current committed surfaces make the intended assertions straightforward: `session-probe.json` wires `session-worktree.sh` on `SessionStart` and `session-checkpoint.sh` on `Stop` (`.github/hooks/session-probe.json:3-18`, `.github/hooks/session-probe.json:55-65`), CAP-254 currently requires the guard and checkpoint hooks (`capabilities/CAP-254-session-worktree-lifecycle.yaml:1-52`), and the lifecycle unit test currently asserts those surfaces exist (`tests/unit/test_session_worktree_lifecycle.py:15-37`).

Strategic classification: repo-local enforcement subtraction, not a new framework primitive. The plan removes a failed process-boundary primitive and keeps only manual/operator worktree tooling; it is not graph-shaped work and does not create a replacement abstraction.

## Required revisions

### R-1: Add the mandatory FR-927 research record or committed alternatives table

Add a `**Research:**` field to FR-927 pointing at a committed `feature-requests/FR-927.research.md` or at an in-body committed alternatives table. The record must be substantive, not shape-only: include 4-6 genuine solution classes, precedent lines, preserved disagreement, and an `is_this_a_graph` answer. At minimum it must disposition full FR-902 hook retirement, Check-8-only retirement, dark-disabling via `fr902.live`, repairing `lane_guard.py`, retaining only SessionStart delivery, and retaining only checkpoint/join provenance.

This is a gate, not polish. The FR template makes Research mandatory for post-FR-890 FRs (`feature-requests/TEMPLATE.md:11-20`), and judge doctrine says a newly created FR whose `**Research:**` field is absent or dangling receives no authority (`.github/skills/judge-fr/doctrine.md:118-128`). FR-927 currently jumps from `Requested`/`First consumer`/`Prior art` directly to `Ideal Result` with no `**Research:**` field (`feature-requests/FR-927-retire-fr902-lane-guard-hooks.md:7-20`), and no committed FR-927 research artifact is present.

### R-2: Provide the RED structural-retirement test before enforcement

Add the committed RED test named by the FR: `.github/hooks/tests/test_fr902_retired.py`. It must fail against the current implementation because the forbidden FR-902 hook machinery still exists, not because of missing fixtures, imports, or path mistakes. It must assert, at minimum: no `lane_guard.py`; no `session-worktree.sh` or `session-checkpoint.sh`; no SessionStart/Stop registrations for those scripts; no `FR902`/`fr902` tokens in `pre-command-guard.sh`; no FR-902 write-verb grep alternation outside the FR-889 lock-mutator fence; and no `FR902_ALLOW_OUTSIDE` in hook scripts or living operator guidance.

FR-927 claims the test is "RED, committed with this FR" and makes it AC-01 (`feature-requests/FR-927-retire-fr902-lane-guard-hooks.md:108-120`), but no committed file exists at `.github/hooks/tests/test_fr902_retired.py`. Judge doctrine treats tests that fail for missing files/fixtures rather than missing implementation as an FR defect (`.github/skills/judge-fr/doctrine.md:58-61`).

### R-3: Make full hook-lifecycle retirement explicit, not implied by Check 8 failures

Add a short scope paragraph explaining why deleting `session-worktree.sh` and `session-checkpoint.sh` is part of the same FR as deleting Check 8. The current Problem evidence is strongest for Check 8 and `FR902_ALLOW_OUTSIDE` false positives (`feature-requests/FR-927-retire-fr902-lane-guard-hooks.md:42-65`), but the deletion list also removes automatic SessionStart lane creation and Stop checkpointing (`feature-requests/FR-927-retire-fr902-lane-guard-hooks.md:80-87`). CAP-254 currently treats those as separate requirements: lane creation/guarding in REQ-YG-629 and checkpoint/GC/join provenance in REQ-YG-630 (`capabilities/CAP-254-session-worktree-lifecycle.yaml:22-52`).

Fold the rationale mechanically: automatic SessionStart and Stop hooks are retired because their only live lifecycle is the failed hook-created lane system; manual `scripts/worktree.sh session`/`gc`, `now.py`, and `session_join.py` remain as retained tooling. If that statement is not true, the checkpoint-retirement concern must be split from the Check 8 lane-guard retirement.

### R-4: Correct FR-925 disposition vocabulary and preserve history

Replace "Mark REJECTED/SUPERSEDED by this FR" with "mark SUPERSEDED by FR-927" and state that FR-925's historical judgement/implementation record is preserved. FR-925 is currently `Approved with revisions (folded 2026-08-30)` (`feature-requests/FR-925-lane-delivery-agent-context.md:1-10`) and records RED/GREEN implementation status plus a pending AC-01 witness (`feature-requests/FR-925-lane-delivery-agent-context.md:145-165`). Calling it "REJECTED/SUPERSEDED" (`feature-requests/FR-927-retire-fr902-lane-guard-hooks.md:105-106`) creates audit ambiguity: a superseded plan is not retroactively rejected.

### R-5: Tighten the measurement and traceability acceptance criteria

Rewrite AC-02 and AC-04 so the enforcer has exact commands/artifacts to satisfy. AC-02 must name how `pre-command-guard.sh` line-count shrinkage is recorded, including the baseline source and destination for the measurement (`feature-requests/FR-927-retire-fr902-lane-guard-hooks.md:121-122`). AC-04 must state the expected new REQ-YG-629 and REQ-YG-630 text at the same level of specificity as the current CAP-254 obligations, because today those requirements explicitly require the PreToolUse lane guard and Stop checkpoint hook (`capabilities/CAP-254-session-worktree-lifecycle.yaml:22-52`). Keep `python scripts/req_coverage.py --strict` as the traceability gate (`feature-requests/FR-927-retire-fr902-lane-guard-hooks.md:126-128`).

### R-6: Add the human-review gate for hook-enforcement deletion

Add an explicit condition to FR-927 that a human must review the hook-enforcement deletion diff before the retirement is treated as live. Judge doctrine requires human review for enforcement-infrastructure changes (`.github/skills/judge-fr/doctrine.md:94-103`). FR-927 removes hook scripts, hook registrations, a PreToolUse guard block, and operator guidance (`feature-requests/FR-927-retire-fr902-lane-guard-hooks.md:72-89`), so the gate is mandatory even though the direction came from the operator.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-927-retire-fr902-lane-guard-hooks.md`: fold R-1 through R-6, update status, and later record implementation status/decisions/deviations. |
| D-2 | `feature-requests/FR-927.research.md` or an equivalent in-body alternatives table referenced by a `**Research:**` field. |
| D-3 | `.github/hooks/tests/test_fr902_retired.py`: permanent structural absence regression test for the retired FR-902 hook machinery. |
| D-4 | `.github/hooks/scripts/pre-command-guard.sh`: remove only the FR-902 Check 8 lane-ownership block and its `FR902_*` plumbing. |
| D-5 | `.github/hooks/scripts/checks/lane_guard.py`: delete. |
| D-6 | `.github/hooks/scripts/session-worktree.sh` and `.github/hooks/scripts/session-checkpoint.sh`: delete only if R-3 is folded; remove their `session-probe.json` registrations. |
| D-7 | `.github/hooks/tests/test_fr902_lane_guard.py`, `.github/hooks/tests/test_fr902_session_worktree.py`, `.github/hooks/tests/test_fr902_checkpoint.py`, `.github/hooks/tests/test_fr902_gc_join.py`, `.github/hooks/tests/fr902_fixtures.py`: delete or move only the surviving substrate/join assertions needed after R-3. |
| D-8 | `capabilities/CAP-254-session-worktree-lifecycle.yaml` and `tests/unit/test_session_worktree_lifecycle.py`: rewrite to retained tooling and keep requirement coverage honest. |
| D-9 | `feature-requests/FR-902-session-worktree-lifecycle.md` and `feature-requests/FR-925-lane-delivery-agent-context.md`: mark FR-902 hook machinery retired and FR-925 superseded by FR-927 without erasing historical status. |
| D-10 | `CLAUDE.md` and `.github/copilot-instructions.md`: remove live FR-902 lane-denial and `FR902_ALLOW_OUTSIDE` guidance; replace with a retirement note. |
| D-11 | `changelog/unreleased/*.md` and `docs/diary/*.md`: removal fragment and metacognitive reflection. |

Not authorized: changing FR-889's OS lock, `main_write.py`, lock-mutator fence, or Check 7 replacement; deleting `scripts/worktree.sh session`/`gc`; deleting `scripts/vscode/now.py`, `scripts/vscode/session_join.py`, existing `session/*` branches, or existing session worktrees; building replacement lane arbitration; changing judge/review doctrine or adapters; changing branch protection, CI required contexts, unrelated hook checks, or YAMLGraph runtime behavior.

## Revised acceptance criteria

- [ ] AC-01: FR-927 contains a `**Research:**` field pointing at a committed FR-927 research artifact or equivalent committed alternatives table with 4-6 solution classes, precedent lines, disagreement preserved, and an `is_this_a_graph` answer.
- [ ] AC-02: `.github/hooks/tests/test_fr902_retired.py` exists, is independent of deleted FR-902 fixtures, fails against the current FR-902 hook machinery, and passes only when the retired surfaces are absent.
- [ ] AC-03: The structural-retirement test asserts no `.github/hooks/scripts/checks/lane_guard.py`, no `.github/hooks/scripts/session-worktree.sh`, no `.github/hooks/scripts/session-checkpoint.sh`, and no `session-probe.json` registrations for the deleted SessionStart/Stop scripts.
- [ ] AC-04: `pre-command-guard.sh` contains no FR-902 Check 8 block, no `FR902`/`fr902` token, no `FR902_ALLOW_OUTSIDE`, and no write-shape grep alternation except the narrow FR-889 lock-mutator fence (`chmod`/`chflags`/`setfacl`) remains intact.
- [ ] AC-05: Hook tests are green after deleting or relocating FR-902-specific tests/fixtures; no orphaned imports of `fr902_fixtures`, `lane_guard.py`, `session-worktree.sh`, or `session-checkpoint.sh` remain.
- [ ] AC-06: `session-probe.json` removes only the `session-worktree.sh` SessionStart entry and `session-checkpoint.sh` Stop entry; all remaining hook registrations are byte-for-byte equivalent except formatting required by JSON editing.
- [ ] AC-07: CAP-254 is rewritten to describe only retained tooling (`scripts/worktree.sh session`/`gc`, `scripts/vscode/now.py`, `scripts/vscode/session_join.py`); REQ-YG-629 no longer requires a PreToolUse lane guard; REQ-YG-630 no longer requires Stop-hook checkpoints; `tests/unit/test_session_worktree_lifecycle.py` matches the retained surfaces; `python scripts/req_coverage.py --strict` is green.
- [ ] AC-08: FR-902 records that its hook machinery is RETIRED by FR-927 while preserving historical enforcement facts; FR-925 is marked SUPERSEDED by FR-927 while preserving its historical approval/implementation record.
- [ ] AC-09: `CLAUDE.md` and `.github/copilot-instructions.md` contain no live instruction to use FR-902 lanes or `FR902_ALLOW_OUTSIDE`; the Copilot Hooks section replaces the FR-902 lane bullet with a one-line retirement note.
- [ ] AC-10: The implementation records the `pre-command-guard.sh` shrink measurement using an explicit before/after line count and stores it in FR-927 implementation status.
- [ ] AC-11: A `type: removal` changelog fragment exists under `changelog/unreleased/`.
- [ ] AC-12: A diary reflection exists under `docs/diary/`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is not active until R-1 through R-6 are folded into FR-927. | GATE |
| C-2 | A human must review the hook-enforcement deletion diff before the retirement is treated as live. | GATE |
| C-3 | The enforcer must not implement from a missing or non-red `test_fr902_retired.py`; the structural absence test is the RED witness for this removal. | GATE |
| C-4 | Do not change FR-889's OS lock, main-checkout mutator fence, or Check 7 replacement while enforcing FR-927. | GATE |
| C-5 | Do not delete retained substrate tooling or existing lanes/branches; only the automatic FR-902 hook machinery and live guidance are in scope. | GATE |
| C-6 | Do not build a replacement lane-arbitration mechanism in this FR. | GATE |

Authority granted: after the required revisions are folded, enforcement may retire the FR-902 automatic hook machinery and pin its absence with structural tests, while preserving FR-889's OS lock and the retained manual/session observability substrate.
