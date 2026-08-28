# Judgement: FR-896 Twelve-Month Cross-Repo Pattern & Model Census

**Verdict:** APPROVED WITH REVISIONS — the census is worth doing and reuses the right map/reduce precedent, but authority activates only after the FR folds the unresolved human choices, exact artifact boundary, graph-authoring route, and public-safe alias/redaction tests into mechanically enforceable scope.

**Prior art:** dispositioned in FR-896's own header (in-body alternatives table) and this judgement's "What is sound" section. FR-802-node-type-usage-census (single-repo node-type census; cited methodology precedent, not a substitute — FR-896 generalizes it cross-repo). FR-895-census-synthesize-tail / FR-892-corpus-census-pipeline-injected-adapters (the shared discover/extract/map/reduce/synthesize shape FR-896 structurally mirrors via a new sibling graph, not a modification). FR-893-diary-trap-census (a different census-family consumer of the same `REQ-YG-624` tool-slot mechanism; lexical noun overlap only — no shared subject matter with FR-896's cross-repo pattern/model scope).

**Reviewed against:** `feature-requests/FR-896-cross-repo-pattern-model-census.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `examples/demos/corpus_census/graph.yaml`; `examples/demos/corpus_census/README.md`; `docs/mercury-census/findings.md`; `feature-requests/FR-802-node-type-usage-census.md`; `feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md`.

## What is sound

The problem is real and has a named first consumer: FR-896 wants the author to use the resulting keep/adopt/retire evidence table when making the next standardization or retirement decision, explicitly paralleling FR-802's node-type census role (`feature-requests/FR-896-cross-repo-pattern-model-census.md:7-11`, `feature-requests/FR-802-node-type-usage-census.md:7-10`). Strategic classification: **contrib/example investigation tooling**, not a new framework primitive; the existing `corpus_census` graph already supplies the reusable discover/extract/map/reduce/tail shape via slot-bound discovery and extraction (`examples/demos/corpus_census/graph.yaml:40-44`, `docs/mercury-census/findings.md:487-499`).

The FR satisfies the measurement raw-read gate in substance. It records three raw discovery samples and surprising details that affect design: local path versus remote-name divergence, unsafe employer-org breadth, and noisy active personal repos (`feature-requests/FR-896-cross-repo-pattern-model-census.md:60-86`). That meets the local judge requirement to withhold authority from metric/scorer work unless the FR evidences concrete raw samples (`.github/copilot-instructions.md:233`).

The redaction direction is also sound. FR-896 rejects full diffs/file bodies (`feature-requests/FR-896-cross-repo-pattern-model-census.md:116-122`, `feature-requests/FR-896-cross-repo-pattern-model-census.md:196-197`), keeps the raw ledger private by default (`feature-requests/FR-896-cross-repo-pattern-model-census.md:134-141`), and reuses the FR-831 private-inventory -> reviewed public-transfer pattern (`feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md:17-28`, `feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md:177`). The `corpus_census` synthesis tail already has a bounded public-safe allowlist and fail-closed citation renderer (`examples/demos/corpus_census/README.md:21-28`).

The plan correctly splits semantic lenses: pattern classification and model/provider extraction are separate single-field map passes (`feature-requests/FR-896-cross-repo-pattern-model-census.md:124-132`). That preserves the prompt-as-subagent-contract discipline and avoids fused rubrics.

## Required revisions

### R-1: Fold the three human choices into the FR before enforcement

Replace the "Questions for the human" section with decisions in the Proposed Solution and Acceptance Criteria. The FR currently leaves GitHub org scope, private ledger location, and sampling cap as options (`feature-requests/FR-896-cross-repo-pattern-model-census.md:207-224`), while the plan and ACs depend on them (`feature-requests/FR-896-cross-repo-pattern-model-census.md:100-108`, `feature-requests/FR-896-cross-repo-pattern-model-census.md:134-141`, `feature-requests/FR-896-cross-repo-pattern-model-census.md:168-170`). Human safety/spend/scope choices must be surfaced, not silently absorbed, but an enforcer cannot operate against unanswered options.

Fold the recommended defaults unless the human changes them: no `terveystalo` org expansion beyond the four named sister repos; private ledger/artifacts live in the existing private `sheikkinen/control-plane` repo; high-volume repos use a documented stratified sample capped at 300 commits per repo. If any decision differs, record it explicitly and update the ACs accordingly.

### R-2: Define the exact artifact boundary and graph-authoring route

State exactly which files may be created or modified. FR-896 says it will reuse and extend `corpus_census`, add new discover/extract bindings, add new judgement rubrics, and possibly author a README under a new example directory (`feature-requests/FR-896-cross-repo-pattern-model-census.md:60-63`, `feature-requests/FR-896-cross-repo-pattern-model-census.md:109-132`, `feature-requests/FR-896-cross-repo-pattern-model-census.md:184-185`), but it does not name the target graph, prompt, tool, adapter, test, doc, or brief paths.

Any creation or material modification of `graph.yaml` or `prompts/*.yaml` must go through the graph-authoring adapter with a committed task brief, because local doctrine binds on artifact class and makes `scripts/author.sh <task-brief.md>` the sole route (`.github/copilot-instructions.md:15`, `.github/skills/graph-authoring/doctrine.md:7-15`, `.github/skills/graph-authoring/doctrine.md:73-88`). If enforcement will not touch graph or prompt YAML, say that explicitly and limit scope to tool manifests/Python tools, tests, private ledger generation, and the final reviewed public document.

### R-3: Specify a feasible model-pin mechanism for the two map passes

The existing shared graph hardcodes `anthropic` / `claude-haiku-4-5` on `judge_items` and `synthesize` (`examples/demos/corpus_census/graph.yaml:92-93`, `examples/demos/corpus_census/graph.yaml:116-117`), while FR-896 requires the map/judge fan-out to run on `inception` / `mercury-2` (`feature-requests/FR-896-cross-repo-pattern-model-census.md:124-132`, `feature-requests/FR-896-cross-repo-pattern-model-census.md:164-166`). The FR must define the implementation mechanism: either an authored graph variant via the graph-authoring route, or an existing supported configuration path with tests proving the effective node config is mercury-pinned for both lenses and not merely documented.

The synthesis tail may remain haiku-tier if the FR says so, because the mercury findings distinguish label-class fan-out from paragraph synthesis (`docs/mercury-census/findings.md:12-15`).

### R-4: Add public-safe repo aliasing and leakage assertions

Resolve the contradiction between "no customer name appears in anything committed" and "only pattern/model labels, repo names, and counts" (`feature-requests/FR-896-cross-repo-pattern-model-census.md:89-96`). Repo names can themselves be customer- or employer-identifying, especially for private sister repos. Add a public-safe alias table to the private ledger/review packet and require the committed brief to use only aliases approved by human review, not raw private repo names unless explicitly cleared.

Extend AC-05 with mechanical assertions over every committed artifact produced by this FR: no commit subject, shortstat detail, SHA, hostname-shaped token, raw private path, or unapproved raw private repo name may appear. The existing public-safe column allowlist is necessary but insufficient because it still permits raw repo names (`feature-requests/FR-896-cross-repo-pattern-model-census.md:171-174`).

### R-5: Make every acceptance criterion mechanically checkable

Split the trailing aggregate ACs into concrete checks with paths and commands. "`Tests added`" and "`Documentation updated`" are not mechanically checkable as written (`feature-requests/FR-896-cross-repo-pattern-model-census.md:182-185`). Replace them with named test files/functions or command-backed assertions for extraction schema, ledger path-prefix guard, citation boundary reuse, graph lint/smoke report if graph artifacts are authored, and the final document's redaction scan.

Also add an AC that the Phase 0 scope table is frozen before any discover/extract operation against **any non-`yamlgraph` repo**, not only sister repos. The current AC protects sister repos but leaves the 54 personal GitHub repos from Sample 3 outside the pre-discovery gate (`feature-requests/FR-896-cross-repo-pattern-model-census.md:80-86`, `feature-requests/FR-896-cross-repo-pattern-model-census.md:161-162`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | FR-896 revised in place with final decisions for org scope, private ledger location, sampling cap, exact artifact paths, and revised ACs. |
| D-2 | Phase 0 committed scope table listing every included/excluded repo, source of inclusion, raw name, public alias, visibility, and inclusion/exclusion reason. |
| D-3 | Read-only discover/extract bindings or tool manifests that enumerate commits and extract only commit metadata. |
| D-4 | Two single-field judgement rubrics/passes: architectural/design pattern label and literal model/provider label. |
| D-5 | LLM-free reducer/ledger path guard writing only to the frozen private location. |
| D-6 | Private ledger and synthesized private brief, retained outside tracked `yamlgraph` paths until human redaction review. |
| D-7 | One reviewed, public-safe committed `yamlgraph/docs/` census document after human review, using only approved aliases and aggregate labels/counts. |
| D-8 | Tests for extraction schema, path guard, model pin/effective graph config, citation boundary, public-safe allowlist, and org-scope prohibition. |
| D-9 | If any graph/prompt artifact is created or materially modified: committed graph-authoring task brief plus `tmp/draft-authoring-report.md` evidence from the adapter route. |

Not authorized: wholesale `terveystalo` org enumeration; cloning/pulling every discovered GitHub repo as part of this FR; reading full diffs or file contents from non-`yamlgraph` repos; committing raw ledger rows, commit subjects, SHAs, shortstat details, hostnames, raw private paths, or unapproved private repo names to `yamlgraph`; changing CI, hooks, judge/review doctrine, provider runtime primitives, graph-authoring doctrine, or the shared corpus-census framework beyond the explicitly named artifact boundary; using the census result as authority to standardize, retire, delete, or migrate any pattern/model without a separate FR.

## Revised acceptance criteria

- [ ] AC-01: FR-896 folds R-1..R-5 before enforcement begins; no discover/extract operation runs against any non-`yamlgraph` repo until this revision is committed.
- [ ] AC-02: A committed Phase 0 scope table lists every candidate repo with source, visibility, raw repo name, public alias, inclusion/exclusion reason, and sampling rule; `terveystalo` org-wide enumeration is explicitly excluded.
- [ ] AC-03: The chosen private ledger/artifact location is a concrete path/repo prefix, and reducer tests fail when output is attempted under `yamlgraph/docs/`, `yamlgraph/tmp/`, or any tracked `yamlgraph` path before human promotion.
- [ ] AC-04: Discover/extract bindings use only commit metadata commands/API fields equivalent to `git log --since="12 months ago" --no-merges --pretty=format:%H` and bounded `git show --stat --format=%s`; tests assert the extracted schema has no diff/body/file-content field.
- [ ] AC-05: High-volume sampling is deterministic and documented per repo/quarter; if capped, the cap is exactly the value folded into the FR and the output records omitted-count metadata.
- [ ] AC-06: Pattern and model/provider lenses run as separate single-field judgements over the same extracted metadata; tests or graph inspection prove the map fan-out uses `provider: inception`, `model: mercury-2`.
- [ ] AC-07: The synthesis tail input allowlist contains only approved repo alias, quarter, label, and count; tests reject commit subject, shortstat detail, SHA, hostname-shaped token, raw private path, and unapproved raw private repo name in any committed artifact.
- [ ] AC-08: Every citation in the public brief validates against a row in the private ledger; invalid citations produce a rejected/private artifact and no public brief.
- [ ] AC-09: Human redaction review is recorded before any public `yamlgraph/docs/` census artifact is committed; there is no automated promotion path.
- [ ] AC-10: The final committed census document states that it is evidence for future standardization/retirement FRs only and grants no authority to change runtime code, graph artifacts, prompts, tests, CAPs, CI, or hooks.
- [ ] AC-11: If graph or prompt YAML is authored or materially modified, the work is executed through graph-authoring with a committed task brief and an authoring report recording lint and smoke results or exact blocked validation.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority activates only after R-1..R-5 are folded into FR-896 and the revised FR is committed. | GATE |
| C-2 | No non-`yamlgraph` repo discovery or extraction may run before the Phase 0 scope table, alias table, sampling rule, and private ledger location are frozen. | GATE |
| C-3 | Any graph/prompt YAML creation or material modification must use the graph-authoring adapter route; direct unsentineled graph authoring is forbidden. | GATE |
| C-4 | The reducer must fail closed on any output path outside the frozen private ledger location until human review promotes a public-safe brief. | GATE |
| C-5 | The public artifact must contain only approved aliases plus aggregate labels/counts/quarters; any raw commit subject, SHA, hostname, private path, or unapproved private repo name blocks promotion. | GATE |
| C-6 | The census output is evidence only; any adoption, retirement, migration, or standardization action requires a separate judged FR. | GATE |

Authority granted: after the revisions are folded, enforcement may build a read-only, redaction-gated cross-repo pattern/model census using the existing corpus-census shape, mercury-pinned map judgements, LLM-free private ledger reduction, and a human-reviewed public-safe summary document only.
