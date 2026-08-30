# Problem brief: diary reflection absence is detected only in CI

**Prior art:** filename-noun hits on other briefs sharing "local, diary,
existence, brief" are unrelated subject matter.
`diary-trap-recurrence-census.md` shares the noun "diary" but concerns
mining diary contents for recurring traps, not enforcing that a diary
exists — distinguished. `corpus-map-reduce-reference-contract.md`,
`census-human-readable-tail.md`, `corpus-census-skeleton-reuse.md` and
`session-accountability-record.md` are corpus/census/session-record
subjects with no enforcement-boundary overlap — not applicable.

## Problem statement

This repository enforces a doctrine step called Distill: every completed
task list must end with a metacognitive reflection file under
`docs/diary/`. Enforcement of that doctrine is split across two
locations, and the split is asymmetric.

The remote enforcement point (`.github/workflows/commitlint.yml`, job
`diary-gate`) is the only place that answers the question "does a diary
reflection EXIST for this work at all?". It extracts an `FR-NNN`
reference from the pull request title, checks the whole
`BASE_SHA..HEAD_SHA` diff for a path matching
`docs/diary/.*reflection.*fr-NNN`, and fails the pull request when no
such path appears. It then validates the content of any matching file
using the shared shell contract in `scripts/gate_artifact_semantics.sh`.

The local enforcement points (`.pre-commit-config.yaml`, hooks
`diary-reflection-check` and `diary-filename-check`) can only answer
"is a diary file that is ALREADY being committed well formed?". Both
hooks are scoped by `files: ^docs/diary/`, so when no diary file is
staged, neither hook runs. Their checks are re-implemented as inline
bash inside the YAML rather than sourcing the shared contract that CI
uses; the shared contract has no local consumer at all — its only
importers are the CI workflow and unit tests.

The consequence: a contributor can complete an entire `feat: FR-NNN`
branch, pass every local hook on every commit, push, open a pull
request, and only then learn that the required reflection was never
written. The feedback arrives after the branch is finished, at a point
where the author's working context for writing the reflection has
already decayed.

The comparable artifact, the changelog fragment, IS gated locally: a
`commit-msg` stage hook named `changelog-required` blocks any
`feat`/`fix` commit whose staged file list contains no
`changelog/unreleased/*.md`. No equivalent local hook exists for the
diary.

There is a plausible structural reason for the asymmetry. Doctrine says
the reflection is the FINAL task of a task list, written after the work
is done. A changelog fragment is naturally written together with the
first commit of a change, so a per-commit check matches its lifecycle. A
per-commit check does not match the diary's lifecycle: it would fail the
first `feat` commit of an arc for the absence of an artifact that
doctrine says comes last. A check that matches the diary's lifecycle
needs visibility over a whole branch range rather than a single commit,
and CI is currently the only place in the workflow that has that
visibility.

The open question this brief poses: where, in a local git workflow whose
required artifact is written last, should absence of that artifact be
detected — and what mechanisms exist for detecting it there, with what
failure modes?

## Classification

enforcement/latency-critical

## Constraints

- The doctrine ordering must not be inverted: the reflection is written
  after the work, not before it. Any check that forces it earlier is
  changing doctrine, not enforcing it.
- The check must have visibility over a branch range, not a single
  commit, because the artifact legitimately does not exist during most
  of the branch's life.
- Local checks in this repository are individually skippable by name
  (`SKIP=<hook-id>`); the blanket bypass `--no-verify` is forbidden by a
  pre-command guard. Skippability is accepted, not a defect.
- The semantic contract for what makes a reflection valid already exists
  in `scripts/gate_artifact_semantics.sh` and must not be duplicated a
  third time.
- The remote gate remains the merge boundary regardless of what is added
  locally; nothing local may become the sole enforcement.
- The default change flow routes all work through a git worktree, a pull
  request, and a squash merge. Pull requests are opened by hand with the
  GitHub CLI; no repository-owned script currently runs between "work is
  finished" and "CI runs".
- Setup documentation currently installs only the `pre-commit` and
  `commit-msg` hook types; no `pre-push` hook is installed anywhere.
- Solo maintainer with an agent-heavy workflow: a mechanism that depends
  on a human remembering to run something by hand is not enforcement.
- Latency budget: the existing local hook suite already runs a ~20s unit
  test pass; any addition must be near-instant shell or stdlib work.

## Witnessed incidents

- A prior feature request (FR-192) rejected a `pre-push` hook proposed
  for tag validation, on the grounds that such hooks are not installed
  by default, are easy to bypass, and were not used anywhere in the
  project. The rejection was for a different purpose but occupies the
  same mechanism territory.
- FR-380: a reflection could pass the local hook and still fail the
  remote gate because the local hook checked only placeholder stubs
  while the remote contract also required a literal `Seed:` marker.
  Parity was closed for content, not for existence.
- FR-373 hardened remote substance validation for the diary and
  changelog gates and explicitly left the local hooks out of scope.
- FR-228: a pipeline-produced `fix` pull request failed the remote gate
  because the reflection file was created and staged locally but never
  committed to the branch, so it was absent from the diff.
- FR-188: an automation prompt emitted reflection text but never wrote a
  file; the miss surfaced only as a remote gate failure.
- FR-191: a reflection existed but was named so the remote gate's path
  pattern did not match it, costing a rename and a re-push.
- FR-761: a reflection had to be renamed to satisfy the remote path
  pattern after the pull request was already open.
- FR-742 measured three separate dead sessions that abandoned the same
  final item, the diary reflection, and concluded that the remote gate
  catches missing reflections only when a pull request happens at all.
