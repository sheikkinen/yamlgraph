# Feature Request: FR-249 Guardrails Pattern Documentation

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-04-19

---

## Summary

Add `reference/guardrails-pattern.md` — a pattern document showing how to compose existing YAMLGraph primitives (`python`, `llm`, `router`, `subgraph`, parallel edges, Pydantic schemas) into input, output, and tool-call guardrail graphs. Include a working demo in `examples/demos/guardrails/` with reference Python tool nodes.

## Value Statement

Graph authors learn to build input sanitization, output validation, and tool-call safety using primitives they already have, without additional dependencies or new framework code.

## Problem

Users building LLM applications need guardrails — input sanitization (PII, injection), output validation (toxicity, hallucination), and tool-call safety (shell injection, allowlists). The ecosystem offers Guardrails AI and NeMo Guardrails, but both require extra dependencies, custom DSLs (Colang), or Python-first APIs.

YAMLGraph already has every primitive needed:

| Primitive | Guardrail use |
|-----------|---------------|
| `type: python` | Deterministic checks (regex PII, injection fingerprints) |
| `type: llm` | Semantic judgment (toxicity, on-topic, factuality) |
| `type: tool` | External moderation APIs |
| Parallel edges | Concurrent checks |
| `type: subgraph` | Composing guardrail graphs into parent pipelines |
| `type: router` | Verdict-based routing (pass/reject/escalate) |
| Pydantic schemas | Structured verdict objects |

No new code is needed. What's missing is a **reference pattern document** showing the composition, plus a **working demo** proving the pattern runs end-to-end.

This follows the precedent of `reference/prompt-deployment.md`: documenting patterns is cheaper than new code (CLAUDE.md §4).

## Proposed Solution

### Deliverable 1: `reference/guardrails-pattern.md`

Six sections covering:

1. **Input Guardrail Graph** — PII detection (`python`), prompt injection detection (`python` + `llm` classifier), topic gating (`llm` judge), parallel fan-out, aggregation node combining verdicts.

2. **Output Guardrail Graph** — Toxicity check (`llm`), factuality cross-reference (`python`), hallucination detection (`llm`), schema compliance (already built-in via Pydantic).

3. **Tool Guardrail Graph** — Shell injection prevention (`python`, referencing existing `shlex.quote` in `tools/shell.py`), URL allowlisting (`python`), argument sanitization.

4. **Composition Pattern** — Wiring guardrail subgraphs into parent pipelines via `type: subgraph` + `type: router`:
   ```yaml
   nodes:
     input_guard:
       type: subgraph
       graph: graphs/guardrails/input-safety.yaml
       variables:
         user_input: "{state.user_input}"
       state_key: input_verdict

     route_input:
       type: router
       route_field: input_verdict.action
       routes:
         pass: primary_llm
         reject: reject_response
         mask: mask_and_continue
   ```

5. **Verdict Schema Convention** — Standardized Pydantic schema for guardrail outputs:
   ```yaml
   schema:
     name: GuardrailVerdict
     fields:
       safe: {type: bool, description: "Pass or fail"}
       category: {type: str, description: "Risk category"}
       severity: {type: str, description: "low, medium, high, critical"}
       reasoning: {type: str, description: "One-sentence explanation"}
       action: {type: str, description: "pass, mask, reject, escalate"}
   ```

6. **Reference Python Tools** — Pointers to `examples/demos/guardrails/nodes/` for minimal deterministic checks.

### Deliverable 2: `examples/demos/guardrails/`

A working demo following existing demo conventions:

```
examples/demos/guardrails/
├── README.md               # Pattern narrative + run commands
├── graph.yaml              # Input guardrail → LLM → output check pipeline
├── prompts/
│   ├── classify_safety.md  # LLM judge prompt for input safety
│   └── main_task.md        # Primary task prompt
└── nodes/
    ├── detect_pii.py       # Regex-based PII detection (email, phone, SSN)
    └── detect_injection.py # Known prompt injection fingerprints
```

The demo graph must be runnable via:
```bash
yamlgraph graph lint examples/demos/guardrails/graph.yaml
yamlgraph graph run examples/demos/guardrails/graph.yaml \
  --var user_input="My email is test@example.com, summarize AI" --full
```

### Deliverable 3: Cross-reference

Add a brief mention in `reference/graph-yaml.md` under an appropriate section linking to `reference/guardrails-pattern.md`.

## Acceptance Criteria

- [ ] `reference/guardrails-pattern.md` exists with all 6 sections
- [ ] `examples/demos/guardrails/` contains a complete, runnable demo graph
- [ ] Demo passes `yamlgraph graph lint`
- [ ] Demo executes successfully with `yamlgraph graph run`
- [ ] `demo-output.log` captured (required by demo-gate CI)
- [ ] Python tool nodes (`detect_pii.py`, `detect_injection.py`) are importable and have unit tests
- [ ] `reference/graph-yaml.md` cross-references the guardrails pattern doc
- [ ] Tests added with `@pytest.mark.req` linking to a new REQ in ARCHITECTURE.md
- [ ] No new framework code — pattern uses only existing primitives
- [ ] Documentation updated (CHANGELOG fragment in `changelog/unreleased/`)

## Alternatives Considered

1. **Add a `guardrail:` node field** — Rejected. This is `framework_costume` (Knowledge Graph trap): guardrails are inherently graph-shaped (parallel checks, conditional routing, aggregation). YAMLGraph is already a graph framework. A dedicated field would hide composition behind a single keyword, reducing flexibility and adding maintenance burden for zero expressiveness gain.

2. **Integrate Guardrails AI or NeMo as dependencies** — Rejected. Adds significant dependency weight (Guardrails AI pulls ~30 transitive deps). The YAML-native approach achieves the same result with zero new dependencies using primitives that already exist and are already tested.

3. **Only document, no demo** — Rejected. Commandment 2: "Never explain abstractly; show working code." A pattern doc without a runnable demo is an unverified claim.

## Related

- **FR-164**: Verification gate pattern — deterministic post-execution checks (related but different: verification is per-node, guardrails are graph-level composition)
- **FR-027**: Execution safety guards — `recursion_limit`, `max_map_items`, `loop_limits`
- **FR-247**: Changelog req cross-validation gate — first concrete instance of the Python pre-filter + LLM judge pattern
- `reference/prompt-deployment.md` — precedent for "document the pattern, don't build the feature"
- `examples/demos/verification-gate/` — existing demo showing per-node verification
- `examples/demos/safety-guards/` — existing demo showing execution safety limits

## Judgement

**Verdict:** APPROVED — 2026-04-19

**Scope frozen.** Authority granted to implement.

**Findings:**

1. **Scope is clear and minimal.** Three deliverables (pattern doc, demo, cross-reference) all serve one concern: documenting guardrails composition. No framework code changes. Follows the `prompt-deployment.md` precedent explicitly (CLAUDE.md §4).

2. **Minor observation:** The primitives table lists `type: tool` → "External moderation APIs," but `type: tool` is a Shell Tool Node in the framework. This is immaterial because the actual proposed demo correctly uses `type: python` and `type: llm` nodes. The implementer should use `type: python` (not `type: tool`) if the pattern doc shows calling external moderation APIs programmatically.

3. **Acceptance criteria are measurable.** All 10 criteria are concrete and verifiable via lint, run, file existence, and test execution.

4. **Demo structure validated.** The `nodes/` directory convention is used by existing demos (`innovation_matrix`, `fi_domain_crawl`, `tavily_rag`). Remember to include `__init__.py` in the `nodes/` directory per existing convention.

5. **Architecture alignment is excellent.** No new abstractions, no new dependencies. Pure composition of existing primitives.

6. **Single responsibility confirmed.** The demo exists to prove the pattern doc (Commandment 2), and the cross-reference is a trivial addition. Not splittable.

**Implementation notes:**
- Ensure `nodes/__init__.py` is included (all existing demo `nodes/` dirs have one)
- Use `type: python` (not `type: tool`) for external API call patterns in the doc
- The `demo-output.log` is required by demo-gate CI — capture during implementation
