---
type: fix
scope: missing
---
- **Missing dependency**: Installed `langchain-google-genai` which was declared in pyproject.toml but not installed in dev environment, causing `test_google_provider` failure.
