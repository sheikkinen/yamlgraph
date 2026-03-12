# Release Checklist

Quick reference for the bump → commit → push → tag flow when pre-commit hooks and merge conflicts complicate the dance.

## Preferred: Atomic Release Script (FR-192)

The canonical release command is `scripts/release.sh`. It performs all steps atomically:

```bash
# One command: freeze → bump → aggregate → commit → tag
scripts/release.sh 0.4.64
git push && git push --tags
```

The script:
1. Validates `changelog/unreleased/` has fragments (fails if empty)
2. Freezes fragments → `changelog/{VERSION}/`
3. Bumps `pyproject.toml` version
4. Regenerates `CHANGELOG.md` via `aggregate_changelog.py`
5. Commits with `chore(release): v{VERSION} changelog freeze`
6. Creates `v{VERSION}` tag

## Manual Flow (if release.sh cannot be used)

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

# 5. Freeze changelog (move unreleased to versioned folder)
VERSION="X.Y.W"
mkdir -p "changelog/${VERSION}"
mv changelog/unreleased/*.md "changelog/${VERSION}/"
python scripts/aggregate_changelog.py > CHANGELOG.md

# 6. Stage and commit (expect hook failures)
git add -A
git commit -F tmp/msg.txt  # Will likely fail on first try

# 7. Handle hook cascade (repeat until green)
# - ruff: auto-fixes, re-stage
# - ruff-format: auto-fixes, re-stage
# - trailing-whitespace: auto-fixes, re-stage
# - req_coverage: Add missing capability/requirement to capabilities/*.yaml
git add -A && git commit -F tmp/msg.txt  # Repeat

# 8. Push and tag
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

## Release Gates (FR-192)

Three enforcement layers prevent changelog release drift:

| Gate | Layer | What it catches |
|------|-------|-----------------|
| `changelog-release-sync` | Pre-commit hook | Version bump with orphaned fragments |
| `scripts/release.sh` | Atomic script | Ensures correct ordering of freeze → bump → commit → tag |
| `release-hygiene` | CI (tag push) | Tag without `changelog/{VERSION}/` folder or with orphaned fragments |

The pre-commit hook `changelog-release-sync` (in `.pre-commit-config.yaml`) blocks any commit that bumps the `pyproject.toml` version while `changelog/unreleased/` still contains `.md` fragments. Use `scripts/release.sh` to avoid this — it freezes first, then bumps.
