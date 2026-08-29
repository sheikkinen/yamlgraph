# Judgement: FR-908 Refactor yamlgraph-daily-digest into slot-bound reusable tools

**Prior art:** inherits the disposition in
`FR-908-daily-digest-slot-bound-refactor.md` — FR-819 is the direct
precedent and is preserved; FR-892 supplies the slot pattern unchanged.
This judgement returns SPLIT, so no authority is granted here; the child
FRs carry their own prior-art dispositions.

**Verdict:** SPLIT - the user pain is real and well evidenced, but FR-908 bundles three independently deliverable changes (email delivery ordering, slot-bound collection reuse, and rank-format boundary hardening) plus a workflow-test baseline; each must re-enter as its own judged FR before enforcement.

**Reviewed against:** `feature-requests/FR-908-daily-digest-slot-bound-refactor.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-819-github-native-digest-poc-repo.md`; `feature-requests/FR-906-release-tool-slots-to-pypi.md`; `feature-requests/FR-907-smtp-email-tool.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.judgement.md`; `feature-requests/FR-892.research.md`; `reference/graph-yaml.md`; `reference/patterns/corpus-map-reduce.md`; `examples/demos/corpus_census/README.md`; `examples/demos/corpus_census/graph.yaml`; `examples/daily_digest/prompts/rank_stories.yaml`; `examples/daily_digest/nodes/formatting.py`; `examples/daily_digest/templates/digest.html`; `yamlgraph/schema_loader.py`; repo doctrine in project instructions.

## What is sound

The FR names concrete consumers and events: the first 06:00 UTC scheduled `yamlgraph-daily-digest` run that writes a bulletin and then emails it, and a later sibling digest repo that changes only slot bindings (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:8-12`). It also gives live operational evidence: eleven scheduled green runs and committed bulletins from 2026-08-18 through 2026-08-28 (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:27-50`).

The delivery problem is a real product gap rather than speculative growth. FR-819 deliberately made the repo itself the runtime, state store, and publication channel with "no ... email" (`feature-requests/FR-819-github-native-digest-poc-repo.md:17-22`), while FR-908 explicitly preserves that premise by adding email alongside the committed bulletin (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:15-23`, `feature-requests/FR-908-daily-digest-slot-bound-refactor.md:219-227`). FR-907 separately scopes the SMTP tool as generic transport, not digest logic (`feature-requests/FR-907-smtp-email-tool.md:24-30`, `feature-requests/FR-907-smtp-email-tool.md:157-159`), which is the right boundary.

The slot-reuse direction conforms to existing architecture instead of inventing a new mechanism. FR-768 manifests are already an enforced declaration-reuse layer over existing runtimes (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:16-19`, `feature-requests/FR-768-tool-manifest-declaration-reuse.md:78-106`), and FR-892/reference docs define invocation-time slot binding with `--tool SLOT=manifest.yaml` and fail-closed binding semantics (`reference/graph-yaml.md:1538-1581`). The corpus-census graph is a committed precedent for graph-declared slots (`examples/demos/corpus_census/graph.yaml:38-46`).

The rank-format seam is a legitimate boundary defect. The prompt schema declares `stories` as `list[Any]` (`examples/daily_digest/prompts/rank_stories.yaml:25-30`), `schema_loader` explicitly maps `Any` and resolves `list[T]` generically (`yamlgraph/schema_loader.py:29-37`, `yamlgraph/schema_loader.py:83-87`), and the renderer passes ranked stories directly into a template that dereferences `s.url`, `s.title`, `s.summary`, `s.reason`, and `s.relevance` (`examples/daily_digest/nodes/formatting.py:57-85`, `examples/daily_digest/templates/digest.html:86-92`). Guarding the deterministic boundary follows the repository law to use Pydantic and raise rather than emit success-shaped fallbacks (`.github/copilot-instructions.md:217-221`).

The proposed acceptance criteria are mostly mechanical: they name transition sequence assertions, simulated failure behavior, absence of file-writing/delivery code from `run_digest.py`, workflow-secret checks, source-switching without `graph.yaml` edits, RED/GREEN evidence, and no empty-bulletin success path (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:174-204`).

## Required revisions

### R-1: Split delivery integration into its own FR

Create a child FR for Phase 1 only: moving bulletin write and README-index update into graph tools, routing `format_markdown -> gate -> write_bulletin -> send_email -> END`, preserving no-op behavior, passing SMTP secrets through workflow env, and updating README. That child FR may consume the FR-907 SMTP tool only after FR-907 is independently approved and enforced, or after an equivalent judged SMTP tool exists. It must not implement the SMTP tool itself; FR-907 owns transport (`feature-requests/FR-907-smtp-email-tool.md:85-188`), while FR-908's proposed Phase 1 owns subject/body assembly and call ordering (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:93-123`, `feature-requests/FR-907-smtp-email-tool.md:157-159`).

### R-2: Split reusable collection slots into its own FR

Create a child FR for Phase 2 only: converting collection to a `collect` slot, shipping at least two source manifests, moving source constants into manifest-supplied config, eliminating `sys.path.insert`, and proving source switching requires no `graph.yaml` edit. This child FR has a hard GATE dependency on FR-906 being enforced because FR-906 records that FR-892 `--tool` is not in `v0.5.22`, that FR-908 cannot slot-bind collection until a release ships, and that the failure is an argparse error before graph load (`feature-requests/FR-906-release-tool-slots-to-pypi.md:28-55`). It must reuse the FR-892 slot semantics exactly (`reference/graph-yaml.md:1538-1581`), not define a digest-specific slot mechanism.

### R-3: Split rank-format boundary hardening into its own FR

Create a child FR for Phase 3 only: typed validation of ranked stories at the first deterministic boundary, dropping individual non-conforming ranked items, raising when no conforming ranked item survives a non-empty ranked response, and optionally reconciling ranked story URLs against the analyzed set. The child FR must include the condemning test for `format_markdown(["a string", "another"])` before the fix (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:157-172`) and must not change framework-side nested schema support, which FR-908 correctly leaves out of scope (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:169-172`, `feature-requests/FR-908-daily-digest-slot-bound-refactor.md:221-222`).

### R-4: Separate the workflow-test baseline or attach it to the first child that changes the workflow

The "Throughout" criteria for `tests/test_workflow.py`, CI-before-digest ordering, and README update are not the same concern as slot binding or ranked-story validation (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:199-204`). Either make them their own workflow-hardening FR, or attach them only to the Phase 1 delivery-integration FR if that is the first child to edit `.github/workflows/digest.yml`. Do not make Phase 2 or Phase 3 wait on workflow assertions unrelated to their surfaces.

### R-5: Resolve the empty-bulletin/no-op ambiguity in the relevant child FRs

The current FR simultaneously authorizes a gate that routes an empty bulletin to END (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:99-114`, `feature-requests/FR-908-daily-digest-slot-bound-refactor.md:176-178`) and a Phase 3 rule that no path emits an empty bulletin as success (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:194-197`). The split FRs must distinguish a legitimate no-new-articles no-op from a malformed/all-dropped ranked response. Use an explicit state predicate or status value, not "empty markdown" alone, so invalid model output cannot be laundered into a green no-op.

### R-6: Add graph-authoring route evidence to any child that materially changes graph or prompt artifacts

Any child FR that creates or materially changes `graph.yaml` or `prompts/*.yaml` must require the governed graph-authoring route and an authoring report. Repo doctrine makes graph/prompt authoring route-bound regardless of task phrasing (`.github/copilot-instructions.md:15`), and FR-819 already recorded the same requirement for the original digest graph adaptation (`feature-requests/FR-819-github-native-digest-poc-repo.md:131-138`, `feature-requests/FR-819-github-native-digest-poc-repo.md:166-168`). FR-908 currently proposes changing `graph.yaml` but omits that gate (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:116-123`).

### R-7: Fold research evidence into each child FR

For each child FR, include a committed research record or an in-body alternatives table with substance. The local research gate permits an equivalent committed in-body alternatives table, but it must preserve real alternatives, precedent lines, disagreement, and the `is_this_a_graph` answer (`.github/skills/judge-fr/doctrine.md:118-128`; `feature-requests/TEMPLATE.md:11-20`). FR-908's table is useful (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:206-217`), but after the split each child needs its own scoped disposition rather than inheriting an omnibus table.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| S-1 | Child FR: daily-digest delivery integration and persist-before-send ordering in `graph.yaml`, `tools/write_bulletin.py`, `tools/write_bulletin.tool.yaml`, `.github/workflows/digest.yml`, `run_digest.py`, and `README.md` |
| S-2 | Child FR: slot-bound reusable collection in `graph.yaml`, source manifests under `sources/*.tool.yaml`, collection node/tool modules, workflow yamlgraph version pin, and `run_digest.py` import-path cleanup |
| S-3 | Child FR: rank-format boundary validation in the formatter and its tests, plus optional URL reconciliation against analyzed inputs |
| S-4 | Child FR or S-1 attachment: workflow-shape tests for cron, concurrency, permissions, SMTP env, and CI-before-digest ordering |

Not authorized under FR-908 as written: implementing all phases in one branch/commit series; implementing SMTP transport inside the digest refactor; changing yamlgraph framework nested-schema support; changing FR-892 slot semantics; changing the committed-SQLite/ledger strategy; retiring `examples/daily_digest`; HTML email rendering; package distribution of `examples/shared`; broad workflow or CI enforcement beyond the digest workflow; any graph/prompt edit outside the graph-authoring route.

## Revised acceptance criteria

- [ ] AC-01: FR-908 is replaced by separate child FRs for S-1, S-2, S-3, and either S-4 or an explicit S-4 attachment to S-1.
- [ ] AC-02: The delivery child FR proves the transition sequence `format_markdown -> gate -> write_bulletin -> send_email -> END`, with a separate no-op route that does not depend solely on empty rendered markdown.
- [ ] AC-03: The delivery child FR proves a simulated send failure exits non-zero after the bulletin file is written but before workflow commit/push.
- [ ] AC-04: The delivery child FR proves `run_digest.py` contains no file-writing or delivery logic after the graph owns both side effects.
- [ ] AC-05: The delivery child FR proves the workflow passes all required `SMTP_*` values to the run step and README documents the SMTP contract.
- [ ] AC-06: The delivery child FR records one real scheduled run ID and commit SHA showing both archive and email delivery.
- [ ] AC-07: The slot-reuse child FR is blocked until a released yamlgraph version includes FR-892 `--tool`; it then pins `yamlgraph>=<released-version>` in the digest workflow.
- [ ] AC-08: The slot-reuse child FR declares `collect` as a tool slot and ships at least two genuinely different source manifests, including current HN/RSS behavior moved out of hardcoded module constants.
- [ ] AC-09: The slot-reuse child FR proves switching source manifests requires no edit to `graph.yaml` and that `run_digest.py` no longer mutates `sys.path`.
- [ ] AC-10: The boundary-hardening child FR commits RED before GREEN for non-conforming ranked items, including the all-strings case.
- [ ] AC-11: The boundary-hardening child FR validates each ranked story against a typed model, drops only individual invalid items, raises when a non-empty ranked response has no valid survivors, and never emits an empty bulletin as success.
- [ ] AC-12: The boundary-hardening child FR preserves a legitimate no-new-articles no-op as a distinct state/route from malformed model output.
- [ ] AC-13: Any child FR that materially edits `graph.yaml` or `prompts/*.yaml` includes graph-authoring report evidence, not merely a passing exit code.
- [ ] AC-14: Every child FR updates its implementation status/decisions, includes applicable tests with requirement tags if this repository is changed, and includes a diary reflection if it becomes a feat/fix implementation.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation authority is granted from FR-908 as written; each split child FR must be judged before enforcement. | GATE |
| C-2 | The delivery child may call only an independently approved/enforced SMTP tool; it must not absorb FR-907 transport scope. | GATE |
| C-3 | The slot-reuse child may not begin until FR-906 (or an equivalent release FR) makes FR-892 `--tool` available to PyPI consumers. | GATE |
| C-4 | The boundary-hardening child must fail closed on malformed ranked output and must not convert malformed/all-dropped model output into the empty-bulletin no-op route. | GATE |
| C-5 | Any graph or prompt artifact edit must use the graph-authoring route and include the authoring report evidence required by repo doctrine. | GATE |
| C-6 | No framework-side schema-loader/nested-model support, committed-SQLite ledger replacement, example retirement, HTML rendering, or shared-package distribution work is authorized by any child unless explicitly scoped and judged there. | GATE |
| C-7 | Any changes to CI, hooks, judge/review doctrine, or other enforcement infrastructure require explicit human review before merge. | GATE |

Authority granted: none from FR-908 as written; authority can activate only through the split child FRs after each is revised, judged, and scoped to one concern.
