# Pre-commit Pytest Not-Slow Demo (FR-286)

This demo proves the FR-286 behavior with executable checks:

1. The root `.pre-commit-config.yaml` pytest hook exactly matches the FR-286 contract and includes `-m "not slow"`.
2. The non-slow subset command (`pytest tests/unit/ ... -m "not slow" --collect-only`) runs and shows deselection behavior.
3. Slow tests are still runnable directly with `-m "slow"`.

## Files

```text
precommit-pytest-not-slow/
├── graph.yaml
├── demo-output.log
└── prompts/
    └── context.yaml
```

## Run

```bash
yamlgraph graph lint examples/demos/precommit-pytest-not-slow/graph.yaml

yamlgraph graph run examples/demos/precommit-pytest-not-slow/graph.yaml \
  --full 2>&1 | tee examples/demos/precommit-pytest-not-slow/demo-output.log
```
