# Task brief: FR-1030 — hello demo submits its greeting as a desktop toast

## Authority

FR-1030 (feature-requests/FR-1030-desktop-toast-notification-tool.md),
judged APPROVED WITH REVISIONS 2026-09-08
(feature-requests/FR-1030-desktop-toast-notification-tool.judgement.md).
Judgement deliverable D-5; conditions C-2 (operator approved the
quickstart side effect, recorded verbatim in the FR), C-6 (this route),
C-3 (submission, never delivery), C-7 (nothing under yamlgraph/).

**Prior art:** `fr-777-convert-brief.md` is the closest structural
precedent — a governed graph edit that swaps/adds `tools:` manifest
references without touching node logic. It differs in that FR-777 only
replaced declarations, while this brief also adds one node and one edge.

## Artifacts to modify (governed)

1. `examples/demos/hello/graph.yaml`

No prompt file changes. No other graph changes.

## The change

The shared tool and its manifest already exist in the committed working
tree at `examples/shared/notify_toast.py` and
`examples/shared/send_toast.tool.yaml` (commit 9db2d51d). Manifest paths
resolve relative to the referencing graph (REQ-YG-574), so
`../../shared/send_toast.tool.yaml` is correct from
`examples/demos/hello/`.

Three edits, nothing else:

**1. Disclose the side effect in `description:`.** The current one-line
description says the graph is a simple greeting generator. It must now
say that running it raises a system notification. Suggested wording
(adapt only for YAML style, not meaning):

```yaml
description: >
  Simple greeting generator demonstrating basic LLM usage, then submitting
  the greeting as a desktop notification (FR-1030). Running this graph
  raises a system toast on macOS, Windows, and Linux.
```

**2. Add a `tools:` block** declaring the shared tool by manifest:

```yaml
tools:
  send_toast:
    manifest: ../../shared/send_toast.tool.yaml
```

**3. Add one `notify` node after `greet`, and rewire the edges:**

```yaml
nodes:
  notify:
    type: tool_call
    tool: send_toast
    args:
      title: "Hello, {state.name}"
      message: "{state.greeting.greeting}"
    state_key: notified
    on_error: skip
    verification:
      question: "Will contain submitted"
      on_fail: warn

edges:
  - from: START
    to: greet
  - from: greet
    to: notify
  - from: notify
    to: END
```

The `verification` block is required and its question is fixed. Lint
rule W022 fires on `on_error: skip` without one, and the obvious
placeholder — `"Will return non-empty"` — is **vacuous here**: the FR-778
envelope is a non-empty dict on the failure path too, so that predicate
passes when the toast did not go out. `"Will contain submitted"` is the
substantive form: the literal `submitted` appears in the envelope only
when the tool returned `{"submitted": True, ...}`, so the skip path
actually warns. Do not substitute a different question.

Lint rule W017 (`on_error: skip` silently drops failures) will still
warn. That warning is correct and accepted: the skip is deliberate, and
the FR records why. Do not repair W017 by changing `on_error`.

`state.greeting` is the dict produced by the existing `greet` node
(`parse_json: true`, inline schema with `greeting`, `emoji`,
`formality_level`), so `{state.greeting.greeting}` selects the greeting
text. Add `notified: dict` to the `state:` block if the loader requires
the key to be declared; check the existing `state:` conventions before
adding it.

`on_error: skip` is required and deliberate: the tool raises on every
failure, and the graph — not the tool — declares that a headless host or
a Linux box without `notify-send` should still reach `END` with a
visible FR-778 failure envelope in `state.notified`.

## Must NOT change

- The `greet` node: prompt, `parse_json`, `variables`, `state_key`,
  temperature — byte-identical.
- `prompts/greet.yaml` — untouched.
- `version`, `name`, `prompts_relative`, `prompts_dir`, `defaults`.
- The existing `state:` keys `name` and `style`.
- Anything under `yamlgraph/` (judgement C-7).
- Anything under `examples/shared/` — the tool and manifest are already
  committed and frozen for this task.

## Validation

- `yamlgraph graph lint examples/demos/hello/graph.yaml` must pass.
- `yamlgraph graph validate examples/demos/hello/graph.yaml` must pass.
- Smoke (this machine is macOS, so a real notification will appear):

  ```bash
  yamlgraph graph run examples/demos/hello/graph.yaml --var name="World" --var style="enthusiastic" --full
  ```

  The result must contain `notified` with `success: True` and a nested
  `result` of `{'submitted': True, 'backend': 'osascript'}`. A
  `success: False` envelope means the smoke did not pass — report it as
  a failure rather than accepting the skip path as success.

- Record the exact smoke command and its outcome honestly in the
  authoring report, including whether the notification was submitted.
