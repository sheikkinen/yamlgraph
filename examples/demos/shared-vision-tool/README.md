# Shared Vision Tool Demo

Minimal demo for `examples.shared.vision_tool.describe_image`. It sends an input
image to the shared vision-capable tool and records a structured title,
description, and tags response in graph state.

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
