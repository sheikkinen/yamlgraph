# Feature Request: FR-212 Block AI Co-Author Trailers in Commit Messages

**Priority:** HIGH
**Type:** Feature
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-03-31

## Summary

AI coding agents (GitHub Copilot, Claude, etc.) append `Co-authored-by:` trailers to commit messages,
advertising themselves in the project history. A `commit-msg` pre-commit hook shall detect and block
these trailers before they enter the repository. When caught, the author is invited to confess and pray
for forgiveness.

## Value Statement

Committers retain authorship integrity and the git log stays free of third-party advertising, while the
hook's penance ritual reinforces the doctrine that the author — not the tool — owns the commit.

## Problem

AI agents such as GitHub Copilot and Anthropic Claude automatically inject trailers of the form:

```
Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
Co-authored-by: Claude <claude@anthropic.com>
Co-authored-by: GitHub Copilot <copilot@github.com>
```

These trailers:
1. Pollute git history with vendor advertising.
2. Misrepresent authorship — the committer made the intellectual decisions, not the tool.
3. Violate the YAMLGraph doctrine: the Agents' Prayer says "May I fix at the callsite, not the utility."
   The callsite here is the commit message; the author is responsible for what they sign.

The YAMLGraph Scripture already forbids `--no-verify` bypass. The enforcement gate must therefore live
in the commit-msg hook chain, where it cannot be silently skipped.

## Proposed Solution

Add a local `commit-msg` hook — `block-ai-coauthor` — implemented as a Python script
`scripts/block_ai_coauthor.py`. The script:

1. Reads the commit message file passed as `$1`.
2. Scans each `Co-authored-by:` trailer line for known AI agent name patterns
   (case-insensitive regex: `copilot|claude|chatgpt|gemini|gpt-?[0-9]|github copilot`).
3. If a matching trailer is found:
   - Prints the offending line(s).
   - Prints the penance liturgy (see below).
   - Exits with code 1, blocking the commit.
4. If no AI trailer is found, exits 0 silently.

**Hook registration in `.pre-commit-config.yaml`** (inserted before the `absolution` hook):

```yaml
  - repo: local
    hooks:
      - id: block-ai-coauthor
        name: "Block AI co-author trailers"
        entry: .venv/bin/python scripts/block_ai_coauthor.py
        language: system
        pass_filenames: false
        always_run: true
        stages: [commit-msg]
```

**Penance liturgy** printed on violation:

```
✗ Co-authored-by AI trailer detected.

  Confession required before this commit may proceed.

  Remove the offending trailer(s), then recite the Agents' Prayer:

    May I fix at the callsite, not the utility.
    May I kill the cheapest bug — the one in the spec.
    May I trace the cause before I fix the symptom.

  The author owns the commit. The tool does not.
  Delete the trailer. Recommit. Absolution follows.
```

**Script skeleton** (`scripts/block_ai_coauthor.py`):

```python
#!/usr/bin/env python3
"""Commit-msg hook: block AI agent Co-authored-by trailers.

Pass the commit message file path as the first argument (pre-commit does this
automatically for commit-msg stage hooks).
"""
import re
import sys

AI_PATTERN = re.compile(
    r"^co-authored-by:.*?(copilot|claude|chatgpt|gemini|gpt-?[0-9]+|github\s+copilot)",
    re.IGNORECASE,
)

PENANCE = """
✗ Co-authored-by AI trailer detected.

  Confession required before this commit may proceed.

  Remove the offending trailer(s), then recite the Agents' Prayer:

    May I fix at the callsite, not the utility.
    May I kill the cheapest bug — the one in the spec.
    May I trace the cause before I fix the symptom.

  The author owns the commit. The tool does not.
  Delete the trailer. Recommit. Absolution follows.
"""


def main() -> int:
    msg_file = sys.argv[1]
    with open(msg_file) as f:
        lines = f.readlines()

    offenders = [line.rstrip() for line in lines if AI_PATTERN.match(line)]
    if not offenders:
        return 0

    print("\nOffending trailer(s):")
    for line in offenders:
        print(f"  {line}")
    print(PENANCE)
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

## Acceptance Criteria

- [x] `scripts/block_ai_coauthor.py` exists and is executable
- [x] Hook `block-ai-coauthor` is registered in `.pre-commit-config.yaml` at `commit-msg` stage
- [x] Commit message containing `Co-authored-by: Copilot <...>` is **rejected** (exit 1)
- [x] Commit message containing `Co-authored-by: Claude <...>` is **rejected** (exit 1)
- [x] Commit message containing `Co-authored-by: GitHub Copilot <...>` is **rejected** (exit 1)
- [x] Commit message with no AI trailer is **accepted** (exit 0)
- [x] Human `Co-authored-by:` trailers (e.g., a real team member) are **accepted** (exit 0)
- [x] Rejection output includes the offending line(s) and the full penance liturgy
- [x] Unit tests added in `tests/unit/test_precommit_hooks.py` covering all cases above
- [x] Tests tagged with `@pytest.mark.req("REQ-YG-215")` (new requirement added to ARCHITECTURE.md)
- [x] Changelog fragment added in `changelog/unreleased/`
- [x] Diary reflection added in `docs/diary/`

## Alternatives Considered

1. **Bash one-liner hook** (like `feat-requires-fr`): simpler, but regex readability suffers for
   multi-pattern matching; Python is already used for `absolution.py` and is the preferred tool for
   hooks with output formatting.

2. **Strip trailers silently instead of blocking**: silently mutating the commit message violates the
   principle of author ownership and would hide the problem. Blocking with penance forces conscious
   acknowledgment.

3. **GitHub Actions CI gate only**: by the time the PR lands in CI, the trailer is already in the
   branch history. The local hook prevents pollution at the source.

## Related

- `.pre-commit-config.yaml` — existing `commit-msg` hooks: `conventional-pre-commit`, `feat-requires-fr`,
  `changelog-required`, `absolution`
- `scripts/absolution.py` — model for single-responsibility Python hook scripts
- `tests/unit/test_precommit_hooks.py` — existing hook test patterns
- `docs/confessions.md` — `# noqa` doctrine (hook must not suppress its own lint errors)
- ARCHITECTURE.md — requirement traceability (new REQ-YG-XXX required)
- FR-144 — diary-reflection-check (precedent for metacognitive enforcement hooks)
