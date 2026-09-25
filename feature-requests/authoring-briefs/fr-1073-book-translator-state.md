# FR-1073 book_translator: Declare the Interrupt Resume Key in State

Governing FR: `feature-requests/FR-1073-map-result-contract.md` (AC-18:
every graph edited under FR-1073 must pass `yamlgraph graph lint`).
`examples/book_translator/graph.yaml` was edited by the FR-1073 map
migration brief and fails lint with one error that exists on `main` too:

```
❌ [E303] Interrupt node 'human_review' resume_key 'reviewed_chunks' not declared in state section
```

## Edit (exact; nothing else)

In `examples/book_translator/graph.yaml`, add one line to the top-level
`state:` block, after `needs_review: bool`:

```yaml
  reviewed_chunks: dict
```

`dict` because both consumers read it as a mapping from chunk index to
corrected text: `examples/book_translator/nodes/tools.py` (`join_chunks`,
`state.get("reviewed_chunks", {})`) and
`examples/book_translator/nodes/assembler.py`. Leave every other key,
comment, node, prompt, edge and file unchanged. Do not touch the W017/W022
warnings.

## Validation

```bash
yamlgraph graph lint examples/book_translator/graph.yaml
yamlgraph graph info examples/book_translator/graph.yaml
```

Expected: lint reports 0 errors (warnings unchanged). The graph calls LLMs;
record the compile check and state honestly that no live run was made.

**Prior art:** FR-1073 migration brief
`feature-requests/authoring-briefs/fr-1073-map-migration.md` (rows 5, 6, 7
of the same graph); review of PR #702 finding P3.
