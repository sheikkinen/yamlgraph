# YAMLGraph Generator - Battle Test Plan

Testing the yamlgraph-generator's ability to produce working graphs for each pattern.

## Status Overview

| Pattern | Generated | Lints | Runs | Notes |
|---------|-----------|-------|------|-------|
| Linear | ✅ | ✅ | ✅ | [Test case](00-linear.md) |
| Agent + Websearch | ✅ | ✅ | ✅ | [Test case](05-agent-tools.md) |
| Router | ⬜ | ⬜ | ⬜ | [Test case](01-router.md) |
| Map | ⬜ | ⬜ | ⬜ | [Test case](02-map.md) |
| Interrupt | ⬜ | ⬜ | ⬜ | [Test case](03-interrupt.md) |
| Subgraph | ⬜ | ⬜ | ⬜ | [Test case](04-subgraph.md) |

## Generator Capability Gaps

| Capability | Status | Notes |
|------------|--------|-------|
| Linear nodes | ✅ | Fully supported |
| Router nodes | ✅ | Routes + conditional edges |
| Agent + websearch | ✅ | Built-in DuckDuckGo |
| Map nodes | ⚠️ | Snippet exists, untested |
| Interrupt nodes | ⚠️ | Snippet exists, no checkpointer config |
| Subgraph creation | ❌ | Only generates main graph |
| Custom Python tools | ⚠️ | Stubs generated, not functional |

## Test Cases

- [00-linear.md](00-linear.md) - Linear pattern test ✅
- [01-router.md](01-router.md) - Router pattern test
- [02-map.md](02-map.md) - Map pattern test
- [03-interrupt.md](03-interrupt.md) - Interrupt pattern test
- [04-subgraph.md](04-subgraph.md) - Subgraph pattern test (deferred)
- [05-agent-tools.md](05-agent-tools.md) - Agent + tools pattern test ✅

## Issue Tracking

| Issue | Pattern | Description | Status |
|-------|---------|-------------|--------|
| No checkpointer | interrupt | Generator does not add checkpointer config | Open |
| No subgraph files | subgraph | Only generates main graph | Open |
| Untested map | map | Snippet exists but not validated | Open |

## Execution Checklist

1. [ ] Run router test → update status
2. [ ] Run map test → update status
3. [ ] Run interrupt test → update status
4. [ ] Update generator based on findings
5. [ ] Re-run failed tests after fixes
