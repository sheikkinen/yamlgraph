# Feature Request: FR-192 Draconian Changelog Release Gate

**Priority:** HIGH
**Type:** Feature
**Status:** Implemented
**Effort:** 2 days
**Requested:** 2026-03-12

## Summary

Enforce changelog freeze before version bump with a pre-commit gate, an atomic release script, and a CI tag-push validator — eliminating the class of release drift where version is bumped but changelog fragments remain orphaned in `unreleased/`.

## Value Statement

Release managers (human and AI) get hard enforcement that changelog fragments are frozen before any version bump commit, reducing release drift from "possible despite documentation" to "impossible without `--no-verify`".

## Problem

The v0.4.63 release demonstrated changelog release drift: version bumped, commit pushed, tag created — all while 21 changelog fragments remained orphaned in `changelog/unreleased/`. The existing documentation in `reference/release-checklist.md` described the correct process, but documentation is advisory. The existing `changelog-gate` CI job (FR-149) only validates that feat/fix PRs include fragments; it does not verify release hygiene (version-to-changelog alignment).

**Root cause**: The release process has four steps — bump version, freeze changelog, commit, tag — but step 2 was **optional**. No gate prevented skipping it.

From the Scripture: *"What is hidden in commit shall be revealed in production."*

What is not gated is not guaranteed.

## Proposed Solution

Three enforcement layers, each catching what the previous might miss:

### Gate 1: Pre-commit Version-Changelog Sync Check

New script `scripts/check_changelog_release_sync.py` registered as a pre-commit hook:

```python
# scripts/check_changelog_release_sync.py
"""
Fail commit if BOTH conditions are true:
1. pyproject.toml version field changed in staged files
2. changelog/unreleased/ contains *.md files (excluding .gitkeep)

This forces changelog freeze before version bump commits.
"""
import subprocess
import sys
from pathlib import Path

def main() -> int:
    # Check if pyproject.toml version changed in staged diff
    diff = subprocess.run(
        ["git", "diff", "--cached", "--", "pyproject.toml"],
        capture_output=True, text=True,
    )
    if 'version = "' not in diff.stdout:
        return 0  # No version change — nothing to gate

    # Check for unreleased fragments
    unreleased = Path("changelog/unreleased")
    fragments = [f for f in unreleased.glob("*.md") if f.name != ".gitkeep"]
    if fragments:
        print("❌ Version bump detected but changelog/unreleased/ has fragments:")
        for f in sorted(fragments):
            print(f"   • {f.name}")
        print()
        print("Freeze first:")
        print('  VERSION="X.Y.Z"')
        print('  mkdir -p "changelog/${VERSION}"')
        print('  mv changelog/unreleased/*.md "changelog/${VERSION}/"')
        print("  python scripts/aggregate_changelog.py > CHANGELOG.md")
        print()
        print("Or use: scripts/release.sh <VERSION>")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Pre-commit hook registration (in `.pre-commit-config.yaml`, `local` repo section):

```yaml
- id: changelog-release-sync
  name: changelog release sync
  entry: .venv/bin/python scripts/check_changelog_release_sync.py
  language: system
  pass_filenames: false
  always_run: true
  stages: [pre-commit]
```

### Gate 2: Atomic Release Script

New script `scripts/release.sh` that encapsulates the entire release flow:

```bash
#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Usage: scripts/release.sh <VERSION>}"

# Step 1: Validate unreleased has fragments
FRAGMENTS=$(find changelog/unreleased -name '*.md' ! -name '.gitkeep' 2>/dev/null)
if [ -z "$FRAGMENTS" ]; then
    echo "❌ No fragments to release in changelog/unreleased/"
    exit 1
fi

# Step 2: Freeze changelog
mkdir -p "changelog/${VERSION}"
mv changelog/unreleased/*.md "changelog/${VERSION}/" 2>/dev/null || true
echo "✓ Froze fragments → changelog/${VERSION}/"

# Step 3: Bump version
sed -i '' "s/^version = .*/version = \"${VERSION}\"/" pyproject.toml
echo "✓ Bumped pyproject.toml → ${VERSION}"

# Step 4: Regenerate CHANGELOG.md
python scripts/aggregate_changelog.py > CHANGELOG.md
echo "✓ Regenerated CHANGELOG.md"

# Step 5: Commit (write msg to file to avoid dquote trap)
mkdir -p tmp
echo "chore(release): v${VERSION} changelog freeze" > tmp/msg.txt
git add changelog/ pyproject.toml CHANGELOG.md
git commit -F tmp/msg.txt

# Step 6: Tag
git tag "v${VERSION}"
echo ""
echo "✓ Release v${VERSION} prepared."
echo "  Run: git push && git push --tags"
```

### Gate 3: CI Tag-Push Release Hygiene

New job in `.github/workflows/commitlint.yml` triggered on tag push:

```yaml
release-hygiene:
  name: Release hygiene (tag validation)
  runs-on: ubuntu-latest
  if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
  steps:
    - uses: actions/checkout@v4
    - name: Verify changelog folder exists for tag
      run: |
        VERSION="${GITHUB_REF#refs/tags/v}"
        if [ ! -d "changelog/${VERSION}" ]; then
          echo "::error::Tag v${VERSION} created without changelog/${VERSION}/ folder"
          echo "Run: scripts/release.sh ${VERSION}"
          exit 1
        fi
        ORPHANS=$(find changelog/unreleased -name '*.md' ! -name '.gitkeep' 2>/dev/null | wc -l | tr -d ' ')
        if [ "$ORPHANS" -gt 0 ]; then
          echo "::error::Tag v${VERSION} pushed with ${ORPHANS} orphaned fragments in changelog/unreleased/"
          exit 1
        fi
        echo "✅ Release hygiene passed for v${VERSION}"
```

The workflow file needs `on: push: tags: ['v*']` added to its trigger conditions.

## Acceptance Criteria

- [x] `scripts/check_changelog_release_sync.py` blocks commit when version bumped with non-empty `unreleased/`
- [x] `scripts/check_changelog_release_sync.py` allows commit when version bumped with empty `unreleased/`
- [x] `scripts/check_changelog_release_sync.py` allows commit when version is NOT bumped (normal development)
- [x] Pre-commit hook `changelog-release-sync` added to `.pre-commit-config.yaml`
- [x] `scripts/release.sh` performs atomic freeze → bump → aggregate → commit → tag
- [x] `scripts/release.sh` fails if no fragments exist in `unreleased/`
- [x] CI `release-hygiene` job validates tag-to-changelog folder alignment on tag push
- [x] `reference/release-checklist.md` updated to reference `scripts/release.sh`
- [x] Unit tests for `check_changelog_release_sync.py`: version-bumped+fragments→fail, version-bumped+empty→pass, no-version-change→pass
- [x] Integration test for `release.sh`: happy path freeze→bump→commit→tag, and fail-on-empty-unreleased
- [x] `reference/release-checklist.md` links to `scripts/release.sh` as the canonical release command

## Alternatives Considered

### Pre-push hook for tag validation
Rejected. Pre-push hooks are unreliable (not installed by default, easily bypassed) and the project does not currently use them. The release script subsumes this — tag creation is gated within `release.sh`.

### Orphan detection lint rule (W023) in `yamlgraph/linter/`
Rejected for scope. The `yamlgraph/linter/` module lints YAML graph definitions, not project meta-files. Adding changelog lint rules there conflates graph authoring concerns with release process concerns. If orphan detection is needed, it belongs as a standalone pre-commit hook or advisory script, not a graph linter check.

### Five-gate approach (all from inbox proposal)
Reduced to three gates. Gates 2 (pre-push) and 4 (lint rule) from the original proposal were dropped: pre-push is subsumed by the release script, and the lint rule is wrong scope. Three layers (local pre-commit → release script → CI) provide defense-in-depth without over-engineering.

### Documentation-only approach
Rejected. The v0.4.63 incident demonstrated that documentation alone does not prevent drift. From the Scripture: *"What is not gated is not guaranteed."*

## Related

- **FR-149** (`FR-149-ci-changelog-gate.md`): CI changelog-gate for feat/fix PRs — predecessor, still needed for PR-level enforcement
- **FR-077** (`FR-077-changelog-commit-enforcement.md`): Local commit-msg hook requiring changelog fragments
- **FR-179**: Append-only changelog fragment architecture (`scripts/aggregate_changelog.py`)
- **FR-150**: Branch protection rules on `main`
- `reference/release-checklist.md`: Current (advisory) release documentation
- `.pre-commit-config.yaml`: Hook registration target
- `.github/workflows/commitlint.yml`: CI workflow target

## Implementation Notes

- The pre-commit hook checks `git diff --cached` (staged changes only), so it only fires when pyproject.toml version is actually being committed.
- `release.sh` uses `tmp/msg.txt` for the commit message per project convention (avoids dquote trap).
- The CI gate on tag push is defense-in-depth; even if bypassed locally with `--no-verify`, CI catches it. However, since tags are not PRs, this job cannot block the tag — it can only fail the workflow run as a signal. True prevention lives in the pre-commit hook.
- FR number reassigned from 189 → 192 because FR-189 is already allocated to "Graduate `downstream_fix` Trap".
