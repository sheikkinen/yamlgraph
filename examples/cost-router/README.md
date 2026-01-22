# Cost Router Example

Route queries to cost-appropriate LLM providers based on complexity classification.

## How It Works

```
Input Query → Classify Complexity (cheap) → Route to:
  - SIMPLE → Granite 4.0 ($0.05/M tokens)
  - MEDIUM → Mistral ($0.15/M tokens)
  - COMPLEX → Claude Haiku ($0.80/M tokens)
```

## Quick Start

```bash
# Install Replicate provider (optional)
pip install -e ".[replicate]"

# Set API keys
export REPLICATE_API_TOKEN=...
export MISTRAL_API_KEY=...
export ANTHROPIC_API_KEY=...

# Run examples
yamlgraph graph run examples/cost-router/cost-router.yaml \
  --var query="What is the capital of France?"
# → Routes to: Granite (simple)

yamlgraph graph run examples/cost-router/cost-router.yaml \
  --var query="Write a Python function for binary search"
# → Routes to: Mistral (medium)

yamlgraph graph run examples/cost-router/cost-router.yaml \
  --var query="Analyze the ethical implications of AI deepfakes"
# → Routes to: Claude (complex)
```

## Classification Criteria

| Level | Use Cases | Model |
|-------|-----------|-------|
| **SIMPLE** | Factual lookups, definitions, short Q&A, conversions | Granite 4.0 |
| **MEDIUM** | Summarization, basic analysis, content generation | Mistral |
| **COMPLEX** | Reasoning, code generation, nuanced analysis | Claude |

## Files

- `cost-router.yaml` - Main graph definition
- `prompts/classify_complexity.yaml` - Classification prompt
- `prompts/execute_query.yaml` - Execution prompt
- `poc_granite.py` - Direct Replicate API test

## Notes

- Replicate doesn't support `response_format`, so we use `parse_json: true` in the classify node
- Granite 4.0 Small has ~1-2s cold start, then ~0.5-1s per request
- Classification itself costs ~0.001 cents per query
