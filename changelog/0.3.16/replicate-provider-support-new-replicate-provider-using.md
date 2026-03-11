---
type: feat
scope: replicate
---
- **Replicate provider support** - New `replicate` provider using LiteLLM for IBM Granite and other Replicate-hosted models
  - Uses `langchain-litellm` for LangChain integration
  - Requires `REPLICATE_API_TOKEN` in `.env`
  - Default model: `ibm-granite/granite-4.0-h-small`
  - Install with: `pip install -e ".[replicate]"`
