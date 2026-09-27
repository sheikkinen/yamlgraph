# Authoring brief: FR-1125 daily_digest example — ranker declares its story properties

Governing FR: feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md
(S-5; this brief closes the YAMLGraph-repository authoring run for the
example copy of the digest).

Repository boundary: **this repository** (`sheikkinen/yamlgraph`),
target directory `examples/daily_digest/`. The standalone digest has its
own brief (`fr-1125-digest-ranker-properties-brief.md`).

## Task

Modify **exactly one file**: `examples/daily_digest/prompts/rank_stories.yaml`.

Replace the `schema:` block (the `fields` form whose `stories` is
`list[dict]`, FR-1121) with the JSON-Schema `output_schema:` form
(FR-1054) declaring every story property the prompt text names:

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

The `system:` and `user:` templates stay byte-identical. No `schema:`
block remains. `examples/daily_digest/graph.yaml` is not touched.

Related artifacts edited by the FR's enforcement, not by this run:
`tests/unit/test_fr1121_ranker_loud_failure.py` (raise-only transform
witness becomes a content witness), `tests/unit/test_fr1123_prompt_census.py`
(the R4 expectation for this file), and the FR-1125 census ledger.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint examples/daily_digest/graph.yaml`; after the
  edit, run the identical command and record it. The after set must
  contain no E016, E017, W028 or W029.
- `yamlgraph graph validate examples/daily_digest/graph.yaml`
- `python -m pytest tests/unit -k "fr1121 or fr1123 or fr1125" -q --no-cov`
- No live smoke: the example's full pipeline is a paid provider run and
  is not authorised by this brief. Record "no smoke, by brief".

**Prior art:** FR-1125 (governing FR; this brief executes its S-5
surface); the spike `docs/spikes/constrained-object-2026-09-27/` (form
C); `fr-1121-example-ranker-brief.md` (the previous run on this file);
FR-1054 (`output_schema` nested objects).
