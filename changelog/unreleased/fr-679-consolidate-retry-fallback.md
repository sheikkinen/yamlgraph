---
type: fix
scope: executor
---
- **FR-679 Consolidate retry/fallback**: Extract the single-attempt structured-output policy (FR-464 `response_format` fallback + JSON extraction) into `executor_base.attempt_structured_invoke`. Both the sync `PromptExecutor._invoke_with_retry` and async `llm_factory_async.invoke_async` retry loops now delegate to it, so the fallback logic exists in exactly one place. Deletes the zero-value `executor._build_schema_hint` wrapper (callers use `executor_base.build_schema_hint`). Behavior-preserving; FR-676 parity tests pass unmodified.
