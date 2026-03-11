---
type: feat
scope: cost
---
- **Cost Router example** - New `examples/cost-router/` demonstrating intelligent query routing
  - Classifies queries as simple/medium/complex using cheap Granite model
  - Routes to appropriate tier: Granite (simple), Mistral (medium), Claude (complex)
  - Demonstrates `parse_json: true` for providers without structured output
