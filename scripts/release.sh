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

# Step 6: Tag
git tag "v${VERSION}"
echo ""
echo "✓ Release v${VERSION} prepared."
echo "  Run: git push && git push --tags"
