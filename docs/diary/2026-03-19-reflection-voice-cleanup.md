# Diary: NC-155/156/157/158 — Voice Codebase Cleanup

**Date:** 2026-03-19
**FRs:** NC-155, NC-156, NC-157, NC-158
**Scope:** voice_runtime, ninchat_voice, outcaller

## What happened

Four cleanup FRs from the voice-review audit, executed in dependency
order: NC-158 → NC-155 → NC-156 → NC-157.

**NC-158** (import paths): 108 import sites across voice_runtime and
outcaller changed from `projects.voice_runtime.xxx` to `voice_runtime.xxx`.
Mechanical sed + conftest.py sys.path fix. Zero test failures.

**NC-155** (test gaps): 18 new tests for TwilioCall, PerTurnStt, and
STT lifecycle in voice_runtime (81 → 99 tests). Hit the lazy-import
mock target trap — `from elevenlabs import ElevenLabs` inside a function
means you must patch `elevenlabs.ElevenLabs`, not the consumer path.

**NC-156** (dead/duplicate code): Extracted `_emit_ui_activity` (3 copies → 1),
replaced `_send_to_engine` (2 copies → FsmEventSender), consolidated
`DEFAULT_BRIDGE_PATH` (7 locations → 1 canonical import). Removed dead
`_SESSIONS` dict from outcaller. Made `source` parameter required (no default)
per judgement amendment.

**NC-157** (server_fsm split): 579 → 201 + 430 lines. Factory pattern
`create_bridge_handlers()` with closure over shared state. 39 test mock paths
updated mechanically with sed.

## Cognitive Process

### Trap: File corruption from overlapping replacements

`replace_string_in_file` on ninchat_send_async_action.py accidentally
consumed the `_dispatch_direct` function because the `oldString` context
window overlapped. **Cure:** for files with dense function boundaries,
do header replacement first (imports only), then use sed for call-site
changes. Never try to replace a 50-line block in a file with adjacent
functions of similar signatures.

### Trap: Lazy-import mock targets (recurring)

This is the second time this pattern has appeared. The rule: **patch where
the name is defined, not where it's consumed. For lazy imports inside
functions, the definition site is the source package (`elevenlabs.ElevenLabs`),
not the consumer module.**

### Insight: Mechanical refactors benefit from dependency ordering

NC-158 before NC-156 was correct. Changing import paths first meant that
the duplicate-extraction work in NC-156 only had to touch the new canonical
paths, not the old `projects.xxx` paths. Same for NC-156 before NC-157 —
extracting helpers before splitting meant no merge conflicts between files.

### Insight: disconnect_state as mutable dict vs nonlocal

When splitting a module that uses `nonlocal` for shared state between
closures, converting to a mutable dict (`disconnect_state["logged"]`)
preserves the same semantics without requiring the closures to share
a lexical scope with the calling code. Clean pattern for factory functions.

### Trap: UI_EVENTS_ENABLED guard breaks tests

After extracting `emit_ui_activity` with the `UI_EVENTS_ENABLED` guard,
existing tests that mocked `subprocess.run` got 0 calls because the guard
short-circuited before reaching the subprocess call. Fix: add
`patch.dict("os.environ", {"UI_EVENTS_ENABLED": "true"})` in test context.

## Metrics

| Metric | Before | After |
|--------|--------|-------|
| voice_runtime tests | 81 | 99 |
| ninchat_voice tests | 361 | 361 |
| outcaller tests | 189 | 189 |
| server_fsm.py lines | 579 | 201 |
| `_emit_ui_activity` copies | 3 | 0 (1 shared) |
| `DEFAULT_BRIDGE_PATH` copies | 7 | 0 (1 canonical) |
| `_send_to_engine` copies | 2 | 0 (FsmEventSender) |

## Seed

When a module has patchable stubs (`tts_speak`, `stt_listen`) at module
level purely for test mockability, is there a cleaner dependency injection
pattern? The current approach works but creates tight coupling between
test mock paths and module structure — any split forces mechanical mock
path updates. Could a DI container or protocol-based injection reduce
this maintenance burden while preserving test isolation?
