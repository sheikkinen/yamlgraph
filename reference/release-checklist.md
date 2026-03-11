# Release Checklist

Quick reference for the bump → commit → push → tag flow when pre-commit hooks and merge conflicts complicate the dance.

## The Flow

```bash
# 1. Pull first (avoid divergence)
git pull

# 2. If conflicts: stash local, pull, pop stash
mv conflicting-file.md conflicting-file-local.md  # if untracked conflicts
git stash
git pull
git stash pop
# Resolve conflicts, then: git add <resolved-files>

# 3. Add changelog fragments (FR-179)
cat > changelog/unreleased/FR-XXX-feature-name.md << 'EOF'
---
type: feat
scope: component
req: REQ-YG-XXX
---
- **FR-XXX Feature Name**: Description. (REQ-YG-XXX)
EOF

# 4. Bump version
sed -i '' 's/version = "X.Y.Z"/version = "X.Y.W"/' pyproject.toml

# 5. Stage and commit (expect hook failures)
git add -A
git commit -F tmp/msg.txt  # Will likely fail on first try

# 6. Handle hook cascade (repeat until green)
# - ruff: auto-fixes, re-stage
# - ruff-format: auto-fixes, re-stage
# - trailing-whitespace: auto-fixes, re-stage
# - req_coverage: Add missing capability/requirement to capabilities/*.yaml
git add -A && git commit -F tmp/msg.txt  # Repeat

# 7. Push and tag
git push
git tag v0.4.XX
git push --tags
```

## Common Hook Failures

| Hook | Symptom | Fix |
|------|---------|-----|
| `ruff` | E402 import order | Add `# noqa: E402` + confession |
| `ruff` | F841 unused variable | Remove or use the variable |
| `ruff-format` | Reformatted files | Just re-stage |
| `trailing-whitespace` | Modified files | Just re-stage |
| `req_coverage` | Phantom REQ-YG-XXX | Add capability YAML to `capabilities/` |

## Phantom Requirement Fix

When `req_coverage --strict` fails with "Phantom requirement IDs":

```bash
# Create capability file
cat > capabilities/CAP-XX-feature-name.yaml << 'EOF'
id: CAP-XX
name: Feature Name
fr: FR-XXX
requirements:
  - id: REQ-YG-XXX
    description: Brief description
EOF
```

## Multi-line Commit Messages

Always write to file, never inline:

```bash
cat > tmp/msg.txt << 'EOF'
feat(scope): FR-XXX summary

- Detail 1
- Detail 2
EOF
git commit -F tmp/msg.txt
```

This avoids the dquote trap from special characters in shell strings.
