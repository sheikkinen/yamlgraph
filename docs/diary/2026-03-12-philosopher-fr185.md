---

## 2026-03-12: Philosopher — Copilot Node Migration

The FR-185 migration from `type: llm` to `type: copilot` for the philosopher's analyze and reflect nodes revealed a recurring pattern: **the PipelineError costume trap**. PipelineError is a Pydantic BaseModel (data structure), not a Python Exception. The FR spec showed `raise PipelineError(...)` which would TypeError at runtime. The fix was trivial — use `ValueError` following established codebase patterns — but the cognitive trap is instructive: a class named `Error` wearing a data-model costume fools both humans and LLMs into treating it as raiseable.

The 4-way unwrap cascade in `write_proposals()` (hasattr → model_dump → dict.get → raw list) was a classic symptom of the **downstream fix trap**: each branch was added to handle a different upstream producer, rather than normalizing at the boundary. CopilotResult → extract_json → Pydantic validation is the cure: one parse path, one validation layer.

**Trap:** plausible_wrong_answer — PipelineError looks raiseable but isn't; the name lies about its nature

**Heuristic:** Normalize at the boundary where external data enters, not downstream where it manifests

**Seed:** Should PipelineError inherit from both BaseModel and Exception to close the costume gap?
