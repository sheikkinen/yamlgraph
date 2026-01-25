# Test Case: Map Pattern

**Status:** ⬜ Not tested

## Request

```
Take a list of topics and generate a short summary for each topic
```

## Reference

Compare with `graphs/map-demo.yaml`

## Validation Commands

```bash
cd examples/yamlgraph_gen

# Generate
python run_generator.py -o outputs/map-test \
  'Take a list of topics and generate a short summary for each topic'

# Structural checks
grep -A15 "type: map" outputs/map-test/graph.yaml
grep "items_key:" outputs/map-test/graph.yaml
grep "item_key:" outputs/map-test/graph.yaml
grep "state_key:" outputs/map-test/graph.yaml

# Execute
source ../../.env && cd outputs/map-test && \
yamlgraph graph run graph.yaml --var 'topics=["quantum computing", "machine learning", "blockchain"]'
```

## Success Criteria

- [ ] Map node has type: map with items_key, item_key, state_key
- [ ] Sub-node defined under node: or sub_node:
- [ ] State has list input field and list/dict output field
- [ ] Prompt handles single item (not list)
- [ ] Execution processes all items and aggregates results

## Results

_To be filled after test execution_

### Generated Structure

```yaml
# Paste relevant graph.yaml sections here
```

### Execution Output

```
# Paste execution output here
```

### Issues Found

| Issue | Description | Severity |
|-------|-------------|----------|
| | | |
