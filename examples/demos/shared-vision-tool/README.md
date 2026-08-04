# Shared Vision Tool Demo

Minimal demo for the shared image description manifest tool. The graph calls the
tool directly with a `tool_call` node and inline arguments:

```yaml
nodes:
  describe:
    type: tool_call
    tool: describe_image
    args:
      image: "{state.image}"
      instruction: "Title, 2-sentence description, and 8 DeviantArt tags."
      provider: google
    state_key: described
```

Validate the graph:

```bash
yamlgraph graph lint examples/demos/shared-vision-tool/graph.yaml
```

Run the demo:

```bash
yamlgraph graph run examples/demos/shared-vision-tool/graph.yaml \
  --var image=examples/demos/shared-vision-tool/fixture.png --full
```

The smoke run requires `GOOGLE_API_KEY`.

The `described` state value is the tool-call result envelope:

```yaml
task_id: "<tool invocation id>"
tool: describe_image
success: true
result:
  title: "<image title>"
  description: "<two-sentence description>"
  tags:
    - "<tag>"
error: null
```
