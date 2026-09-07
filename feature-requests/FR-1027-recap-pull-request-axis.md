# Feature Request: Recap Pull-Request Axis — What the Week Decided, Not Only What It Committed

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged 2026-09-07 — APPROVED WITH REVISIONS; R-1..R-5 folded (C-1 satisfied). Enforcement authority active for the frozen scope; C-3 (workflow credential wiring) and C-7 (RECAP_PAT scope) are human decisions before merge.
**Effort:** 0.5 days
**Requested:** 2026-09-07
**First consumer / first event:** the operator, next Monday morning, opening
`docs/recaps/<ISO-week>.md` on `main` — the artifact FR-821's cron already
publishes — and reading, for the first time, which pull requests merged last
week, which were closed unmerged, and which are still open. Second consumer:
any agent session running the recap against another repository
(`--var repo_path=…`) as `changelog_first_diagnostic` input, at the moment it
needs to know what is awaiting a merge decision.
**Research:** [FR-1027.research.md](FR-1027.research.md) — FR-890 sole route,
`scripts/research.sh` run 2026-09-07T14:19:33Z over
`feature-requests/research-briefs/recap-pr-axis-brief.md`. Four of five
personas executed (`yamlgraph_native_finding` failed the 400-character
`candidate` bound; its prose is preserved in the record's failure line and
is not counted); four distinct solution classes counted. The
Subtractionist's outright dissent and the librarian's timeline-API dissent
are preserved in the record and dispositioned under Alternatives.
`--verify-artifact` on the raw draft passes; `--verify-promotion` reports a
hash mismatch by design (LF normalisation on this Windows host, FR-955
precedent).
**Prior art:**
- [FR-700-timeframe-recap-example.md](FR-700-timeframe-recap-example.md) —
  created `examples/demos/recap/` and the contracts this FR must not break
  (`git -C {repo_path}` portability, convention-absence tolerance, `-n 300`
  cap with truncation reported, exactly one LLM node). This FR adds one axis
  to that graph; it does not create a second recap.
- [FR-702-recap-disposition-axis.md](FR-702-recap-disposition-axis.md) — the
  same `research_as_inventory` defect one level up: FR-702 gave FR *files* a
  disposition axis from their `Status:` field. Pull requests carry the same
  decision and still have none. DISTINCT: FR-702's source is a local `git
  grep` at HEAD; this FR's source is a hosted remote over the network.
- [FR-703-recap-status-join-post-pass.md](FR-703-recap-status-join-post-pass.md),
  [FR-704-recap-orphans-bypass-model.md](FR-704-recap-orphans-bypass-model.md)
  — binding precedent, adopted verbatim rather than re-litigated: joins and
  list assembly are code, collected lines reach the output bit-exact, the
  model neither copies nor joins. This FR's axis bypasses the model entirely,
  which is why the prompt and schema do not change.
- [FR-930-recap-code-owned-fr-reference-reconciliation.md](FR-930-recap-code-owned-fr-reference-reconciliation.md) — reconciles
  model-authored `FR|NC-N` tokens against a deterministic universe and
  explicitly leaves `#N` unchecked. DISTINCT: this FR does not extend
  reconciliation, because it never shows the model a pull-request number.
- [FR-821-weekly-recap-automation-pr.md](FR-821-weekly-recap-automation-pr.md)
  — the scheduled consumer that inherits this axis for free. Its workflow and
  renderer change under this FR; the graph it invokes is the same graph.
- [FR-819-github-native-digest-poc-repo.md](FR-819-github-native-digest-poc-repo.md)
  — precedent that a yamlgraph pipeline runs unattended in GitHub Actions with
  commit-based publication. Not a deliverable here.
- [FR-962-person-profile-census-authored-prs.md](FR-962-person-profile-census-authored-prs.md),
  [FR-899-org-repo-census-azure.md](FR-899-org-repo-census-azure.md) — the
  `gh`-based collection precedent, and the boundary this FR reuses
  (`examples/demos/corpus_census/adapters/corpus_adapters.py:101`, fixed argv,
  `shell=False`). DISTINCT: those are census pipelines whose unit of analysis
  is a PR or a repo, each with a map LLM call per unit and a reducer. This FR
  adds no LLM call and no per-PR classification; it collects one page and
  buckets it. `is_this_a_graph`: the graph already exists — this is a node in
  it, not a new pipeline.
- [FR-922-recap-bare-repo-test-skip-and-latency-investigation.md](FR-922-recap-bare-repo-test-skip-and-latency-investigation.md)
  — measured one recap invocation on a 3-commit bare repo at 283s and left the
  test unskipped with a gray-zone status. Binding on this FR as a latency
  budget: the new node must not add a second slow path, and the bare-repo
  integration test must not gain a network dependency.
- [FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md](FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md)
  — `reference/patterns/corpus-map-reduce.md`, the pattern for "read every
  commit or PR and summarize it". Dispositioned as NOT the shape here: one
  bucketing pass over one `gh` page is not a corpus map-reduce, and invoking
  that pattern for ~100 rows of mechanical metadata would be
  `growth_as_default`.
- [FR-046-diary-world-digest.md](046-diary-world-digest.md) — its rejected
  "GitHub Action only" option is not re-entered: publication remains FR-821's,
  unchanged.

## Summary

Add a pull-request axis to the existing `examples/demos/recap/` graph: one
graph-local python node derives the repository's `owner/name` from
`repo_path`'s `origin` remote, fetches one capped page of pull requests via
**exactly one bounded `gh` subprocess invocation** with fixed argv, and buckets
them into **merged in window**, **closed unmerged in window**, and **open
now** — membership decided against the exact epoch `git rev-parse --since`
returns, ordering and line assembly owned by code, each line bit-exact with
the number, dates, days open and title. The
axis never transits the model: the synthesis prompt and its schema are
unchanged, and the lists are attached by the existing `finalize_recap`
post-pass exactly as FR-704 attaches orphans. `scripts/weekly_recap.py` gains
the three sections; FR-821's workflow gains a token so the Monday cron can see
them. A repository with no `origin`, a non-GitHub remote, or no working `gh`
credential still produces a recap, and says in one line why the axis is
absent — distinguishable in state from an axis that ran and found nothing, and
from one that hit its 300-row cap.

## Value Statement

A reader of the weekly recap learns what the repository *decided* last week —
what shipped, what was abandoned, what is still waiting — instead of only what
it committed; and work that produced no commit, including every rejection,
stops being invisible.

## Problem

`examples/demos/recap/graph.yaml` collects entirely from the local git object
store: five `git log` calls and one `git grep`. Neither it nor
`scripts/weekly_recap.py` reads pull requests.

On this repository that omits most of the week's decision record. In the seven
days to 2026-09-07 `main` received 108 commits, 92 of them (85%) squash merges
whose subject ends in `(#N)`. Squash merge is the required strategy here
(`CLAUDE.md`, Pull Request Conventions), so the pull request holds the review
rounds, the check results, the open duration, and the merge-or-abandon
decision; the commit keeps only a title and a number the recap cannot resolve.

Two gaps are structural rather than cosmetic:

1. **Work decided against leaves no trace.** A pull request closed unmerged
   contributes zero commits to `main`, so a git-only recap of that week is
   silent about it. FR-702 already established for this exact artifact that a
   rejection is a deliverable and that a week of judgement work must not read
   as an empty week — a principle that today holds only for FR files, which
   carry a `Status:` field, and not for the pull requests carrying the same
   decision.
2. **Work still in flight is equally invisible.** An open pull request has no
   commit on `main`. A recap whose stated purpose is to orient whoever resumes
   after a week cannot tell them what awaits a merge decision or has gone
   stale — the state that most changes the next action.

Both are the `research_as_inventory` trap at the level FR-702 did not reach:
the recap describes activity that produced commits, and is silent on outcomes
that did not.

## Ideal Result

Monday's `docs/recaps/<ISO-week>.md` reports the week's decisions, not just its
commits: three code-assembled sections listing the pull requests merged, the
pull requests closed unmerged, and the pull requests still open, each row
carrying a paste-safe number, the dates, how many days it was open, and its
title — with no mechanical field anywhere in the file having passed through a
model, and with the same graph still producing a complete recap of a bare local
clone that has no remote, no credential, and no network.
## Judgement fold (2026-09-07)

Judged **APPROVED WITH REVISIONS** — [judgement](FR-1027-recap-pull-request-axis.judgement.md),
round 1 of the FR-1022 two-round budget. R-1 through R-5 are folded into the
sections below; the acceptance criteria are the judge's revised AC-01..AC-18
verbatim. Deltas from the pre-judgement draft, recorded so the change is
auditable:

| # | Revision | Where it landed |
|---|----------|-----------------|
| R-1 | Exact epoch controls membership; UTC date conversion is display-only. Stable code-owned ordering defined. | § 1 steps 2 and 4; AC-05, AC-06 |
| R-2 | "One network call" → **exactly one `gh` subprocess invocation**; 60 s timeout; four named narrow exception classes; no broad catch. | § 1 step 3; AC-08, AC-09 |
| R-3 | Three remote families with optional `.git`; malformed / local / non-GitHub remotes are unavailable with stable reasons and **no** `gh` call; argv-injection witness required. | § 1 step 1; AC-04, AC-08 |
| R-4 | `truncated` → `cap_reached`, "results may be truncated"; the axis note renders **once, before** the three sections, and cannot be suppressed by non-empty buckets; unavailable sections render `(not collected)`. | § 1 step 3, § 2, § 3; AC-11, AC-13 |
| R-5 | The real-run witness is a named file, `FR-1027.witness.md`, with a mechanically asserted `#627|` line. | AC-15 |

**Gates carried into enforcement** (all seven are GATE severity in the
judgement; C-1 is satisfied by this fold):

- **C-2** — `graph.yaml` is materially modified, so implementation goes
  through the governed graph-authoring route (`scripts/author.sh`) and
  preserves its validation report. Manual editing of the graph artifact is
  denied mechanically (FR-767).
- **C-3** — *for the human*: the `.github/workflows/weekly-recap.yml`
  credential wiring is enforcement-infrastructure input and must be approved
  by human review before merge. This FR does not self-certify it.
- **C-4** — the axis stays code-owned: never in the prompt, the model schema,
  a model-visible variable, or the reconciliation universe.
- **C-5** — no broad handler, silent fallback, unbounded wait, or fabricated
  empty-success state.
- **C-6** — reaching the cap qualifies the whole axis as potentially partial.
- **C-7** — *for the human*: if `RECAP_PAT` cannot read PR metadata, stop and
  return to planning rather than adding permissions, a second secret, or a
  token input. The PAT's scopes are not readable from outside the secret, so
  this cannot be verified before the first scheduled run; the failure mode is
  benign and self-reporting (the axis renders its own unavailable note), and
  the local witness run under AC-15 uses the developer's own `gh` credential.

The judgement carries no `### Questions for the human` section; per FR-740 that
is an omission rather than a "none", and C-3 and C-7 above are the two
decisions it should have surfaced.

## Proposed Solution

The minimal path back from the ideal result is one collection node, one
attachment in the existing post-pass, three renderer sections, and one
workflow env line. No new framework code, no new prompt, no new schema field,
no new LLM call.

### 1. One graph-local collection node

New `examples/demos/recap/nodes/prs.py`, registered as a `type: python` tool
and one node placed between `get_fr_statuses` and `partition`:

```yaml
tools:
  collect_prs_fn:
    type: python
    module: examples.demos.recap.nodes.prs
    function: collect_prs
    description: "PR axis (FR-1027): origin→owner/name, one bounded gh invocation, code-owned buckets; absence, unreachability and cap are reported, never substituted."

nodes:
  get_prs:
    type: python
    tool: collect_prs_fn
    requires: [repo_path, since]
```

`collect_prs(state)` returns one state key, `pr_axis: dict`, and does four
things in order, each of which can end the node with a recorded reason instead
of an exception.

**Step 1 — Identify (R-3).** `git -C <repo_path> remote get-url origin`
(fixed argv, `shell=False`). The accepted remote families, each with an
optional `.git` suffix, are exactly:

```
https://github.com/<owner>/<name>[.git]
git@github.com:<owner>/<name>[.git]
ssh://git@github.com/<owner>/<name>[.git]
```

Anything else ends the node **before any `gh` invocation**, with a stable
specific reason: `"no origin remote"`, `"origin host is <host>, not
github.com"`, `"origin is a local path remote"`, or `"origin URL is malformed
(no owner/name)"`. The derived `owner/name` is passed as **one** argv element,
never concatenated into a string that a shell or `gh` could re-split.

**Step 2 — Bound the window (R-1).** `git -C <repo_path> rev-parse
--since=<since>` returns `--max-age=<epoch>`; `<since>` is passed as one argv
element. **That exact epoch is the comparison boundary.** Membership is
inclusive against the epoch:

- `merged` when `mergedAt` is non-null and `mergedAt >= epoch`
- `closed_unmerged` when `mergedAt` is null, `closedAt` is non-null and
  `closedAt >= epoch`
- `open` when `state == "OPEN"`, regardless of age — staleness is the point

Everything else is dropped. The epoch is converted to a UTC `YYYY-MM-DD`
**only for the dates printed in a line**; the conversion never touches the
comparison, so a PR merged at 03:00 UTC on the boundary day is not silently
included or excluded by midnight truncation. Git's own date parser is reused,
so `since` keeps accepting exactly what the graph already accepts ("1 week
ago", "yesterday", "2026-07-01") with no second grammar and no new dependency.
An invalid `since` and a non-repository `repo_path` stay **loud**: the existing
git collection already fails those inputs and this node must not soften them.

**Step 3 — Collect (R-2, R-4).** Exactly **one** `gh` subprocess invocation
per recap, fixed argv, `shell=False`, with a **60-second timeout** matching
the cited precedent (`corpus_adapters.py:98-106`):

```
gh pr list --repo <owner/name> --state all --limit 300
           --json number,title,state,createdAt,mergedAt,closedAt
```

`gh pr list --limit 300` may paginate internally, so the claim is one
subprocess invocation, not one HTTP request. Four **narrow** exception classes
are handled, each returning `available: False`, empty buckets, and a stable
non-empty reason — no broad `except Exception`:

| Failure | Reason string |
|---|---|
| `FileNotFoundError` | `"gh not found on PATH"` |
| `subprocess.TimeoutExpired` | `"gh timed out after 60s"` |
| `subprocess.CalledProcessError` | `"gh exited <code>: <first stderr line>"`, or `"gh exited <code> with no stderr"` when stderr is blank |
| `json.JSONDecodeError`, or a row missing a required field | `"gh returned unparseable JSON"` / `"gh row missing required field <name>"` |

Exactly 300 returned rows set `cap_reached: True`. Per R-4 this is **not** a
proof of truncation — a 301st row is not observable — so the recorded and
rendered wording is "cap reached; results may be truncated", and the buckets
claim completeness only *within the returned capped response*.

**Step 4 — Bucket and order, in code (R-1).** Ordering is code-owned and
stable, never dependent on undocumented `gh` response order:

- `merged` and `closed_unmerged`: decision timestamp descending, then PR
  number descending
- `open`: `createdAt` descending, then PR number descending

Each bucket is a list of lines assembled by string formatting, never by a
model:

```
#633|2026-09-06→2026-09-07|1d|feat(judge): FR-1022 round sentinel — third judgement is fixed text, not a model call
#627|2026-09-06→2026-09-06|0d|docs(doctrine): FR-1013 doctrine and reference sweep after Chaplain removal
#640|2026-09-05→open|2d|docs(fr): FR-1027 recap pull-request axis
```

Days are whole elapsed UTC days, `floor((end - start) / 86400)`; an open row's
end is the collection timestamp. Titles are copied verbatim from the `gh` JSON.

`pr_axis` shape (the code-owned contract):

```python
{"available": True,  "reason": "", "cap_reached": False,
 "merged": [...], "closed_unmerged": [...], "open": [...]}
{"available": False, "reason": "no origin remote", "cap_reached": False,
 "merged": [], "closed_unmerged": [], "open": []}
```

`available: True` with three empty lists is a week with no pull requests;
`available: False` is a week we could not look at. Commandment 6: the two are
different values, and the renderer prints different text for them.

### 2. Attachment by the existing post-pass

`finalize_recap` in `nodes/partition.py` already owns the assembly of
code-only fields (FR-704 orphans). It gains four keys read straight from
`pr_axis` — `pr_merged`, `pr_closed_unmerged`, `pr_open`, and one axis-level
`pr_axis_note` composed as:

- available and cap not reached → `""`
- unavailable → `"pull-request axis unavailable: <reason>"`
- cap reached → `"pull-request cap of 300 reached; results may be truncated"`,
  appended after the unavailable clause if both hold

No reconciliation is needed and none is added: the model never sees a pull
request, so it cannot invent one (C-4).

`prompts/recap.yaml` is **not modified**. The inline schema stays
`{workstreams, hotspots}`. This is the whole reason the change is 0.5 days:
FR-704 already built the channel for code-owned output, and this axis uses it.

### 3. Renderer and cron

`scripts/weekly_recap.py`: `SECTIONS` gains the three keys, with a title map
so `pr_closed_unmerged` renders as `## Pull requests closed unmerged` rather
than `## Pr_closed_unmerged`. Per R-4 the note has **one** placement that
cannot be suppressed: when `pr_axis_note` is non-empty it is emitted **once,
before** the three PR sections, whether or not their buckets carry rows. An
available empty bucket renders `(none)`, as the three pre-existing sections
do; an unavailable bucket renders `(not collected)`, because `(none)` would
assert an observation that was never made. Existing section headings and
order are untouched.

`.github/workflows/weekly-recap.yml`: the `Run recap` step's `env` gains
`GH_TOKEN: ${{ secrets.RECAP_PAT }}` — the existing secret, scoped to that one
step, no new credential and no new workflow permission (C-3, C-7). `gh` is
preinstalled on `ubuntu-latest`; without a token the axis would report itself
unavailable every Monday, which is honest but useless.

### 4. Registry and witness

`capabilities/CAP-195-timeframe-recap-demo.yaml`: `fr:` gains FR-1027; a new
requirement `REQ-YG-669` states the axis contract. `ARCHITECTURE.md`
regenerated. Per R-5 the real run is committed as
`feature-requests/FR-1027.witness.md`, recording the run date, repository
slug, exact `since` input, collection timestamp, cap status and the three
buckets, with a test asserting its closed-unmerged section carries a line
beginning `#627|`.

## Acceptance Criteria

Verbatim from the judgement's revised set.

- [ ] **AC-01** `yamlgraph graph lint examples/demos/recap/graph.yaml` passes
      and the graph has exactly one LLM node, `synthesize`.
- [ ] **AC-02** `prompts/recap.yaml` is byte-identical to its pre-change
      content; its schema fields are exactly `{workstreams, hotspots}` and its
      template references no PR state.
- [ ] **AC-03** The existing tool-node set and every existing `type: shell`
      command remain unchanged; `test_collection_is_tool_nodes` and
      `test_git_commands_are_portable` pass unmodified.
- [ ] **AC-04** Unit tests accept the three GitHub remote families and optional
      `.git` suffix from R-3; missing, malformed, local/file, and non-GitHub
      remotes return stable unavailable reasons and never invoke `gh`.
- [ ] **AC-05** A unit test proves `--since=<since>` is passed as one argv
      element to `git rev-parse`, the exact returned epoch controls inclusive
      timestamp membership, and UTC date conversion is display-only.
- [ ] **AC-06** A scrambled committed fixture proves exact bucket membership
      and R-1 ordering for in-window merged, before-window merged, in-window
      closed-unmerged, before-window closed-unmerged, and old open PRs.
- [ ] **AC-07** Every line equals `#<number>|<created>→<end>|<N>d|<title>`
      exactly, including fixture title bytes; duration is whole elapsed UTC
      days.
- [ ] **AC-08** Exactly one fixed-argv, `shell=False` `gh` subprocess
      invocation is attempted for an eligible remote, with a 60-second
      timeout; a crafted remote cannot add or split argv.
- [ ] **AC-09** Missing `gh`, timeout, non-zero exit with and without stderr,
      invalid JSON, and missing required JSON fields each yield
      `available: False`, empty buckets, and a stable non-empty reason through
      narrow exception handling.
- [ ] **AC-10** Available zero-row output is distinct from unavailable output;
      no error branch fabricates populated buckets.
- [ ] **AC-11** A 300-row fixture marks `cap_reached: True` and reports that
      results may be truncated; a 299-row fixture does not. The contract
      claims completeness only within the returned capped response.
- [ ] **AC-12** `finalize_recap` attaches the three buckets and one axis note
      while leaving `workstreams`, `orphans`, `hotspots`, and
      `unverified_refs` behavior unchanged; inherited FR-702/703/704/930 tests
      pass unmodified.
- [ ] **AC-13** Exact renderer tests cover available-empty as `(none)`,
      unavailable as one visible axis note plus `(not collected)`, and
      cap-reached output with both non-empty and empty buckets; existing
      section headings and order are preserved.
- [ ] **AC-14** The bare-repo integration fixture has no origin and makes no
      `gh` call; the complete recap records the absent-origin note without
      adding a second slow/network path.
- [ ] **AC-15** `feature-requests/FR-1027.witness.md` contains the metadata
      required by R-5 and a closed-unmerged line beginning `#627|`, verified
      mechanically.
- [ ] **AC-16** `.github/workflows/weekly-recap.yml` passes
      `${{ secrets.RECAP_PAT }}` as `GH_TOKEN` only to the recap step,
      verified by a workflow-YAML test.
- [ ] **AC-17** RED tests and GREEN implementation are separate commits and
      `git log` shows that order.
- [ ] **AC-18** `CAP-195` contains `REQ-YG-669`; every new test carries
      `@pytest.mark.req("REQ-YG-669")`; regenerated `ARCHITECTURE.md`, strict
      requirement coverage, targeted recap tests, graph lint, README,
      changelog fragment, FR implementation notes, and diary distillation are
      present and passing.

## Alternatives Considered

Recorded in full, with disagreement preserved, in
[FR-1027.research.md](FR-1027.research.md). The four that shaped this proposal:

1. **A `gh` shell tool instead of a python node.** Rejected: every existing
   shell tool in this graph is asserted to be a portable `git -C {repo_path}`
   command (`test_git_commands_are_portable`), a `gh` command would break that
   invariant, and stdout cannot distinguish "no pull requests" from "no
   credential" without a `|| true` — the silent fallback
   `test_no_silent_fallback_in_commands` forbids.
2. **Show the model the pull requests and let it join them to workstreams.**
   Rejected: FR-703 and FR-704 were both written because this graph's model
   corrupted mechanical fields (a one-character hash corruption, reproducibly,
   twice). PR numbers would need FR-930-style reconciliation extended to `#N`.
   The join is also not required by the ideal result, so it is scope creep with
   momentum.
3. **A census pipeline over the week's pull requests** (the FR-962 /
   `corpus-map-reduce` shape, one LLM classification per PR). Rejected as
   `growth_as_default`: the gap is mechanical metadata the reader can read, not
   a classification, and a per-PR LLM call on a cron already measured at 283s
   for one invocation (FR-922) buys nothing the buckets do not give. The
   Subtractionist's cost objection is adopted as the bound the judgement froze:
   exactly one `gh` subprocess invocation per recap, with a 60-second timeout.
4. **A second, standalone weekly-summary graph.** Rejected: FR-700's graph is
   in scheduled production use and already answers the timeframe question for
   any repository; a parallel artifact would duplicate the git collection and
   split the Monday output in two.

## Related

- `examples/demos/recap/` (graph, prompt, `nodes/partition.py`, README)
- `scripts/weekly_recap.py`, `.github/workflows/weekly-recap.yml`,
  `docs/recaps/`
- `examples/demos/corpus_census/adapters/corpus_adapters.py:101` — the `gh`
  boundary reused
- `tests/unit/test_recap_demo.py`,
  `tests/integration/test_recap_demo_integration.py`
- `capabilities/CAP-195-timeframe-recap-demo.yaml`
- Scripture: `research_as_inventory`, `changelog_first_diagnostic`,
  `plausible_wrong_answer`, `growth_as_default`
