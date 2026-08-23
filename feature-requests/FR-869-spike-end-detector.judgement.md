# Judgement: FR-869 Spike-End Detector - Warn When an Unenforced Repo Goes Live

**Verdict:** APPROVED WITH REVISIONS -- the detector belongs in its own enforcement-infrastructure FR and the need is proven, but authority activates only after the warning delivery channel, foreign-repo resolution, diff matcher, suppression/audit semantics, and human-review gate are made mechanically exact.

**Reviewed against:** `feature-requests/FR-869-spike-end-detector.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `docs/plan-ramp-spike-to-governed.md`; `docs/diary/diary-2026-08-23-the-spike-ends-at-a-commit.md`; `docs/diary/diary-2026-08-23-nothing-announces-the-absent-guard.md`; `feature-requests/FR-864-ramp-spike-to-governed.md`; `feature-requests/FR-864-ramp-spike-to-governed.judgement.md`; `feature-requests/FR-865-ramp-installer.md`; `feature-requests/FR-865-ramp-installer.judgement.md`; `feature-requests/FR-865-ramp-installer.amendment.judgement.md`; `feature-requests/FR-866-ramp-tailoring-graphs.md`; `feature-requests/FR-866-ramp-tailoring-graphs.judgement.md`; `feature-requests/FR-867-ramp-deviant-daily.md`; `feature-requests/FR-867-ramp-deviant-daily.judgement.md`; `feature-requests/FR-868-scripture-dev-salvage.md`; `feature-requests/FR-868-scripture-dev-salvage.judgement.md`; `.github/hooks/README.md`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/hooks/tests/test_pre_command_guard.py`; `.github/hooks/tests/conftest.py`. No author chat narrative was consumed, and no judge route was invoked.

**Prior art:** dispositioned in the body — FR-864 and its judgement named this detector and excluded it as separate enforcement-infrastructure work (controlling); FR-865…FR-868 are neighboring ramp-family surfaces, non-overlap; the two 2026-08-23 diary entries are the evidence record. No REJECTED prior art occupies this territory. FR-869 is the subject FR.

## What is sound

The problem is real and correctly located one layer above the missing control. FR-869 states the first consumer and event precisely: a commit introducing a scheduled workflow in a foreign repo with empty hooks should produce a warning naming `scripts/ramp.sh` instead of silence (`feature-requests/FR-869-spike-end-detector.md:14-18`). The diary evidence supports both halves: the spike transition is mechanically visible in commits adding unattended/public behavior (`docs/diary/diary-2026-08-23-the-spike-ends-at-a-commit.md:22-45`), and the absent repo hooks were silent while the workspace-level Copilot guard still followed the session (`docs/diary/diary-2026-08-23-nothing-announces-the-absent-guard.md:18-29`, `67-80`).

The split from the ramp family is correct. FR-864's judgement explicitly excluded `pre-command-guard.sh`, CI enforcement, judge/review doctrine, and spike/unenforced-repo detector behavior unless a separate enforcement-infrastructure FR authorized it (`feature-requests/FR-864-ramp-spike-to-governed.judgement.md:53-55`, `83-88`). The ramp plan repeats that FR-869 is the separate warn-only detector and that without it the "next repo, same week" measure is unreachable (`docs/plan-ramp-spike-to-governed.md:144-151`, `171-176`). FR-865 through FR-868 occupy neighboring but non-overlapping surfaces: installer assets, target-tailoring graphs, applying the ramp to `deviant-daily`, and `scripture-dev` salvage (`docs/plan-ramp-spike-to-governed.md:67-76`).

Warn-only is the right product boundary. The diary distinguishes informing the human from constraining the agent and rejects blocking as the wrong authority transfer (`docs/diary/diary-2026-08-23-nothing-announces-the-absent-guard.md:87-93`). FR-869 preserves that distinction: exit behavior is never affected, a blocking version is deferred to a new FR, and `.ramp-declined` lets a deliberate Tier-0 spike be made explicit (`feature-requests/FR-869-spike-end-detector.md:79-85`, `95-100`).

The implementation is feasible in the existing hook architecture, with revisions. The PreToolUse guard already parses hook JSON, inspects only terminal commands after the graph-authoring check, and logs audit entries (`.github/hooks/scripts/pre-command-guard.sh:52-83`, `169-305`, `371-373`). The hook README documents `pre-command-guard` as the active PreToolUse enforcement surface and lists the existing tests and audit log contract (`.github/hooks/README.md:70-80`, `137-155`, `208-218`). The existing pre-command test helper already runs the shell hook with JSON payloads, isolated `HOOK_LOG_DIR`, and captured output (`.github/hooks/tests/test_pre_command_guard.py:24-50`), so fixture scratch-repo tests are practical.

Strategic classification: **enforcement-infrastructure governance patch**, not a YAMLGraph framework primitive. It is a narrow guard enhancement around existing hook infrastructure and does not change YAMLGraph graph/runtime semantics.

## Required revisions

### R-1: Define a non-blocking warning delivery channel that preserves the hook JSON contract

Revise the FR so "prints a warning" has one exact implementation contract. The existing hook contract returns JSON on stdout (`.github/hooks/README.md:61-67`), and `pre-command-guard.sh` currently emits only JSON for approve/deny outcomes (`.github/hooks/scripts/pre-command-guard.sh:39-50`, `301-305`, `371-372`). A raw warning line on stdout before or after `{"decision":"approve"}` risks corrupting the hook response rather than warning the operator.

Fold this by requiring one of two explicit channels: either the warning is carried in a documented approve JSON field that the Copilot hook runtime displays, or it is written to stderr while stdout remains valid approve JSON, with a test proving the warning is visible in captured hook output and the stdout JSON remains parseable. The FR must state the exact output shape for one warning, two warnings, and no warning. Tests must assert no `permissionDecision: "deny"` appears in any FR-869 trigger case.

### R-2: Freeze foreign-repo and command-form resolution

Define exactly how the guard determines that a commit is happening in a foreign repo. FR-869 says checks are scoped to `git commit` commands in a foreign cwd (`feature-requests/FR-869-spike-end-detector.md:33-39`, `69-71`), but the current parser extracts command, tool name, session id, and tool use id only; it does not parse the hook payload's `cwd` (`.github/hooks/scripts/pre-command-guard.sh:52-83`). Without a closed contract, the implementation can either warn in this repo, miss nested repo cwd cases, or miss common shell forms such as `git -C <repo> commit`.

Fold this by adding a resolution table. At minimum: the hook-owning repo root is resolved from `.github/hooks/scripts/pre-command-guard.sh`; the command repo root is resolved from the hook payload `cwd` for plain `git commit`; nested directories inside either repo are normalized to their repo root; this repo never warns; non-git directories do not warn; and unsupported command forms are named. If `git -C <path> commit` or leading `cd <path> && git commit` are in scope, specify how the target path is parsed and add tests. If they are deliberately out of scope, state that explicitly so the bypass is a known limitation rather than accidental behavior.

### R-3: Make the hook-state and suppression contracts exact

Replace "empty `.git/hooks/`" and "missing or empty `.git/hooks/pre-commit`" with one mechanical predicate. FR-869 uses both formulations (`feature-requests/FR-869-spike-end-detector.md:16-18`, `33-39`, `72-78`, `89-91`), but those are not identical: a repo can have no `pre-commit` file, an empty `pre-commit`, an executable placeholder, a non-empty `commit-msg`, or hooks installed through a nonstandard path.

Fold this by defining the FR-869 predicate as exactly one of: `pre-commit` missing, `pre-commit` zero bytes, or the entire `.git/hooks/` directory absent/empty. If the detector intentionally treats only `pre-commit` as the governance witness, say so and update the "empty hooks" language. Also freeze suppression as repo-root `.ramp-declined`, never created by the guard, with tests for present/absent marker behavior. The marker should suppress both warnings but still create a non-secret audit entry such as `reason=ramp-declined` so a suppressed warning remains forensically visible.

### R-4: Specify the staged workflow diff matcher and data-leakage boundary

Make the spike-end signal mechanically checkable and non-leaky. FR-869 says `git diff --cached` adds `schedule:` or `secrets.` under `.github/workflows/` (`feature-requests/FR-869-spike-end-detector.md:75-80`, `92-94`), but it does not state whether matches come from added lines only, context lines, file headers, deleted lines, `.yaml` and `.yml` names, or comments. It also does not forbid logging the matched diff line, which could reveal secret names or workflow details.

Fold this by requiring the implementation to inspect only staged added lines in `.github/workflows/*.yml` and `.github/workflows/*.yaml`, excluding diff metadata lines such as `+++`. Define the exact match terms, for example added `schedule:` keys and added `secrets.` references. The warning and audit details must never include diff content, secret names, secret values, or workflow line text; they may include only repo identity, reason code, and whether the spike-end condition was present. Tests must cover added `schedule:`, added `secrets.`, deleted/context-only matches, non-workflow files, hooked repos, and `.ramp-declined`.

### R-5: Add the enforcement-infrastructure human-review gate to the FR

Add a human-review criterion before this guard change can become active. FR-869 correctly recognizes that it edits "the guard that edits everything else" (`feature-requests/FR-869-spike-end-detector.md:119-122`), and judge doctrine requires enforcement-infrastructure changes to be treated as adversarial input with explicit GATE conditions (`.github/skills/judge-fr/doctrine.md:96-101`). The current acceptance criteria require tests but do not require the human to review the exact warning behavior, suppression marker, and audit schema before the guard starts emitting new operational guidance.

Fold this by adding a criterion that records human review of the final guard diff, exact warning strings, suppression semantics, and audit reason names before merge or activation. This review must be recorded in the FR implementation section and must not authorize any ramp installer, CI, graph, judge/review doctrine, or target-repo changes.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-869-spike-end-detector.md` folding R-1 through R-5 |
| D-2 | `.github/hooks/scripts/pre-command-guard.sh` warn-only detector changes |
| D-3 | `.github/hooks/tests/test_pre_command_guard.py` fixture scratch-repo tests for foreign-cwd commit warnings |
| D-4 | `.github/hooks/README.md` documentation update for warning channels and audit reason names, if the behavior becomes part of the hook contract |
| D-5 | FR implementation-status update with RED/GREEN evidence, human-review record, and non-secret validation output |

Not authorized: changing any YAMLGraph runtime primitive; creating or materially editing `graph.yaml` or `prompts/*.yaml`; running graph-authoring, judge, review, or yamlgraph commands; implementing `scripts/ramp.sh` or ramp assets; applying the ramp to `deviant-daily` or any sibling repo; modifying target repositories; changing CI, pre-commit hook installation, judge/review doctrine, graph-authoring doctrine, branch protection, GitHub repository settings, or blocking policy; logging staged diff content, secrets, token-bearing values, hook audit logs, or target repo archives.

## Revised acceptance criteria

- [ ] AC-01: FR-869 is revised to define the warning output channel, foreign-repo resolution table, hook-state predicate, suppression marker contract, staged diff matcher, audit reason names, data-leakage boundary, and human-review gate from R-1 through R-5.
- [ ] AC-02: A fixture foreign repo with `pre-commit` missing according to the revised predicate, invoked through the supported plain `git commit`/payload-cwd command form, emits exactly the unenforced-repo warning through the approved non-blocking channel and returns parseable approve JSON with no deny decision.
- [ ] AC-03: A fixture foreign repo with a zero-byte or otherwise in-scope missing/empty `pre-commit` state emits the unenforced-repo warning; a fixture repo outside that predicate does not.
- [ ] AC-04: A staged added line matching `schedule:` in `.github/workflows/*.yml` or `.github/workflows/*.yaml` in an unenforced foreign repo emits the spike-end warning in addition to the unenforced-repo warning.
- [ ] AC-05: A staged added line matching `secrets.` in `.github/workflows/*.yml` or `.github/workflows/*.yaml` in an unenforced foreign repo emits the spike-end warning in addition to the unenforced-repo warning.
- [ ] AC-06: The same staged workflow diff in a fixture repo with the revised hook-state predicate satisfied as "enforced" emits no FR-869 warnings and still returns approve JSON.
- [ ] AC-07: Deleted lines, context lines, diff metadata, comments if excluded by the revised matcher, and non-workflow files do not trigger the spike-end warning.
- [ ] AC-08: Commits inside this repo, non-commit terminal commands, and non-terminal tools do not run the new foreign-repo git-diff inspection path and preserve the existing approve/pass behavior.
- [ ] AC-09: A repo-root `.ramp-declined` marker suppresses both FR-869 warnings, is never created by the guard, and records a non-secret suppression audit entry.
- [ ] AC-10: Every emitted warning records a non-secret audit entry with a stable reason name; audit details include no staged diff content, secret names, secret values, absolute paths outside the minimum repo identity policy, hook logs, or token-bearing text.
- [ ] AC-11: Source scans or targeted tests prove the implementation performs no mutating git command against the foreign repo and never changes the guard's deny/allow decision for FR-869 trigger cases.
- [ ] AC-12: Tests are added before implementation for the revised behavior above, using fixture scratch repos and isolated `HOOK_LOG_DIR`, with RED/GREEN evidence recorded in the FR.
- [ ] AC-13: The final guard diff, warning strings, suppression behavior, and audit schema receive recorded human review before activation.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into `feature-requests/FR-869-spike-end-detector.md`. | GATE |
| C-2 | Do not invoke or re-run the judge, judge skill, judge graph, or yamlgraph while acting on this judgement. | GATE |
| C-3 | FR-869 remains warn-only forever under this scope: no `permissionDecision: deny`, non-zero hook failure, commit blocking, branch protection change, or warn-then-block policy may be added. | GATE |
| C-4 | The hook stdout/return contract must remain valid for the Copilot PreToolUse runtime; warning delivery must not corrupt the approve JSON. | GATE |
| C-5 | Foreign-repo inspection may use only read-only filesystem and git operations; no command may stage, commit, write, install hooks, create `.ramp-declined`, or otherwise mutate a foreign repo. | GATE |
| C-6 | Warning text and audit entries must not contain staged diff content, secret names, secret values, credentials, token-bearing logs, or target repo archives. | GATE |
| C-7 | Enforcement-infrastructure human review is mandatory before activation because this modifies the live guard. | GATE |
| C-8 | If implementation requires changing ramp installer assets, CI policy, graph artifacts, judge/review doctrine, graph-authoring doctrine, or any target repo, stop for the owning FR or a new judgement. | GATE |

Authority granted: after the required revisions are folded and human review is recorded, enforcement may add the warn-only FR-869 detector to `.github/hooks/scripts/pre-command-guard.sh`, update directly related hook tests/docs, and record non-secret validation evidence within the frozen scope above.
