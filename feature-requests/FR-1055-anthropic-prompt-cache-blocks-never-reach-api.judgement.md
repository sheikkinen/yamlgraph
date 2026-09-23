# Judgement: FR-1055 Anthropic prompt-cache blocks never reach the API (and the system prompt is dropped with them)

**Verdict:** APPROVED WITH REVISIONS — the core provider-boundary repair is minimal, feasible, and directly testable, but authority activates only after the FR answers the mandatory graph-fit question and removes or resolves its ambiguous, paid, downstream, dependency-policy, and release criteria.

**Reviewed against:** `feature-requests/FR-1055-anthropic-prompt-cache-blocks-never-reach-api.md`; cited evidence `yamlgraph/executor_base.py`, `tests/unit/test_prompt_caching_fr276.py`, `pyproject.toml`, `ARCHITECTURE.md`, `reference/prompt-yaml.md`, `scripts/req_coverage.py`, `feature-requests/FR-219.md`, `feature-requests/FR-276.md`, `feature-requests/FR-381-batch-llm-node-anthropic-messages-batch-api.md`, `feature-requests/FR-382-prompt-caching-chaplain-system-prompts.md`, `feature-requests/FR-449-agent-structured-output-anthropic-bugfix.md`, `examples/demos/prompt-caching/graph.yaml`, `examples/demos/prompt-caching/prompts/analyze.yaml`, `examples/demos/prompt-caching/prompts/reflect.yaml`, `examples/demos/prompt-caching/README.md`, and `examples/demos/prompt-caching/demo-output.log`; repo doctrine `.github/copilot-instructions.md`, `.github/skills/judge-fr/doctrine.md`, and `.github/skills/judge-fr/judgement.template.md`.

## What is sound

- **Scope and feasibility:** The causal chain is specific: both segmented-system entry paths converge on `_build_system_message_from_segments` (`yamlgraph/executor_base.py:240-273`), and its Anthropic branch places blocks in `additional_kwargs` while leaving `content` empty (`yamlgraph/executor_base.py:324-338`). The proposed production change at FR lines 150-177 repairs that single boundary rather than adding a new interface.
- **Consistency:** The summary, executed no-network probe, ideal result, and chosen alternative all identify the same defect and destination shape (FR lines 33-40, 66-92, 143-177, and 224-232). Scalar system prompts follow a separate branch (`yamlgraph/executor_base.py:266-270`), supporting the claimed unaffected surface.
- **Architecture alignment:** This restores the existing CAP-131 contract rather than extending it. REQ-YG-289 requires Anthropic `cache_control` injection and REQ-YG-290 preserves non-Anthropic flattening (`ARCHITECTURE.md:1797-1816`, duplicated in detail at lines 3392-3403). The public prompt reference already promises those provider semantics (`reference/prompt-yaml.md:67-97`).
- **Prior art:** FR-276 established the primitive and explicitly required verification of LangChain's supported message construction; FR-219 claimed a cache benefit while leaving live usage verification as a next step; FR-382 is a downstream consumer; FR-381 is a separate batch API proposal; and FR-449 concerns a different Anthropic message boundary. FR-1055 distinguishes each at lines 14-31 rather than treating prior work as proof.
- **Measurability and testability of the core repair:** The proposed seam test crosses producer and consumer and checks both instruction survival and cache metadata (FR lines 179-194). Existing tests demonstrably stop at the producer: Anthropic assertions read `additional_kwargs["content"]` at `tests/unit/test_prompt_caching_fr276.py:199`, `:230`, and `:345`.
- **Strategic classification:** This is a **framework primitive repair**. It restores the already-declared CAP-131 behavior for the shared builder used by `system_segments` and list-form `system`; it does not authorize a new cache abstraction, provider API, or graph.
- **Single responsibility at the implementation core:** One message-construction defect explains both the lost system instruction and absent cache marker. Those are two consequences of one boundary error, not separate fixes.

## Required revisions

### R-1: Add the mandatory `is_this_a_graph` research answer

Fold this explicit answer into the Research section: **No. This work is one deterministic provider-boundary assignment plus focused Python tests; it contains no per-item model operation, multi-stage LLM pipeline, or subagent fan-out, and no existing graph is a better execution vehicle.** The current alternatives table supplies five genuine solution classes and executed evidence, but omits the graph-fit answer required by `.github/skills/judge-fr/doctrine.md:118-128` and `.github/copilot-instructions.md:129`.

### R-2: Freeze the FR to the shared-builder repair and its direct witnesses

Replace the current acceptance list at FR lines 200-222 with the revised criteria below. Remove FR-382 prompt re-verification and release publication from this implementation scope. FR-382 is historical downstream-consumer evidence, not a named current file-and-command witness, while release is a later lifecycle action. Do not modify Chaplain/Copilot prompts, release metadata, tags, or the external `yamlgraph-visual-novel` repository under FR-1055 authority.

### R-3: Resolve the dependency-policy contradiction in favor of the seam test

Delete the "`langchain-anthropic` gains an upper bound, or ..." alternative at FR lines 218-219 and state that the seam test is the selected dependency-drift guard. The FR itself establishes that the declared floor reproduces the bug and that a pin is not the cure (FR lines 111-120); authorizing an unspecified upper bound would be both ambiguous and orthogonal to the one-line boundary repair. Any dependency upper-bound policy requires a separate FR with a selected version and dependency-governance evidence.

### R-4: Make the live Anthropic spend a recorded human decision

Add this explicit question to the FR and record the operator's answer before enforcement: **"Approve one paid Anthropic verification run, with the raw second-call usage record committed to `examples/demos/prompt-caching/demo-output.log` and copied into this FR?"** If approved, the artifact must show the second call's exact non-zero cache-read field and value; prose such as the current log's "`Cache hit!`" claim (`examples/demos/prompt-caching/demo-output.log:13-14`) is insufficient. If declined or credentials are unavailable, remove the paid-run and log-regeneration criteria from this FR and file them as release verification; do not synthesize a success-shaped log.

### R-5: Make every authorized criterion executable and requirement-linked

Name the test file, assertions, requirement marker, and commands exactly as in the revised criteria. Replace "`Documentation updated`" with a mechanically bounded documentation decision: because `reference/prompt-yaml.md:67-97` already states the intended public behavior, either make no documentation edit and record "no public contract change," or identify the exact lines and assertion that are inaccurate. The new seam test must carry `@pytest.mark.req("REQ-YG-289")`, as required by `.github/copilot-instructions.md:169-171`.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/executor_base.py`: put Anthropic text blocks in `SystemMessage.content`; do not change non-Anthropic or scalar-system construction |
| D-2 | `tests/unit/test_prompt_caching_fr276.py`: update all Anthropic producer assertions and add one producer-to-`langchain_anthropic._format_messages` seam regression test |
| D-3 | `feature-requests/FR-1055-anthropic-prompt-cache-blocks-never-reach-api.md`: fold R-1 through R-5, implementation status, decisions, and actual verification evidence |
| D-4 | `changelog/unreleased/`: one FR-1055 fix fragment tied to the existing CAP-131 requirement |
| D-5 | `docs/diary/`: one Distill entry with a `Seed:` after implementation |
| D-6 | `examples/demos/prompt-caching/demo-output.log`: only if the operator explicitly approves the paid verification in R-4 |

Not authorized: a `langchain-anthropic` upper bound; changes to `yamlgraph/utils/prompts.py`, provider factories, batch APIs, Chaplain/Copilot prompt files, graph or prompt YAML artifacts, the external `yamlgraph-visual-novel` repository, version bumps, releases, tags, or unrelated prompt-cache refactors. A public-doc edit is not authorized unless the FR first names the inaccurate statement it will correct.

## Revised acceptance criteria

- [ ] AC-01: A RED test tagged `@pytest.mark.req("REQ-YG-289")` demonstrates that `_build_system_message_from_segments([{"content": "STABLE", "cache": True}], {}, None, "anthropic")` does not deliver a non-empty system block through `langchain_anthropic._format_messages`.
- [ ] AC-02: After the production change, the Anthropic `SystemMessage.content` equals a list containing the rendered text block and `{"cache_control": {"type": "ephemeral"}}`; `SystemMessage.additional_kwargs` does not carry a duplicate `content` payload.
- [ ] AC-03: The seam test composes `_build_system_message_from_segments` with `langchain_anthropic._format_messages` and asserts the exact rendered system text `"STABLE"` plus the exact ephemeral cache-control object, not merely truthiness.
- [ ] AC-04: Anthropic producer assertions at `tests/unit/test_prompt_caching_fr276.py:199`, `:230`, and `:345` read `.content`; the non-Anthropic assertion at `:277` remains valid and non-Anthropic providers still receive one flattened string.
- [ ] AC-05: Existing scalar `system:` tests remain green, demonstrating that the branch at `yamlgraph/executor_base.py:266-270` is unchanged.
- [ ] AC-06: `pytest tests/unit/test_prompt_caching_fr276.py -q --no-cov` passes.
- [ ] AC-07: `python scripts/req_coverage.py --strict` passes, and the new seam test is linked to REQ-YG-289.
- [ ] AC-08: The FR records that the existing public prompt contract needs no edit, or names and verifies the exact documentation correction.
- [ ] AC-09: A valid FR-1055 fix fragment exists under `changelog/unreleased/`, and the required Distill entry exists under `docs/diary/` with a `Seed:`.
- [ ] AC-10: If and only if the operator approves the paid run in R-4, the second call's raw non-zero cache-read field and value appear in both `examples/demos/prompt-caching/demo-output.log` and the FR; otherwise the FR records the declined/deferred decision and contains no claim of a measured cache hit.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into the FR before changing production code; authority does not activate from this draft alone. | GATE |
| C-2 | Commit the condemning REQ-YG-289 test as RED before the production fix, then implement only the shared-builder change needed to make it GREEN. | GATE |
| C-3 | Do not use paid Anthropic API capacity or replace the demo log without the explicit operator decision required by R-4. | GATE |
| C-4 | Do not pin `langchain-anthropic`, edit downstream prompts/graphs, or perform release operations under this FR. | GATE |
| C-5 | Treat the private LangChain formatter seam as a deliberate drift detector: a future import/signature failure is a dependency-contract signal to investigate, not a reason to weaken or silently skip the test. | GATE |

Authority granted: after the revisions and human spend decision are folded into the FR, implementation may change the Anthropic branch of `_build_system_message_from_segments`, update and add the focused REQ-YG-289 tests, record the bounded FR/changelog/diary artifacts, and—only if approved—capture one honest live cache-read witness.
