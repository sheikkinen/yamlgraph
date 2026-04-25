# Prompt Caching Demo

This demo demonstrates Anthropic prompt caching using `system_segments` to optimize costs and performance in multi-step LLM workflows.

## Overview

This example shows how to structure prompts with cacheable segments to enable Anthropic's prompt caching feature, which can reduce costs by up to 90% for repeated context.

## How It Works

The demo uses two LLM nodes (`analyze` and `reflect`) that share identical cached system segments:

1. **Shared Cached Context**: Both prompts include a large, stable system segment marked with `cache: true`
2. **Task-Specific Context**: Each prompt has a unique segment with `cache: false` for task-specific instructions  
3. **Cost Optimization**: The second LLM call benefits from Anthropic's prompt cache, reusing the cached prefix

## system_segments Structure

```yaml
system_segments:
  - content: |
      # Large stable context about YAMLGraph framework
      # This gets cached across both nodes
    cache: true
  - content: |
      # Task-specific instructions
      # This varies per node and isn't cached
    cache: false
```

## Benefits

- **Cost Reduction**: Cached tokens cost 90% less than regular tokens
- **Performance**: Faster processing for cached prefixes
- **Scalability**: Enables complex multi-step workflows with shared context

## Running the Demo

```bash
cd examples/demos/prompt-caching
yamlgraph graph run graph.yaml --var topic="machine learning pipelines" --full
```

## Caching Behavior

- First LLM call (`analyze`): Establishes cache for the shared system segment
- Second LLM call (`reflect`): Hits cache for the identical segment, paying reduced cost
- Cache lifetime: 5 minutes for frequent reuse patterns

## When to Use Prompt Caching

Prompt caching is most effective for:
- Multi-step workflows with shared context
- Workflows with large, stable system prompts  
- Repeated executions with consistent prefixes
- Cost-sensitive applications processing many requests

## Note

This feature requires `provider: anthropic` and an Anthropic API key. Other providers ignore the cache flags gracefully.