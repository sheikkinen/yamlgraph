---
name: release-version
description: "Release a new YAMLGraph version. Use when: bumping version, creating a release, tagging, pushing a release, freezing changelog, or handling pre-commit hook cascades during release."
argument-hint: "version number like '0.4.62'"
---

# Release Version

Bump, commit, push, and tag a YAMLGraph release. Canonical source: `reference/release-checklist.md`.

## Recommended: Atomic Release Script

```bash
scripts/release.sh 0.4.XX
git push && git push --tags
```

The script handles: validate changelog fragments → freeze to `changelog/0.4.XX/` → bump `pyproject.toml` → regenerate `CHANGELOG.md` → commit → tag.

## Manual Flow

### 1. Pull First

```bash
git pull
```

### 2. Add Changelog Fragments

```bash
cat > changelog/unreleased/FR-XXX-feature-name.md << 'EOF'
---
type: feat
scope: component
req: REQ-YG-XXX
---
- **FR-XXX Feature Name**: Description. (REQ-YG-XXX)
EOF
```

Fragment `type:` values: `feat` → Added, `fix` → Fixed, `removal` → Removed.

### 3. Bump Version

```bash
sed -i '' 's/version = "X.Y.Z"/version = "X.Y.W"/' pyproject.toml
```

### 4. Freeze Changelog

```bash
VERSION="X.Y.W"
mkdir -p "changelog/${VERSION}"
mv changelog/unreleased/*.md "changelog/${VERSION}/"
python scripts/aggregate_changelog.py > CHANGELOG.md
```

### 5. Commit (Handle Hook Cascade)

```bash
cat > tmp/msg.txt << 'EOF'
chore(release): vX.Y.W
EOF
git add -A
git commit -F tmp/msg.txt
```

Hooks will likely auto-fix files on first attempt. Re-stage and retry:

```bash
git add -A && git commit -F tmp/msg.txt
```

### 6. Push and Tag

```bash
git push
git tag vX.Y.W
git push --tags
```

### 7. Post-Push Verification

```bash
gh run list --limit 5 --json name,status,conclusion,headBranch \
  --jq '.[] | "\(.status) \(.conclusion // "—") \(.name) \(.headBranch)"'
gh release create vX.Y.W --title "vX.Y.W" --generate-notes
```

## Common Hook Failures

| Hook | Fix |
|------|-----|
| `ruff` | Auto-fixes style; re-stage |
| `ruff-format` | Auto-fixes format; re-stage |
| `trailing-whitespace` | Auto-fixes; re-stage |
| `req_coverage` | Add capability YAML to `capabilities/` |

## Phantom Requirement Fix

When `req_coverage --strict` fails:

```bash
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

Always write to file to avoid dquote trap:

```bash
cat > tmp/msg.txt << 'EOF'
feat(scope): FR-XXX summary

- Detail 1
- Detail 2
EOF
git commit -F tmp/msg.txt
```
