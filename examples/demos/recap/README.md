# Recap — Timeframe Change Inventory (FR-700)

Answers *"what changed in this repo in the last day/week?"* for **any** git
repository. Deterministic git collection via `type: tool` nodes; exactly one
LLM node groups the inventory into workstreams and flags **orphans** —
commits with no FR/issue reference, and graph/prompt YAML changes with no
changelog fragment.

Mechanizes the Scripture's `changelog_first_diagnostic` cure: enumerate what
changed before reproducing anything.

> **Scheduled consumer (FR-821):** this graph runs every Monday via
> [.github/workflows/weekly-recap.yml](../../../.github/workflows/weekly-recap.yml)
> and publishes `docs/recaps/<ISO-week>.md` to `main` through an
> auto-merged automation PR. Renderer: `scripts/weekly_recap.py`.

## Run

```bash
# On this repository
yamlgraph graph run examples/demos/recap/graph.yaml \
  --var since="1 week ago" --var repo_path=. --full

# On any other repository
yamlgraph graph run examples/demos/recap/graph.yaml \
  --var since="yesterday" --var repo_path=/path/to/repo --full
```

## Output (structured state, via `--full`)

| Field | Meaning |
|-------|---------|
| `workstreams` | Commits grouped by FR reference or theme (model judgement), each tagged with the **verbatim** FR `[Status: …]` at HEAD by code (or `[no FR status]`) |
| `orphans` | **Code-assembled** (FR-704): unreferenced commit lines copied bit-exact — every hash is `git show`-safe — plus graph/prompt changes in a fragment-less window |
| `hotspots` | Files touched by multiple workstreams (model judgement) |
| `pr_merged` / `pr_closed_unmerged` / `pr_open` | **FR-1027, code-assembled**: the window's pull requests as `#<number>\|<created>→<end>\|<N>d\|<title>`, ordered by decision timestamp then number descending (open rows by creation date). Merged and closed-unmerged are windowed; **open rows are never filtered by age** — staleness is the point |
| `pr_axis_note` | Empty when the axis read cleanly. Otherwise why it could not (`no origin remote`, `origin host is …, not github.com`, `gh timed out after 60s`, …) and/or that the 300-row cap was reached |

Convention absence (no `feature-requests/` / `changelog/unreleased/`) is
detected by the Jinja2 template and reported to the model as "not detected" —
the raw `fr_changes`/`fragments` state keys stay available for downstream code.

## Portability

- All git commands use `git -C {repo_path}` — no cwd assumptions, no reflog syntax.
- Missing convention paths yield empty output natively (`git log -- <missing>` exits 0).
- A `repo_path` that is **not** a git repo fails loudly (tool node raises).
- Commit collection capped at 300; truncation is reported, not hidden.

## Pull-request axis (FR-1027)

A git-only recap cannot see what a window *decided*. A pull request closed
without merging contributes zero commits, and an open one contributes none
either — so the week's rejections and its work-in-flight are both structurally
invisible. [nodes/prs.py](nodes/prs.py) adds that axis:

1. **Identify** — `git -C <repo_path> remote get-url origin`, parsed for
   `owner/name`. Three families accepted, each with an optional `.git`:
   `https://github.com/o/n`, `git@github.com:o/n`, `ssh://git@github.com/o/n`.
2. **Bound** — `git rev-parse --since=<since>` returns an epoch, and **that
   epoch** is the comparison boundary. The UTC date is only ever printed, so a
   pull request merged at 03:00 on the boundary day is not moved in or out by
   midnight truncation.
3. **Collect** — exactly **one** `gh` subprocess invocation per recap, fixed
   argv, `shell=False`, 60-second timeout, 300-row cap. (`gh pr list --limit
   300` paginates internally, so the promise is one subprocess, not one HTTP
   request.)
4. **Bucket** — in code, ordered in code, lines assembled in code. The model
   never sees a pull request, so it cannot invent one.

### It degrades honestly, and says so

The axis is optional enrichment in exactly the way `feature-requests/` is: a
plain local clone still produces a full recap.

| Situation | `pr_axis` | Rendered |
|-----------|-----------|----------|
| Window had no pull requests | `available: True`, empty buckets | `(none)` |
| No `origin`, non-GitHub host, local remote, malformed URL | `available: False` + reason, **no `gh` call at all** | one note, then `(not collected)` |
| `gh` missing, unauthenticated, timed out, or returned junk | `available: False` + reason | one note, then `(not collected)` |
| 300 rows returned | `available: True`, `cap_reached: True` | note says results **may** be truncated |

Three deliberate refusals here:

- **`(none)` is never printed for an axis that made no observation.** An empty
  list and an unread source are different claims (Commandment 6).
- **The cap note renders once, before the sections, and cannot be suppressed
  by non-empty buckets** — a warning that vanishes when the page is full is
  worse than no warning.
- **Only four exception classes are absorbed** (`FileNotFoundError`,
  `TimeoutExpired`, `CalledProcessError`, unparseable/incomplete JSON). A
  `repo_path` that is not a git repository still fails loudly, and any
  unexpected error propagates rather than being reported as an empty week.

One inherited quirk, recorded rather than hidden: `git rev-parse --since="not
a date"` returns the *current* epoch with exit 0, exactly as `git log --since`
does for the five collection tools above. The axis uses git's own parser and
inherits that silence rather than diverging from the rest of the graph.

## Difference from git-report

| Aspect | [git-report](../git-report/) | recap |
|--------|------------------------------|-------|
| Pattern | `agent` node — LLM decides which tools to call | Fixed pipeline — `type: tool` chain, LLM never picks tools |
| Question | Open-ended ("who touched X?") | Fixed ("what changed since T?") |
| Judgements | Multi-step exploration | Exactly one (group + flag orphans) |
| Partitioning | Model reads raw output | Jinja2 partitions paths in the template |
| Repo assumptions | Current directory | Any repo via `--var repo_path` |

## Teaching points

1. `type: tool` nodes for deterministic collection — no LLM in the loop until judgement is actually needed.
2. Mechanizable work is split by kind: file-*path* partitioning and truncation/convention notices live in Jinja2 in the prompt template; commit-*reference* detection (FR-702), the id→status join (FR-703), and orphan assembly (FR-704) are `type: python` passes around the LLM node ([nodes/partition.py](nodes/partition.py)). The schema holds exactly two judgement fields — every transport field the model once carried produced a field defect (mid-subject false positives, silent join drops, hash corruption) and was evicted to code.
3. Disposition is collected and joined by code, never by the model: a `git grep` tool reads verbatim FR `Status:` lines at HEAD; a post-pass appends `[Status: …]` per id (per-id tags when a merged workstream's statuses differ). Its exit-1 ("no matches") is normalized at the boundary while real errors still fail loudly.
4. Inline schema keeps serialization out of the model's job: lists only, Pydantic-validated. The prompt's only formatting demand: name FR ids in full, never shorthand — so downstream arithmetic is never starved.
