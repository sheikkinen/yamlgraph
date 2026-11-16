#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Usage: scripts/release.sh <VERSION>}"

# FR-1167: the release commit must reach main through a squash-merged PR
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" = "main" ]; then
    echo "❌ Refusing to release on main: run on release/v${VERSION} and open a PR"
    echo "   See reference/release-checklist.md"
    exit 1
fi

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
sed -i '' "s/^__version__ = .*/__version__ = \"${VERSION}\"/" yamlgraph/__init__.py
echo "✓ Bumped pyproject.toml + yamlgraph/__init__.py → ${VERSION}"

# Step 4: Regenerate CHANGELOG.md
python3 scripts/aggregate_changelog.py > CHANGELOG.md
echo "✓ Regenerated CHANGELOG.md"

# Step 5: Commit (write msg to file to avoid dquote trap)
mkdir -p tmp
echo "chore(release): v${VERSION} changelog freeze" > tmp/msg.txt
git add changelog/ pyproject.toml yamlgraph/__init__.py CHANGELOG.md
git commit -F tmp/msg.txt

echo ""
echo "✓ Release v${VERSION} committed on ${BRANCH} (not tagged: the tag goes on the squash commit)."
echo "  Next (reference/release-checklist.md):"
echo "    git push -u origin ${BRANCH}"
echo "    gh pr create --title \"chore(release): v${VERSION} changelog freeze\" --fill"
echo "    after green PR checks and the human merge decision: gh pr merge <N> --squash --delete-branch"
echo "    SHA=\$(gh pr view <N> --json state,mergeCommit -q .mergeCommit.oid); git fetch origin"
echo "    git tag v${VERSION} \$SHA"
echo "    git push origin v${VERSION}"
