# Shared Vision Tool Demo Model Pin

Update `examples/demos/shared-vision-tool/graph.yaml` so the existing `describe` tool call uses provider `google` and explicitly passes model `gemini-3.5-flash`.

Do not change the graph structure, state shape, tool manifest, prompt text, README, or demo output. This is a minimal graph configuration edit only.

Validate with:

```bash
yamlgraph graph lint examples/demos/shared-vision-tool/graph.yaml
```

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
