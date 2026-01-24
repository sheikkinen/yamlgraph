# Email Classifier

> Classify emails by urgency and route to appropriate handlers.

## Usage

```bash
yamlgraph graph run graph.yaml --var email="Subject: Server down! Our production servers are not responding. Please help ASAP!"
```

## Pipeline Flow

1. **classify_email** (router) - Analyzes email and determines urgency
2. Routes to: urgent_handler, normal_handler, or low_priority_handler
3. **format_response** - Formats the handler's output

## Patterns Used

- Router (conditional branching)
- Linear (post-processing)
