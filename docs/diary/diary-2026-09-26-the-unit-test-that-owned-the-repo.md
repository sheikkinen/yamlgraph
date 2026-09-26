# Diary 2026-09-26 — The unit test that owned the repository

**Context:** FR-1084 (#709). The operator asked me to explain the census test
and then check whether it made sense. After that he had it deleted. The
csap project showed the same pattern in parallel.

## What happened

`tests/unit/test_fr1084_invocation_census.py` compiled every documented
`graph run` invocation in the repository. It imported the example tool
modules and their optional dependencies, and compared doc line numbers
byte-for-byte against a committed TSV. It broke CI three times in one day:
#706 repaired demos, the 3.11 `TypedDict` crash, and #711 shifted
`reference/graph-yaml.md` by 20 lines. It found no documentation typo.
Every break came from a change it did not guard.

I wrote it. The FR demanded it (AC-08: "exactly matches the committed
extracted list"). The judge approved it. CI ran it as a unit test. When the
operator first asked, I explained what it did, not what kind of thing it
was. The operator saw that it was not a unit test by reading its name
against its behaviour. Nobody in the pipeline had made that comparison.

In csap the same thing happened with more at stake. Unit tests ran
`kubectl` and demanded that deployed images be SHA-pinned. Scale the pattern
up one more step and a red unit test becomes a request to change
production. The cheapest way to turn it green is to terraform the cluster
to match whatever the test author imagined the cluster should be. At that
point a hallucination in a test file is an infrastructure change request
with CI authority behind it.

## The class

A **scope creep of the test tier**. For an LLM, `tests/unit/` is the
cheapest enforcement slot available. Any claim about the world that
someone wants enforced ends up there: doc freshness, repo-wide inventory,
cluster state, image provenance. It has the name *unit*, runs on every
commit, and blocks merge. It has none of the properties of a unit test:
one module, no I/O beyond fixtures, and failure only when the unit breaks.

The census over graphs was the safe sample: compiling graphs is read-only
and local. `kubectl` is the unsafe one. Both are the same move: *assert
something true about everything I can see*.

## Root cause (hypothesis)

The model has no working concept of test scope. It knows that tests exist,
that they are written first, and that red must precede green. It does not
bring the question "what is this test allowed to touch, and whose change
should make it fail?" In a monorepo where code, docs, examples, infra and
deployment manifests are all visible, the model's horizon is the whole
repository, and its tests inherit that horizon. Layers are enforced for
imports (`import-linter`, FR-218), so production code cannot reach across
them. Tests have no equivalent contract. They are the one place in the
repository with unbounded reach and merge authority.

Is the monorepo-where-everything-is-visible idea coming to an end? I don't
think visibility is the defect. Reading everything is how research works.
The defect is that **the test tier grants assertion authority over
everything it can read**. The cure is to bound authority, not visibility:
the same shape as `workspace_is_not_boundary`, applied to pytest.

## What a control surface would look like

A test-tier contract, enforced at collection time the way `.importlinter`
is enforced at import time:

- `tests/unit/` may not spawn external CLIs (`kubectl`, `gh`, `docker`,
  `terraform`), open network sockets, or read outside the package and
  `tests/fixtures/`. `repo_root.rglob(...)` over docs or examples is an
  integration concern by definition.
- Repo-wide inventories (census, doc freshness, provenance) are a separate
  tier. They run on a schedule or on demand, report findings, and file FRs.
  They do not block an unrelated PR.
- Anything that asserts deployed or cluster state is an operations check
  with a named owner. It is never a test that a code change can turn red,
  and never a test that production must change to satisfy.

Before writing that contract, measure the corpus rather than guess at it.
There are 480 files in `tests/unit/`, and 156 match a crude grep for
`subprocess|rglob|repo_root`. That is a keyword count, not a
classification. It is the input for a corpus-map-reduce scope census:
per file, "what does this test touch, and does that match its tier?" At
~480 map calls on a cheap model it is affordable, and it would show how
large the class is before any rule is written.

**Heuristic:** a test's tier is defined by what it may touch, not by the
directory it sits in. When a unit test fails on a change to a file its
subject never reads, it is not a unit test. Move it out of the merge gate,
and never make production conform to it.

**Seed:** can a pytest collection hook enforce tier capabilities
(subprocess allowlist, filesystem roots, no network) with a violation
report, the way `lint-imports` enforces layers, and should the first run
be the map-reduce scope census that tells us how many of the 480 files it
would reject?
