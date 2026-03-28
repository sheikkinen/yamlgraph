# Changelog Fragments

This directory contains changelog fragments following the [Keep a Changelog](https://keepachangelog.com/) format.

## Fragment Format

Create a markdown file in `unreleased/` with YAML front matter:

```markdown
---
type: feat
scope: core
req: REQ-001
---
- **FR-001 Description**: Details of the change. (REQ-001)
```

### Fields

| Field | Required | Values |
|-------|----------|--------|
| `type` | Yes | `feat` (Added), `fix` (Fixed), `removal` (Removed) |
| `scope` | No | Short scope identifier (e.g., `core`, `cli`, `api`) |
| `req` | No | Requirement ID (e.g., `REQ-001`) |

### File Naming

Use descriptive kebab-case: `FR-001-add-feature.md` or `fix-broken-parser.md`

## Generating CHANGELOG.md

```bash
# Shell version (no Python)
./scripts/aggregate_changelog.sh > CHANGELOG.md

# Python version (requires PyYAML)
python scripts/aggregate_changelog.py > CHANGELOG.md
```

## Release Workflow

```bash
VERSION="1.0.0"
mkdir -p "changelog/${VERSION}"
mv changelog/unreleased/*.md "changelog/${VERSION}/"
./scripts/aggregate_changelog.sh > CHANGELOG.md
git add changelog/
git commit -m "chore(release): ${VERSION} changelog freeze"
```
