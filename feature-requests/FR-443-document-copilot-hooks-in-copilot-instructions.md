# Feature Request: FR-443 Document Copilot Hooks in copilot-instructions.md

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.25 days
**Requested:** 2026-05-21

## Summary

Add a concise `### Copilot Hooks (.github/hooks/)` subsection under **Conventions** in `.github/copilot-instructions.md` so agents can self-debug hook denials without blind retries.

## Value Statement

Agents hitting hook denials get immediate, local doctrine for what failed and where to look, reducing retry loops and unnecessary user intervention.

## Problem

`.github/copilot-instructions.md` currently contains only one generic hook line:

- `Pre-commit, Pre- and Post-command hooks enforce style, commit format, and trailer rules — read hook output on failure before retrying.`

This lacks actionable details (what gets blocked, where checks live, how lockdown works, how reasoning sentinel behaves, and where to find full contract docs). The hook system is mature and documented in `.github/hooks/README.md`, but the primary instruction file does not surface a short operational map at point-of-use.

## Research Findings

1. `.github/hooks/README.md` already documents the full hook contract, lifecycle events, lock/unlock command channel, audit logging, and script layout.
2. `.github/hooks/pre-command-guard.json` wires `PreToolUse` to `.github/hooks/scripts/pre-command-guard.sh`.
3. `.github/hooks/post-edit-checks.json` wires modular `PostToolUse` checks (`python-checks.sh`, `yaml-checks.sh`, `markdown-checks.sh`, `fr-checks.sh`).
4. `.github/hooks/reasoning-pattern-check.json` wires the reasoning sentinel (`reasoning-pattern-check.sh`) that arms one-shot denials consumed by pre-command guard.
5. Existing implemented FRs (FR-414, FR-434, FR-442) show hook behavior evolved, but this specific user-facing summary is still missing from `.github/copilot-instructions.md`.

## Objectives

1. Add a short, high-signal hooks subsection in `.github/copilot-instructions.md`.
2. Make first-denial troubleshooting self-serve (what failed, what to read next).
3. Keep content concise and non-duplicative by linking `.github/hooks/README.md` for full detail.

## Constraints

1. Single responsibility: documentation-only change in `.github/copilot-instructions.md`.
2. No behavior changes in hook scripts, hook JSON config, CI workflows, or pre-commit.
3. Keep subsection concise (target <=15 lines) and operational.
4. Preserve existing doctrine ordering and headings outside the new subsection.

## Proposed Solution

Insert this subsection under `### Conventions` in `.github/copilot-instructions.md`:

```markdown
### Copilot Hooks (.github/hooks/)
- **PreToolUse**: `pre-command-guard.sh` blocks Co-authored-by trailers, `--no-verify`, multiline `git commit -m`, and pytest `| head/tail` without `tee`.
- **PostToolUse**: modular post-edit checks run via `python-checks.sh`, `yaml-checks.sh`, `markdown-checks.sh`, and `fr-checks.sh`.
- **Reasoning sentinel**: `reasoning-pattern-check.sh` can arm a one-shot denial consumed on the next tool call.
- **Lockdown channel**: run `.github/hooks/cmd lockdown|unlock|status` through terminal tool calls.
- **Audit trail**: decisions are logged in `.github/hooks/logs/audit.jsonl`.
- **Full contract**: see `.github/hooks/README.md` for architecture, outputs, and debugging workflow.
```

## Failing Acceptance Tests (RED)

Create:

- `.github/hooks/tests/test_copilot_instructions_hooks_docs_red.py`

Planned RED tests:

1. `test_ac01_hooks_subsection_exists_under_conventions`
   - Assert `.github/copilot-instructions.md` contains `### Copilot Hooks (.github/hooks/)` after the `### Conventions` heading.
2. `test_ac02_hooks_subsection_contains_required_operational_tokens`
   - Assert subsection includes: `pre-command-guard.sh`, `python-checks.sh`, `yaml-checks.sh`, `markdown-checks.sh`, `fr-checks.sh`, `reasoning-pattern-check.sh`, `.github/hooks/cmd lockdown`, `audit.jsonl`, `.github/hooks/README.md`.
3. `test_ac03_hooks_subsection_is_concise`
   - Assert subsection body is <=15 non-empty lines.

RED command:

```bash
pytest -q --no-cov .github/hooks/tests/test_copilot_instructions_hooks_docs_red.py
```

Expected RED reason before implementation: subsection does not exist in `.github/copilot-instructions.md`, so all AC tests fail.

## Acceptance Criteria

- [x] `.github/copilot-instructions.md` contains `### Copilot Hooks (.github/hooks/)` under `### Conventions`
- [x] Subsection explicitly mentions PreToolUse guard behavior (`pre-command-guard.sh`) and blocked command classes
- [x] Subsection explicitly mentions PostToolUse modular check scripts (`python-checks.sh`, `yaml-checks.sh`, `markdown-checks.sh`, `fr-checks.sh`)
- [x] Subsection documents reasoning-pattern sentinel behavior at a high level
- [x] Subsection documents lockdown command channel (`.github/hooks/cmd lockdown|unlock|status`)
- [x] Subsection references audit log path `.github/hooks/logs/audit.jsonl`
- [x] Subsection links `.github/hooks/README.md` as canonical detailed reference
- [x] Subsection is concise (<=15 non-empty lines)
- [x] RED tests added and passing after implementation

## Alternatives Considered

1. **Do nothing**: Rejected — leaves first-time denial handling opaque in the primary instruction file.
2. **Paste full README content into copilot-instructions**: Rejected — too verbose and high drift risk.
3. **Only link README with no inline summary**: Rejected — insufficiently actionable at denial time.
4. **Document in `CLAUDE.md` instead**: Rejected for this FR scope; issue targets `.github/copilot-instructions.md`.

## Related

- GitHub issue: `#431` — FR-443: Document Copilot hooks in copilot-instructions.md
- `.github/copilot-instructions.md`
- `.github/hooks/README.md`
- `.github/hooks/pre-command-guard.json`
- `.github/hooks/post-edit-checks.json`
- `.github/hooks/reasoning-pattern-check.json`
- `feature-requests/FR-414-copilot-hook-audit-logging.md`
- `feature-requests/FR-434-hook-modular-refactor.md`
- `feature-requests/FR-442-pre-command-guard-parse-consolidation.md`
