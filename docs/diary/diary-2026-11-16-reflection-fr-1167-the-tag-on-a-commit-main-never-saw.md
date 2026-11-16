# Reflection: FR-1167 — the tag on a commit main never saw

**Date:** 2026-11-16
**FR:** [FR-1167](../../feature-requests/FR-1167-release-flow-branch-pr-tag-squash.md)

## What happened

v0.6.6 was frozen, merged and never published. The release script tagged the
branch commit, and squash merge throws that commit away. The checklist
described a direct-push flow that branch protection had retired long before.
Each release since then worked only because the operator remembered the real
route. The one time the memory failed, the version sat merged but unpublished,
and nothing flagged it until PyPI was compared against `pyproject.toml`.

## Trap: the procedure that outlived its topology

A release document encodes the repository's topology at the time it was
written: where commits land, which commit survives, what triggers CI. Squash
merge and protected main changed that topology. The document and the script
didn't change, so they kept making an artifact (a tag on the branch commit)
whose meaning had gone. Nothing failed loudly, because the tag pointed at a
real commit.

## Heuristic

When the merge strategy or branch protection changes, check every script that
names a commit SHA, tag or ref. Ask which commit survives on main and whether
the script points at that one.

## Seed:

Could the release-hygiene CI job compare the latest `changelog/X.Y.Z/` freeze
on main against the published tags and PyPI, so that "merged but untagged" is
reported the day it happens rather than discovered at the next release?
