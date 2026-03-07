# FR: Lint rule for skip_if_exists in cycles

## Pain
`skip_if_exists: true` on a node inside a cycle causes the node to execute once, then return cached output forever. The graph loops but produces identical results each iteration. Diary 2026-02-22 documents this trap.

## Proposal
Add lint check: warn when `skip_if_exists: true` is set on any node that participates in a cycle.

## Implementation
- Location: `yamlgraph/linter/checks_semantic.py`
- Infrastructure: `detect_loop_nodes()` already exists
- Effort: ~20 lines

## Acceptance
- [ ] Lint warns on `skip_if_exists: true` for nodes in cycles
- [ ] Test covers the warning
- [ ] Existing graphs pass (no false positives in examples/)
