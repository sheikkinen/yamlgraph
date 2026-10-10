# Judgement: FR-1146 Omit Temperature for Anthropic Models That Reject It

**Verdict:** APPROVED WITH REVISIONS — the provider-boundary omission rule is narrow, evidenced, and feasible; authority activates only after R-1 through R-4 are folded into the feature request.

**Reviewed against:** `feature-requests/FR-1146-anthropic-temperature-deprecated.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-455-reasoning-model-temperature-guard.md`; `feature-requests/FR-451-agent-temperature-zero-bug.md`; `feature-requests/FR-071-thinking-budget-graph-level.md`; `feature-requests/FR-1144-race-node-thinking-budget.md`; `feature-requests/FR-1144-race-node-thinking-budget.judgement.md`; `feature-requests/FR-1145-openai-compatible-provider.md`; `feature-requests/FR-1145-openai-compatible-provider.judgement.md`; `yamlgraph/utils/llm_factory.py` at cited revision `f93f8afa` and current `HEAD`; `yamlgraph/utils/llm_providers.py`; `tests/unit/test_llm_factory.py`; `ARCHITECTURE.md`.

**Prior art:** [FR-1146-anthropic-temperature-deprecated.md](FR-1146-anthropic-temperature-deprecated.md) — the FR this judgement rules on, not precedent; dismissed; [FR-455-reasoning-model-temperature-guard.md](FR-455-reasoning-model-temperature-guard.md) — OpenAI guard pattern this extends, unchanged. (Added by the FR author at filing to satisfy the FR-738 gate; not judge output.)

## What is sound

The problem is real and the proposed boundary is correct. The committed FR records direct acceptance probes showing that omission and `temperature=1` succeed while `0` and `0.7` fail on `claude-sonnet-5-5`, and that eight listed models reject non-default sampling while five older lines accept it (`FR-1146:38-80`). `create_llm` currently converts `None` to `0.7`, applies the Anthropic thinking override, and only then selects the model and applies the existing OpenAI omission guard (`llm_factory.py:165-197`). The Anthropic constructor then passes temperature unconditionally (`llm_providers.py:28-43`). Setting the post-resolution value to `None` at this seam is therefore smaller and more reliable than retrying after a provider error or changing individual graphs.

Scope and single responsibility are otherwise sound. The FR changes one provider's sampling-parameter construction rule and explicitly excludes adaptive thinking, `top_p`/`top_k`, and lint policy (`FR-1146:197-209`). The asynchronous factory already delegates to the synchronous seam according to the FR's committed code read (`FR-1146:50-56`), so a second implementation path is unnecessary. The proposal also preserves the distinct FR-451 resolution concern (`FR-451:9-32`), the FR-071 thinking-temperature rule (`FR-071:62,89-106`), and the FR-455 all-callers factory pattern (`FR-455:35-54`).

Feasibility and architecture alignment are established by current code and Probe 4. Provider dispatch already accepts `float | None` (`llm_providers.py:352-377`), and the cache key is computed from the resolved temperature before construction (`llm_factory.py:199-213`). Only `_create_anthropic_llm` needs its annotation widened; `ChatAnthropic` already omits `None` from the request payload according to the committed probe (`FR-1146:89-94`). Existing FR-455 tests provide the local test shape and use `REQ-YG-010` (`tests/unit/test_llm_factory.py:540-567`; `ARCHITECTURE.md:640`).

The research record is substantive. It names the first failing event, reports four concrete probes, preserves the undocumented-metadata disagreement rather than treating correlation as contract, dispositions six genuine solution classes, answers `is_this_a_graph`, and distinguishes all cited prior art (`FR-1146:5-22,38-94,182-195`). This is not measurement tooling, so the raw-output measurement gate does not apply.

Strategic classification: **Framework primitive**. This is a corrective extension of the shared multi-provider factory used by every synchronous and asynchronous LLM construction path, with multiple model lines and node types as consumers. No example-local or documentation-only change can prevent the provider 400.

Testability is strong after the revisions below: request-payload inspection proves the wire shape without a network call, identity assertions prove cache canonicalization, captured logs prove observability, and the already-planned live hello run proves the actual provider path. The present criteria omit some of those stated contracts, so authority is conditional rather than immediate.

## Required revisions

### R-1: Narrow the promised result to sampling compatibility

Replace the Ideal Result claim that "any Claude model id ... runs every LLM node unchanged" (`FR-1146:96-102`) with a sampling-specific contract: for Anthropic calls without enabled extended thinking, models classified as accepting sampling retain the resolved temperature; all other model ids omit it. Replace "told once" with the exact observable contract that each omission decision emits an info log naming the model.

State explicitly that this authority does not make `thinking_budget >= 1024` work on models requiring adaptive thinking. The FR already records that such calls fail for a separate reason and assigns them to a follow-up (`FR-1146:197-204`); the Ideal Result must not promise their success.

### R-2: Remove unprobed prefixes from the accepting allowlist

Freeze `ANTHROPIC_SAMPLING_MODEL_PREFIXES` to the five model-line prefixes supported by Probe 2: `claude-haiku-4-5`, `claude-sonnet-4-5`, `claude-sonnet-4-6`, `claude-opus-4-5`, and `claude-opus-4-6`. Remove `claude-3` and the unlisted legacy 4.0/4.1 entries from the proposed tuple (`FR-1146:134-146`).

An accepting prefix is an affirmative claim that preserves a caller-controlled parameter and must have direct evidence. The chosen alternative says unknown ids fail safe by omission (`FR-1146:190-195`); speculative legacy entries reverse that rule. A legacy prefix may be restored only if its direct request probe and result are folded into the committed FR before enforcement.

### R-3: Add witnesses for precedence and cache semantics

Expand the acceptance criteria beyond the three payload examples (`FR-1146:171-177`) to require:

1. An enabled-thinking call on a rejecting model keeps the FR-071 override at `temperature=1`; the Anthropic omission guard must run after the thinking override and must not replace it with `None`.
2. Calls for the same rejecting model at `temperature=0` and `temperature=0.7` return the same cached client because both canonicalize to a `None` cache-key value.
3. Calls for an accepting model at distinct temperatures remain distinct and preserve their respective payload values.
4. The omission log is asserted at info level and names the selected model.

These are stated solution constraints at `FR-1146:160-169`, but no current acceptance criterion condemns an implementation that violates them.

### R-4: Make verification and traceability exact

Replace the unspecified existing requirement marker (`FR-1146:179`) with `@pytest.mark.req("REQ-YG-010")`, matching the existing factory guard tests (`tests/unit/test_llm_factory.py:545-567`) and the architecture registry (`ARCHITECTURE.md:640`). Add RED-before-GREEN history, `python scripts/req_coverage.py --strict`, the targeted factory test command, the fast unit suite, and an exact changelog artifact carrying `type: fix` and `req: REQ-YG-010`.

Retain the enforce-time Probe 2 rerun from Planned Operations (`FR-1146:104-123`) and require its model ids and outcomes to be recorded in the FR implementation status or PR evidence. If any currently listed accepting line rejects a non-default temperature, remove its prefix before GREEN implementation; do not add runtime model discovery.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/utils/llm_factory.py`: add the five-prefix Anthropic sampling-acceptance tuple and omit temperature for other Anthropic model ids after thinking override and before cache-key construction |
| D-2 | `yamlgraph/utils/llm_providers.py`: widen `_create_anthropic_llm`'s temperature annotation to `float | None` and preserve `ChatAnthropic`'s native omission behavior |
| D-3 | `tests/unit/test_llm_factory.py`: RED-first REQ-YG-010 payload, precedence, logging, unknown-model, non-Anthropic, and cache witnesses |
| D-4 | One `changelog/unreleased/fr-1146-anthropic-temperature-deprecated.md` fix fragment with `req: REQ-YG-010` |
| D-5 | `feature-requests/FR-1146-anthropic-temperature-deprecated.md`: fold revisions, record the enforce-time probe, and record implementation status, decisions, and deviations |
| D-6 | PR evidence: successful live `examples/demos/hello/graph.yaml` run with `claude-sonnet-5-5` |

Not authorized: adaptive thinking or `output_config.effort`; changes to FR-071 thinking payloads; `top_p` or `top_k` configuration; runtime `models.list` calls; capability inference from `thinking.enabled.supported`; retry-on-400 behavior; linter warnings; graph or prompt edits; provider-generalized sampling abstractions; OpenAI guard changes; dependency upgrades; new capability or requirement IDs.

## Revised acceptance criteria

- [ ] AC-01: `create_llm(provider="anthropic", model="claude-sonnet-5-5", temperature=0.7)` produces a client whose `_get_request_payload("hi")` has no `temperature` key.
- [ ] AC-02: AC-01 also holds for explicit `temperature=0`, input `temperature=None`, and unknown future id `claude-sonnet-6`.
- [ ] AC-03: Each of the five frozen accepting prefixes preserves a non-default temperature in the request payload; at minimum, the test matrix includes `claude-haiku-4-5` and one date-suffixed accepted model id.
- [ ] AC-04: An Anthropic model outside the five accepting prefixes with `thinking_budget >= 1024` retains the existing forced `temperature=1` payload value; the sampling omission guard does not null an FR-071 override.
- [ ] AC-05: For the same rejecting model and otherwise identical construction inputs, `temperature=0` and `temperature=0.7` return the same cached client after canonicalization to `None`.
- [ ] AC-06: For an accepting model and otherwise identical inputs, two distinct temperatures remain distinct cache entries and retain their respective request-payload values.
- [ ] AC-07: Omission emits an info log naming the selected model; accepted-temperature and thinking-override paths do not emit the omission log.
- [ ] AC-08: Existing FR-455 OpenAI reasoning-model tests and non-reasoning behavior remain unchanged, and a non-Anthropic provider preserves its current temperature behavior.
- [ ] AC-09: The enforce-time direct probe covers every model returned by `models.list`, records the ids and non-default-temperature outcomes, and confirms every accepting listed model matches one of the five frozen prefixes. A contradiction removes or narrows a prefix before GREEN implementation.
- [ ] AC-10: `ANTHROPIC_MODEL=claude-sonnet-5-5 yamlgraph graph run examples/demos/hello/graph.yaml --var name=World --var style="holy see of code"` exits 0, and its log is attached to the PR.
- [ ] AC-11: Every new test carries `@pytest.mark.req("REQ-YG-010")`; failing witnesses precede production implementation in git history.
- [ ] AC-12: `pytest tests/unit/test_llm_factory.py -q --no-cov` and `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` pass.
- [ ] AC-13: `python scripts/req_coverage.py --strict` passes.
- [ ] AC-14: `changelog/unreleased/fr-1146-anthropic-temperature-deprecated.md` has `type: fix`, `scope: llm`, `req: REQ-YG-010`, and describes Anthropic temperature omission.
- [ ] AC-15: The FR records the folded judgement revisions and, after enforcement, the probe evidence, implementation status, and any deviations.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 and the revised acceptance criteria into the FR before production implementation begins. | GATE |
| C-2 | Treat the accepting tuple as evidence-backed and closed: only the five probed prefixes are authorized; every other Anthropic model id omits temperature unless direct contrary evidence is first folded into the FR. | GATE |
| C-3 | Apply the Anthropic omission rule after FR-071 thinking override and before cache-key construction; never omit a forced `temperature=1`. | GATE |
| C-4 | Preserve the `None -> 0.7` default for every other provider and for accepting Anthropic model lines, and preserve the FR-455 OpenAI branch unchanged. | GATE |
| C-5 | Commit failing REQ-YG-010 witnesses before GREEN implementation and satisfy the targeted tests, fast unit suite, strict requirement coverage, enforce-time model probe, and live hello witness. | GATE |
| C-6 | Any need for adaptive thinking, runtime capability discovery, retries, linter policy, dependency changes, or additional sampling parameters stops enforcement and returns as a separate FR. | GATE |

Authority granted: after R-1 through R-4 are folded, implementation may add the evidence-backed Anthropic sampling guard at the shared factory boundary, widen the Anthropic constructor annotation, add the frozen witnesses and release record, and produce the named live evidence.
