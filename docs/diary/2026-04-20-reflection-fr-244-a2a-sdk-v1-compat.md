# Diary: FR-244 A2A SDK v1.0 Compatibility

**Date:** 2026-04-20
**FR:** FR-244
**REQ:** REQ-YG-245
**Duration:** ~2 hours

## Cognitive Process

The FR described three simple changes: remove `kind` from Part construction, update extraction logic, bump the version pin. The estimated effort was "Small (1-2 hours)". This turned out to be accurate in wall-clock time but wildly inaccurate in scope — the actual migration touched every A2A file and required fixing 96 tests.

## Trap: FR Underestimated Scope

The FR was written when v1.0 was anticipated but not yet available. It assumed the breaking changes would be limited to the `kind` discriminator removal. In reality, a2a-sdk v1.0 switched its entire model layer from Pydantic to Protocol Buffers, causing cascading changes:

- `TextPart` class removed entirely
- `DataPart` class removed entirely
- All enums renamed (`Role.user` → `Role.ROLE_USER`, `TaskState.working` → `TaskState.TASK_STATE_WORKING`)
- `A2AStarletteApplication` removed, replaced by route factory functions
- `EventQueue.close()` removed
- `TaskStatusUpdateEvent.final` field removed
- `AgentCard.url` field removed
- `model_dump()` → `MessageToDict()` for serialization
- `InMemoryTaskStore` methods now require `ServerCallContext`

**Cure applied:** Instead of updating the FR spec iteratively, I treated it as a living document — the acceptance criteria captured the intent (no `kind` field, tests pass, ruff clean), and the implementation expanded to cover all actual breakages. The FR's acceptance criteria were still valid; the "tests pass" criterion implicitly covered the broader scope.

## Insight: Protobuf Migration is a Boundary Change

This migration perfectly illustrates the Scripture's `the_one_law`: normalize at the boundary where external data enters. The a2a-sdk is an external boundary — when it switched from Pydantic to protobuf, every downstream consumer broke. The fix was systematic: update every boundary point (imports, constructors, enum references, serialization) rather than trying to create an abstraction layer.

The temptation was to create a compatibility shim (`Part.from_text()`, etc.) but the Scripture explicitly forbids this: "No shims, no adapters, no compat flags." Direct migration was the right call.

## Insight: v1.0 Stable Not Yet Released

The a2a-sdk v1.0 stable is not on PyPI — only alphas (1.0.0a0–1.0.0a3). The version pin `>=1.0.0a0,<2.0` is correct but should be reviewed when v1.0 stable releases. Pre-release pins require `pip install --pre` or explicit version specifiers.

## Heuristic

**"Version bump FRs hide migration icebergs."** When an FR says "bump dependency X", the actual scope is unknowable until you install the new version and watch the tests fail. The RED phase (run tests, observe failures) is the true scope discovery mechanism. Trust the test suite, not the FR's estimated diff.

## Seed

When a dependency switches its serialization format (Pydantic → protobuf), should we add a boundary test that asserts the wire format of key types? A test like `assert isinstance(Part(), google.protobuf.message.Message)` would catch the next such migration at the import level, before cascading failures obscure the root cause.
