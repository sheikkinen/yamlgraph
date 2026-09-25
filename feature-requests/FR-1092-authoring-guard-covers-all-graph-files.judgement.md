# Judgement: FR-1092 Authoring guard covers all graph files

**Prior art:** `FR-1092-authoring-guard-covers-all-graph-files.md` is the FR this judgement governs. FR-767 (guard origin, R-2 bright line), FR-1014 (dir-aware guard) and FR-1093 (read-only commands) are dispositioned in the FR and reviewed below.

**Verdict:** SPLIT — the graph-identity coverage fix is evidenced and feasible, but the folded read-route hint is an orthogonal concern with its own consumer, evidence, behavior contract, and acceptance test; neither concern has implementation authority until it is separately filed, judged, and its boundary defects below are resolved.

**Reviewed against:** `feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `feature-requests/TEMPLATE.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/hooks/tests/test_authoring_guard.py`; `.github/hooks/README.md`; `scripts/check_authoring_proof.py`; `tests/unit/test_fr1014_authoring_proof_dir_graphs.py`; `.pre-commit-config.yaml`; `feature-requests/FR-767-graph-authoring-sole-route.md`; `feature-requests/FR-767-graph-authoring-sole-route.judgement.md`; `feature-requests/FR-1014-dir-aware-authoring-guard.md`; `feature-requests/FR-1093-authoring-guard-read-only-commands.md`; `ARCHITECTURE.md`; `capabilities/CAP-158-copilot-skill-promotion.yaml`.

## What is sound

The primary defect is real, bounded, and supported by repository evidence. The current guard recognizes named path classes in `governed_path()` rather than the full graph artifact class (`.github/hooks/scripts/pre-command-guard.sh:165-173`), while FR-1092 records 82 tracked, differently named graph files and 22 nested prompts outside those arms (`feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md:87-128`). The first consumer is concrete, and the unsentineled probes demonstrate an enforcement gap rather than a hypothetical preference (`feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md:7-13`, `:129-150`).

The core proposal conforms before extending. It preserves the token-bound sentinel and the existing `graphs/` depth rules, extends the established PreToolUse guard and local commit backstop, and proposes RED witnesses on the existing hook harness and REQ-YG-423 truth-table surface (`feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md:190-243`, `:252-307`). The implementation is feasible with repository tools: the hook already embeds Python for editor and terminal classification (`.github/hooks/scripts/pre-command-guard.sh:151-270`), the backstop already reads staged additions (`scripts/check_authoring_proof.py:31-48`), and the current tests already exercise editor tools, terminal shapes, sentinel states, and mirrored predicates (`.github/hooks/tests/test_authoring_guard.py:121-279`; `tests/unit/test_fr1014_authoring_proof_dir_graphs.py:25-132`).

The research substitute is substantive enough for this non-measurement FR. It contains six genuinely different solution classes, dispositions each, preserves dissent, and answers `is_this_a_graph` (`feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md:313-352`). Prior art, including rejected FRs, is explicitly dispositioned (`feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md:19-59`).

Strategically, the core concern is enforcement hardening of the existing graph-authoring pattern, not a new framework primitive. Its use cases are the differently named graphs and nested prompts already present in `examples/`; no runtime graph abstraction is added. The read-route wording is separately pattern documentation for an existing false-positive recovery route. Their adjacency in one shell file does not make them one responsibility.

The strongest case against the proposed split is implementation economy: both concerns alter the same denial block, so one patch avoids repeat review. That does not overcome the doctrine's responsibility boundary. FR-1093 expressly defines itself as changing no allow/deny decision (`feature-requests/FR-1093-authoring-guard-read-only-commands.md:4`), whereas FR-1092 changes which paths and payloads are denied. FR-1092 item 8 and AC-12 retain FR-1093's separate consumer and outcome (`feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md:244-250`, `:308-310`). The judge rubric requires orthogonal bundles to split (`.github/skills/judge-fr/doctrine.md:49-50`).

## Required revisions

### R-1: Refile the graph-identity coverage concern alone

Create a new FR containing the differently named graph coverage, nested prompt coverage, editor/terminal/backstop predicates, truth table, documentation, requirement traceability, changelog, implementation record, and adversarial review gate. Remove Proposed Solution item 8, AC-12, the FR-1093 audit census, and every read-route denial-text deliverable. Cite this SPLIT judgement and disposition FR-1092 as its parent. The new FR re-enters judgement at round 1 and receives no inherited authority.

### R-2: Refile the read-route hint as its own concern

Reopen FR-1093 as a new FR file or create a successor containing only the fail-closed denial hint, README read-route documentation, and tests proving that the hint changes no allow/deny decision. Cite this SPLIT judgement and disposition FR-1093's withdrawal. Do not make its implementation depend on the graph-coverage FR; whichever implementation lands second must reconcile the shared denial block without broadening its own scope.

### R-3: Replace the claimed shared predicate with a surface-specific decision matrix

In the graph-coverage successor, replace the claim that the guard, backstop, and pre-commit selector "give the same answer" with one explicit matrix keyed by `(surface, tool/operation, path, pre-write content, incoming or staged content, expected invocation, expected governance decision)`.

The matrix must distinguish:

- editor governance, which the proposal makes content-sensitive;
- terminal governance, which the proposal makes path-wide for `examples/**/*.ya?ml` destinations;
- the pre-commit `files:` selector, which only decides whether the hook runs and must therefore match data YAML too; and
- the proof script, which currently examines staged additions only (`scripts/check_authoring_proof.py:2-11`, `:31-42`).

Add assertions for a non-graph data YAML row on all four surfaces. Do not call selector invocation a governance decision, and do not claim staged modification coverage unless the successor explicitly changes `--diff-filter=A` and supplies RED tests for that change. The current "same predicate lives in three surfaces" contract (`.github/hooks/README.md:84-90`) must be revised honestly if the accepted design intentionally gives the surfaces different predicates.

### R-4: State how the content classifier changes FR-767 C-4

The graph-coverage successor must explicitly supersede FR-767 C-4 for artifact identity while preserving its prohibition on classifying edit materiality. Fold this exact boundary into the proposal and conditions:

> For editor tools and staged additions under `examples/`, a deterministic content predicate may classify artifact identity. Once classified, every unsentineled write is denied without judging whether the edit is material. Terminal writes remain path-wide and fail closed.

This is required because FR-767 currently says the materiality boundary is path-based and forbids a semantic edit classifier (`feature-requests/FR-767-graph-authoring-sole-route.judgement.md:86`), while FR-1092 deliberately selects content classification for editor tools (`feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md:195-215`, `:324-330`). If the successor does not supersede C-4 in those narrow terms, it must select FR-1092 alternative 1 instead.

### R-5: Make the graph syntax claim honest and directly testable

Rename and rewrite the graph-coverage successor so it promises the exact syntax recognized by its predicate, not "every graph." The selected regex does not recognize top-level YAML flow style, and FR-1092 explicitly leaves that accepted loader form out of scope (`feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md:363-366`). Define the governed content class as block-style YAML containing a quoted or unquoted `nodes` key at column zero, and add negative tests for an indented `nodes:` fragment and a flow-style `{nodes: ...}` graph. Alternatively, use a parser-based predicate and specify a fail-closed dependency/error contract; do not retain the universal title with the regex design.

### R-6: Specify fragment attribution for editor payloads

Define how `replace_string_in_file`, every `multi_replace_string_in_file` replacement, and each `apply_patch` file section are associated with content before applying `is_graph_text`. A `nodes:` line belonging to one patch section must not classify another YAML path, and a fragment inserted at a nested indentation must not be treated as a top-level key merely because the fragment string starts at column zero. Add RED rows for a multi-file patch and a nested replacement. The present proposal names incoming fields but does not define final-content reconstruction or section attribution (`feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md:204-215`), so AC-01 cannot yet derive complete tests for the promised no-false-positive behavior.

### R-7: Record the operator's unresolved scope decisions

Before the graph-coverage successor returns to judgement, its committed text must record explicit operator answers to these questions:

1. **Terminal data-YAML writes:** authorize path-wide denial for every shell write destination under `examples/**/*.ya?ml`, or choose path-wide governance for every tool. Evidence and recommended default are FR-1092 H-1 and alternatives 1-2 (`feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md:317-330`, `:373-375`).
2. **Nested prompts:** govern every YAML depth below an `examples/**/prompts/` directory, yes or no (`feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md:200-203`, `:376-377`).
3. **Other roots and snippets:** keep graphs outside `examples/` and `graphs/`, plus `yamlgraph_gen` fragments, out of scope, or require separate FRs; do not silently widen this successor (`feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md:354-362`, `:381-384`).
4. **Existing marker cleanup:** leave FR-767's REQ-YG-527 markers untouched or authorize a separate hygiene FR; do not bundle retagging into this successor (`feature-requests/FR-1092-authoring-guard-covers-all-graph-files.md:367-369`, `:385-387`).

Suggested defaults are not decisions. The judge may not absorb them on the operator's behalf (`.github/skills/judge-fr/doctrine.md:100-101`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | New graph-coverage FR: differently named block-style graphs and nested prompts under `examples/`, with surface-specific predicate matrix, RED/GREEN tests, docs, traceability, and review gates. |
| D-2 | New read-route FR: catch-all denial hint and README documentation only, with decision-preservation tests. |
| D-3 | FR-1092: record the SPLIT disposition and links to both successor FRs; no implementation record may claim authority from this draft. |

Not authorized under FR-1092: any hook, pre-commit, proof-script, doctrine, architecture, capability, changelog, or test implementation; changes to `graphs/` depth rules; governance of graph files outside `examples/` and `graphs/`; governance of `yamlgraph_gen` fragments; support for YAML flow-style graphs; retagging existing FR-767 tests; changes to sentinel identity/lifecycle; new allow paths; changes to judge/review routes; or combining the two successor concerns merely because they touch the same denial block.

## Revised acceptance criteria

### Graph-coverage successor

- [ ] AC-G01: The FR contains no read-route hint, FR-1093 census, or denial-documentation criterion unrelated to graph/prompt identity.
- [ ] AC-G02: A surface-specific matrix distinguishes editor governance, terminal governance, selector invocation, and staged-addition proof decisions for graph, nested-prompt, ordinary-data, indented-fragment, and flow-style rows.
- [ ] AC-G03: The FR explicitly supersedes FR-767 C-4 only for deterministic artifact-identity classification and preserves bright-line denial for every write once an artifact is classified.
- [ ] AC-G04: RED tests directly cover tracked differently named graphs, synthetic new block-style graphs, nested prompts, ordinary data YAML, indented `nodes:`, flow-style YAML, unreadable paths, multi-file patch attribution, nested replacement context, path-wide terminal writes, sentineled allows, and staged-addition proof behavior.
- [ ] AC-G05: The pre-commit selector is tested as invocation routing, not asserted to be the same content-governance predicate as the editor or proof script.
- [ ] AC-G06: The operator decisions in R-7 are recorded in the committed FR before judgement.
- [ ] AC-G07: All new tests carry `REQ-YG-423`; architecture, CAP-158, hook documentation, graph-authoring doctrine, changelog, implementation record, and diary changes describe only the accepted boundary.
- [ ] AC-G08: `scripts/review.sh` review and independent human review are recorded before merge.

### Read-route successor

- [ ] AC-R01: The existing fail-closed `load_and_compile` probe remains denied and the catch-all denial names the approved read/search, lint, and `tmp/` script routes.
- [ ] AC-R02: Redirect, `tee`, copy/move, and editor-tool denials retain their existing route text without the read-only hint.
- [ ] AC-R03: Existing and new tests prove no allow/deny decision changes.
- [ ] AC-R04: README commands and denial text are tested against one shared documentation table.
- [ ] AC-R05: `scripts/review.sh` review and independent human review are recorded before merge.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | FR-1092 grants no implementation authority. Both successor concerns must independently complete Plan → Judge → Enforce. | GATE |
| C-2 | The graph-coverage successor must not implement the read-route hint; the read-route successor must not change governed paths, content classification, or terminal decisions. | GATE |
| C-3 | Surface-specific behavior must be explicit: editor content classification, terminal path-wide denial, selector invocation, and staged proof may differ only as specified and tested. | GATE |
| C-4 | Content classification may identify an artifact only after the successor explicitly supersedes FR-767 C-4 in the narrow terms of R-4; it must never classify whether an edit is material. | GATE |
| C-5 | Ambiguous or unreadable governed writes fail closed; no parser or file-read error may become approval. | GATE |
| C-6 | No successor may claim coverage for YAML flow-style graphs while the selected predicate excludes them. | GATE |
| C-7 | Human answers to R-7 must be committed before authority; suggested defaults are not authorization. | GATE |
| C-8 | Every enforcement-infrastructure implementation requires `scripts/review.sh` plus independent human review before merge. | GATE |

Authority granted: none under FR-1092; authority may be granted only by separate judgements on the two successor FRs after the revisions and gates above are satisfied.
