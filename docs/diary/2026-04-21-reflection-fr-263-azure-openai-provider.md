# Diary: FR-263 Azure OpenAI Provider

**Date:** 2026-04-21
**FR:** FR-263
**Author:** Copilot

## Trap: File-Size Gate as Refactoring Signal

When adding the Azure provider to `llm_factory.py`, the file-size gate (450 lines) triggered. The immediate instinct was to squeeze the code in — but the gate was actually signaling a legitimate extraction point.

## Insight: Provider Functions Are a Natural Module Boundary

All `_create_<provider>_llm()` functions share the same contract: `(model, temperature, **kwargs) → BaseChatModel`. They import their SDK lazily, configure credentials from env vars, and return a LangChain chat model. This is a textbook module boundary — cohesive, independent, and easily testable in isolation.

The extraction to `llm_providers.py` reduced `llm_factory.py` from 490 to 194 lines, making the factory's caching/validation logic much clearer without the provider noise.

## Heuristic

**Gate-as-signal:** When a gate (file-size, complexity, coverage) blocks a change, treat the gate's threshold as a design signal, not an obstacle. The gate often points at the correct refactoring boundary.

## Seed

Could provider functions be made fully declarative — a registry mapping provider names to (sdk_class, env_var, base_url) tuples — eliminating the dispatch chain entirely?
