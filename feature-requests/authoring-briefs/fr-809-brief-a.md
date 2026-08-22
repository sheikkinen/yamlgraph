# Task: API Discovery Orchestrator v2 — add recon and browser-sniff routing (FR-809)

Extend the existing orchestrator `examples/api-discovery/graph.yaml` and its
prompts `examples/api-discovery/prompts/generate_candidates.yaml` and
`examples/api-discovery/prompts/synthesize.yaml` with two already-Enforced
steps. Do not create new graphs; modify these existing files only. Do not
modify any step graph under `examples/api-discovery/steps/` or any leaf tool
under `examples/api-discovery/tools/`.

## Frozen contract (judgement R-1..R-3 — do not deviate)

1. **Recon (optional front):** new `tool_call` node `recon` on the existing
   manifest `examples/api-discovery/steps/recon.tool.yaml` (tool name
   `recon`, `on_error: fail`). Gate with a new input state key `use_recon`
   (`type: bool`, `default: true`). Edge topology: START path reaches
   `recon` only via a condition containing `use_recon == true`; a bypass
   edge with `use_recon != true` goes to `generate_candidates`; recon's only
   exit is `generate_candidates`. Recon's wrapper state key is
   `recon_result` (dict, default `{}`). `generate_candidates` must receive
   `recon_result` as an additional variable (prior-art evidence: candidate
   base URLs, auth hints, schema hints) alongside its existing variables;
   extend its prompt to consume that evidence when non-empty.

2. **Parsed outputs (FR-810):** add `parsed_key` to three tool_call nodes:
   `endpoint_probe` → `probe_findings`, `page_analysis` → `page_findings`,
   new `browser_sniff` → `sniff_findings`. The `parsed_key` field is
   documented in reference/graph-yaml.md (tool_call section).

3. **Browser-sniff (conditional last resort):** new `tool_call` node
   `browser_sniff` on the existing manifest
   `examples/api-discovery/steps/browser_sniff.tool.yaml` (`on_error:
   fail`), wrapper state key `sniff_result` (dict, default `{}`). Exactly
   one entry edge, from `page_analysis`, whose condition contains exactly
   the clauses `page_findings.is_spa == true` and
   `page_findings.api_found != true` — never any candidate_urls hint.
   The pre-existing `page_analysis` edges (platform_confirm on
   `has_platform_hint`, synthesize fallback) must remain and must not fire
   when the SPA clause fires (make the three conditions mutually
   exclusive). After browser_sniff, route so its findings reach the
   confirmation/synthesis path (an exit edge to `synthesize` is
   sufficient; sniffed evidence flows via state).

4. **sniff_url (deterministic, no LLM):** `browser_sniff` args must pass
   `url: "{state.sniff_url}"` (plus `timeout` and `max_iterations` per the
   manifest input_mapping). `sniff_url` is produced by exactly one non-llm
   node selecting the FIRST element of the HTML page list that
   page-analysis received. State expressions do not support list indexing;
   use a `type: python` node (precedent: `examples/demos/python-variables/`
   — module-based python tool). Place the selection function in a new
   Python module inside `examples/api-discovery/` (e.g.
   `examples/api-discovery/nodes/select_sniff_url.py`); it must be pure
   (no I/O, no LLM).

5. **Terminal schema (R-3):** in the synthesize prompt's `output_schema`,
   add optional property `manual_reason` (type string) keeping
   `additionalProperties: false` and the existing `required` list; add a
   prompt rule: when `verdict` is `needs_manual`, `manual_reason` is
   mandatory and must carry the browser-sniff manual reason verbatim
   (e.g. `captcha`); otherwise omit it or return empty.

6. **steps_tried copy-only (AC-07):** extend the "Actual steps that ran"
   section of the synthesize user prompt with `- recon` gated by
   `{% if recon_result | default({}) %}` and `- browser-sniff` gated by
   `{% if sniff_result | default({}) %}`; also render both wrappers'
   JSON below the existing step dumps. `steps_tried` rules stay copy-only.

## Committed witnesses (must pass)

The RED suite `tests/unit/test_fr809_orchestrator_v2.py` encodes the exact
structural expectations above (node types, parsed keys, edge conditions,
schema fields, evidence gating). Read it before authoring.

## Validation (run these; no live network smokes in this brief)

```bash
yamlgraph graph lint examples/api-discovery/graph.yaml
pytest tests/unit/test_fr809_orchestrator_v2.py tests/unit/test_fr791_api_discovery_orchestrator.py -q --no-cov
```

Both must be fully green. Record commands, outcomes, and any repairs
honestly in tmp/draft-authoring-report.md. Live FR-791 regression smokes
and FR-784 fixture smokes run in a separate resumed validation brief.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
