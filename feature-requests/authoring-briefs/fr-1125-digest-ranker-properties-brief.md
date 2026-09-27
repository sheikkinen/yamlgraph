# Authoring brief: FR-1125 standalone digest — ranker declares its story properties

Governing FR: feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md
(S-5; this brief closes the standalone-digest authoring run).

Repository boundary: the **external** repository
`sheikkinen/yamlgraph-daily-digest`, checked out beside this one; on
this host the checkout is `C:/src/yamlgraph-daily-digest`. The
authoring route runs from this YAMLGraph checkout with
`AUTHOR_WORKDIR` set to that checkout, every edit happens there and
not in the YAMLGraph checkout, and every path below is relative to the
digest checkout. Nothing from that checkout is committed here.

## Task

Modify **exactly one file** in the digest checkout: `prompts/rank_stories.yaml`.

Replace the `schema:` block (the `fields` form whose `stories` is
`list[dict]`) with the JSON-Schema `output_schema:` form (FR-1054) that
declares every story property the prompt text already names:

```yaml
output_schema:
  type: object
  properties:
    stories:
      type: array
      description: "Top 5-8 stories, each with title, url, summary, relevance, reason"
      items:
        type: object
        properties:
          title: {type: string, description: "Article title"}
          url: {type: string, description: "Article URL"}
          summary: {type: string, description: "2-3 sentence summary"}
          relevance: {type: number, description: "0.0-1.0 relevance score"}
          reason: {type: string, description: "Why this story was selected"}
        required: [title, url, summary, relevance, reason]
  required: [stories]
```

The `system:` and `user:` templates stay byte-identical (they already
read flat `item.title` etc. since FR-1122). No `schema:` block remains.
`graph.yaml` is not touched.

Related artifacts edited by the FR's enforcement in the digest
repository, not by this run: `tests/test_fr1121_ranker_loud_failure.py`
(the raise-only transform witness becomes a content witness: the
transformed item schema keeps the five properties) and, if needed,
`tests/test_fr905_ranked_validation.py`'s schema test.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint graph.yaml` (digest checkout); after the edit,
  run the identical command and record it. On the target yamlgraph
  release the after set must contain no E016, E017, W028 or W029.
- `yamlgraph graph validate graph.yaml`
- `python -m pytest tests -q` in the digest checkout — every FR-905,
  FR-1121 and FR-1122 test must pass after the edit.
- No live smoke in this run. The production witness is the next
  scheduled run after merge (FR-1125 AC-09): a bulletin with a non-zero
  story count.

**Prior art:** FR-1125 (governing FR; this brief executes its S-5
surface); the spike `docs/spikes/constrained-object-2026-09-27/`
(form C is this exact schema and returned three full stories);
FR-1121 digest brief and FR-1122 brief (the two earlier runs on this
file); FR-1054 (`output_schema` nested objects); FR-905 (the Python
boundary that still validates each story).
