---
type: feat
scope: executor
req: REQ-YG-543
---
- **FR-715 PromptRequest — One Object Through the Front Door**: the prompt-execution parameter set is now defined once, as the frozen `PromptRequest` dataclass in `executor_base`. `execute_prompt` keeps its exact public keyword signature as a thin constructor; `PromptExecutor.execute` consumes the object. The codebase's only real jscpd clone (the twice-copied 16-parameter signature + docstring in `executor.py`) is deleted; signature-parity witnesses make three-places drift (the `max_tokens`/`thinking_budget` history) structurally impossible. Known pre-existing gap recorded: the async front door lacks `max_tokens`/`thinking_budget` — pinned as a subset witness, not silently equalized. (REQ-YG-543)
