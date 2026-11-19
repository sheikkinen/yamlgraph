# Judgement: FR-1170 Azure Non-Thinking Mode (`thinking_budget: 0`)

**Verdict:** APPROVED WITH REVISIONS — the evidenced provider-boundary correction is minimal; implementation authority activates only after R-1 through R-3 are folded into the FR, with live execution separately gated on owner authorization.

**Prior art:** [FR-1170-azure-thinking-off.md](FR-1170-azure-thinking-off.md) is the judged FR itself. [FR-1056](FR-1056-deepseek-thinking-off.md) (and its judgement) is the direct precedent whose zero-only `reasoning_effort: "none"` contract this FR copies for Azure. [FR-1148](FR-1148-anthropic-thinking-off.md) (and its judgement) is the Anthropic sibling of the same "`thinking_budget: 0` means off" contract; it touches only the Anthropic factory and is neither superseded nor extended here.

**Reviewed against:** committed `feature-requests/FR-1170-azure-thinking-off.md` (last changed in `479250cd`); `yamlgraph/utils/llm_providers.py`; `yamlgraph/utils/llm_factory.py`; `yamlgraph/node_factory/race_node.py`; `feature-requests/FR-1056-deepseek-thinking-off.md` and its `.judgement.md`; `feature-requests/FR-263-azure-openai-provider.md`; `feature-requests/FR-680-provider-dispatch-registry.md`; `feature-requests/FR-455-reasoning-model-temperature-guard.md`; `feature-requests/FR-1144-race-node-thinking-budget.md` and its `.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; supplied `CLAUDE.md` repo doctrine. External cited evidence: `terveystalo/customer-service-agent-platform#884` merge metadata and `feature-requests/evidence/NC-584-luna-probe.md`, sections 7-9, at its merge commit `982de7b8c66aab874320104b3cf22a96c7b084b5`. The working tree was clean before this draft. No author transcript, uncommitted notes, or unrelated implementation files were consumed.

## What is sound

1. **Scope:** The smallest useful change is exactly the proposed zero-value mapping in the existing Azure factory and dispatch registry, not a new YAML field or model-name heuristic (`FR-1170:79-85,106-121,187-191`). Other providers, effort tuning, and the CSAP rollout remain outside scope (`FR-1170:203-209`).
2. **Consistency:** Zero, omission, accepted nonzero budgets, and unsupported token budgets have distinct, coherent meanings (`FR-1170:106-116,142-159`). The explicit deployment-error policy is honest about Azure's broader model catalog (`FR-1170:123-135`). Two dependent contracts need correction: FR-1144's old dispatch assertion and the advice for overriding an inherited zero; see R-1 and R-2.
3. **Measurability:** AC-01 through AC-09 and AC-11/12 identify payload assertions, log records, exceptions, cache identities, registry artifacts, documentation, and commit history (`FR-1170:142-179`). AC-10 identifies an observable HTTP result, but does not yet separate existing evidence from new paid execution or bound that execution; see R-3.
4. **Feasibility:** The dispatch omission is visible at `llm_providers.py:319-364`; the Azure factory currently lacks the parameter (`:37-78`). DeepSeek already implements the proposed mapping and DEBUG behavior (`:81-110`). The public factory's existing guard and cache support the proposal without executable changes (`llm_factory.py:110-130,260-270`). The committed FR records the SDK payload probe (`FR-1170:117-121`); this judgement does not claim to have rerun it.
5. **Architecture alignment:** Normalizing at provider construction follows FR-263, FR-680, and the direct FR-1056 precedent (`FR-1170:24-36`). Race construction already forwards the resolved budget (`race_node.py:189-207,347-348,399`), so no race implementation change is needed.
6. **Single responsibility:** This is one concern: making Azure honor an existing off switch. Payload tests, traceability, documentation, and bounded compatibility evidence support that concern rather than introducing another feature (`FR-1170:140-179`).
7. **Strategic classification:** **Contrib/example**, under the rubric's one-to-two-use-case category: a provider-specific gap in existing abstractions, not a new framework primitive. This matches the FR-1056 judgement's classification; the production correction still belongs in the existing core provider factory.
8. **Testability:** Keyless failing tests can be derived directly from AC-01, AC-03, and AC-05, using real client construction and payload inspection rather than live inference (`FR-1170:142-162`). Cache isolation and dummy credentials are explicitly specified. R-1 prevents an obsolete, previously intentional assertion from remaining red after the correction.

The strongest case against approval is FR-1144's deliberate refusal to change Azure behavior: its existing mini deployment already used zero reasoning tokens, and other Azure deployments might reject `reasoning_effort` (`FR-1144-race-node-thinking-budget.md:235`). The new Luna evidence resolves the first objection: the default payload fails with a temperature error, while N-T0 and N-TS succeed with reasoning disabled (NC-584 evidence `:981-982,1047-1055`). The second objection remains real and is explicitly accepted as a loud provider error, not concealed by a guessed deployment-name allowlist (`FR-1170:125-135,188`). This authorizes neither a clinical-suitability claim nor a CSAP production rollout; the evidence expressly excludes those conclusions (NC-584 evidence `:1013-1019`).

Research meets the local substance gate: five genuine alternatives, observed API behavior, an SDK payload observation, named precedents, and an explicit `is_this_a_graph` answer (`FR-1170:16-40,117-121,185-191`). This is not measurement tooling, so the metric-tooling raw-output gate does not apply. The cited deferred/rejected Azure alternative in FR-1144 is material precedent, not merely an incidental demo mention; R-1 makes its supersession explicit.

## Required revisions

### R-1: Supersede FR-1144's Azure dispatch assertion explicitly

Add a prior-art disposition stating that FR-1170 intentionally supersedes only FR-1144 AC-06's expectation that Azure receives no budget. FR-1144 records a real test, `test_vertex_factory_gets_zero_azure_factory_gets_none`, asserting Azure's factory is called with `(model, 0.0)` while Vertex receives `(model, 0.0, 0)` (`FR-1144-race-node-thinking-budget.md:149,160,181`). Adding Azure to the dispatch registry necessarily changes that call.

Authorize updating that existing witness in `tests/unit/test_race_node.py`: rename it to describe the new contract, expect Azure's factory to receive zero, and retain the Vertex assertion and mixed-candidate construction coverage. Preserve its existing requirement association for race forwarding; mark new Azure payload witnesses with REQ-YG-732. Add an acceptance criterion that the affected race/provider-dispatch tests pass. Do not edit the historical FR-1144 judgement or change race production behavior.

### R-2: Correct the escape path for inherited graph defaults

Replace the blanket advice to remove `thinking_budget: 0` "from that node" (`FR-1170:127-129`). The first consumer uses a graph default (`:10-11,131-132`), and absence or `None` at a race node inherits that default (`race_node.py:347-348`); removal therefore does not reliably stop the new field.

State the two supported remedies without changing resolution semantics: remove zero at its defining configuration level, or override an inherited zero on that node with an accepted nonzero portability value such as `512`, which omits `reasoning_effort`. Extend AC-05 with a keyless race-node case using `defaults.thinking_budget=0` and node-level `thinking_budget=512`; assert that the Azure candidate payload omits `reasoning_effort`. Keep the existing zero-value payload case.

Also clarify "llm_factory.py: no change" (`FR-1170:114`) as "no executable behavior change"; AC-09 explicitly requires its docstring to change (`:167-170`).

### R-3: Bound and authorize the live compatibility witness

Rewrite AC-10 to distinguish evidence reuse from new execution. The immutable NC-584 N-T0 record already proves Luna accepts the combined fields (evidence `:1049,1055`). Its mini baseline uses temperature alone (`:1035,1072`), while its mini `none` timing rows do not establish that combined payload (`:899-900`). Do not claim either partial result proves the missing mini combination.

Permit the existing Luna N-T0 record to satisfy the Luna half. Require one owner-authorized, minimal, non-sensitive chat request for `aaa-gpt-5.4-mini` with both `temperature: 0` and `reasoning_effort: "none"`; at most one Luna request is needed if the existing record cannot be reused. Set a finite output-token cap, finite timeout, and no automatic retries. Record deployment/model, HTTP status, and reasoning-token count only, with an immutable source citation for reused evidence. Treat an absent token count as unavailable, not zero.

Surface this explicit owner decision in the FR: **Has the CSAP TEST account owner authorized the bounded compatibility probe and its spend?** Existing NC-584 authority is not authorization for a new run. If authorization or credentials are unavailable, record AC-10 as blocked; do not silently waive it or run the probe. Unit tests remain entirely keyless.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/utils/llm_providers.py`: Azure factory parameter, zero-only `reasoning_effort`, DEBUG logging for ignored values, and dispatch allowlist/comment |
| D-2 | Focused keyless Azure payload/cache/error/log witnesses; affected FR-1144 dispatch witness and race inheritance/payload cases in `tests/unit/test_race_node.py` |
| D-3 | `yamlgraph/utils/llm_factory.py` docstring only; Azure contract and inherited-default guidance in `reference/graph-yaml.md` |
| D-4 | `capabilities/CAP-307-azure-non-thinking.yaml`, REQ-YG-732, and regenerated `ARCHITECTURE.md`; resolve a verified ID collision as already allowed by AC-08 |
| D-5 | One providers-scoped fix fragment under `changelog/unreleased/` |
| D-6 | FR-1170 revision folds, bounded compatibility evidence, implementation status, decisions, and deviations |

Not authorized: executable `llm_factory.py` changes; adding Azure to its native token-budget `THINKING_PROVIDERS`; cache redesign; effort tuning; new YAML fields; model-name heuristics; error suppression or provider fallbacks; linter/schema changes; race/router production changes; changes to other providers; dependency upgrades absent a demonstrated blocker returned to planning; graph/prompt authoring; CSAP repository mutations, version-pin changes, rollout, or clinical/quality evaluation; unbounded live tests or benchmarks.

## Revised acceptance criteria

- [ ] AC-01: With isolated cache and dummy Azure credentials, `create_llm(provider="azure", model="aaa-gpt-6-luna", temperature=0.0, thinking_budget=0)` returns `AzureAIOpenAIApiChatModel`; its request payload contains `reasoning_effort == "none"` and `temperature == 0.0`.
- [ ] AC-02: The same call with the budget omitted has no `reasoning_effort` payload key.
- [ ] AC-03: Budget `512` does not raise, omits the field, and produces a DEBUG record naming `512` and `azure`.
- [ ] AC-04: Budget `8000` raises `ValueError` naming the supported token-budget providers; Azure remains outside the native-budget allowlist.
- [ ] AC-05: Through a real race node's candidate-construction path, node-level zero produces an Azure payload with `reasoning_effort == "none"`; node-level `512` overriding graph-default zero produces a payload without the field. Mock invocation, not the factory/dispatch path under examination.
- [ ] AC-06: Existing DeepSeek, Anthropic, Google, and Vertex thinking behavior remains unchanged; omitted, zero, and `512` Azure calls do not alias in the cache. Update the obsolete FR-1144 Azure-factory call assertion to receive zero while retaining its Vertex and mixed-race assertions; affected race/provider-dispatch tests pass.
- [ ] AC-07: New tests are keyless and carry `@pytest.mark.req("REQ-YG-732")`; retained race-forwarding witnesses retain their relevant requirement mapping; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-08: CAP-307 defines REQ-YG-732 and `ARCHITECTURE.md` is regenerated with `scripts/aggregate_capabilities.py`. The requirement records zero, omission/accepted nonzero, and unsupported token-budget cases. If those identifiers are taken, use the next verified free pair consistently and record the substitution in FR-1170.
- [ ] AC-09: `reference/graph-yaml.md` and the `create_llm` docstring state zero/omission/accepted-other semantics, the retained `>=1024` rejection, and unsupported-deployment provider errors. Configuration guidance explains how to override inherited zero without changing resolution behavior.
- [ ] AC-10: Record HTTP 200 compatibility evidence for the combined `temperature: 0` and `reasoning_effort: "none"` payload on both named deployments. Reuse the immutable Luna N-T0 evidence; obtain missing evidence only under the explicit owner authorization and bounded request policy in R-3. Record only model/deployment, status, and reasoning-token count, plus reused-source provenance; no content or credentials. Missing authorization/evidence leaves this criterion blocked.
- [ ] AC-11: A `changelog/unreleased/` fragment has `type: fix`, `scope: providers`, and identifies FR-1170 / REQ-YG-732 or the recorded collision-free replacement.
- [ ] AC-12: Git history contains a genuinely failing RED behavioral test commit before GREEN implementation; FR-1170 records revision folds, implementation status, decisions, evidence, and deviations.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 and these acceptance criteria into committed FR-1170 before production implementation. This draft is not a promoted judgement. | GATE |
| C-2 | Preserve asymmetric allowlists: Azure enters only dispatch-side `_THINKING_PROVIDERS`; unsupported budgets at or above 1024 still raise. | GATE |
| C-3 | Emit `reasoning_effort="none"` only for zero. Omission and accepted nonzero values must not add the field; log ignored values without leaking credentials. | GATE |
| C-4 | Preserve graph-default resolution, race behavior, other providers, lazy Azure import, credential validation, and request bounds. Adjust only the directly invalidated test assertion. | GATE |
| C-5 | Commit RED before GREEN; satisfy focused Azure and affected race/provider regressions, strict requirement coverage, and applicable repository checks. | GATE |
| C-6 | Owner decision required before any new paid request: has the CSAP TEST owner authorized the bounded compatibility probe and spend? No authorization means no live execution; missing AC-10 evidence blocks completion, not keyless implementation after the revision gate. | GATE |
| C-7 | No product/clinical suitability or rollout authority is granted; no CSAP changes or additional provider features may be bundled. Record implementation decisions/deviations in FR-1170. | GATE |

Authority granted: conditional on folding R-1 through R-3 and normal judgement promotion, implement only the frozen Azure zero-value mapping and its directly dependent witnesses, traceability, documentation, and changelog; new live requests require the separate owner decision in C-6.
