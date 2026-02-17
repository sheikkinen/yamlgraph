# Feature Request: Enforce FR Reference in feat: Commits

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-17
**Implemented:** 2026-02-17

## Summary

Add a commit-msg hook that requires `feat:` commits to reference a feature request (`FR-XXX`).

## Problem

The Scripture says "write the feature request" but this is cultural, not enforced. Features can be committed without documented planning. This creates risk of:
- Undocumented design decisions
- Features without acceptance criteria
- No audit trail for "why was this added?"

However, enforcing FR for *all* commits would create bureaucratic overhead for trivial changes (typos, dependency bumps, etc.).

## Proposed Solution

Use Conventional Commits prefixes to selectively enforce:

| Prefix | Requires FR | Rationale |
|--------|-------------|-----------|
| `feat:` | ✅ Yes | New capability needs planning |
| `fix:` | ❌ No | Bug fixes are reactive |
| `chore:` | ❌ No | Maintenance |
| `docs:` | ❌ No | Documentation |
| `refactor:` | ❌ No | Internal restructuring |
| `test:` | ❌ No | Test additions |
| `style:` | ❌ No | Formatting |
| `ci:` | ❌ No | CI/CD changes |
| `build:` | ❌ No | Build system |

### Implementation

Add to `.pre-commit-config.yaml`:

```yaml
  - repo: local
    hooks:
      - id: feat-requires-fr
        name: feat: commits require FR-XXX
        entry: bash -c 'msg=$(cat "$1"); if [[ "$msg" =~ ^feat: ]] && ! [[ "$msg" =~ FR-[0-9]+ ]]; then echo "ERROR: feat: commits require FR-XXX reference"; echo "Example: feat: FR-038 add commit enforcement"; exit 1; fi'
        language: system
        stages: [commit-msg]
        always_run: true
```

### Valid Examples

```
feat: FR-030 add subgraph streaming
feat(streaming): FR-030 add subgraphs parameter
fix: handle dict tokens in streaming
chore: update dependencies
docs: clarify streaming usage
```

### Invalid (blocked)

```
feat: add streaming support
feat(api): new endpoint
```

## Acceptance Criteria

- [x] Pre-commit hook added for `commit-msg` stage
- [x] `feat:` commits without `FR-XXX` are blocked
- [x] Other prefixes (`fix:`, `chore:`, etc.) are not blocked
- [x] Documentation updated in copilot-instructions.md
- [x] Hook tested with valid and invalid commit messages

## Implementation Notes

- Hook installed: `pre-commit install --hook-type commit-msg`
- Pattern uses bash variables to avoid quoting issues with parentheses in regex
- Tested with: `feat: add streaming` (blocked), `feat: FR-038 add enforcement` (pass), `fix: handle edge case` (pass)

## Alternatives Considered

1. **No enforcement** — Current state. Relies on discipline.
2. **Enforce all commits** — Too bureaucratic for trivial changes.
3. **Enforce yamlgraph/ changes only** — Complex to implement, doesn't align with commit intent.

## Related

- `.pre-commit-config.yaml` — Hook configuration
- `.github/copilot-instructions.md` — Sermon of the Chaplain (Plan step)
- Conventional Commits: https://www.conventionalcommits.org/
