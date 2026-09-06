# Keep or retire: the ramp, two weeks after its only install

**Date:** 2026-09-06
**Trigger:** operator: "explain the ramp feature", then "keep or retire".
**Context:** FR-864 (SPLIT) and its children FR-865 installer, FR-866
tailoring graphs, FR-867 first application, FR-868 salvage, FR-869
spike-end detector; all judged 2026-08-23, enforced 2026-08-24. No
commit has touched `ramp/`, `scripts/ramp_installer.py` or the three
`examples/demos/ramp_*` graphs for their own sake since.

## The question and why it is not idle

The ramp exists because a previous distributor, `scripture-dev`
(FR-207), shipped once, was never consumed, and sat for five months
with `Status: Implemented` while its `scripture.yaml` still read
`project_name: my-minesweeper`. The ramp's founding argument was that a
distributor that is not a consumer has nothing forcing it to stay true.
Two weeks in, the ramp is itself a distributor with one consumer. Asking
"keep or retire" now, on evidence, is the only way to avoid asking it in
February by inspection.

## What the record shows

Evidence gathered 2026-09-06 against `main` at `ec109c7e` and the
target repository over the GitHub API.

**The self-consuming design held.** All eight `mirror_exact` assets in
`ramp/manifest.yaml` are byte-identical to their live counterparts. The
drift test exists and is the mechanism; it costs nothing while green.

**The one install is alive and in use.** `sheikkinen/deviant-daily`
carries every Tier 3 destination today: pre-commit config, `AGENTS.md`,
`.github/hooks`, a tests workflow, `docs/incidents.md`, a nineteen-entry
capability registry, `scripts/judge.sh`, `scripts/req_coverage.py`. Its
tests workflow has run twenty-one times since the ramp, eighteen green.
The daily publish has been green for the twelve most recent runs. The
target authored and judged its own FR-886 through the installed route
the day after the ramp. That is the measure the case study set for
"acquired the process rather than a copy of it", and it is met.

**Something depends on it.** FR-869's spike-end warning in
`pre-command-guard.sh` names `scripts/ramp.sh <repo> --tier 1` as the
cure. Retiring the installer would leave an enforcement warning pointing
at nothing.

**Against it, honestly:**

- No second consumer. `ramp/consumers.md` has one row. The plan said
  "the next repo starts tomorrow"; the next spike, `yamlgraph-outsider`,
  went a different route.
- FR-867 never closed. Twelve of nineteen acceptance criteria are
  unchecked, including the CI witness and the blocked-commit witness.
  The target runs fine; the paperwork is what is stale.
- The installer does not run on Windows. Every installer test errors on
  this host: `os.path.normpath` produces backslashes so the manifest's
  "source not normalized" check rejects every entry, and the bash
  wrapper fails with `WinError 193`. The tailoring-graph tests pass. A
  portability gap, not rot; `main` is green on its Linux runner.
- The three tailoring graphs ran once. The 2026-08-24 diary records
  their output validating perfectly and being substantively wrong until
  a human read it. Nobody has run them since. The curated Tier 1
  pre-commit config ships twelve hook ids against forty-four live here;
  intentional curation, but drift with no test naming it.

## Verdict

Keep the mechanical core: `scripts/ramp.sh`, the manifest, the assets,
the drift tests, the consumers table. Leave the three tailoring graphs
as demos with no promise of currency. Close FR-867 with an honest record
of what was witnessed and what was not. Write the retirement trigger
down now so it is not a judgement call later.

Proposed trigger: no second row in `ramp/consumers.md` by 2026-12-31, or
a red drift test that stays red for thirty days. Either fires a
retirement FR of the FR-1004 shape, not a quiet leave-in-place.

## Trap

**Status is not evidence of use.** FR-207 read `Implemented` for five
months while dead. FR-867 reads `APPROVED WITH REVISIONS` with twelve
open boxes while its target runs green daily. The status line was wrong
in opposite directions both times. What told the truth was the
consumer's own record: its workflow runs, its commits, its FRs. The
question "does anything flow back, and does the target still run the
thing" is answerable mechanically from the target and never from the
source repo's paperwork.

**Heuristic:** for any distributor artifact, the keep-or-retire evidence
lives in the consumer, not in the FR. Query the consumer's CI runs and
recent commits before reading the FR's status line. The
`cross_project_graduation` sweep already reads `ramp/consumers.md`; a
`ramp.sh --check` that queries each consumer row's workflow runs would
make this diary entry unnecessary next time.

**Seed:** if the retirement trigger is "no second consumer by a date",
what does a second consumer actually look like? The next spike chose
the outsider route, not the ramp. Is that because the ramp's Tier 1
contract (pyproject, pytest, ruff) excluded it, or because nothing
announced the ramp at the moment the spike went live? FR-869 warns when
hooks are absent. Does it fire in a repository that has no `.git/hooks`
because it has no commits yet?
