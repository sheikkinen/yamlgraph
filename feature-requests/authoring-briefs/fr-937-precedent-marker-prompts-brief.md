# FR-937 Research Route: Teach Personas the Accepted Precedent Marker

**Prior art:** `fr-896-research-route-traceability-brief.md` — supersedes in
part. FR-896 authored the precedent instruction these prompts still carry,
including the `brief-echo:` demotion marker; this brief replaces exactly that
instruction with the bounded `none-retrieved` contract FR-938 put in the reducer,
leaving the rest of FR-896's traceability wording intact.
`fix-research-agent-vars-brief.md` — unrelated; it addressed variable wiring in
the research agent node, not prompt precedent vocabulary.

Update the persona prompt YAML files under
`examples/demos/research-route/prompts/` so the precedent instruction matches
the contract the reducer and the artifact preflight actually enforce.

## Why

FR-896 sanctioned a `brief-echo:` marker as a *demotion* — the row survived but
scored zero. FR-938 retired it: restating the brief as its own precedent is not
precedent. The reducer now **raises** on it and accepts a bounded
`none-retrieved` claim instead. That replacement never reached the prompts:

```
grep -l "brief-echo"     examples/demos/research-route/prompts/*.yaml  → 5 of 5
grep -l "none-retrieved" examples/demos/research-route/prompts/*.yaml  → 0
```

A persona with no precedent therefore has exactly one instruction, and obeying
it kills the run. Witnessed three times on 2026-08-31 (see
`feature-requests/FR-937-evidence.md`).

## The four internal persona prompts

`os_infra_primitivist.yaml`, `data_process_planner.yaml`,
`yamlgraph_native_planner.yaml`, `subtractionist.yaml`.

**Edit 1 — the `## Precedent contract` section.** It currently ends:

```
  If the only support
  for the candidate is the problem brief itself, write the literal marker
  `brief-echo:` followed by what is being restated; the row is retained but
  excluded from scoring. A fabricated identifier fails the whole run.
```

Replace the two `brief-echo` sentences with the bounded honest miss. The
replacement must state, in the prompt's own voice:

- when the prior-art retrieval block shown above returned **no** hits, and no
  committed identifier, URL, path or Scripture key supports the candidate,
  write exactly `none-retrieved` as the entire precedent value;
- `none-retrieved` is a claim about the retrieval, not a convenience: claiming
  it when the block listed hits is rejected;
- restating the problem brief is never precedent;
- a fabricated identifier still fails the whole run.

The literal token `none-retrieved` must appear verbatim. The token `brief-echo`
must not appear anywhere in the file.

**Edit 2 — the `precedent` field description in the schema.** It currently
reads:

```
Concrete committed identifier or brief-echo marker supporting the candidate.
```

Say instead that it is a concrete committed identifier, or `none-retrieved`
when retrieval came back empty. Keep the rest of the description — the two
short sentences, roughly 40 words, hard cap 400 characters, over-length output
is rejected and never truncated — byte-for-byte.

## The librarian prompt

`librarian_structure.yaml`: remove every occurrence of `brief-echo` and
**nothing else**. The librarian cites a real URL copied from its tool results
and has no internal honest-miss escape; do not offer it `none-retrieved`, do
not soften the URL requirement, do not touch its schema.

## Do not

Change `graph.yaml`, node wiring, state keys, the tool manifest, the persona
list, the table columns, any `max_length`, the verdict or solution-class enums,
the README, or any prose unrelated to the precedent contract. No new persona,
no new field. This is a prompt-text edit in five files.

## Validate with

```bash
yamlgraph graph lint examples/demos/research-route/graph.yaml
grep -c brief-echo examples/demos/research-route/prompts/*.yaml   # all zero
grep -c none-retrieved examples/demos/research-route/prompts/*.yaml
# four internal prompts ≥ 1, librarian_structure.yaml exactly 0
```
