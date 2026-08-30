# Judgement: FR-935 Deny gh pr merge --admin outside break-glass

**Verdict:** APPROVED WITH REVISIONS — the agent-boundary denial is a small, evidenced use of the existing PreToolUse guard, but authority activates only after the research record is substantive, FR-934 has made the non-admin queue path operational, and the self-authorizing `BREAK_GLASS=1` bypass is removed.

**Prior art:** the only filename-noun hit is the parent FR itself; its prior-art record is dispositioned in the FR body and confirmed here — the PreToolUse guard family (`pre-command-guard.sh`, CAP-192/REQ-YG-527 branch-deny guidance) owns the boundary this FR extends with one rule, `reference/break-glass.md` owns the human emergency path left unmodified, and FR-934 is the prerequisite queue this guard protects (C-2). No prior or REJECTED FR governs the agent-issued merge verb.

**Reviewed against:** `feature-requests/FR-935-deny-admin-merge-outside-break-glass.md`; `docs/plan-research-merge-queue.md`; `feature-requests/research-briefs/fr934-merge-integration-toll-brief.md`; `feature-requests/FR-934-merge-queue-on-main.md`; `feature-requests/FR-889-os-enforced-main-write-lock.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/hooks/README.md`; `.github/hooks/tests/test_pre_command_guard.py`; `.github/hooks/tests/conftest.py`; `reference/break-glass.md`; `CLAUDE.md`; `ARCHITECTURE.md`; `capabilities/CAP-192-branch-deny-guidance-manual-worktree-lane.yaml`.

## What is sound

The problem is real and the first consumer is explicit. The FR records at least four same-day sessions using `--admin` as the routine merge verb, including PRs #519 and #520 (`feature-requests/FR-935-deny-admin-merge-outside-break-glass.md:8-13`), while the shared problem brief explains that this bypass makes required contexts ineffective in practice (`feature-requests/research-briefs/fr934-merge-integration-toll-brief.md:34-47`). The platform research independently identifies the same failure mode and sequences a dedicated guard after the queue work (`docs/plan-research-merge-queue.md:59-64`, `docs/plan-research-merge-queue.md:81-97`).

The scope is minimal and single-purpose: one existing command boundary denies one hazardous flag, while branch protection, the human browser path, and server-side policy remain outside this FR (`feature-requests/FR-935-deny-admin-merge-outside-break-glass.md:63-78`). This follows the repository's boundary and merge-enforcement doctrine (`.github/copilot-instructions.md:51-53`, `.github/copilot-instructions.md:159-160`) rather than inventing a second enforcement service.

The implementation is feasible and architecture-aligned. `pre-command-guard.sh` already parses terminal payloads, emits denials, and writes stable audit rows (`.github/hooks/scripts/pre-command-guard.sh:19-34`, `.github/hooks/scripts/pre-command-guard.sh:52-83`, `.github/hooks/scripts/pre-command-guard.sh:309-340`). The hook contract and isolated `HOOK_LOG_DIR` test seam are documented (`.github/hooks/README.md:61-76`, `.github/hooks/README.md:153-161`, `.github/hooks/README.md:303-309`), and `.github/hooks/tests/test_pre_command_guard.py` already executes real hook payloads and distinguishes command invocations from harmless textual mentions (`.github/hooks/tests/test_pre_command_guard.py:23-45`, `.github/hooks/tests/test_pre_command_guard.py:70-75`, `.github/hooks/tests/test_pre_command_guard.py:138-177`).

Most behavior is directly testable: deny the actual admin-merge invocation, preserve the plain queue verb, assert denial text, and inspect the isolated JSONL audit row. Strategically this is a repository-local contrib/enforcement rule for one concrete use case using an existing abstraction with one missing policy check; it is not a framework primitive.

## Required revisions

### R-1: Replace the non-substantive research reference before authority

Promote a compliant committed research record for FR-935, produced by rerunning the sole research route after its cited artifact-contract defect is repaired or by supplying an equivalent committed record. The record must contain 4-6 genuine solution classes, a precedent line for each, preserved planner disagreement, and an explicit `is_this_a_graph` answer. Update the FR's `**Research:**` field to point to that record.

The current platform survey recommends this rule but does not compare 4-6 solution classes or preserve disagreement (`docs/plan-research-merge-queue.md:81-100`), and the shared brief stops at problem, classification, constraints, and incidents (`feature-requests/research-briefs/fr934-merge-integration-toll-brief.md:16-82`). Recording that the route failed does not satisfy the prospective substance gate, which withholds authority from strawman research and requires solution classes, precedent, disagreement, and the graph answer (`.github/skills/judge-fr/doctrine.md:118-129`).

### R-2: Make FR-934 an enforceable prerequisite

Fold a dependency gate into the FR: FR-935 enforcement may begin only after FR-934 is merged and its implementation record proves that the merge queue is required on `main`, `strict` is false, and the required merge-group contexts report successfully. The FR already says its first event occurs after the queue is live and that the compliant verb auto-enqueues under FR-934 (`feature-requests/FR-935-deny-admin-merge-outside-break-glass.md:8-10`, `feature-requests/FR-935-deny-admin-merge-outside-break-glass.md:35-38`), but the dependency appears only as a Related note (`feature-requests/FR-935-deny-admin-merge-outside-break-glass.md:104-108`). FR-934 is still Proposed (`feature-requests/FR-934-merge-queue-on-main.md:3-5`), and its mechanical queue witnesses are AC-02 and AC-03 (`feature-requests/FR-934-merge-queue-on-main.md:121-128`). Denying the current routine escape before the replacement path works is not authorized.

### R-3: Remove the self-authorizing command-line escape

Delete `BREAK_GLASS=1` from the Summary, Proposed Solution, tests, and acceptance criteria. A bare variable that the same agent can add to its next command is not an authorization boundary; it turns the denial into an extra token while claiming to make bypass exceptional. The existing break-glass contract restricts bypass to named emergencies, places override authority with repository admins, and requires a diary incident record within 24 hours (`reference/break-glass.md:5-18`, `reference/break-glass.md:48-53`, `reference/break-glass.md:68-94`). Preserve that existing human path: the PreToolUse guard must deny agent-issued `gh pr merge --admin` even when prefixed with `BREAK_GLASS=1`, and its message must point the operator to `reference/break-glass.md`.

This is the smaller change that satisfies the stated problem and preserves the FR's own boundary between agent commands and the human browser (`feature-requests/FR-935-deny-admin-merge-outside-break-glass.md:75-78`). No edit to `reference/break-glass.md` is required or authorized.

### R-4: Define actual invocation matching and use the existing hook-test seam

Replace the ambiguous phrase "commands matching `gh pr merge`" with a behavioral boundary: deny terminal command segments that actually invoke `gh pr merge` and include `--admin`, regardless of the relative order of `--admin` and `--squash`; do not deny plain `gh pr merge --squash`, other `gh` subcommands, or search/echo text that merely mentions the forbidden command. Add the witnesses to `.github/hooks/tests/test_pre_command_guard.py`, not an unspecified `tests/unit/test_*guard*.py` family, and use `HOOK_LOG_DIR` to assert a stable denial reason without touching the live audit log. Update `.github/hooks/README.md`'s active-check table and audit-reason documentation.

The existing guard explicitly distinguishes executable contexts from grep/echo mentions for another forbidden flag (`.github/hooks/scripts/pre-command-guard.sh:334-340`), and the existing behavioral suite already encodes that false-positive contract (`.github/hooks/tests/test_pre_command_guard.py:138-177`). This revision makes the scope measurable without authorizing a generalized shell parser.

### R-5: Add requirement traceability and completion artifacts

Treat the admin-merge denial as a new capability. Add a capability registry file with a new `REQ-YG-XXX`, add the corresponding `ARCHITECTURE.md` capability index and requirement entry, tag every new test with that requirement, and reference the same requirement from the changelog fragment. Do not reuse `REQ-YG-527`: it specifically governs branch-create denial guidance (`ARCHITECTURE.md:510`, `ARCHITECTURE.md:2462-2466`; `capabilities/CAP-192-branch-deny-guidance-manual-worktree-lane.yaml:1-16`). The repository requires a capability file and requirement marker for every new capability (`.github/copilot-instructions.md:175-178`).

Also add the FR implementation record and the required diary reflection. These are process artifacts for this change, not permission to modify unrelated doctrine.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised FR and compliant committed FR-935 research record |
| D-2 | `.github/hooks/scripts/pre-command-guard.sh` admin-merge denial and stable audit reason |
| D-3 | `.github/hooks/tests/test_pre_command_guard.py` behavioral and audit witnesses |
| D-4 | `.github/hooks/README.md` active-check and audit-reason documentation |
| D-5 | One new `capabilities/CAP-XXX-*.yaml` file plus matching `ARCHITECTURE.md` index/requirement entries |
| D-6 | `changelog/unreleased/` feature fragment using the new requirement |
| D-7 | FR-935 implementation record and one `docs/diary/` reflection |

Not authorized: changing GitHub branch-protection or merge-queue settings; editing workflows or FR-934 implementation surfaces; changing `CLAUDE.md` merge ritual; modifying `reference/break-glass.md`; adding an agent-set escape variable, sentinel, or new user-command channel; blocking human UI/admin actions; removing admin rights; building a generalized shell parser; changing unrelated PreToolUse checks.

## Revised acceptance criteria

- [ ] AC-01: Real hook invocations of `gh pr merge --squash --admin` and `gh pr merge --admin --squash` are denied; the tests assert the PreToolUse denial response.
- [ ] AC-02: The denial message names `gh pr merge --squash` as the compliant queue verb and points to `reference/break-glass.md`; the isolated audit log contains one `decision: deny` row with a stable admin-merge reason.
- [ ] AC-03: `gh pr merge --squash`, a non-merge `gh` command, and grep/echo text that merely mentions `gh pr merge --admin` are approved by the real hook.
- [ ] AC-04: `BREAK_GLASS=1 gh pr merge --squash --admin` remains denied, proving that an agent cannot self-authorize the documented human emergency path.
- [ ] AC-05: `.github/hooks/README.md` lists the new denial, compliant command, break-glass pointer, and stable audit reason.
- [ ] AC-06: A new capability file and matching `ARCHITECTURE.md` entries define a new `REQ-YG-XXX`; all new hook tests and the changelog fragment reference it; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-07: A RED commit containing the failing hook witnesses precedes the GREEN guard implementation commit in the PR history.
- [ ] AC-08: The feature changelog fragment, FR-935 implementation record, and diary reflection are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement until R-1 through R-5 are folded into FR-935 and the compliant research record is committed. | GATE |
| C-2 | Do not enable the denial until FR-934 is merged and its implementation record proves queue-required `main`, `strict: false`, and successful required merge-group contexts. | GATE |
| C-3 | No agent-set environment variable, sentinel, or command-channel token may bypass the admin-merge denial. Human emergency override remains outside the agent PreToolUse boundary under `reference/break-glass.md`. | GATE |
| C-4 | Because this changes enforcement infrastructure, a human must review the guard diff and its false-positive/false-negative witnesses before merge. | GATE |
| C-5 | Preserve all unrelated PreToolUse behavior and the fail-closed input parser; tests must use an isolated audit directory. | GATE |
| C-6 | Do not modify branch protection, merge-queue workflows/settings, `CLAUDE.md`, or `reference/break-glass.md` under FR-935. | GATE |

Authority granted: after the revisions are folded and C-1 through C-4 are satisfied, implement only the agent-side `gh pr merge --admin` denial, its behavioral/audit tests, documentation, traceability, and completion artifacts within the frozen surfaces above.
