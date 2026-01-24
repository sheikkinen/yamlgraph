# Example Gallery

> Pre-generated example pipelines demonstrating YAMLGraph patterns.

## Examples

| Example | Pattern | Description |
|---------|---------|-------------|
| [email-classifier](email-classifier/) | Router | Classify emails by urgency and route to handlers |
| [batch-processor](batch-processor/) | Map | Process items in parallel |
| [multi-step-form](multi-step-form/) | Interrupt | Multi-step form with human review |
| [content-pipeline](content-pipeline/) | Linear | Generate and format content |
| [cost-router](cost-router/) | Router | Route by complexity to different models |

## Usage

Each example includes:
- `graph.yaml` - The pipeline definition
- `prompts/*.yaml` - Prompt templates
- `README.md` - Usage instructions

Run any example:
```bash
cd examples/yamlgraph_gen/gallery/<example>
yamlgraph graph run graph.yaml --var input="your input"
```

## Generating New Examples

Use the generator to create custom pipelines:
```bash
python examples/yamlgraph_gen/run_generator.py "Your request here" -o ./my-pipeline
```
