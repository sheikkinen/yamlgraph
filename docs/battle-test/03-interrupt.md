# Test Case: Interrupt Pattern

**Status:** ⬜ Not tested

## Request

```
Ask the user for their name, then generate a personalized welcome message
```

## Reference

Compare with `graphs/interview-demo.yaml`

## Known Limitations

Generator may not include checkpointer config. This test validates structure; execution requires enhancement.

## Validation Commands

```bash
cd examples/yamlgraph_gen

# Generate
python run_generator.py -o outputs/interrupt-test \
  'Ask the user for their name, then generate a personalized welcome message'

# Structural checks
grep -A8 "type: interrupt" outputs/interrupt-test/graph.yaml
grep "resume_key:" outputs/interrupt-test/graph.yaml
grep -A3 "checkpointer:" outputs/interrupt-test/graph.yaml || echo "MISSING: checkpointer config"
```

## Success Criteria

- [ ] Interrupt node has type: interrupt with resume_key
- [ ] Prompt asks a clear question
- [ ] Following node uses the resume_key value
- [ ] Checkpointer config present (may need manual add)

## Generator Enhancement Needed

Auto-add checkpointer config when interrupt pattern detected:

```yaml
checkpointer:
  type: memory
```

## Results

_To be filled after test execution_

### Generated Structure

```yaml
# Paste relevant graph.yaml sections here
```

### Issues Found

| Issue | Description | Severity |
|-------|-------------|----------|
| | | |
