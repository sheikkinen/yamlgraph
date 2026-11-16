# Release Checklist

How to release yamlgraph `X.Y.Z` to PyPI. Main is locked (FR-889) and only takes squash-merged PRs, so the release commit reaches main through a PR. Publishing starts when the tag `vX.Y.Z` is pushed: `.github/workflows/workflow.yml` then runs `build → publish → create-release`. **A merged release PR without a pushed tag publishes nothing** (FR-1167: v0.6.6).

## Route

```bash
# 1. Branch from an up-to-date origin/main in a worktree (main stays locked)
git fetch origin
scripts/worktree.sh new vX.Y.Z --prefix release/
cd tmp/worktrees/release/vX.Y.Z

# 2. Freeze, bump and commit. release.sh refuses to run on main and does not tag.
scripts/release.sh X.Y.Z

# 3. Push only the branch and open the PR
git push -u origin release/vX.Y.Z
gh pr create --title "chore(release): vX.Y.Z changelog freeze" --fill
```

4. Wait for the required PR checks, and merge-group checks if any, to pass.
5. **The human merge decision.** Green checks are not merge authority; the operator decides.

```bash
gh pr merge <N> --squash --delete-branch

# 6. Find the exact squash commit and check it
gh pr view <N> --json state,mergeCommit        # state must be MERGED
SHA=$(gh pr view <N> --json mergeCommit -q .mergeCommit.oid)
git fetch origin
git merge-base --is-ancestor "$SHA" origin/main && echo on-main
git show "$SHA:pyproject.toml" | grep '^version = "X.Y.Z"'
git show "$SHA:yamlgraph/__init__.py" | grep '__version__ = "X.Y.Z"'
git ls-tree -d "$SHA" changelog/X.Y.Z               # frozen fragments exist

# 7. Tag that commit and push only that tag
git tag -l vX.Y.Z      # must print nothing; if the tag already exists, stop and inspect
git tag vX.Y.Z "$SHA"
git push origin vX.Y.Z
```

Never tag the release branch commit, and never tag "whatever main is now". The squash merge creates a new commit; that commit is the one that publishes. Never delete or force-move an existing tag.

## Verify publication

There is no ordinary push-to-main CI run: `workflow.yml` triggers on PRs, merge groups and tags. The tag run is the publishing gate.

```bash
gh run list --branch vX.Y.Z --workflow CI --limit 1   # then: gh run watch <id>
gh run view <id> --json jobs -q '.jobs[]|.conclusion+" "+.name'
# build, publish, create-release: all success
gh release view vX.Y.Z                                 # created by the workflow
curl -s https://pypi.org/pypi/yamlgraph/X.Y.Z/json | python3 -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
# must print X.Y.Z
```

The workflow creates the GitHub release. Do not create it by hand.

## Recovery: merged but untagged

The freeze PR was merged but no tag was pushed, so PyPI still shows the previous version. Run steps 6–7 with **that PR's** squash SHA, then verify. If the tag CI fails, stop: fix the cause in a new FR and release the next version. Do not retarget the tag to dodge the failure. If the tag already exists, stop and inspect.

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
