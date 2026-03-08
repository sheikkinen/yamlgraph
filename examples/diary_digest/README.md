# Diary Digest

Automated daily digest pipeline that fetches world developments across configured topics and synthesizes them into a diary-style entry.

**FR-046:** Demonstrates scheduled LLM pipelines with external data feeds.

## Key Features

- **Data files**: Topic configuration via `feeds.yaml`, seed questions via `seeds.yaml`
- **Custom nodes**: Python tools for fetching and processing feed data
- **Map nodes**: Parallel topic processing

## Running

```bash
yamlgraph graph run examples/diary_digest/graph.yaml --full
```

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Main pipeline definition |
| `feeds.yaml` | Topic configuration for digest sources |
| `seeds.yaml` | Auto-curated seed questions and ideas |
| `nodes/` | Custom Python node implementations |
| `prompts/` | YAML prompt templates |
