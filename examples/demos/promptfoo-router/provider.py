"""Promptfoo Python provider for YAMLGraph graphs."""

from yamlgraph.compile.graph_loader import invoke_graph


def call_api(prompt, options, context):
    """Promptfoo calls this for each test case.

    See: https://www.promptfoo.dev/docs/providers/python/
    """
    config = options.get("config", {})
    graph_path = config.get("graph", "graph.yaml")
    output_key = config.get("output_key", "response")
    variables = context.get("vars", {})

    result = invoke_graph(graph_path, variables)

    # Return both classification and response for assertion flexibility
    output_parts = []
    if "classification" in result:
        classification = result["classification"]
        if isinstance(classification, dict):
            output_parts.append(f"TONE: {classification.get('tone', 'unknown')}")
            output_parts.append(f"CONFIDENCE: {classification.get('confidence', 0)}")
        else:
            # Router stores route field value as string
            output_parts.append(f"TONE: {classification}")
    if output_key in result:
        output_parts.append(f"RESPONSE: {result[output_key]}")

    return {
        "output": "\n".join(output_parts),
        "metadata": {
            "classification": result.get("classification"),
            "graph": graph_path,
        },
    }
