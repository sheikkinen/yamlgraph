---
type: feat
scope: langsmith
---
- **LangSmith trace URL display (FR-022)** — After each `graph run` invoke, the LangSmith trace URL is printed when tracing is enabled (`LANGCHAIN_TRACING_V2=true` + `LANGSMITH_API_KEY`). New `--share-trace` flag makes the trace publicly accessible and prints the shareable URL.
