# Problem brief: the weekly recap cannot see a pull request

**Prior art:** FR-700 (the `recap` demo graph — `examples/demos/recap/`, five
deterministic `type: tool` git nodes plus one LLM synthesis node, `--var since`
/ `--var repo_path`, portable to any git repository); FR-702 (recap
disposition axis — "workstreams list activity, not outcome"; verbatim FR
`Status:` lines, orphan partition mechanized out of the model); FR-703 (status
join as a deterministic post-pass); FR-704 (orphans assembled in code, commit
lines bit-exact); FR-930 (model-authored FR/NC refs reconciled against a
deterministic universe; `#N` tokens explicitly out of that scope); FR-821
(Monday cron runs the same graph, publishes `docs/recaps/<ISO-week>.md` via an
auto-merged PR; renderer `scripts/weekly_recap.py`); FR-962 and FR-899 (`gh`
based census adapters); `examples/demos/corpus_census/adapters/corpus_adapters.py`
(the committed `gh` boundary: `_gh()` line 101, fixed argv, `shell=False`,
`# noqa: S603`); `yamlgraph/tools/shell.py` (shell boundary: trusted YAML
command template, `shlex.quote()` on variables, `success_codes`); Scripture
`research_as_inventory`, `changelog_first_diagnostic`.

## Problem statement

`examples/demos/recap/graph.yaml` answers "what changed here last week?"
entirely from the local git object store — five `git log` calls and one
`git grep`. Neither the graph nor the `scripts/weekly_recap.py` renderer that
publishes its output every Monday reads pull requests.

On this repository that removes most of the week's decision record. In the
seven days to 2026-09-07, `main` received 108 commits, 92 of them (85%)
squash merges whose subject ends in `(#N)`. Squash merge is the required
strategy here, so the pull request holds the review rounds, check results,
open duration, and merge-or-abandon outcome; the commit keeps only a title
and a number the recap cannot resolve.

Two gaps are structural, not cosmetic. Work decided against leaves no trace:
a pull request closed unmerged contributes zero commits, so a git-only recap
is silent about it — even though FR-702 established for this same artifact
that a rejection is a deliverable. Work still in flight is equally invisible:
an open pull request has no commit on `main`, so a recap meant to orient
whoever resumes cannot say what awaits a merge decision or has gone stale.

There is also an identity question to settle first. The graph's only
repository input is `repo_path`, a filesystem path, chosen in FR-700 so the
demo runs against any git repository. Pull requests belong to a hosted
remote, reached over the network under an authenticated identity. Whatever
supplies the owner/name pair must not break the contract that a plain local
clone, or a repository missing the conventions, still yields a recap.

## Classification

judgement/analysis/generation

## Constraints

- Any git repository must still work via `--var repo_path`. No remote and no
  working credential must yield a recap, not an error. An empty axis and an
  unreachable axis must be distinguishable in state; substituting one for the
  other is forbidden (Commandment 6).
- FR-821's cron freezes the graph's arguments in
  `.github/workflows/weekly-recap.yml` and renders through
  `scripts/weekly_recap.py`. A new required input breaks that consumer. The
  recap step's env today carries no GitHub token.
- FR-703 and FR-704 bind this graph: joins and assembly are code. Any
  mechanically derivable field — a number, a state, a duration, a count —
  must not be asked of the model, whose remaining job is grouping and prose.
- Collected identifiers must reach the output bit-exact so every number is
  paste-safe. FR-930 reconciles model-authored FR/NC refs but leaves `#N`
  unchecked, so a model-retyped PR number has no witness today.
- Git collection is capped at 300 with truncation reported. A week with 100+
  pull requests is normal here, so any new collection needs the same.
- Five serial `type: tool` hops already precede the single LLM call, on a
  cron with a wall-clock budget. Network calls are not `git log`.
- `docs/recaps/` is committed output on protected `main`; the renderer's
  section contract changes under the same change or not at all.
- No new framework primitive: FR-700 shipped as YAML plus a graph-local
  python node module.

## Witnessed incidents

- The week's defining negative event is absent from git. Between 2026-08-31
  and 2026-09-07 exactly one pull request closed unmerged: #627,
  `docs(doctrine): FR-1013 doctrine and reference sweep after Chaplain
  removal`, closed 2026-09-06 after four judge rounds and three review
  rounds; FR-1013 was marked REJECTED and re-filed shorter as FR-1019.
  `git log --since="1 week ago"` on `main` holds none of its commits.
- Raw read of `docs/recaps/2026-W34.md`: all 26 workstream lines derive from
  commit subjects; the word "PR" never appears and no line carries a
  pull-request number though the commits do. Two details a generated sample
  would not produce — a multi-FR workstream concatenates several status
  strings and truncates one mid-sentence (`[Status: … this is the separate]`),
  and the 34-line Orphans section is dominated by `chore(release):` and
  `docs(diary):` commits, reading as noise rather than warning.
- `docs/recaps/` holds `2026-W34.md`, `2026-W35.md` and `2026-W36.md` and
  nothing for the current week as of 2026-09-07.
- Merge volume: `gh pr list --state merged` returns a full 100-item page for
  `mergedAt > 2026-08-31`. The 85% figure is
  `git log --since="1 week ago" --pretty=%s | grep -cE '\(#[0-9]+\)$'` = 92
  of 108.
- Open duration is already days wide: #633 was created 2026-09-06 and merged
  2026-09-07; #601, #602, #603 and #605 show the same overnight pattern.
  Nothing in a commit records that a change waited.
- A merged pull request's title can be the only record and can say nothing:
  #624 merged as `chore: Feat/diary chaplain`, a branch name promoted to a
  subject, referencing no FR. It counts as referenced solely because of
  `(#624)`.
- `gh` is already load-bearing here: `scripts/outsider.sh`,
  `scripts/review.sh` and the census adapters all shell out to it.
