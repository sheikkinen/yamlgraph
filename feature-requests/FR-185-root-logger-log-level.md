# Feature Request: Root Logger Respects LOG_LEVEL

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2025-03-12

## Summary

Configure the Python root logger in `setup_logging()` so non-yamlgraph modules (e.g. `projects.*`) also respect the `LOG_LEVEL` environment variable.

## Value Statement

Project developers get consistent log-level control across all modules without manually configuring every logger namespace.

## Problem

`setup_logging()` only configures the `yamlgraph` namespace logger. Modules outside that namespace (e.g. `projects.ninchat_voice`, application-level code) fall back to the root logger's default WARNING level, ignoring the `LOG_LEVEL` env var. This forces developers to add per-module logging configuration.

## Proposed Solution

After configuring the `yamlgraph` logger, also set the root logger's level and add a handler (if none exists) using the same formatter and level:

```python
root = logging.getLogger()
root.setLevel(getattr(logging, level.upper()))
if not root.handlers:
    root_handler = logging.StreamHandler(sys.stderr)
    root_handler.setFormatter(StructuredFormatter(use_json=use_json))
    root.addHandler(root_handler)
```

The guard `if not root.handlers` prevents adding duplicate handlers when `setup_logging()` is called multiple times or when another framework has already configured the root logger.

## Acceptance Criteria

- [ ] `setup_logging(level="DEBUG")` sets root logger to DEBUG
- [ ] Non-yamlgraph loggers (e.g. `logging.getLogger("projects.foo")`) emit at the configured level
- [ ] Root handler only added when no handlers exist (idempotent)
- [ ] Existing yamlgraph logger behavior unchanged

## Implementation

- File: `yamlgraph/utils/logging.py` — `setup_logging()` function
- Requirement: REQ-YG-046
