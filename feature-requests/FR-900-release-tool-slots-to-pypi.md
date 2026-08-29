# Feature Request: Release yamlgraph so tool slots reach PyPI consumers

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-29
**First consumer / first event:** `yamlgraph-daily-digest` (FR-902), at the
moment its workflow runs `pip install yamlgraph` and invokes
`yamlgraph graph run graph.yaml --tool collect=sources/hn_rss.tool.yaml`.
That command exits non-zero against every version currently on PyPI.
**Research:** in-body `## Alternatives Considered` dispositioned table
(FR-889 style — an equivalent committed record per the TEMPLATE note).
**Prior art:** FR-901 and FR-902 are siblings filed in the same arc, not
precedent — FR-902 is the blocked consumer that motivates this release and
FR-901 needs only FR-768 manifests, already published. FR-187 (CI
dependency security scan) and FR-127 (conventional commit enforcement)
match on `release`/`pypi` but govern CI gates that run *during* a release,
not the decision to cut one; both remain in force and this FR changes
neither. FR-196 matches on `release` only and concerns unrelated release
notes. No prior FR proposes or rejects publishing a yamlgraph version;
this is a routine execution of `reference/release-checklist.md`, not a new
mechanism.

## Summary

FR-892 invocation-time tool-slot binding (`--tool`) is on `main` but not in
any published artifact. The latest PyPI release, `0.5.22`, is tagged at
`d8491fd9` (2026-08-17); FR-892 merged at `06d1dfe4` (2026-08-26).
`git merge-base --is-ancestor 06d1dfe4 v0.5.22` returns false. Cut a
release so external repos that install yamlgraph from PyPI can use slots.

## Value Statement

Repositories that consume yamlgraph as a dependency — not as a checkout —
gain access to tool slots, which is the only mechanism that lets one
pipeline graph serve many corpora without re-authoring.

## Problem

`main` carries **298 commits** since `v0.5.22`. The gap is invisible from
inside this repo, where every consumer is an editable install and every
example is a sibling directory. It becomes visible the moment an external
repo depends on the package:

| Feature | Added | In `v0.5.22`? |
|---|---|---|
| FR-768 tool manifests | `45389ba4` (2026-08-04) | yes |
| FR-892 tool slots (`--tool`) | `06d1dfe4` (2026-08-26) | **no** |

FR-902 plans to slot-bind the digest's collection tools. It cannot, until
this ships. The dependency is hard, not stylistic: the `--tool` flag does
not exist in the installed CLI, so the failure is an argparse error before
any graph loads.

A second, narrower observation belongs here because the release surfaces
it: `pyproject.toml` excludes `examples*` from the wheel
(`[tool.setuptools.packages.find] exclude`). The manifests under
`examples/shared/` — the toolbelt, `describe_image`, `split_document`,
`render_page` — are therefore **unreachable** from any PyPI consumer.
This FR does not change that. It records it so FR-902 does not plan
against a capability that does not exist, and so a future FR can decide
the question deliberately (see Related).

## Ideal Result

An external repo can `pip install 'yamlgraph>=0.5.23'` and immediately use
every tool-composition feature this repo documents in
`reference/graph-yaml.md` — manifests and slots alike — with no checkout,
no editable install, and no vendored copy of the framework. The release
itself is unremarkable: the existing checklist, run.

## Proposed Solution

Follow `reference/release-checklist.md` verbatim. No new mechanism.

```bash
VERSION="0.5.23"
mkdir -p "changelog/${VERSION}"
mv changelog/unreleased/*.md "changelog/${VERSION}/"
python scripts/aggregate_changelog.py > CHANGELOG.md
# bump pyproject, commit, push, tag — hook cascade per the checklist
```

Verification that the release actually carries the feature, rather than
trusting the version number:

```bash
python -m venv /tmp/relcheck && /tmp/relcheck/bin/pip install 'yamlgraph==0.5.23'
/tmp/relcheck/bin/yamlgraph graph run --help | grep -- --tool
```

`pyproject.toml` already reads `version = "0.5.22"` while the `v0.5.22`
tag points at an older commit, so the bump must land on a number above
the current file value, not above the tag.

## Acceptance Criteria

- [ ] A release tag exists whose commit has `06d1dfe4` as an ancestor
      (`git merge-base --is-ancestor 06d1dfe4 <tag>` exits 0)
- [ ] `pip install yamlgraph==<version>` into a clean venv, and
      `yamlgraph graph run --help` lists `--tool`
- [ ] A slot-bound graph runs end to end from that clean venv — the
      `examples/demos/corpus_census` fixture pair is the smoke, executed
      from a directory that is **not** a yamlgraph checkout
- [ ] `changelog/unreleased/` is frozen into `changelog/<version>/` and
      `CHANGELOG.md` regenerated
- [ ] The `examples*`-excluded-from-wheel finding is recorded in the FR
      Related section, with no code change in this FR

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | FR-902 installs yamlgraph from git (`pip install git+https://…@main`) | **Rejected.** Makes the digest depend on an unpinned moving branch; a broken `main` silently breaks an unattended 06:00 UTC cron with no one watching. Also hides the release gap instead of closing it. |
| A2 | FR-902 vendors a checkout of yamlgraph into its runner | **Rejected.** Reintroduces the `sys.path` coupling the refactor exists to remove, and forks the framework per consumer. |
| A3 | FR-902 drops slots, uses plain FR-768 manifests only (in `v0.5.22`) | **Viable fallback, not preferred.** Manifests alone give reuse-by-reference but not caller-supplied implementations, so "another digest" still means editing `graph.yaml`. FR-902 Phase 1 proceeds on this basis regardless; this FR unblocks Phase 2. |
| A4 | Also package `examples/shared/` manifests into the wheel | **Deferred, not rejected.** A real gap, but it is a distribution-policy decision (what is a public artifact vs. a demo) that deserves its own FR and its own judgement. Bundling it here would make a routine release carry a scope argument. |
| A5 | Do nothing; wait for the next release to happen incidentally | **Rejected.** 298 commits and 12 days of drift is how the gap arose. The consumer is now concrete and blocked. |

## Related

- FR-892 corpus-census pipeline / injected adapters — the feature awaiting release
- FR-768 tool manifests — already published in `v0.5.22`
- FR-819 GitHub-native digest PoC repo — created the consumer repo
- FR-902 daily-digest refactor — the blocked consumer
- `reference/release-checklist.md` — the procedure this FR follows
- `pyproject.toml` `[tool.setuptools.packages.find] exclude` — the
  `examples*` exclusion; candidate for a follow-on FR (A4)
