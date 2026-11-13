# Judgement: FR-1159 Ship the Map Memo as `yamlgraph.contrib.map_memo`

**Verdict:** APPROVED WITH REVISIONS — The contrib relocation is minimal and justified; authority activates only after R-1 through R-3 are folded into the committed FR and the gates below are met.

**Prior art:** FR-1158 (rejected core node; contrib classification accepted), FR-1116, FR-1120, FR-755 as dispositioned in the FR.

**Reviewed against:** Committed inputs at `7e42f56bb4612cf02fdfece7ade2507393e56bc0`, limited to:

- `feature-requests\FR-1159-map-memo-contrib.md` (entire FR, including its equivalent research record).
- `feature-requests\FR-1158-cached-map-node.md` and `feature-requests\FR-1158-cached-map-node.judgement.md`.
- `feature-requests\FR-1116-map-memo-file-corpus.md` (lines 1-260), `feature-requests\FR-1120-census-map-memo.md` (lines 1-275), `feature-requests\FR-755-utils-fsm-ownership-ruling.md`, and `feature-requests\FR-1157-cap164-register-fr1156.md`.
- `examples\shared\map_memo.py`, `examples\shared\map_memo_split.tool.yaml`, `examples\shared\map_memo_merge.tool.yaml`, and `examples\shared\README.md`.
- `yamlgraph\tools\manifest.py`, `yamlgraph\contrib\__init__.py`, and `pyproject.toml` (lines 1-240).
- `tests\unit\test_fr1116_map_memo.py`, `tests\unit\test_fr1120_map_memo_versions.py`, and `tests\unit\test_fr1120_census_memo_graph.py`; `tests\unit\test_fr1113_meta_map.py` (lines 1-240 and targeted memo/call-counter search matches).
- `capabilities\CAP-289-map-memo-file-corpus.yaml` and `capabilities\CAP-292-census-map-memo.yaml`.
- `.github\skills\judge-fr\doctrine.md`, `.github\skills\judge-fr\judgement.template.md`, and repository doctrine supplied from `.github\copilot-instructions.md` and `CLAUDE.md`.

The FR and inspected implementation evidence have no changes relative to HEAD. Uncommitted adapter changes and untracked files were not consumed. No author transcript or planning narrative informed this verdict. This file is a draft, not a promoted judgement.

## What is sound

The installed-user problem is real: `pyproject.toml:173-175` excludes examples, whereas the requested module lives under the discovered package. The existing manifest translator already preserves `module:` declarations (`yamlgraph\tools\manifest.py:94-110`). Moving the deterministic SQLite helper, rather than inventing another map compiler, addresses that packaging boundary without changing orchestration.

The rejected precedent is substantively dispositioned. FR-1159 lines 15-28 and 142-149 retain FR-1116/FR-1120 semantics, accept FR-1158's contrib classification, and reject duplicate implementations. Its five alternatives cover genuinely different delivery/architecture choices, preserve the rejected-core disagreement, and answer `is_this_a_graph`. This satisfies the equivalent committed research-record route. No measurement-tooling raw-sample gate applies.

**Strongest case against approval:** no external installed consumer is evidenced, and moving mature code risks registration drift merely to support a demonstration. Nevertheless, two real consumers already share this implementation, package exclusion is factual, and the proposed move adds no new execution mechanism. That supports contrib, not a framework primitive; the demo is a witness, not a third independent use case.

| Rubric criterion | Assessment |
|---|---|
| 1. Scope | Minimal and cohesive: one implementation moves, two manifests change, tests/docs and an installed-style demo accompany it (FR lines 32-36, 82-112). Registry path maintenance is missing, not a reason to enlarge the feature. |
| 2. Consistency | Requires R-1 and R-2: freezing CAP-289/CAP-292 conflicts with deleting their registered module; immutable assertion bodies conflict with the explicitly required manifest assertion change (FR lines 90-107, 119-123). |
| 3. Measurability | Most ACs are checkable. R-3 removes the package-discovery proxy for the explicit installed-wheel promise (FR lines 50-54, 124-126). |
| 4. Feasibility | Existing dependencies suffice: the helper imports stdlib, Pydantic and `yamlgraph.models`; `PythonRuntime` accepts exactly one module/path source (`manifest.py:33-48`). The clean CI recipe is concretely cited through FR-1157. |
| 5. Architecture alignment | Deterministic I/O stays in Python; the new demonstration uses existing map/subgraph/tool abstractions. FR-755's Ruling explicitly supports a supported-but-peripheral contrib tier. No compiler or state change is needed. |
| 6. Single responsibility | One concern: distribute an existing memo implementation and prove reuse through its installed import surface. The demo and dependency-path repairs support that concern; SPLIT is unwarranted. |
| 7. Strategic classification | **Contrib/example**: two existing consumers, existing graph primitives, and a packaging gap. This implements rather than evades the FR-1158 classification. |
| 8. Testability | Existing functional tests already exercise file versions, opaque versions, transactions and graph reuse. Relocation witnesses are directly derivable after R-2/R-3; no speculative new API or unavailable fixture is needed. |

## Required revisions

### R-1: Repoint the capability registry instead of freezing deleted paths

Replace FR lines 105-107 with an explicit authorization for mechanical path updates in CAP-289 and CAP-292. CAP-289 names the old module in its description and both module lists (`capabilities\CAP-289-map-memo-file-corpus.yaml:4,11,28`); CAP-292 names it in both module lists (`capabilities\CAP-292-census-map-memo.yaml:9,29`). Leaving these unchanged knowingly registers a deleted implementation.

Replace those module-path occurrences with `yamlgraph/contrib/map_memo.py`, including CAP-289's descriptive path. Preserve the existing capability IDs, requirement IDs, behavioral requirement text, and historical FR ownership. CAP-302 / REQ-YG-726 remains the separate owner of distribution/relocation witnesses and must register FR-1159. Permit only generated architecture changes resulting from these registry edits, not manual unrelated architecture rewrites.

### R-2: Specify the one necessary assertion-contract change

Amend AC-03 and the Planned Operations stop condition to preserve all behavioral assertions, while explicitly allowing the existing manifest-source assertion to change from a resolved file path to `tool["module"] == "yamlgraph.contrib.map_memo"` plus absence of `"path"`.

The current witness accesses `tool["path"]` at `tests\unit\test_fr1116_map_memo.py:360-367`; it cannot pass unchanged after the required manifest translation. This is an intentional source-contract change, not changed memo behavior. Permit necessary import strings, path references, and the path-specific loader docstring to change. Preserve the actual manifest-loaded split/merge execution witness at lines 382-398 and every existing outcome, error, signature, attribution and call-count assertion.

### R-3: Prove the installed-wheel contract with the built artifact

Replace AC-04's package-discovery alternative with a provider-free witness that builds an actual wheel and inspects its archive for `yamlgraph/contrib/map_memo.py` and absence of the former example module. Package discovery alone enumerates packages, not proof of usable installed code.

Install that wheel non-editably into an isolated environment with declared dependencies available, and run a fresh interpreter from outside the checkout with checkout paths absent from `PYTHONPATH`. Assert that the memo module originates in that installation, load both functions through inline `module:` tool declarations, and perform a split/merge round trip over temporary files and a store. A second split must return no work. This uses the existing API and no provider.

Define AC-05's separate fresh-interpreter assertion as absence of `yamlgraph.contrib.map_memo` from `sys.modules` after importing only `yamlgraph.contrib`; do not assert that no transitive dependency anywhere imports `sqlite3`. The requirement is lazy memo loading, not ownership of unrelated import side effects.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1: Relocated implementation | `examples\shared\map_memo.py` to `yamlgraph\contrib\map_memo.py`; only relocation/docstring changes |
| D-2: Existing consumer bindings | The two `examples\shared\map_memo_*.tool.yaml` runtime sources; existing graph artifacts remain unchanged |
| D-3: Public usage documentation | Memo section of `examples\shared\README.md`; contrib module-list docstring, without a new re-export |
| D-4: Registry integrity | CAP-289/CAP-292 path maintenance; new CAP-302 / REQ-YG-726 registration; corresponding generated architecture output |
| D-5: Focused evidence | Named existing test files with R-2's narrow exception; `tests\unit\test_fr1159_map_memo_contrib.py` for distribution, lazy-import and demo witnesses |
| D-6: Small demonstration | `examples\demos\map_memo\` with three notes, read-to-LLM subgraph worker, inline module tools, split/map/merge and its authoring report |
| D-7: Delivery record | FR implementation/status updates, feature changelog fragment, and scoped diary entry with a **Seed:** |

Not authorized: a core node type or memo key; compiler, state, manifest-schema or CLI changes; changed memo signatures, store format, failure reuse, thresholds or persistence behavior; old-path shims, duplicate implementations or eager re-exports; existing consumer graph/prompt rewrites; packaged manifest lookup machinery; TTL, pruning, new backends or new identity modes; enforcement-infrastructure edits.

## Revised acceptance criteria

- [ ] AC-01: The implementation exists only at `yamlgraph\contrib\map_memo.py`, with a baseline-relative diff showing no executable changes. No executable import, including subprocess source strings, uses `examples.shared.map_memo`; Git rename/history evidence identifies the source move.
- [ ] AC-02: Both existing manifests use `runtime.module: yamlgraph.contrib.map_memo` without `runtime.path`. FR-768 translation asserts the module source and both resolved functions execute the existing split/merge witness successfully.
- [ ] AC-03: The four named existing suites pass with their behavioral assertions preserved. Only imports/path references, path-specific documentation and the precise R-2 manifest-source assertion exception change; existing consumer graphs/prompts are unchanged.
- [ ] AC-04: A REQ-YG-726 provider-free witness builds and inspects the wheel, installs it non-editably, and proves installation-origin imports, inline module tool resolution, split/merge execution and second-split reuse outside the checkout as specified in R-3.
- [ ] AC-05: In a fresh interpreter, importing `yamlgraph.contrib` does not load `yamlgraph.contrib.map_memo`; the contrib initializer adds only module-list documentation, not a memo re-export.
- [ ] AC-06: The actual compiled demo runs with only `execute_prompt` patched, isolated copies of its three notes and a temporary store. With fresh graph state on each invocation, per-run provider-call counts are 3, 0 and 1 after editing exactly one note; run 2 reports `reused_ok == 3`. Run-2 ordered records equal run 1's, and run 3 retains the unchanged notes' records.
- [ ] AC-07: The demo follows `scripts\author.sh`, has a substantive honest authoring report, and lints clean. The recorded live two-run smoke uses one initially empty isolated store, totals at most 10 provider calls, and demonstrates zero worker calls plus three reused successes on run 2. Record the provider/model, exact commands and observed counts, not merely exit codes.
- [ ] AC-08: CAP-289/CAP-292 contain the new implementation path in every affected registry location without behavioral requirement changes. CAP-302 / REQ-YG-726 registers FR-1159 and its witnesses; any architecture regeneration is limited to corresponding registry output.
- [ ] AC-09: The targeted command in Planned Operations, `python scripts\req_coverage.py --strict`, `lint-imports`, relevant Ruff checks/formatting and the cited FR-1157 clean CI-mirror fast suite pass on the committed candidate. The FR records candidate identity, commands, results and deviations; the README, feature fragment and diary **Seed:** are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| GATE-1 | Fold R-1 through R-3 and the revised ACs into the committed FR before implementation; promoting this draft alone does not satisfy those conditions. | GATE |
| GATE-2 | Preserve executable memo behavior and existing consumer graph artifacts. A needed semantic change stops this relocation and requires separately judged scope; do not weaken behavior assertions to finish the move. | GATE |
| GATE-3 | Use the graph-authoring route for the new demo and evaluate the authoring report, not only its exit status. | GATE |
| GATE-4 | Live spend is limited to the committed FR's recorded operator authorization: the two-run demo smoke, at most 10 provider calls total. No existing-consumer live runs or uncapped retries are authorized. Missing credentials or an exhausted cap must be recorded as an unmet AC, not replaced by a mocked live-success claim. | GATE |
| GATE-5 | Follow RED/GREEN and requirement traceability; keep distribution proof independent of checkout imports, and complete FR implementation recording and Distill. | GATE |

Authority granted: conditional authority to relocate and distribute the unchanged memo helper as contrib, repair its direct references, and author the bounded demonstration, only after the required revisions are committed; no core map capability is authorized.
