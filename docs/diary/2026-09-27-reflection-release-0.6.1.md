# Release 0.6.1: tag the artifact that passed

## Observation

The release script prepares a tag before the repository's PR squash merge.
Using that tag after merging would publish a different commit from the one
on main. Repository instructions describe CHANGELOG.md as untracked, but
the actual index tracks it; the generated release update belongs in this
commit. This release uses the documented manual flow in an isolated
worktree and will tag only the merged release commit.

## Heuristic

Verify the current publishing workflow, not merely the release helper's
success message. Version declarations must agree, frozen fragments must
retain their content, and the tag must identify the merged artifact. The
tag workflow owns package publication and GitHub release creation; avoid a
second manual publisher racing it.

**Seed:** Should the release helper become preparation-only, leaving tag
creation to a verified merged-commit step?
