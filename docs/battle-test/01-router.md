# Test Case: Router Pattern

**Status:** ⬜ Not tested

## Request

```
Classify customer feedback as positive, negative, or neutral, and generate an appropriate response for each type
```

## Reference

Compare with `graphs/router-demo.yaml`

## Validation Commands

```bash
cd examples/yamlgraph_gen

# Generate
python run_generator.py -o outputs/router-test \
  'Classify customer feedback as positive, negative, or neutral, and generate an appropriate response for each type'

# Structural checks
grep -A5 "type: router" outputs/router-test/graph.yaml
grep -A10 "routes:" outputs/router-test/graph.yaml
grep -A20 "edges:" outputs/router-test/graph.yaml

# Execute
source ../../.env && cd outputs/router-test && \
yamlgraph graph run graph.yaml --var 'feedback=This product is amazing, I love it!'
```

## Success Criteria

- [ ] Router node has type: router with routes: mapping
- [ ] Route keys match schema field (e.g., intent or sentiment)
- [ ] Each route target has a corresponding handler node
- [ ] Edges connect router to all handlers
- [ ] No orphan nodes (all nodes reachable from START)
- [ ] Prompts exist for router and all handlers
- [ ] Execution routes correctly based on input

## Test Inputs

| Input | Expected Route |
|-------|----------------|
| "This product is amazing!" | positive |
| "Terrible service, never again" | negative |
| "It works as expected" | neutral |

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
