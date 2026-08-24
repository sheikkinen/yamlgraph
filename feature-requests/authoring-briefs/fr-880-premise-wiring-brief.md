# Authoring Brief: FR-880 Memory-Curation Premise Wiring

**Governing FR:**
`feature-requests/FR-880-memory-curation-premise-wiring-and-baseline-bootstrap.md`

**Judgement:**
`feature-requests/FR-880-memory-curation-premise-wiring-and-baseline-bootstrap.judgement.md`
(APPROVED WITH REVISIONS; this committed brief satisfies R-1/C-1.)

**Prior art:** `examples/memory-curation/graph.yaml` is the existing
FR-875 artifact to amend; `feature-requests/authoring-briefs/fr-875-memory-curation-brief.md`
is its original authoring input. FR-878 added the deterministic
`premise_kind` boundary in reconcile/apply but did not wire the graph.
No other graph territory is in scope.

## Existing Inputs

- Existing graph: `examples/memory-curation/graph.yaml`
- Existing glue: `examples/memory-curation/nodes/graph_nodes.py`
- Existing deterministic validator:
  `examples/memory-curation/nodes/reconcile.py`
- Existing apply policy: `examples/memory-curation/apply.py`
- Existing fixture corpus:
  `examples/memory-curation/fixtures/memories/repo/durable-boundary-fact.md`
- Existing documentation: `examples/memory-curation/README.md`

## Required Correction

Modify the existing graph so callers must supply two distinct inputs:

- `premise_kind`: exact policy metadata, accepted values downstream are
  `hygiene | export_publication`; controls apply approval tier.
- `audience_premise`: free-text semantic context for the per-note LLM
  judgement; remains required and unchanged.

Required graph wiring:

```yaml
state:
  premise_kind: str

nodes:
  reconcile:
    variables:
      premise_kind: "{state.premise_kind}"
```

Modify `reconcile_memory_dispositions()` in
`examples/memory-curation/nodes/graph_nodes.py` so its subprocess command
passes the exact graph state value:

```text
--premise-kind <state.premise_kind>
```

No default, normalization, or inference from `audience_premise`.
`reconcile.py` remains the exact enum validator. Missing state must fail
clearly before apply; unknown value must fail reconciliation.

## Artifact Boundary

Create or modify only:

- `examples/memory-curation/graph.yaml` (governed artifact)
- `examples/memory-curation/nodes/graph_nodes.py`
- `examples/memory-curation/README.md`
- `tests/unit/test_memory_curation_premise.py`
- `tmp/draft-authoring-report.md` (route proof; not committed)

**Do not modify prompt YAML.** Do not change judgement schema, apply tier
semantics, hooks, framework primitives, or live memory content.

## Witnesses

Tests use temp/fixture memory roots only and must prove:

1. Graph config declares and wires `premise_kind` into reconcile.
2. Glue transports `hygiene` unchanged into final disposition JSON.
3. Glue transports `export_publication` unchanged.
4. Missing graph/glue state fails clearly before apply.
5. Unknown value reaches deterministic reconcile validation and fails;
   it is never defaulted or normalized.
6. No apply invocation occurs in failure witnesses.

Tag tests to existing CAP-247 coverage if its requirements already cover
metadata transport; otherwise report the need for a successor REQ in the
authoring report rather than inventing an ID.

## Documentation

Update README command examples to require both:

```text
--var premise_kind=hygiene
--var audience_premise="machine-local working memory ..."
```

Explain in one sentence: `premise_kind` controls policy/approval tier;
`audience_premise` grounds semantic judgement.

## Validation

```bash
yamlgraph graph lint examples/memory-curation/graph.yaml
pytest tests/unit/test_memory_curation_premise.py -q --no-cov
PROVIDER=vertex yamlgraph graph run examples/memory-curation/graph.yaml --var memory_root=examples/memory-curation/fixtures/memories --var premise_kind=hygiene --var audience_premise="public synthetic fixture; worst-case reader: internet" --full
```

After smoke, assert `tmp/memory-curation/disposition.json` contains
`"premise_kind": "hygiene"` and covers all three fixture notes.

## Report

Write `tmp/draft-authoring-report.md` with the required headings:
`Artifacts`, `Precedent`, `Validation`, `Repairs`, `Blocked validation`.
Explicitly state that no prompt YAML changed.
