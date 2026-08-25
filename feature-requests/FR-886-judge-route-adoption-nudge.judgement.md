# Judgement: FR-886 Judge-Route Adoption Nudge

**Prior art:** dispositioned in the FR (sole judge route NC-412/415; FR-767 sentinel mechanism; two_strike_split doctrine; FR-884 evidence).

**Verdict:** APPROVED WITH REVISIONS — the adoption-gap problem is real and the sentinel/nudge shape is appropriate, but authority activates only after the FR specifies a hook-visible judge lineage sentinel, an advisory-not-deny delivery path, and mechanically bounded detection/measurement criteria.

**Reviewed against:** `feature-requests/FR-886-judge-route-adoption-nudge.md`; `docs/FR-884-session-task-shapes.md`; `docs/FR-884-raw-read-log.md`; `feature-requests/FR-767-graph-authoring-sole-route.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/SKILL.md`; `.github/skills/judge-fr/MANIFEST.yaml`; `.github/skills/judge-fr/judgement.template.md`; `.github/hooks/scripts/reasoning-pattern-check.sh`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/hooks/scripts/checks/fr-checks.sh`; `.github/hooks/scripts/checks/common.sh`; `.github/hooks/tests/test_reasoning_pattern_check.py`; `.github/hooks/tests/test_authoring_guard.py`; `.github/copilot-instructions.md`.

## What is sound

FR-886 targets a demonstrated adoption gap rather than inventing a second judge. FR-884 reports judge-fr as 18.5% of the classified window token share while noting the judge graph already existed (`docs/FR-884-session-task-shapes.md:18-20`), and the raw read includes a dedicated serial judging session with roughly 29 of 30 turns spent on manual judge/rejudge loops (`docs/FR-884-raw-read-log.md:17-19`). The first consumer is named (`feature-requests/FR-886-judge-route-adoption-nudge.md:8-10`), the preferred route is already canonical (`.github/skills/judge-fr/SKILL.md:31-40`, `.github/skills/judge-fr/MANIFEST.yaml:43-48`), and the proposal correctly follows the `two_strike_split` doctrine that repeated prompt failures should move into code (`.github/copilot-instructions.md:116`).

The chosen precedent is architecturally aligned: FR-767 used a per-run sentinel plus PreToolUse guard to turn a sole-route claim into a mechanical boundary (`feature-requests/FR-767-graph-authoring-sole-route.md:119-147`), and the hook already has reusable parsing/audit helpers (`.github/hooks/scripts/checks/common.sh:30-112`) plus direct tests for sentinel scoping and one-shot behavior (`.github/hooks/tests/test_authoring_guard.py:73-82`, `.github/hooks/tests/test_reasoning_pattern_check.py:488-547`).

Strategic classification: framework tooling primitive. This is enforcement infrastructure for an existing governed route, not a new graph, example, or documentation-only pattern.

## Required revisions

### R-1: Define a hook-visible judge lineage sentinel

Revise the FR to specify the exact sentinel contract the hook will inspect. The current `scripts/judge.sh` lineage guard is only `JUDGE_EXECUTION=1` in the child process (`scripts/judge.sh:19-22`, `scripts/judge.sh:54-55`); it is not a per-run file/token contract like FR-767's authoring sentinel. Add the concrete environment variables, sentinel file path, token validation rule, lifetime, and cleanup behavior, or explicitly state that `scripts/judge.sh` must be amended to create them. Include tests for matching token, missing token, stale/mismatched token, and re-entry exemption.

### R-2: Replace the reasoning-pattern denial channel with an advisory channel

The FR currently says to arm the existing reasoning sentinel as an advisory (`feature-requests/FR-886-judge-route-adoption-nudge.md:60-62`), but the existing channel denies the next tool call and consumes the sentinel (`.github/hooks/scripts/pre-command-guard.sh:101-110`), and its tests assert denial (`.github/hooks/tests/test_reasoning_pattern_check.py:410-438`). Revise the delivery design to either emit PostToolUse feedback immediately or add a separate one-shot advisory sentinel that returns an allow/approve result with a message. Do not reuse the existing reasoning-pattern deny path unless the FR changes phase 1 from advisory to denial.

### R-3: Mechanically bound the detection surface and false-positive exclusions

Replace "judgement-shaped writes" with exact match rules. At minimum, detection must be limited to writes that create/update `feature-requests/*.judgement.md` or add a line matching the verdict taxonomy (`**Verdict:** APPROVED`, `APPROVED WITH REVISIONS`, `REJECTED`, or `SPLIT`) in a feature-request file. Add explicit exclusions for ordinary FR prose, cited prior judgements, template text, and this draft artifact in `tmp/`. The current `fr-checks.sh` only handles feature-request markdown feedback and prior-art reminders (`.github/hooks/scripts/checks/fr-checks.sh:16-83`), so the FR must state whether this lands there or in a new dedicated PostToolUse check.

### R-4: Split immediate implementation checks from the 30-day outcome metric

Keep the 30-day recensus target, but revise it into a documented follow-up measurement rather than an implementation-time pass/fail gate. Add the exact FR-884 classifier command, window semantics, output artifact path, and the query/calculation that computes "interactive judge-fr share < 5%." The current AC names the target but not the command (`feature-requests/FR-886-judge-route-adoption-nudge.md:77-79`), while FR-884's report makes clear the classifier and shares are estimates over a time window (`docs/FR-884-session-task-shapes.md:3-12`).

### R-5: Add a human-review gate for hook enforcement changes

Add an explicit enforcement condition that hook changes touching PreToolUse/PostToolUse behavior require human review before being treated as adopted. Judge doctrine requires adversarial review for enforcement-infrastructure changes (`.github/skills/judge-fr/doctrine.md:94-101`), and repo doctrine treats instruction/enforcement outputs as adversarial input (`.github/copilot-instructions.md:83-85`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | PostToolUse judgement-route detector in `.github/hooks/scripts/checks/fr-checks.sh` or a new dedicated hook script wired into the existing hook runner |
| D-2 | Hook-visible judge lineage sentinel support in `scripts/judge.sh` and/or hook environment handling |
| D-3 | One-shot advisory delivery mechanism that does not deny phase-1 tool calls |
| D-4 | Unit tests under `.github/hooks/tests/` covering detection, false positives, sentinel exemption, one-shot advisory behavior, audit rows, and deny-mode-off default |
| D-5 | FR implementation-status update with the exact recensus command and output artifact path |
| D-6 | Changelog fragment and diary reflection |

Not authorized: building or modifying the judge graph's judgement logic; changing the 8-criterion judge doctrine or verdict taxonomy; making phase-1 denial the default; blocking ordinary edits to FR prose that do not render a verdict; broad transcript scanning of private chat content; adding a second judge route; changing graph-authoring guards beyond reuse by pattern.

## Revised acceptance criteria

- [ ] AC-01: Unsentineled writes creating/updating `feature-requests/*.judgement.md` trigger exactly one advisory naming `scripts/judge.sh <fr-path>`.
- [ ] AC-02: Unsentineled writes that add a verdict-taxonomy line to `feature-requests/*.md` trigger exactly one advisory; ordinary FR prose, cited judgement text, templates, and `tmp/*.md` drafts do not trigger.
- [ ] AC-03: A `scripts/judge.sh`-launched execution carries a hook-visible judge lineage sentinel and is exempt; missing, stale, or mismatched sentinel data does not exempt.
- [ ] AC-04: Phase 1 never denies a tool call. The first subsequent relevant hook event emits or consumes the advisory once, and later calls in the same session do not repeat it unless a new unsentineled judgement write occurs.
- [ ] AC-05: Every advisory fire writes an audit row to `.github/hooks/logs/audit.jsonl` with hook name, session id when present, FR path, decision, and reason.
- [ ] AC-06: Deny-mode exists behind an explicit documented flag and defaults OFF; tests prove default advisory behavior and opt-in deny behavior.
- [ ] AC-07: Targeted hook tests in `.github/hooks/tests/` cover positive detection, false positives, lineage exemption, one-shot behavior, audit logging, and deny-mode default.
- [ ] AC-08: The FR records the exact recensus command, window semantics, and output artifact path for the next 30-day measurement of interactive judge-fr share < 5%.
- [ ] AC-09: Changelog fragment and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into the FR before implementation begins; no enforcement authority exists for the current text. | GATE |
| C-2 | Phase 1 must be advisory by default. Any default deny behavior requires a separate FR or an amended human-approved scope. | GATE |
| C-3 | The hook must not read the author's chat transcript or uncommitted working notes to infer intent; input closure for detection is the tool event, file path, written content, sentinel state, and repo files. | GATE |
| C-4 | Hook and sentinel changes are enforcement infrastructure and require human review before adoption. | GATE |
| C-5 | Do not weaken existing judge route, authoring route, reasoning-pattern, Co-authored-by, `--no-verify`, or graph-artifact guards while implementing this nudge. | GATE |

Authority granted: after the required revisions are folded into `feature-requests/FR-886-judge-route-adoption-nudge.md`, implement only the advisory judge-route adoption nudge and its hook tests within the frozen scope above.
