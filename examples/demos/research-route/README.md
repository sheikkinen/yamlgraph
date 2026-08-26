# research-route — Closed-Input Alternatives (FR-890)

Task shapes: "explore the solution space for a problem before planning",
"fan a closed brief out to orthogonal personas", "dispositioned
alternatives table with disagreement preserved".

The research sole route: a CLOSED problem brief (problem statement,
classification enum, constraints, witnessed incidents — no
solution-shaped sections) fans out to five planner personas with
orthogonal priors:

1. **os-infra-primitivist** — what does the platform/kernel already enforce?
2. **data-process-planner** — what schema/process change dissolves it?
3. **yamlgraph-native-planner** — consults graph `Task shapes:` inventory;
   records the `is_this_a_graph` answer.
4. **subtractionist** — delete the requirement (`growth_as_default` check).
5. **librarian** — web-grounded (`search_web`); must cite a real URL.

An LLM-free reducer validates every finding and writes
`tmp/draft-alternatives.md`: frozen 7-column table, 4–6 distinct
solution classes, no empty cells, disagreement preserved as rows —
never voted away. The librarian fails closed: an `Error:` string is
not a citation.

## Run

Sole route (preflight + lock + sentinel + artifact verification):

```bash
scripts/research.sh tests/fixtures/fr890/clean-brief.md
```

Direct graph run (skips the wrapper contract — demos only):

```bash
yamlgraph graph run examples/demos/research-route/graph.yaml \
  --var brief_path=tests/fixtures/fr890/clean-brief.md
```

On acceptance, promote the artifact to
`feature-requests/FR-XXX.research.md` and reference it from the FR's
mandatory `**Research:**` field. Exemplar of a full run:
`feature-requests/FR-888.research.md` — where the route surfaced the
OS-permissions solution class the original planning session missed.

All LLM nodes pin `claude-haiku-4-5` at temperature 0.
