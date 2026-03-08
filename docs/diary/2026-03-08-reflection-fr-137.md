## 2026-03-08: FR-137 — DeepSeek Provider Reflection

**Context:** FR-137 added DeepSeek as the ninth LLM provider to the `create_llm()` factory. The implementation followed the established xAI/Inception pattern — `ChatOpenAI` with a custom `base_url`, no new dependencies, copy-paste of existing dispatch routing. The feature shipped cleanly: factory update, integration test with API key guard, docs updates, provider count bump from 8 to 9. Yet the reflection was skipped.

**Trap:** *batch_fatigue* — By the ninth provider, the addition pattern felt mechanical. `_create_deepseek_llm()` was a five-line function copying `_create_xai_lm()` with a different URL and model default. The low novelty suppressed the metacognitive step. The Distill obligation exists precisely for routine work: when the task feels trivial, the reflection reveals whether the process is healthy or merely habitual. The absence of difficulty is not the absence of insight.

**Heuristic:** Routine completion is a signal to reflect, not a signal to skip. The less novel the task, the more likely the reflection will surface process-level observations (like "should we have a provider checklist?") that prevent drift. Schedule the reflection as a task item, not an afterthought — treat it as the final test that must pass before merge.

**Seed:** As provider count grows beyond nine, should the framework generate a provider-addition checklist (env var, factory entry, default model, integration test, docs update, reflection) from a template — or would that automation itself become the next batch_fatigue trap?
