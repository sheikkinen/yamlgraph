# FR-937 witnesses — exact cells and observed output

**Prior art:** the retrieval returns this file's own siblings —
`FR-937-research-precedent-vocabulary-drift.md` and `FR-937.research.md`, both
matching on the filename noun `witnesses`. They are the FR and its research
record; this file is their evidence appendix, not a competing proposal, so
there is nothing to distinguish. (The hits are a known gap: `build_prior_art`
self-excludes by path, so same-FR siblings survive the filter — filed to the
chaplain inbox as `prior-art-self-exclusion-misses-judgement-sibling.md`.)

Run logs live under `logs/`, which is gitignored. This file is the committed
evidence: the exact strings that produced each witness, reproducible by the
recorded command. Test fixtures for AC-03 must use the cells verbatim from
here, not paraphrases.

## W-3 — reducer accepts, preflight rejects (`none-retrieved` direction)

Command, run 2026-08-31 in the `featfr932-prior-art-in-research` worktree:

```
PYTHONPATH="$PWD" PATH="$PWD/.venv/bin:$PATH" \
  ./scripts/research.sh \
  feature-requests/research-briefs/fr-937-precedent-vocabulary-drift-brief.md
```

Graph outcome — accepted by `research_tools`:

```
result: {'artifact': 'tmp/draft-alternatives.md', 'rows': 5,
         'non_echo_rows': 5, 'classes': 3}
```

Wrapper outcome — rejected by `research_preflight`, exit 65:

```
research_preflight: artifact: 'none-retrieved' claimed but prior-art retrieval
returned hits: 'FR-896 (precedent traceability), FR-932 (none-retrieved bounded
claim), CAP-248 (research sole route).'
```

The precedent cell, verbatim (subtractionist row, also in
[FR-937.research.md](FR-937.research.md)):

```
FR-896 (precedent traceability), FR-932 (none-retrieved bounded claim), CAP-248 (research sole route).
```

Three committed identifiers. The cell is `traceable` under
`research_tools._classify_precedent`, which resolves identifiers first, and a
`none-retrieved` violation under `research_preflight._check_precedent`, which
tests the marker first.

## W-6 — same disagreement, `brief-echo` direction

Command, run 2026-08-31 in the same worktree, regenerating the demo proof log:

```
PYTHONPATH="$PWD" PATH="$PWD/.venv/bin:$PATH" \
  ./scripts/research.sh tests/fixtures/fr890/clean-brief.md \
  > examples/demos/research-route/demo-output.log 2>&1
```

Graph outcome — accepted:

```
result: {'artifact': 'tmp/draft-alternatives.md', 'rows': 5,
         'non_echo_rows': 5, 'classes': 4}
```

Wrapper outcome — rejected, exit 65:

```
research_preflight: artifact: 'brief-echo' is not precedent — the brief cannot
cite itself: 'FR-890 research-route graph; CAP-248 research sole route
(closed-input alternatives); brief-echo: planning phase must gain input closure
comparable to judge/review/author routes.'
research.sh: contract violated (graph rc=0): …/tmp/draft-alternatives.md fails
the frozen schema
```

The precedent cell, verbatim (yamlgraph-native-planner row):

```
FR-890 research-route graph; CAP-248 research sole route (closed-input alternatives); brief-echo: planning phase must gain input closure comparable to judge/review/author routes.
```

Two committed identifiers followed by the marker. Mirror image of W-3.

Consequence: `examples/demos/research-route/demo-output.log` cannot be
regenerated while this stands, so the `demo-proof-check` hook blocks any change
under `examples/demos/research-route/`. The FR-938 renumber left that file's
`FR-932` comments stale for this reason; AC-08 clears them.

## W-1 / W-2 — the reachable instruction is fatal

Command, run twice on 2026-08-31, byte-identical failures at
`temperature: 0.0`:

```
PYTHONPATH="$PWD" PATH="$PWD/.venv/bin:$PATH" \
  ./scripts/research.sh \
  feature-requests/research-briefs/operator-coffee-physical-actuation-brief.md
```

Outcome — raised inside `reduce_findings`, graph exit 1, no artifact:

```
'brief-echo' is not precedent — the brief cannot cite itself; cite committed
state or declare 'none-retrieved': 'brief-echo: agent knows when the wait is…'
```

Retrieval was empty for this brief: the subject has no committed precedent.
The persona followed its prompt, which is the only instruction it has:

```
$ grep -l "brief-echo"     examples/demos/research-route/prompts/*.yaml | wc -l
5
$ grep -l "none-retrieved" examples/demos/research-route/prompts/*.yaml | wc -l
0
```
