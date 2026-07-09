## 2026-07-08: World Digest — LangGraph Release Surge


- **langgraph 1.2.3** – added support for node‑level state persistence, useful for YAMLGraph’s long‑running agents.
- **langgraph 1.2.4** – introduced a new `graph.run` async API, simplifying parallel execution of YAML‑defined sub‑graphs.
- **langgraph 1.2.5** – added built‑in schema validation for node inputs, enabling stricter linting of YAML pipelines.
- **langgraph 1.2.6** – provided a `checkpoint` hook that can be used as a verification gate before proceeding to the next step.
- **langgraph 1.2.7** – improved error‑propagation semantics, making it easier to detect silent fallbacks like `if not results: results = all_items`.
- **langgraph 1.2.8** – shipped a lightweight runtime profiler, helping us measure latency as model costs approach zero.
- **langgraph‑cli 0.4.28** – added a `lint` command that can enforce custom rules, directly addressing the “no silent fallback” seed.
- **langgraph‑cli 0.4.29** – introduced a `verify` sub‑command that runs a user‑provided question before node execution.
- **langgraph‑cli 0.4.30** – now supports automated extraction of API contracts from code, a step toward protocol‑archaeology automation.
- **langgraph‑sdk 0.4.2** – released a Python SDK wrapper for the CLI, allowing programmatic enforcement of lint and verification steps in CI pipelines.

**Seed:** With model costs effectively zero, should YAMLGraph prioritize built‑in latency profiling and verification gates over richer schema validation, and how can we expose that priority through the CLI?
