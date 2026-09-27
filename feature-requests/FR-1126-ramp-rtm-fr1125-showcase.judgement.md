# Judgement: FR-1126 ramp_rtm as the FR-1125 showcase — the refused shape and the filled one

**Verdict:** APPROVED WITH REVISIONS — the documentation-and-witness shape is minimal and testable, but implementation authority activates only after R-1 through R-3 are folded into the FR.

**Reviewed against:** `feature-requests/FR-1126-ramp-rtm-fr1125-showcase.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `docs/development-process.md`; cited evidence `docs/spikes/constrained-object-2026-09-27/README.md`, `feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md`, `feature-requests/FR-1123-untyped-subschema-constrained-decoding-gate.md`, `feature-requests/FR-1113-meta-map-demo.md`, `feature-requests/FR-1054-nested-object-schemas-reach-the-provider.md`, `feature-requests/FR-866-ramp-tailoring-graphs.md`, `reference/prompt-yaml.md`, `examples/demos/ramp_rtm/README.md`, `examples/demos/ramp_rtm/graph.yaml`, `examples/demos/ramp_rtm/prompts/derive_reqs.yaml`, `examples/demos/ramp_rtm/demo-output.log`, `yamlgraph/linter/checks_schema.py`, `yamlgraph/linter/graph_linter.py`, `yamlgraph/linter/checks.py`, `yamlgraph/utils/schema_walk.py`, `capabilities/CAP-164-structured-output-fallback.yaml`, `tests/unit/test_fr1125_open_objects.py`, `tests/unit/test_fr1123_sdk_parity.py`, `tests/unit/test_ci_demo_proof_gate.py`, `scripts/check_demo_proof.sh`; cited GitHub PR #734 and its committed proof `0cc2c3ff57a5fe635ad669477476504929ef9066:examples/demos/ramp_rtm/demo-output.log`.

## What is sound

- **Scope:** The FR changes one existing README and adds one focused rot guard. That is smaller than creating another graph/demo and directly satisfies the stated reader need (`FR-1126:69-79`, `FR-1126:151-157`).
- **Consistency:** The ideal, solution, and exclusions consistently preserve the already-working graph and prompt. The remaining inconsistencies are bounded to environment resolution, proof provenance, and what “exact” means; R-1 through R-3 make those statements single-valued.
- **Measurability:** The proposed witness names concrete strings, one linter code/path, a clean-after code set, and the exact five transformed properties (`FR-1126:120-140`, `FR-1126:160-173`). These become fully mechanical after R-3 removes the prefix loophole.
- **Feasibility:** E017 already traverses map sub-nodes as `derive/node` (`yamlgraph/linter/checks_schema.py:40-83`); `lint_graph` exposes typed issues (`yamlgraph/linter/graph_linter.py:111-170`); the public `anthropic.transform_schema` surface exists in the pinned SDK; and the committed prompt declares the five proposed item properties.
- **Architecture alignment:** This reuses the public linter, schema loader, provider transform, existing demo, and existing REQ-YG-712 rather than adding framework behavior or another capability. CAP-164 already defines untyped/open-object refusal (`capabilities/CAP-164-structured-output-fallback.yaml:55-75`).
- **Single responsibility:** README teaching plus its direct anti-drift witness are one documentation responsibility, not orthogonal features.
- **Strategic classification:** **Pattern documentation.** FR-1125 already supplied the primitive and migrated the example; FR-1126 exposes that existing behavior at its first-consumer surface.
- **Testability:** A failing README assertion can be written before the documentation, while the before/after linter and transformed-schema assertions can be derived directly from the revised criteria. No LLM call is needed.
- The research field has substantive committed mechanism evidence, five dispositioned alternatives, an `is_this_a_graph` answer, and differentiated prior art (`FR-1126:15-34`, `FR-1126:175-185`), satisfying the prospective FR-890 gate without inventing a research route after the fact.

## Required revisions

### R-1: Pin the provider and claimed model at every executable boundary

Replace the refusal reproduction with an explicit Anthropic environment, not an unset-provider assumption: `PROVIDER=anthropic yamlgraph graph lint tmp/ramp_rtm/graph.yaml`. Require the test to set `PROVIDER=anthropic` before both before/after lint assertions. The resolver reads `PROVIDER` before falling back to Anthropic (`yamlgraph/utils/schema_walk.py:50-59`), and FR-1125 records that a host `.env` previously changed this exact classification (`feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md:336-343`).

The live command must also set `ANTHROPIC_MODEL=claude-haiku-4-5` if the README retains the claim that this command makes two calls on that model. Otherwise remove the fixed-model claim and describe it as the configured Anthropic model. Do not present an environment-overridable default as a pinned execution.

### R-2: Make proof provenance and the demo-proof gate truthful

Rewrite Research and S-3 to state that the Anthropic proof is commit `0cc2c3ff57a5fe635ad669477476504929ef9066` in still-open #734, not the `demo-output.log` currently present on this branch. The current file records a 2026-08-23 DeepSeek run, while the cited commit records the 2026-09-27 `anthropic/claude-haiku-4-5` run.

Require the implementation PR to contain that exact successful Anthropic log in its own diff. If #734 lands first, change only the proof header to identify the same run as the FR-1126 reused proof; preserve the raw run body. This is required because any demo README change without a `demo-output.log` change fails the repository gate (`tests/unit/test_ci_demo_proof_gate.py:243-251`; `scripts/check_demo_proof.sh:4-50`). Record #734 as merged, superseded, or still depended upon in the FR implementation record. No new paid run is required.

### R-3: Test the complete documented E017 message, not an arbitrary prefix

Resolve the contradiction between “the exact E017 message” (`FR-1126:72-73`, `FR-1126:94-99`) and the proposed prefix comparison (`FR-1126:138-140`, `FR-1126:169-170`). The README must quote the complete `[E017] ` plus `LintIssue.message` text for the single before-copy finding. The test may normalize Markdown line wrapping and surrounding whitespace, but after normalization it must assert equality, not an 80-character prefix and not an ellipsis-truncated message.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/demos/ramp_rtm/README.md`: one FR-1125 showcase section containing the rule, complete E017 diagnostic, before/after schema excerpts, pinned zero-token lint reproduction, pinned live command, proof pointer, and reference link |
| D-2 | `tests/unit/test_fr1126_ramp_rtm_showcase.py`: README contract, deterministic before/after lint checks, exact normalized diagnostic equality, and five-property transformed-schema witness under REQ-YG-712 |
| D-3 | `examples/demos/ramp_rtm/demo-output.log`: the exact successful Anthropic proof from `0cc2c3ff`, with at most a provenance-header update if needed to place the log in the implementation diff |
| D-4 | `feature-requests/FR-1126-ramp-rtm-fr1125-showcase.md`: folded revisions, implementation status/decisions, RED/GREEN SHAs, proof disposition, and exact validation results |
| D-5 | One Distill entry under `docs/diary/` with a `**Seed:**` |

Not authorized: edits to `examples/demos/ramp_rtm/graph.yaml` or any `prompts/*.yaml`; framework, linter, provider, capability, reference, CI, or hook changes; a new demo; E016 documentation; a new requirement or capability; a changelog fragment; weakening or replacing REQ-YG-712; a new paid LLM run.

## Revised acceptance criteria

- [ ] AC-01: The README contains the heading `## Anthropic and open objects (FR-1125)` and all seven frozen elements: the two-sentence rule, complete E017 diagnostic, before/after schema excerpts, zero-token reproduction, live command, proof pointer, and reference link.
- [ ] AC-02 (RED first): A commit before the README implementation adds the focused test and fails only its README assertions; a later GREEN commit adds the section. The FR records both SHAs.
- [ ] AC-03: With `PROVIDER=anthropic` explicitly set, a temporary copy using the pre-FR-1125 `schema:` / `entries: list[dict]` form produces exactly one E017 whose message names `derive/node` and `entries.items`; no open-object prompt is committed under `examples/`.
- [ ] AC-04: With `PROVIDER=anthropic` explicitly set, the committed demo has none of E016, E017, W028, or W029. Passing its prompt model through public `anthropic.transform_schema` preserves exactly `req_id`, `statement`, `witness_tests`, `confidence`, and `status`, requires all five, and yields `additionalProperties: false`.
- [ ] AC-05: After whitespace normalization, the README's complete E017 diagnostic equals `[E017] ` plus the sole before-copy E017 `LintIssue.message`; prefix-only and ellipsis-truncated comparisons fail.
- [ ] AC-06: The README's refusal command sets `PROVIDER=anthropic`. Its live command sets `PROVIDER=anthropic` and either sets `ANTHROPIC_MODEL=claude-haiku-4-5` or omits any fixed-model claim.
- [ ] AC-07: The implementation diff contains a semantically valid `examples/demos/ramp_rtm/demo-output.log` from commit `0cc2c3ff`; it identifies Anthropic/`claude-haiku-4-5`, a successful two-branch run, and populated entries carrying all five declared fields. The demo-proof gate passes without a new paid run.
- [ ] AC-08: Every test carries `@pytest.mark.req("REQ-YG-712")`; the focused FR-1126 test and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-09: The FR implementation record states the final #734 disposition, RED/GREEN SHAs, and exact validation results; a Distill diary entry with `**Seed:**` is present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 and replace the original acceptance list with AC-01 through AC-09 before production edits. | GATE |
| C-2 | Keep provider-sensitive lint witnesses explicit with `PROVIDER=anthropic`; do not rely on the host environment or `.env`. | GATE |
| C-3 | Put the cited `0cc2c3ff` Anthropic proof in the implementation diff and satisfy the demo-proof gate; do not represent the current DeepSeek log as that proof. | GATE |
| C-4 | Preserve exact diagnostic equality after whitespace normalization; no prefix-only assertion. | GATE |
| C-5 | Keep RED and GREEN in separate commits, with RED failing on the missing README section rather than import, fixture, provider, or setup errors. | GATE |
| C-6 | Do not edit governed graph/prompt artifacts or framework/enforcement code under this authority. | GATE |
| C-7 | Reuse REQ-YG-712 and the cited live run; do not create a capability, requirement, changelog fragment, or paid replacement run. | GATE |

Authority granted: after the FR folds R-1 through R-3, implement only D-1 through D-5 under AC-01 through AC-09 and C-1 through C-7.
