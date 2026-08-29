# Feature Request: Release yamlgraph so tool slots reach PyPI consumers

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-08-29
**First consumer / first event:** `yamlgraph-daily-digest` (FR-908), at the
moment its workflow runs `pip install yamlgraph` and invokes
`yamlgraph graph run graph.yaml --tool collect=sources/hn_rss.tool.yaml`.
That command exits non-zero against every version currently on PyPI.
**Research:** in-body `## Alternatives Considered` dispositioned table
(FR-889 style — an equivalent committed record per the TEMPLATE note).
**Prior art:** FR-907 and FR-908 are siblings filed in the same arc, not
precedent — FR-908 is the blocked consumer that motivates this release and
FR-907 (SMTP email tool) needs only FR-768 manifests, already published.
FR-187 (CI
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

FR-908 plans to slot-bind the digest's collection tools. It cannot, until
this ships. The dependency is hard, not stylistic: the `--tool` flag does
not exist in the installed CLI, so the failure is an argparse error before
any graph loads.

A second, narrower observation belongs here because the release surfaces
it: `pyproject.toml` excludes `examples*` from the wheel
(`[tool.setuptools.packages.find] exclude`). The manifests under
`examples/shared/` — the toolbelt, `describe_image`, `split_document`,
`render_page` — are therefore **unreachable** from any PyPI consumer.
This FR does not change that. It records it so FR-908 does not plan
against a capability that does not exist, and so a future FR can decide
the question deliberately (see Related).

## Ideal Result

An external repo can `pip install 'yamlgraph>=0.5.23'` and immediately use
every tool-composition feature this repo documents in
`reference/graph-yaml.md` — manifests and slots alike — with no checkout,
no editable install, and no vendored copy of the framework. The release
itself is unremarkable: the existing checklist, run.

## Proposed Solution

Use the canonical release path. No new mechanism, and no hand-rolled
sequence — `scripts/release.sh` owns every state change (R-1):

```bash
scripts/release.sh <version>
git push && git push --tags
```

`<version>` must be the next unclaimed version **above the current source
version** (`pyproject.toml` reads `0.5.22` while the `v0.5.22` tag points
at an older commit, so the bump is against the file, not the tag) and
absent from PyPI and from local/remote tags.

`scripts/release.sh` freezes `changelog/unreleased/` into
`changelog/<version>/`, bumps **both** `pyproject.toml` and
`yamlgraph/__init__.py`, regenerates `CHANGELOG.md`, commits exactly those
files, and creates the `v<version>` tag. The tag then triggers the
existing build/publish workflow. There is no manual fallback in this FR:
reproducing those steps by hand is how the `__init__.py` bump gets missed.

### Verification, by artifact rather than by version number

Help surface:

```bash
python -m venv /tmp/yamlgraph-relcheck
/tmp/yamlgraph-relcheck/bin/pip install "yamlgraph==<version>"
/tmp/yamlgraph-relcheck/bin/yamlgraph graph run --help | grep -- '--tool'
```

Slot smoke, run from **outside any yamlgraph checkout** — necessary
because `examples*` is excluded from the wheel, so the fixture must be
copied rather than imported (R-2):

```bash
tmpdir="$(mktemp -d)"
cp -R examples/demos/corpus_census "$tmpdir/corpus_census"
cd "$tmpdir/corpus_census"
/tmp/yamlgraph-relcheck/bin/yamlgraph graph run graph.yaml \
  --tool discover=fixtures/discover.tool.yaml \
  --tool extract=fixtures/extract.tool.yaml \
  --var source=fixtures/corpus \
  --var rubric="classify each document's main topic in one word" \
  --var output_path="$tmpdir/corpus-census-ledger.md" \
  --var brief_path="$tmpdir/census-brief.md" \
  --var brief_rubric="What does this corpus cover overall?"
```

## Implementation Status

**Enforced 2026-08-29.** Released as **v0.5.23** (`03f779bf`, tag pushed;
workflow 33272323339 — `core-test`, `test (3.11)`, `test (3.12)`, `build`,
`publish`, `create-release` all green). 42 fragments frozen.

| AC | Result |
|---|---|
| AC-01 R-1/R-2 folded before enforcement | ✅ |
| AC-02 `scripts/release.sh 0.5.23` | ✅ |
| AC-03 release commit changes only release-owned surfaces | ⚠️ **deviation** — carries two release-blocking remediations (below) |
| AC-04 both version files at 0.5.23, `changelog/unreleased/` empty | ✅ |
| AC-05 `git merge-base --is-ancestor 06d1dfe4 v0.5.23` | ✅ exits 0 |
| AC-06 tag workflow publishes to PyPI | ✅ `pip index versions yamlgraph` → 0.5.23 |
| AC-07 clean venv outside repo: `--tool` in `graph run --help` | ✅ `--tool TOOL_BINDINGS  Bind a tool slot to an FR-768 manifest` |
| AC-08 exact R-2 smoke writes ledger **and** brief | ⚠️ **partial** — ledger yes, brief no (below) |
| AC-09 `examples*` wheel-exclusion recorded, no packaging change | ✅ |

### AC-03 deviation: two release-blocking remediations

Both were latent and surfaced only because a release touches
`pyproject.toml`, which runs hooks that ordinary commits skip:

1. **`pypdf` undeclared since FR-892.** `examples/demos` is `extra-backed`
   in the taxonomy, so the direct-import scan treats its imports as
   core-strict. Declared as a `corpus-census` extra with its own taxonomy
   row and a `docs/dependency-rationale.yaml` entry.
2. **`lint_inline_llm.py` walked the filesystem.** It failed on another
   session's *gitignored* scratch file under `tmp/` — a file it could
   never be asked to fix. Now enumerates `git ls-files`. Same defect as
   FR-907: a check that reads the filesystem where it means to read the
   repository.

Folding these into the release commit rather than splitting them was a
judgement call: the alternative left 46 staged release files sitting in a
shared index across a separate PR cycle, with three other sessions active
in the same checkout.

### AC-08 partial: the census demo is not portable

Verified from `$(mktemp -d)/corpus_census`, outside any git repository,
against the clean 0.5.23 venv. **Slot binding works**: both `--tool`
bindings resolved, discover → extract → map → reduce ran, and `ledger.md`
was written with real per-item judgements (`claude-haiku-4-5`,
`judge_item.v1`, three fixture documents classified with evidence spans).
That is the capability this release exists to publish, and it is proven.

The run then failed at the FR-895 brief tail with
`No module named 'examples'`. Cause:
`examples/demos/corpus_census/tools.py:200,216` does
`from examples.demos.corpus_census.adapters import census_brief` — an
absolute import rooted at the repo, which cannot resolve outside a
checkout because `examples*` is excluded from the wheel (AC-09).

So the demo runs only in-repo. This is a **pre-existing portability
defect in the demo**, not a defect in the release or in slot binding, and
it makes AC-08 unsatisfiable as the judgement worded it — the Judge
assumed the fixture pair was self-contained. Not fixed here: changing
`tools.py` is outside this FR's frozen scope. Candidate follow-up: make
the brief tail import relative to the graph directory, the way the slot
manifests already resolve.

## Acceptance Criteria

- [ ] `scripts/release.sh <version>` runs with `<version>` above the
      current source version and absent from PyPI and from git tags
- [ ] The release commit changes only release-owned surfaces:
      `changelog/<version>/`, `CHANGELOG.md`, `pyproject.toml`,
      `yamlgraph/__init__.py`
- [ ] `pyproject.toml` and `yamlgraph/__init__.py` both carry
      `<version>`, and `changelog/unreleased/` holds no `.md` fragments
- [ ] A release tag exists whose commit has `06d1dfe4` as an ancestor
      (`git merge-base --is-ancestor 06d1dfe4 v<version>` exits 0)
- [ ] The tag workflow publishes `yamlgraph==<version>`, or enforcement
      records the failed workflow URL and stops without bypassing release
      infrastructure
- [ ] In a fresh venv outside the repository,
      `pip install "yamlgraph==<version>"` succeeds and
      `yamlgraph graph run --help | grep -- '--tool'` exits 0
- [ ] The exact R-2 smoke, run from a copied `corpus_census` directory
      outside any yamlgraph checkout, exits 0 and writes both the ledger
      and the brief
- [ ] The `examples*` wheel-exclusion finding remains recorded in Related,
      with no packaging-policy code change in this FR

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | FR-908 installs yamlgraph from git (`pip install git+https://…@main`) | **Rejected.** Makes the digest depend on an unpinned moving branch; a broken `main` silently breaks an unattended 06:00 UTC cron with no one watching. Also hides the release gap instead of closing it. |
| A2 | FR-908 vendors a checkout of yamlgraph into its runner | **Rejected.** Reintroduces the `sys.path` coupling the refactor exists to remove, and forks the framework per consumer. |
| A3 | FR-908 drops slots, uses plain FR-768 manifests only (in `v0.5.22`) | **Viable fallback, not preferred.** Manifests alone give reuse-by-reference but not caller-supplied implementations, so "another digest" still means editing `graph.yaml`. FR-908 Phase 1 proceeds on this basis regardless; this FR unblocks Phase 2. |
| A4 | Also package `examples/shared/` manifests into the wheel | **Deferred, not rejected.** A real gap, but it is a distribution-policy decision (what is a public artifact vs. a demo) that deserves its own FR and its own judgement. Bundling it here would make a routine release carry a scope argument. |
| A5 | Do nothing; wait for the next release to happen incidentally | **Rejected.** 298 commits and 12 days of drift is how the gap arose. The consumer is now concrete and blocked. |

## Related

- FR-892 corpus-census pipeline / injected adapters — the feature awaiting release
- FR-768 tool manifests — already published in `v0.5.22`
- FR-819 GitHub-native digest PoC repo — created the consumer repo
- FR-907 SMTP email tool — sibling in the same arc; needs only FR-768
  manifests, so it is **not** blocked by this release
- FR-908 daily-digest refactor — the blocked consumer
- `reference/release-checklist.md` — the procedure this FR follows
- `pyproject.toml` `[tool.setuptools.packages.find] exclude` — the
  `examples*` exclusion; candidate for a follow-on FR (A4)
