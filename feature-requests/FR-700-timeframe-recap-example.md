# Feature Request: Timeframe Recap Example Graph (works on any repo)

**Priority:** MEDIUM
**Type:** Feature
**Status:** In Progress
**Effort:** 1 day
**Requested:** 2026-07-08
**Judged:** 2026-07-08 — scope frozen. 8 findings resolved (see Judgement section).

## Summary

An example graph `examples/demos/recap/` that answers "what changed in this repo in the last day/week?" — deterministic git collection via shell tools, one LLM synthesis prompt that groups changes into workstreams and flags orphan changes (commits with no FR/issue reference, prompt/graph edits with no changelog fragment). Must run against **any** git repository via `--var repo_path=...`; YAMLGraph-specific conventions (feature-requests/, changelog/unreleased/, docs/diary/) are optional enrichment, not requirements.

## Value Statement

Developers and LLM agents resuming work after a busy day/week get a structured change inventory instead of reconstructing it from raw `git log` — mechanizing the Scripture's `changelog_first_diagnostic` cure and the `recent_changes_blindness` trap.

## Problem

During an active day/week, many unrelated features land in parallel. Changes to code, graph YAML, and prompt YAML accumulate with no unified view:

- `git log --oneline` is semantically opaque for graph/prompt YAML — a 6-line prompt diff can change pipeline behavior more than 600 lines of Python, and it is invisible in a commit subject.
- Changelog fragments only cover `feat`/`fix` with fragments; prompt/graph tweaks slip through.
- Nobody diffs which FRs changed status in a window.
- The Scripture demands "enumerate every commit since the last known good" as an explicit first step, but the cure exists only as doctrine text — `detection_without_enforcement`.

Existing partial coverage: `examples/demos/git-report/` (open-ended agent Q&A, no timeframe, no FR awareness), `diary_digest` (cognitive reflections, not change inventory).

## Proposed Solution

New demo at `examples/demos/recap/` following the git-report pattern: shell tools + one LLM node. **No new framework code** — pure YAML graph + prompt.

### Graph sketch

```yaml
version: "1.0"
name: recap
description: Timeframe change recap for any git repository

state:
  since: str        # e.g. "1 week ago", "yesterday", "2026-07-01"
  repo_path: str    # default "." — any git repo

tools:
  commits_since:
    type: shell
    command: git -C {repo_path} log --since={since} -n 300 --pretty=format:'%h|%ad|%s' --date=short
    parse: text
  file_churn:
    type: shell
    command: git -C {repo_path} log --since={since} -n 300 --numstat --pretty=format:'%h'
    parse: text
  changed_frs:
    type: shell
    command: git -C {repo_path} log --since={since} --name-only --pretty=format: -- feature-requests/
    parse: text
  new_changelog_fragments:
    type: shell
    command: git -C {repo_path} log --since={since} --diff-filter=A --name-only --pretty=format: -- changelog/unreleased/
    parse: text

nodes:
  # Deterministic collection: one `type: tool` node per tool, chained.
  # No LLM involvement; each writes its own state_key.
  get_commits:      {type: tool, tool: commits_since, state_key: commits}
  get_churn:        {type: tool, tool: file_churn, state_key: churn}
  get_frs:          {type: tool, tool: changed_frs, state_key: fr_changes}
  get_fragments:    {type: tool, tool: new_changelog_fragments, state_key: fragments}
  synthesize:       # the ONE llm node, prompt: recap, inline schema
```

Judgement notes on the tool layer:

- `diff --stat "@{...}"` (reflog syntax) was removed: reflog time is local-only,
  breaks on fresh clones, and nested quoting fights `shlex.quote()` sanitization.
  Per-file churn comes from `--numstat` instead (F1).
- Commit collection is capped at `-n 300`; the prompt template states when the
  cap was hit so the model reports truncation instead of implying completeness (F5).
- No `|| true`: `git log -- missing-path/` already exits 0 with empty output on
  repos lacking the convention; a `repo_path` that is not a git repo must fail
  loudly (Commandment 6 — no silent fallbacks) (F4).
```

### Prompt contract (one judgement)

`prompts/recap.yaml` — single synthesis job: given commits, diffstat, and file lists partitioned by kind (code / graph YAML / prompt YAML / docs), produce:

1. **Workstreams** — commits grouped by FR reference or common theme, each with file-layer breakdown (code / graph / prompt).
2. **Orphans** — commits with no FR-XXX/issue reference; prompt/graph files changed with no changelog fragment (section emitted only when the repo has those conventions — empty convention inputs must yield "no conventions detected", never an error or hallucinated findings).
3. **Hotspots** — files touched by multiple workstreams.

Output via inline schema (Pydantic-validated): `workstreams: list`, `orphans: list[str]`, `hotspots: list[str]`, `conventions_detected: bool`. The demo shows the structured state via `--full`; **no markdown rendering is in scope** — serialization stays out of the model's judgement (F6).

File-kind partitioning (code / graph YAML / prompt YAML / other) is done by **Jinja2 in the prompt's user template** from the raw `--numstat` paths — simple path heuristics (`.py`, `graphs/`, `prompts/`), no content sniffing, no Python node (F3).

### Portability rules ("works on any repo")

- All git commands use `git -C {repo_path}`; no `cd`, no assumptions about cwd, no reflog syntax.
- Convention tools (`changed_frs`, `new_changelog_fragments`) tolerate absent paths natively (`git log -- <missing>` exits 0, empty output). A `repo_path` that is not a git repo fails loudly.
- File-kind partition via Jinja2 path heuristics in the prompt template (`.py`, `graphs/`, `prompts/`); not hardcoded to yamlgraph layout beyond those directory-name heuristics.
- No dependency on `feature-requests/`, `changelog/`, or `docs/diary/` existing.

### Invocation

```bash
yamlgraph graph run examples/demos/recap/graph.yaml \
  --var since="1 week ago" --var repo_path=. --full
```

## Acceptance Criteria

- [ ] `yamlgraph graph lint examples/demos/recap/graph.yaml` passes clean (unit test, no LLM)
- [ ] Graph compiles and dynamic state builds with mock LLM (unit test, no LLM)
- [ ] Demo runs on the yamlgraph repo itself and produces workstream + orphan sections (`demo-output.log` committed, per demo-gate FR-206)
- [ ] Demo runs on a bare temp git repo (3 commits, no FR/changelog/diary conventions) without error; `conventions_detected` is false and orphans/workstreams contain no hallucinated FR references (integration test, API-key-guarded)
- [ ] Orphan detection: a fixture commit without `FR-XXX`/`NC-XXX`/`#NNN` reference appears in `orphans` — asserted with tolerant matching (contains/prefix, never exact equality) (integration test, API-key-guarded)
- [ ] Non-git `repo_path` fails loudly with a `PipelineError`; no empty-recap fallback (unit test, no LLM)
- [ ] Exactly one LLM node (`synthesize`); all collection is `type: tool` nodes (prompt contract: one judgement)
- [ ] All runtime variables pass through existing `shlex.quote()` sanitization (no new shell surface)
- [ ] Capability file `capabilities/CAP-XXX-timeframe-recap-demo.yaml` with a new `REQ-YG-XXX`; all tests tagged `@pytest.mark.req`; `python scripts/req_coverage.py --strict` passes
- [ ] README.md in `examples/demos/recap/` with usage + "how this differs from git-report" table
- [ ] Changelog fragment in `changelog/unreleased/`
- [ ] Diary entry in `docs/diary/`

## Judgement (2026-07-08)

Scope frozen. Findings and resolutions:

| # | Finding | Resolution |
|---|---------|------------|
| F1 | `diff --stat "@{'{since}'}"` uses reflog time — local-only, clone-breaking, quote-nesting vs sanitization | Tool removed; churn via `git log --numstat` |
| F2 | `collect` node had no type — ambiguous | Pinned: one `type: tool` node per tool (verified in reference/graph-yaml.md §type: tool) |
| F3 | Partition location ambiguous ("prompt input assembly") | Pinned: Jinja2 path heuristics in prompt user template; no Python node |
| F4 | `\|\| true` = silent fallback; masks not-a-repo failure | Removed; `git log -- <missing>` exits 0 natively; non-repo fails loudly |
| F5 | Unbounded commit input can flood context | Capped `-n 300`; prompt reports truncation |
| F6 | "Rendered as markdown by `--full`" contradicts structured schema | Structured schema only; markdown rendering out of scope |
| F7 | No CAP/REQ traceability | Added CAP + REQ + `req_coverage.py --strict` criterion |
| F8 | LLM-output assertions under-specified | Tolerant matching; integration tests API-key-guarded; unit layer LLM-free |

**Out of scope (purge list):** markdown/HTML rendering, scheduling (launchd), `yamlgraph recap` CLI subcommand, diary/docs enrichment beyond the two convention tools, config for custom path heuristics, non-git VCS.

## Alternatives Considered

1. **Documented shell one-liner** (`git log --since + diff --stat`): covers the deterministic 80%, but fails the actual pain point — semantic opacity of graph/prompt YAML diffs and orphan cross-referencing. Rejected as sole solution; the one-liner IS the tool layer of this graph.
2. **Python CLI subcommand (`yamlgraph recap`)**: framework code for an application concern; violates "does this belong in YAMLGraph?" reflection. Rejected — examples/ is the right home.
3. **Extend git-report demo**: git-report teaches agent+tools with open-ended queries; recap is a fixed pipeline with one judgement. Merging would blur both teaching purposes (`false_duplicate` — syntactic similarity ≠ semantic equivalence). Rejected.
4. **Chronicle/session-store standup**: covers editor sessions, not repo commits; complementary, not overlapping.

## Related

- `examples/demos/git-report/graph.yaml` — pattern source (shell tools + agent)
- Scripture: `changelog_first_diagnostic` cure, `recent_changes_blindness` trap, Addendum ("the diff is cheaper than any test")
- FR-206 demo-gate (demo-output.log requirement)
- User memory: prompt-as-subagent-contract (one judgement per prompt)
