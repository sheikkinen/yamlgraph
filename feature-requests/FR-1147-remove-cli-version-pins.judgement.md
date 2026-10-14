# Judgement: FR-1147 Remove CLI Version Pinning (Claude Code, opencode, Copilot)

**Verdict:** REJECTED — the version-shape direction is feasible and narrowly scoped, but this post-FR-890 proposal receives no implementation authority until its research evidence is substantive, its canonical requirement source is included, and its acceptance contract is made internally consistent and operationally witnessed.

**Reviewed against:** `feature-requests/FR-1147-remove-cli-version-pins.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-959-claude-cli-backend-primitive.md`; `feature-requests/FR-959-claude-cli-backend-primitive.judgement.md`; `feature-requests/evidence/FR-959-claude-auth-probe.md`; `feature-requests/FR-1048-opencode-cli-backend.md`; `feature-requests/evidence/FR-1048-opencode-cli-probe.md`; `feature-requests/FR-931-judge-review-model-pin-gpt56sol.md`; `feature-requests/FR-982-unit-suite-runs-with-tracer-live.md`; `docs/2026-09-05-research-pi-agent-runtime.md`; `yamlgraph/node_factory/copilot_runtime_claude.py`; `yamlgraph/node_factory/copilot_runtime_opencode.py`; `yamlgraph/node_factory/copilot_runtime.py`; `tests/unit/test_fr959_claude_backend.py`; `tests/unit/test_fr960_claude_judge_variant.py`; `tests/unit/test_fr1048_opencode_backend.py`; `tests/unit/test_fr1049_opencode_judge_variant.py`; `tests/unit/test_fr982_tracing_off_in_tests.py`; `capabilities/CAP-30-copilot-node.yaml`; `ARCHITECTURE.md`; `reference/graph-yaml.md`; `reference/development-operations.md`; `scripts/aggregate_changelog.py`; `scripts/check_changelog_req.py`; `tests/fixtures/fr890/FR-998-fixture-missing-research.judgement.md`.

## What is sound

The problem is real and current. The FR names a concrete first consumer and an observed refusal caused solely by the installed Claude banner moving from `2.1.255` to `2.1.296` (`feature-requests/FR-1147-remove-cli-version-pins.md:8-12,59-69`). The existing code confirms that both affected runtimes compare complete stdout against one-element allowlists before execution (`yamlgraph/node_factory/copilot_runtime_claude.py:34-40,128-138`; `yamlgraph/node_factory/copilot_runtime_opencode.py:33-35,196-206`), while the Copilot runtime has no analogous version subprocess (`yamlgraph/node_factory/copilot_runtime.py:220-224`).

The proposed change is architecturally aligned with the existing boundary design. Claude auth still crosses `_ClaudeAuthStatus`, result stdout still crosses `_ClaudeEnvelope`, and opencode output still crosses its typed fail-closed event state machine (`yamlgraph/node_factory/copilot_runtime_claude.py:66-77,141-149,200-228`; `yamlgraph/node_factory/copilot_runtime_opencode.py:219-233,292-326`). Preserving those checks while replacing only exact release membership with full-banner shape validation is smaller than deleting either preflight or changing payer/output contracts. The retained Claude product suffix directly preserves the foreign-binary witness in the existing test (`tests/unit/test_fr959_claude_backend.py:398-409`), and the cited opencode capture establishes that its observed banner is a bare semantic version (`feature-requests/evidence/FR-1048-opencode-cli-probe.md:16-23`).

Scope and single responsibility are sound: Claude and opencode are two instances of one release-pinning policy, while payer rules, argv, envelopes, event vocabulary, model pins, and Copilot execution are explicitly excluded (`feature-requests/FR-1147-remove-cli-version-pins.md:160-200,226-231`). This is maintenance of a reusable framework primitive, not a contrib example or documentation-only pattern: the preflight behavior is shared by arbitrary copilot nodes and by the FR-960/FR-1049 judge variants (`feature-requests/FR-1147-remove-cli-version-pins.md:8-12,145-147`).

Feasibility and direct testability are also established. Existing tests already isolate probe order, foreign banners, version drift, auth, argv, envelopes, event transitions, and judge routing (`tests/unit/test_fr959_claude_backend.py:367-419`; `tests/unit/test_fr1048_opencode_backend.py:282-323`; `tests/unit/test_fr960_claude_judge_variant.py:297-317`; `tests/unit/test_fr1049_opencode_judge_variant.py:305-325`). The implementation therefore requires no new abstraction or dependency.

## Required revisions

### R-1: Supply substantive committed research before re-entry

Replace the current research pointer with a committed research record or rewrite the in-body table so it satisfies every local research field: four to six genuine solution classes, a precedent line for each class, preserved disagreement, and an explicit `is_this_a_graph` answer (`.github/skills/judge-fr/doctrine.md:118-130`). The current two-column table lists dispositions but no solution-class analysis, no preserved dissent, and no `is_this_a_graph` answer; two decisions are delegated back to the judge rather than analyzed (`feature-requests/FR-1147-remove-cli-version-pins.md:13-14,233-243`). A shape-valid table is not substantive research, and the prospective rule grants no authority in that state (`.github/skills/judge-fr/doctrine.md:118-128`).

Fold these two unresolved choices into the revised plan: retain opencode's per-invocation probe because it supplies a named missing/broken-binary preflight and logged version; do not add a minimum-version floor because the FR identifies no older-version defect or witnessed threshold. Preserve the strongest dissent: accepting every future shape-valid release no longer proves flag semantics in advance, especially for Claude's accepted-but-undocumented `--max-turns` behavior recorded on `2.1.255` (`feature-requests/evidence/FR-959-claude-auth-probe.md`, §4.3). State that typed parsing and nonzero exits fail closed on observed contract breakage, but do not claim the shape check predicts all future semantic drift.

### R-2: Update the canonical requirement source, then regenerate its view

Add `capabilities/CAP-30-copilot-node.yaml` to the deliverables. Revise REQ-YG-641 there from an exact supported-version check pinned to one probe to a per-invocation ASCII semantic-version Claude product-banner check followed by the unchanged auth check (`capabilities/CAP-30-copilot-node.yaml:86-97`). Revise REQ-YG-679 there to state the retained per-invocation opencode ASCII semantic-version banner check, because tests will continue to tag that requirement. Regenerate `ARCHITECTURE.md`; do not treat its generated row as the source of truth. The current plan authorizes only a direct `ARCHITECTURE.md` wording edit (`feature-requests/FR-1147-remove-cli-version-pins.md:189-200`) even though the capability registry owns these requirement descriptions and repository traceability requires tests to link to registered requirements (`.github/copilot-instructions.md:169-171`).

Keep the proposed reference updates and dated historical notes, and make the changelog criterion assert the exact fragment path, valid front matter, body requirement references, and `python scripts/check_changelog_req.py --strict` result. The repository gates feature fragments and validates `req:` IDs against the capability registry (`reference/development-operations.md:98-100`).

### R-3: Make the banner and regression contract exact

Specify ASCII digits, not Python `\d`: use full-string patterns equivalent to `[0-9]+\.[0-9]+\.[0-9]+ \(Claude Code\)` and `[0-9]+\.[0-9]+\.[0-9]+` after the existing surrounding-whitespace strip. Add direct rejection cases for a foreign Claude product, product-prefixed opencode output, empty output, extra lines/text, malformed component counts, Unicode digits, and nonzero exits. Require failures to include the exit code and bounded observed stdout/stderr, so a nonzero process with empty stdout does not produce an uninformative success-shaped diagnostic. The proposed `\d` patterns admit Unicode digits, while the ideal requires refusals to name what was observed (`feature-requests/FR-1147-remove-cli-version-pins.md:127-132,168-183`).

Rewrite AC-5. The exact-version assertions cannot remain "unchanged": Claude currently requires `2.1.254` to fail and opencode requires `1.17.9` to fail (`tests/unit/test_fr959_claude_backend.py:394-419`; `tests/unit/test_fr1048_opencode_backend.py:313-323`). Name the invariant assertions that remain byte-identical—auth, environment stripping, argv order, typed envelope, event transitions, model resolution, session handling—and separately name the version tests that must change. Number the documentation/changelog criterion and give every new test a registered requirement marker. These changes remove the contradiction between planned test edits and AC-5 (`feature-requests/FR-1147-remove-cli-version-pins.md:145-147,202-224`).

### R-4: Bound the promise and witness the physical release transition

Replace “a vendor CLI auto-update never requires a YAMLGraph commit” with the enforceable promise: a release that preserves the accepted banner, payer, argv, and typed output contracts does not require an allowlist-only YAMLGraph commit. A vendor release that changes a consumed contract may still require a repository change, and the FR must not promise otherwise (`feature-requests/FR-1147-remove-cli-version-pins.md:127-132`).

Add a post-GREEN live witness on the installed `2.1.296 (Claude Code)` binary that executes one minimal, non-file-writing backend call with the unchanged auth/environment boundary and records the command shape, banner, auth method, exit status, redacted result head, and commit SHA. The FR currently records read-only version/auth/help probes but no successful `-p` run on the release whose operability motivates the change (`feature-requests/FR-1147-remove-cli-version-pins.md:71-89,137-156`). **Human decision required:** the named spend owner must explicitly authorize this one minimal subscription-billed witness before it runs; if authorization is withheld, revise the FR to claim only syntactic banner acceptance, not restored end-to-end operability. No live opencode run is required on this host because the FR states it is absent and cites the committed `1.18.31` raw banner (`feature-requests/FR-1147-remove-cli-version-pins.md:91-116,144`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | No implementation deliverable is authorized under this FR. |

For a revised proposal, the maximum eligible scope is: Claude and opencode banner-shape preflight in `yamlgraph/node_factory/copilot_runtime_claude.py` and `yamlgraph/node_factory/copilot_runtime_opencode.py`; directly affected unit/judge-variant tests; canonical REQ-YG-641/REQ-YG-679 text in `capabilities/CAP-30-copilot-node.yaml` and regenerated `ARCHITECTURE.md`; the two preflight paragraphs in `reference/graph-yaml.md`; dated notes in FR-959 and FR-1048; one changelog fragment; the FR implementation record; and one diary entry.

Not authorized: changes to the Copilot runtime; adding any CLI version allowlist or minimum-version floor; deleting or caching either version probe; changing Claude auth methods, stripped environment variables, argv, prompt/tool semantics, or envelope schema; changing opencode model resolution, argv, session semantics, payer handling, event vocabulary, or state machine; changing judge/review graphs or model pins; introducing a shared backend registry or new dependency; or modifying unrelated graph/prompt artifacts.

## Revised acceptance criteria

- [ ] AC-01: The revised FR references a committed research record or contains an equivalent dispositioned table satisfying `.github/skills/judge-fr/doctrine.md:118-130`, including four to six solution classes, precedent, preserved disagreement, and `is_this_a_graph`.
- [ ] AC-02: Requirement-tagged tests prove `2.1.255 (Claude Code)` and `2.1.296 (Claude Code)` pass Claude banner preflight and reach auth, while `1.18.31` and `1.99.0` pass opencode banner preflight and reach the run call.
- [ ] AC-03: Direct tests reject a foreign Claude product, prefixed opencode banner, empty output, extra text/lines, malformed component counts, Unicode digits, and nonzero probe exits before auth/agent execution; each error names exit status and bounded stdout/stderr.
- [ ] AC-04: Two executions still produce probe/auth/agent ordering for Claude and probe/agent ordering for opencode, with no cache.
- [ ] AC-05: Existing auth, environment, argv, envelope, model-resolution, session, event-vocabulary, transition, and no-state-update assertions retain their behavior; only assertions whose stated contract is exact release membership are rewritten.
- [ ] AC-06: `git grep -E "CLAUDE_SUPPORTED_(VERSIONS|BANNERS)|OPENCODE_SUPPORTED_BANNERS" -- yamlgraph tests reference ARCHITECTURE.md capabilities` returns no matches, while the historical FR notes remain as dated records.
- [ ] AC-07: `capabilities/CAP-30-copilot-node.yaml` defines the final REQ-YG-641 and REQ-YG-679 banner contracts; generated `ARCHITECTURE.md` agrees; `reference/graph-yaml.md` documents the same accepted and rejected shapes.
- [ ] AC-08: A requirement-tagged Copilot runtime test proves one agent subprocess and no `copilot --version` call, without changing `yamlgraph/node_factory/copilot_runtime.py`.
- [ ] AC-09: After named spend-owner authorization, a post-GREEN live witness on Claude Code `2.1.296` records commit SHA, banner, auth method, redacted command/result evidence, and successful typed backend completion; refusal of authorization is recorded and the FR's operability claim is narrowed before re-judgement.
- [ ] AC-10: `changelog/unreleased/fr-1147-cli-version-pins.md` has valid `type: feat`, `scope: copilot`, and `req: REQ-YG-641, REQ-YG-679` front matter; its body cites both requirements; `python scripts/check_changelog_req.py --strict` passes.
- [ ] AC-11: Git history contains a substantive RED commit for the new accepted-release tests before GREEN, and `python scripts/req_coverage.py --strict` plus the named targeted unit suite pass.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement this FR until substantive committed research satisfying R-1 is folded into the plan and the revised proposal is independently judged. | GATE |
| C-2 | The capability registry is the requirement source of truth; update `CAP-30-copilot-node.yaml` before regenerating `ARCHITECTURE.md`. | GATE |
| C-3 | Banner checks must use full-string ASCII semantic-version shapes and retain per-invocation ordering; no allowlist, floor, deletion, or cache is authorized. | GATE |
| C-4 | Claude auth/environment/envelope and opencode model/session/event-state-machine boundaries must remain unchanged and fail closed. | GATE |
| C-5 | The named spend owner must explicitly authorize the one live Claude `2.1.296` witness; the enforcer may not infer consent or silently substitute a mock for that operational claim. | GATE |
| C-6 | No Copilot runtime, judge/review graph, model pin, or governed graph/prompt artifact may change under this scope. | GATE |

Authority granted: none; return FR-1147 to planning, fold R-1 through R-4, and re-enter independent judgement before implementation.
