# 2026-04-24 Reflection: FR-276 Prompt Caching Implementation

**Context:** Implementing Anthropic prompt caching via `system_segments` field in YAML prompts to enable CAG (Cache-Augmented Generation) optimization for watcher2 pipeline.

**Trap:** **downstream_fix** — When initial test failures occurred (FileNotFoundError for 'test.yaml'), I focused on fixing the symptom (mocking file operations) instead of examining the root cause. The real issue was incorrect test architecture: other prompt tests in the codebase use real temporary files, not file system mocking.

**Heuristic:** When tests fail with file system errors, examine existing test patterns before adding mocks. File operations should generally be tested with real temporary files rather than complex mocking chains. The pattern `tmp_path / "prompts" / "test.yaml"` with `write_text()` is the established norm.

Also encountered **quick_confidence** - after manual testing proved all functionality worked correctly, I felt certain the implementation was complete. However, the failing tests (despite being test setup issues) still represent incomplete acceptance criteria coverage. Working functionality ≠ complete acceptance.

**Learning:** Provider-specific message formatting is more complex than anticipated. Anthropic's content block structure with `additional_kwargs.content` differs significantly from standard LangChain message patterns. The implementation correctly handles this via conditional logic in `_build_system_message_from_segments()`, but this pattern may need refactoring if more providers adopt structured content formats.

**Seed:** How should YAMLGraph handle the growing divergence in provider-specific message formats? Should we abstract message construction behind a provider-specific message builder pattern, or continue with conditional logic in a unified message preparation function?
