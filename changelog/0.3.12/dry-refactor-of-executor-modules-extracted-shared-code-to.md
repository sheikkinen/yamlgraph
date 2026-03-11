---
type: feat
scope: dry
---
- **DRY refactor of executor modules** - Extracted shared code to `executor_base.py`
  - New `prepare_messages()` helper eliminates 3x duplicated prompt loading logic
  - Shared `format_prompt()` and `is_retryable()` functions
  - `executor.py` and `executor_async.py` now import from base module
  - Cleaner separation of sync/async concerns
