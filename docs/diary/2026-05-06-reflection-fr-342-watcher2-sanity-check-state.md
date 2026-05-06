# Reflection: FR-342 Watcher2 Sanity-Check

**Date:** 2026-05-06
**FR:** FR-342 — Structured output for hello world demo
**Reviewer:** watcher2 (post-validate sanity)

## What Happened

The enforce step added an inline `schema:` block to `greet.yaml` and declared AC-01
through AC-05 satisfied. The demo-output.log was refreshed with a successful run
showing structured fields (`greeting`, `emoji`, `formality_level`). A new integration
test file was created and the directly-coupled smoke test was updated.

## Root Cause of Concern

**`parse_json: true` silently bypasses the `schema:` path.**

In `yamlgraph/node_factory/llm_nodes.py` lines 97–99:

```python
parse_json = node_config.get("parse_json", False)
if parse_json:
    output_model = None   # schema from prompt YAML is never loaded
```

Adding both `schema:` in `greet.yaml` and `parse_json: true` in `graph.yaml` means the
schema block is decorative — it never drives `llm.with_structured_output()`. The
structured dict in `demo-output.log` is produced by prompt engineering + `extract_json()`,
not by the framework's typed-output mechanism.

The FR constraint explicitly states:
> "Use inline `schema:` in prompt YAML (not new Python schema classes)."

The docstring in `llm_providers.py` for `parse_json` says:
> "Use `parse_json: true` in node config **instead of** output_schema in prompts."

These are mutually exclusive paths. The implementation chose the wrong one while leaving
the unused schema in place.

## Trap

**downstream_fix** — Structure appeared in the output (the symptom was resolved) so the
mechanism was not audited. `parse_json: true` was added because the schema path may have
been unreliable with the Inception/Mercury-2 provider, but the workaround was not
documented and left the schema block as misleading scaffolding.

## Additional Concerns

1. **`test_ac02` and `test_ac04` lack API key skip guards.** Both call `compiled.invoke()`
   unconditionally. In CI without `INCEPTION_API_KEY` (or whichever provider the default
   graph selects) these tests will error, not skip.

2. **AC-03 assertion is weak.** The OR condition (`"greeting:" in content or
   "formality_level:" in content or "emoji:" in content`) passes if even one field name
   appears anywhere in the log. This does not prove a successful structured run.

3. **"backward compatibility" comment in `test_ac04`.** The phrase appears only in a test
   comment (outside `yamlgraph/`), so the pre-commit grep and `test_no_backward_compat`
   unit test do not catch it. Still violates doctrine spirit.

## What Worked

- Scope was correctly bounded to hello demo assets and directly-coupled tests.
- The existing `test_fr323` was updated with a `_greeting_text()` helper that handles
  both structured and scalar shapes — a tolerant-matching fix at the right callsite.
- Changelog fragment and FR status were both updated.
- The demo-output.log now shows a successful run replacing the previous ERROR run.

## Seed

Can the framework assert at graph-compile time that `parse_json: true` and a prompt-level
`schema:` are mutually exclusive, emitting a clear configuration error rather than silently
discarding the schema? A validation check here would prevent "schema-as-decoration" from
reaching production undetected.
