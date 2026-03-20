# Diary: Multi-Call Lifecycle Bugs — The Singleton's Bill Comes Due

**Date:** 2026-03-19
**Theme:** Session state isolation in a singleton architecture

## Reflection

Five bugs, one root cause: the singleton `TelcoSession` is reused across calls, but the cleanup between calls was incomplete at every layer — transport, FSM context, and action guards.

**Bug taxonomy (from transport up to application):**

| Layer | Bug | Symptom |
|-------|-----|---------|
| Transport | `abort_listen` sends sentinel after `reset_for_new_call()` | Call 2 STT dies instantly (0 frames) |
| Transport | `reset()` doesn't stop STT before clearing reference | Orphaned feed task, RuntimeWarning |
| FSM context | `user_utterance` persists across calls | Call 2 graph crashes on stale transcript |
| FSM context | `disconnect_logged` closure never reset | Call 2 disconnect silently swallowed |
| Action guard | `_ninchat_sent_*` never cleared after dispatch | Question 2+ gets no ninchat response, 30s timeout |

**Trap:** `partial_remediation` — Each cleanup path (call_cleanup, call_abort, session.reset) cleared *some* state but not all. The cleanup code grew organically: guards added for one bug, data keys for another, transport fields for a third. No single author saw the full picture because each layer was fixed in isolation.

**Trap:** `downstream_fix` — The initial instinct for the sentinel leak was to add a drain in `PersistentSttSession.start()`. That's defense-in-depth (and we added it), but the real fix was guarding `_on_abort_listen` with `if session.stt is None` — normalize at the boundary where the stale signal enters, not downstream where it manifests.

**Trap:** `plausible_wrong_answer` — The first hypothesis for "subsequent calls fail" was the sentinel leak. The logs showed a different root cause entirely: stale `user_utterance` in FSM context causing the questionnaire graph to crash. The sentinel fix was necessary but insufficient. Reading the coordinator log (not just server.log) revealed the real causal chain.

**Heuristic:** In a singleton-reuse architecture, cleanup is a contract, not a courtesy. Every mutable field set during a call must have a corresponding clear in cleanup. The test for completeness: can you grep for every `context[key] = ` and find a matching `context.pop(key` or `del context[key]` in a cleanup path?

**Heuristic:** `the_one_law` applied to guard keys: a fire-and-forget action that sets a guard must clear it in its `finally` block, not rely on state-transition cleanup. The yamlgraph_async action had this right; ninchat_send_async didn't.

**Observation:** The TDD discipline caught a subtle test assumption error. The existing `test_clears_bridge_sent_guards` asserted `user_utterance` was preserved as an "unrelated key" — but our fix intentionally clears it. The test's assumption was the old (buggy) contract. Updating the test to use `some_other_key` instead was the correct response: the test should verify the *intended* behavior, not the accidental one.

**Seed:** Should the statemachine engine support a `context_reset` directive on state entry — a declarative list of keys to clear when entering `idle`? This would move the cleanup contract from imperative action code to the FSM configuration, making it auditable and complete by construction.
