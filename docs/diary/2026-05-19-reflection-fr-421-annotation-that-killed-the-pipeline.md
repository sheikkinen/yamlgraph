# Chapter 23: The Annotation That Killed The Pipeline

*On partial_remediation and boundary_inventory: a one-line fix that took a pipeline down for hours because the audit stopped at the cited example.*

---

## I. The Setup

FR-419 added `ActionConfig(extra="forbid")` to enforce a strict schema at the boundary where YAML action config enters the FSM bridge. The intent was sound: catch typos early, reject unknown fields at parse time. `type` and `params` were stripped before validation because the engine injects them — they are not authored fields.

The tests passed. The commit shipped. The pipeline immediately began failing on every topic.

---

## II. The Trap

The failure mode was `partial_remediation` wearing `audit_as_ritual`'s face.

When the envelope-stripping was designed, the audit asked: "what keys does the engine inject?" Answer: `type`, `params`. Those were stripped. But the audit stopped there. It did not ask: "what keys do *authors* put in action blocks that are not execution fields?"

Every single `yamlgraph_async` action block in `watcher-pipeline-v2.yaml` carries a `description:` field — a human-readable label for the step. It had been there since the pipeline was written. `extra="forbid"` rejected it immediately on every `execute()` call, returning the failure event before the graph was ever launched.

The log said: `invalid action config: 1 validation error for ActionConfig — description — Extra inputs are not permitted`. Thirteen topics failed. The fix was two characters: add `"description"` to a frozenset.

---

## III. Why It Took This Long To Surface

Two bugs were in series. FR-419 (description rejection) fired first and aborted before the graph launched. FR-420 (extract_event couldn't read plain dicts) would only surface after FR-419 was fixed. The second bug was invisible behind the first.

The investigation ran bottom-up: logs showed `event=error` at the judge step → looked at event_map logic → found extract_event had no dict branch → fixed that. Then looked again and found the description field rejection at setup → fixed that. Both fixes were necessary; neither alone was sufficient.

This is the **downstream_fix** trap in its clearest form: the symptom (`event=error` at judge) pointed to event routing logic. The root cause was earlier in the chain, at config validation. The fix at the symptom site would have been wasted.

---

## IV. The Cure

Two separate boundaries, two separate fixes:

**Boundary 1 — action config parsing**: Distinguish engine-injected keys (`type`, `params`) from author-annotation keys (`description`). Both are not execution fields. Both must be stripped before `ActionConfig.model_validate()`. The constant was renamed `_STRIP_BEFORE_VALIDATE` with a comment separating the two categories. `ActionConfig` itself must not have a `description` field — that would put a documentation concern inside the execution contract.

**Boundary 2 — graph output parsing**: `extract_event()` received a plain dict because LangGraph serializes Pydantic state fields when the TypedDict annotation says `dict`. The fix unified the dict and `model_dump()` branches — both iterate string field values looking for event_map matches.

The condemning test for Boundary 1 uses the verbatim judge action block from `watcher-pipeline-v2.yaml`, not a synthetic example. It proves the exact payload that failed.

---

## V. The Heuristic

When you add `extra="forbid"` to a schema that consumes external config, audit is not complete after enumerating the fields you *know about*. The harder question is: **what fields do authors put in this config that carry no runtime meaning?** Documentation fields, labels, comments-as-keys — these exist in every YAML config written by humans. They are not typos. They must be classified and stripped at the boundary.

**The audit must ask two questions, not one:**
1. What execution fields exist? → model them.
2. What non-execution fields exist in real usage? → strip them.

Stopping at question 1 is `partial_remediation`.

---

**Seed:** Can `_STRIP_BEFORE_VALIDATE` be derived automatically by parsing all pipeline YAML files at startup and collecting keys that never appear in `ActionConfig.model_fields`? This would make the strip set self-maintaining as new annotation fields are added to the pipeline config.
