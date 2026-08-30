# Judgement: FR-904 Slot-bound digest collection

**Verdict:** APPROVED WITH REVISIONS — the split child is the right one-concern slice and reuses the existing slot/manifest architecture, but authority activates only after the FR replaces stale placeholders, freezes the second binding and collector ABI, and removes the impossible "manifest-supplied config" claim under the current manifest schema.

**Reviewed against:** `feature-requests/FR-904-slot-bound-digest-collection.md`; `feature-requests/FR-908-daily-digest-slot-bound-refactor.md`; `feature-requests/FR-908-daily-digest-slot-bound-refactor.judgement.md`; `feature-requests/FR-906-release-tool-slots-to-pypi.md`; `feature-requests/FR-906-release-tool-slots-to-pypi.judgement.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-777-shared-shell-toolbelt-manifests.judgement.md`; `reference/graph-yaml.md`; `examples/demos/corpus_census/README.md`; `examples/demos/corpus_census/graph.yaml`; `examples/daily_digest/graph.yaml`; `examples/daily_digest/run_digest.py`; `examples/daily_digest/nodes/sources.py`; `yamlgraph/tools/manifest.py`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; repo doctrine in project instructions.

## What is sound

The FR correctly implements only the Phase 2 child required by the FR-908 SPLIT judgement. FR-908 R-2 required a separate child for "converting collection to a `collect` slot, shipping at least two source manifests, moving source constants into manifest-supplied config, eliminating `sys.path.insert`, and proving source switching requires no `graph.yaml` edit" (`feature-requests/FR-908-daily-digest-slot-bound-refactor.judgement.md:31-33`). FR-904 confines itself to collection reuse and explicitly excludes delivery/email, rank-format validation, SQLite/ledger work, and `examples/shared/` packaging (`feature-requests/FR-904-slot-bound-digest-collection.md:145-150`).

The problem is real and evidenced. FR-904 identifies hardcoded collection state: `nodes/sources.py` owns the HN endpoint and `RSS_FEEDS` constant, `graph.yaml` uses inline `type: python, module: nodes.*` tools, and `run_digest.py` mutates `sys.path` to make those module imports work (`feature-requests/FR-904-slot-bound-digest-collection.md:36-39`). The cited surface confirms that shape: the current graph declares `fetch_sources` as `module: nodes.sources` (`examples/daily_digest/graph.yaml:27-34`), the runner inserts the digest directory into `sys.path` (`examples/daily_digest/run_digest.py:16-19`), and the source module hardcodes `HN_API_BASE` plus `RSS_FEEDS` (`examples/daily_digest/nodes/sources.py:12-16`).

The architecture choice is aligned with prior work. FR-892 defines invocation-time tool binding as the one authorized surface, `yamlgraph graph run ... --tool SLOT=path/to/manifest.yaml`, with CWD-relative binding paths and fail-closed typed errors before any LLM call (`feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:64-79`). The public reference repeats the same slot rules and failure modes (`reference/graph-yaml.md:1538-1581`), and the committed corpus-census graph demonstrates graph-declared slots bound at runtime (`examples/demos/corpus_census/graph.yaml:38-46`; `examples/demos/corpus_census/README.md:3-16`). FR-768 supplies manifest translation over existing shell/python/graph runtimes without a new execution engine (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:78-106`).

The research and prior-art gate is substantially satisfied. FR-904 includes a scoped alternatives table covering inline collection, `--var` feed lists, shared packaging, a digest-specific slot mechanism, one-binding deferral, and waiting for another repo (`feature-requests/FR-904-slot-bound-digest-collection.md:130-139`), plus an explicit `is_this_a_graph` answer (`feature-requests/FR-904-slot-bound-digest-collection.md:141-143`). That matches the local judge requirement that in-body research must preserve real alternatives and an `is_this_a_graph` answer (`.github/skills/judge-fr/doctrine.md:118-128`).

Strategic classification: **Contrib/example consumer of an existing framework primitive**. FR-904 does not need a new framework mechanism because FR-892 delivered the slot primitive and FR-768 delivered manifests; the change applies those primitives to one digest pipeline and its proof bindings (`feature-requests/FR-904-slot-bound-digest-collection.md:15-20`, `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:140-155`).

## Required revisions

### R-1: Replace the FR-906 placeholder gate with the exact released version

Update the status, blocking dependency, command examples, acceptance criteria, and workflow-pin wording to name the concrete version that satisfies the gate: `yamlgraph>=0.5.23` and `pip install "yamlgraph==0.5.23"` unless a newer already-published release supersedes it before enforcement. FR-904 still says "GATED on FR-906" and uses `<FR-906 version>` placeholders (`feature-requests/FR-904-slot-bound-digest-collection.md:5`, `feature-requests/FR-904-slot-bound-digest-collection.md:59-66`, `feature-requests/FR-904-slot-bound-digest-collection.md:113-125`), while FR-906 is now enforced as `v0.5.23` and its clean-venv help check proves `--tool` is present (`feature-requests/FR-906-release-tool-slots-to-pypi.md:124-140`).

### R-2: Freeze the collector ABI and output schema

Add an explicit collector contract section that says what the `collect` slot receives and what downstream nodes receive after it runs. The contract must state the node variables used to supply `config`, and must freeze the resulting `raw_articles` shape as a list of article records with at least `title`, `url`, `source`, and `timestamp`, preserving the current HN/RSS article shape (`examples/daily_digest/nodes/sources.py:31-36`, `examples/daily_digest/nodes/sources.py:77-83`, `examples/daily_digest/nodes/sources.py:93-100`). FR-904 currently specifies only `args: [config]` (`feature-requests/FR-904-slot-bound-digest-collection.md:72-79`), but FR-892's slot contract names the expected inputs and output shape (`feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:64-69`). Without the output shape, a second binding can satisfy the slot mechanically while breaking filtering/content/ranking downstream.

### R-3: Remove "manifest-supplied config" unless a separate framework FR adds manifest config

Revise the HN/RSS binding design so it uses the current FR-768 manifest schema exactly. `ToolManifest` permits only `name`, `description`, and `runtime`, and every manifest model has `extra="forbid"` (`yamlgraph/tools/manifest.py:22-70`); Python manifests permit only `runtime.type`, `function`, and exactly one of `path` or `module` (`yamlgraph/tools/manifest.py:33-49`). Therefore a `.tool.yaml` file cannot currently carry feed-list config. Replace "feed lists arrive as manifest-supplied config" (`feature-requests/FR-904-slot-bound-digest-collection.md:94-95`, `feature-requests/FR-904-slot-bound-digest-collection.md:120-121`) with a mechanism already supported by the repo: source-specific Python implementation/data files referenced by the manifest, with no change to `yamlgraph/tools/manifest.py`. If manifest-level config is desired, stop and file a separate framework FR; this FR may not extend the manifest schema.

### R-4: Replace the `<second>` placeholder with one exact second source binding

Freeze the second binding before enforcement by naming its manifest path, implementation file(s), required inputs/config, and smoke command. The current table leaves the enforcer to choose between "arXiv, GitHub releases, or a caller-supplied feed list" (`feature-requests/FR-904-slot-bound-digest-collection.md:92-95`), which is a product/design decision rather than an implementation detail. A mechanically checkable acceptance test needs one exact second source, not a menu.

### R-5: Make non-collection manifest conversion a first-class deliverable or drop the `sys.path` criterion

If `run_digest.py` must stop mutating `sys.path`, the FR must explicitly authorize converting every remaining `module: nodes.*` tool reference needed by the graph to path/manifest-relative declarations, not only the collection stage. The current graph has five inline module tools (`examples/daily_digest/graph.yaml:27-57`), and the runner's `sys.path.insert` exists because those imports are module-relative (`examples/daily_digest/run_digest.py:16-19`). FR-904 says manifest-ising "the four existing node modules" removes the hack (`feature-requests/FR-904-slot-bound-digest-collection.md:100-104`) but its summary and primary scope only mention collection (`feature-requests/FR-904-slot-bound-digest-collection.md:22-26`). Freeze the collateral as a deliverable with exact surfaces, or remove `run_digest.py` path cleanup from this FR.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-904-slot-bound-digest-collection.md` revisions folding R-1 through R-5 before enforcement |
| D-2 | Digest `graph.yaml`: `collect` declared as an FR-892 tool slot with an explicit contract, and the existing collection node rewired to produce the unchanged `raw_articles` downstream state |
| D-3 | `sources/hn_rss.tool.yaml` plus its source-owned implementation/data files preserving current HN/RSS behavior |
| D-4 | One exact second source manifest plus its source-owned implementation/data files, proving source switching without graph edits |
| D-5 | Any non-collection path/manifest conversion necessary to remove `run_digest.py` `sys.path` mutation, limited to existing digest node modules |
| D-6 | Tests or command transcripts proving slot binding success, missing binding, undeclared slot, runtime-outside-allowlist failure, unchanged `graph.yaml` hash across source switches, current HN/RSS behavior preservation, and absence of the old centralized `RSS_FEEDS` constant |
| D-7 | Digest workflow dependency pin to `yamlgraph>=0.5.23` or the exact newer release named by the folded FR |
| D-8 | Graph-authoring report for the material `graph.yaml` change |
| D-9 | FR implementation-status/decision update, changelog fragment if required by the target repo policy, and one real scheduled run record with run ID and commit SHA |

Not authorized: delivery ordering or email-node work from FR-903; rank-to-format validation from FR-905; replacing `digest.db` with JSONL/ledger storage; packaging `examples/shared/` or any demo assets into the yamlgraph wheel; changes to FR-892 slot semantics; changes to FR-768 manifest schema or `yamlgraph/tools/manifest.py`; framework-side nested schema support; retiring `examples/daily_digest`; broad workflow/CI/hook/judge/review-doctrine changes beyond the digest workflow version pin required here.

## Revised acceptance criteria

- [ ] AC-01: The FR is revised to fold R-1 through R-5 before enforcement starts.
- [ ] AC-02: A fresh environment installs `yamlgraph==0.5.23` or the exact newer release named by the folded FR, and `yamlgraph graph run --help | grep -- '--tool'` exits 0 before digest changes begin.
- [ ] AC-03: `graph.yaml` declares `tools.collect.slot: true` with an explicit `contract` that includes `runtimes: [python]`, `args: [config]`, the node variables that supply `config`, and the frozen `raw_articles` article-record output shape.
- [ ] AC-04: `sources/hn_rss.tool.yaml` validates as an FR-768 `ToolManifest` and preserves the current HN/RSS article output shape without any unsupported manifest keys.
- [ ] AC-05: One exact second source manifest named in the revised FR validates as an FR-768 `ToolManifest` and produces the same `raw_articles` article-record output shape through a genuinely different source strategy.
- [ ] AC-06: Running the digest once with `--tool collect=sources/hn_rss.tool.yaml` and once with the named second binding succeeds against the same `graph.yaml`; a hash captured before, between, and after the two runs proves `graph.yaml` was not edited.
- [ ] AC-07: `RSS_FEEDS` no longer exists as a centralized module constant in the shared collection module, and feed/source settings live only in source-owned implementation/data files referenced by their manifests.
- [ ] AC-08: Missing `collect` binding, `--tool` binding for an undeclared slot, and a manifest whose runtime is outside `contract.runtimes` each raise `ToolSlotBindingError` before any digest node or LLM executes.
- [ ] AC-09: `run_digest.py` contains no `sys.path` mutation; if this is achieved by converting non-collection tools, only the existing digest node modules named by the revised FR are converted.
- [ ] AC-10: The digest workflow pins yamlgraph to `>=0.5.23` or the exact newer release named by the folded FR.
- [ ] AC-11: The `graph.yaml` edit is produced through the governed graph-authoring route, and the authoring report records lint plus smoke evidence for both source bindings.
- [ ] AC-12: One real scheduled run of the slot-bound graph succeeds and is recorded in the FR with run ID, commit SHA, selected source binding, and yamlgraph package version.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into `feature-requests/FR-904-slot-bound-digest-collection.md`. | GATE |
| C-2 | Use a released yamlgraph package containing FR-892 `--tool`; as of the consumed evidence, the first acceptable version is `0.5.23`. Editable installs, git installs, and vendored framework checkouts do not satisfy the gate. | GATE |
| C-3 | Do not change `yamlgraph/`, FR-892 slot semantics, or the FR-768 `ToolManifest` schema under this FR. If manifest-level config or new slot validation is needed, stop and file a separate framework FR. | GATE |
| C-4 | The second source binding must be named and shipped in this FR; a single-binding slot or a placeholder source does not demonstrate reuse. | GATE |
| C-5 | Any material `graph.yaml` edit must use the graph-authoring route and retain the authoring report; do not hand-edit the graph outside that route. | GATE |
| C-6 | Keep FR-903 delivery/email work, FR-905 rank-format validation, SQLite/ledger changes, package-distribution policy, and example retirement out of this enforcement. | GATE |

Authority granted: after the revisions are folded, the enforcer may implement only the digest collection slot refactor and its directly necessary path/manifest cleanup, two source bindings, workflow yamlgraph pin, validation evidence, and scheduled-run proof.
