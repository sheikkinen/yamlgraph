# Authoring brief: pattern_model_census pipeline graph (FR-896)

Create `examples/demos/pattern_model_census/` — a read-only census graph
that classifies **architectural/design patterns** and **LLM model/provider
mentions** from git commit metadata, structurally mirroring
`examples/demos/corpus_census/` (FR-892/FR-895) but as a **new, separate**
graph. Do **not** modify `examples/demos/corpus_census/` in any way — it is
a shared pipeline with other consumers.

Governing FR: `feature-requests/FR-896-cross-repo-pattern-model-census.md`
(judged; see `feature-requests/FR-896-cross-repo-pattern-model-census.judgement.md`
for the frozen scope, R-1..R-5, and Conditions for enforcement C-1..C-6).
This brief implements Phases 0.5–4 of that FR's Proposed Solution only
(discover → extract → two judge lenses → reduce/ledger). Synthesis
(Phase 5) and the human redaction promotion gate (Phase 6) are explicitly
OUT of scope for this authoring pass — do not add a synthesis node.

## Required shape

- `tools:` declares TWO invocation-time slots, same mechanism as
  `corpus_census` (do not hardcode a corpus-specific tool in the shared
  slot contract):
  - `discover: {slot: true, contract: {args: [source]}}` — enumerates
    commits for one repo path; returns a list (JSON array of commit SHAs
    acceptable).
  - `extract: {slot: true, contract: {args: [item]}}` — returns one
    commit's metadata only.
- **Real production tool manifests** (bound by callers at run time, not
  hardcoded into `graph.yaml`), under this example's own `tools/`
  directory:
  - `tools/git_discover.tool.yaml` + a Python function running
    `git log --since="12 months ago" --no-merges --pretty=format:%H`
    against the repo path given as `source`, returning the SHA list.
    Repo path must be passed through `shlex.quote()` / subprocess arg
    lists (never shell string interpolation) per the repo's shell-
    injection Security Notes.
  - `tools/git_extract.tool.yaml` + a Python function running
    `git show --stat --format=%s <sha>` (bounded to a small fixed line
    count) against one commit, returning
    `{repo, sha, date, subject, shortstat}` **only** — must NOT return
    diff bodies, file contents, or any other field. This is a hard
    constraint from FR-896 AC-03; write a unit test asserting the
    returned dict has exactly these keys.
- **Fixture tool manifests** for the demo/smoke path (self-contained,
  no live git, no nested `.git` directory anywhere under the example —
  nested repos inside `yamlgraph` are forbidden): create a new small
  JSON file of 4-6 synthetic commit records shaped like the real
  extract output (`repo`, `sha`, `date`, `subject`, `shortstat`) under
  a new `fixtures/` directory, and author two new tool manifests that
  read from it, following the precedent pattern in
  `examples/demos/corpus_census/fixtures/fixture_tools.py` (an
  existing committed file — read it before authoring the new ones).
- Pipeline nodes:
  1. `discover` (python/tool node via the discover slot) → `items` list.
  2. `extract_items`: `type: map` over `{state.items}` invoking the
     extract slot per item → `contents` (collect).
  3. `judge_pattern`: `type: map` over contents; sub-node `type: llm`,
     **`provider: inception`, `model: mercury-2`, `temperature: 0`,
     `on_error: skip`** (NOT `anthropic`/`claude-haiku-4-5` —
     this is the FR-896 R-3 requirement; write a test that parses
     `graph.yaml` and asserts this node's `provider`/`model` fields
     literally). Prompt `judge_pattern` with an inline schema requiring
     exactly one field: `pattern` (str or null) — the dominant
     architectural/design pattern implied by `subject` + `shortstat`,
     or null. Single field only — do not add confidence/evidence/other
     fields to this prompt's schema (FR-896 keeps each lens to one
     judgement).
  4. `judge_model`: same map shape as `judge_pattern`, same
     `provider: inception` / `model: mercury-2` pin, separate prompt
     `judge_model` with an inline schema requiring exactly one field:
     `model_mentioned` (str or null) — a literal LLM provider/model
     token the commit subject/shortstat mentions or changes, or null.
  5. `reduce_ledger`: python tool (LLM-FREE, in this example's
     `tools.py`) that:
     - Joins `judge_pattern`/`judge_model` findings with the extracted
       metadata by index.
     - Requires a `repo_alias` input (state variable) distinct from the
       raw repo path/name; every ledger row carries `repo_alias`, never
       the raw repo path.
     - Aggregates counts by `repo_alias × quarter × label` for both
       lenses; writes a JSONL ledger + markdown summary to
       `{state.output_path}`.
     - **Path-prefix guard (FR-896 AC-06):** raise (fail closed) if the
       resolved `output_path` is inside this yamlgraph repository and is
       NOT under its `tmp/` directory. Write a unit test asserting the
       guard raises for a path like `docs/foo.md` and passes for a path
       under `tmp/`.
     - Never includes `sha`, full commit subject text, or diff content
       in the markdown summary meant for eventual public promotion —
       those may remain in the JSONL working ledger only (private,
       internal use), but the markdown output must carry only
       `repo_alias`, `label`, `count`, `quarter` columns.
  6. No synthesize node — stop at `reduce_ledger` (Phase 5/6 deferred).
- State: `source` (str), `repo_alias` (str), `rubric` fields not needed
  (rubrics are fixed per-lens prompts, not a runtime variable, unlike
  `corpus_census`), `items` (list), `contents` (list, sorted_add),
  `pattern_findings` (list, sorted_add), `model_findings` (list,
  sorted_add), `ledger` (dict), `output_path` (str).
- `config: {max_map_items: 200}` (fixture-sized default; real runs may
  override via `--var` if the schema supports it — do not hardcode a
  low ceiling that silently truncates real census runs without
  recording the omission, per FR-896 AC-05 "full census, no cap").

## Constraints

- Cheap-map discipline: both judge nodes pin model + provider +
  temperature explicitly to `inception`/`mercury-2`.
- The reducer is deterministic code — no LLM anywhere in reduce.
- One judgement per prompt (`judge_pattern`, `judge_model` are separate
  prompts/nodes) — do not fuse both fields into one schema.
- Smoke test: bind the fixture manifests and run the graph end-to-end
  with `--var source=<fixture path> --var repo_alias=fixture-demo
  --var output_path=tmp/pattern-model-census-fixture-ledger.md`; verify
  the ledger artifact exists with one row per fixture item per lens.
- Lint clean; record lint + smoke in the authoring report.
- Do not create, read, or reference any real sister-repo or personal
  GitHub-repo data in this authoring pass — fixtures only. Binding the
  real `tools/git_discover.tool.yaml` / `tools/git_extract.tool.yaml`
  against actual repos is a separate, later enforcement step (FR-896
  Phase 1 proper), not this authoring pass.

## Precedents to honor

- `examples/demos/corpus_census/` (discover/extract slot mechanism, map
  fan-out shape, LLM-free reducer with fail-closed validation) — adapt
  the STRUCTURE, do not modify the file.
- `examples/demos/map/` (basic `type: map` node config reference).
- FR-896's own R-2/R-3 finding: `yamlgraph/node_factory/llm_nodes.py`
  resolves `provider`/`model` from static YAML config at compile time
  (`node_config.get("provider", defaults.get("provider"))`) — there is
  no state/Jinja templating for these fields, which is why this is a
  new graph rather than a config override of `corpus_census`.

**Prior art:** dispositioned in FR-896 (in-body alternatives table); sibling brief `fr-892-corpus-census-brief.md` is the structural precedent for the slot mechanism and reducer shape, not a duplicate target (different graph, different model pin, different field shape, no synthesis node).
