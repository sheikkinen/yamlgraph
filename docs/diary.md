# Development Diary

Metacognitive reflections on development process.

Previous: [diary-2026-03-04.md](diary-2026-03-04.md) — 17 entries, 2026-03-04.

---

## Entry 88 — 2026-03-05: Documents Are Code Too

**Context:** NC-125 — full audit of all 5 docs in `projects/ninchat_voice/docs/`. Three stale documents found and corrected: `dataflow.md` (4 stale sections), `fsm-research.md` (no tombstone), `architectural-options-event-model.md` (no tombstone, open questions unanswered). Committed `1e3f2e6`.

**The pattern:** Design docs written at pre-implementation time inevitably become stale at the moment the implementation lands. The code was cleaned in NC-124 (NC-118/119/120 bugs fixed) but the docs still described the *problem* as if it were active. Section 6 of `dataflow.md` said "⚠ Data loss point (NC-118 bug)" — not "former bug, here's the fix" — four commits after the fix. The bug note had become a ghost: authoritative-looking, actively misleading.

**The distinction that matters: archival vs. reference.** `fsm-research.md` and `architectural-options-event-model.md` are *design exploration* documents. They record the path taken, not the destination. But without a tombstone header, a reader approaching them cold cannot distinguish "this is the current architecture" from "this was the thinking that led to the architecture." Archival documents need a clear sign at the entry: "this is where we were, not where we are." The resolution notes on open questions in the event model doc transform it from a dangling list of unanswered concerns into a closed decision record.

**The trap: treating docs as done once written.** Documentation debt accumulates silently. Unlike a test that fails red or a type error that fails CI, a stale doc emits no signal. It only manifests when a future reader acts on outdated information. The correct pattern: when closing any NC/FR that fixes a bug, the fix task list should include "update every doc that mentioned this bug."

**Heuristic:** Every active bug marker (⚠, TODO, FIXME, bug status) in documentation is a debt clock. When the bug is fixed, the doc must transition from "here is the problem" to "here is what we built to solve it." Bug descriptions that outlast their fixes are retrospectively misleading.

**Seed:** Could a lint pass detect documentation debt automatically? Grep for known NC/FR numbers in docs, cross-reference their status in `feature-requests/`, flag any doc that mentions bugs marked as implemented. "Traceability for documentation" — the same principle as requirement traceability for tests, applied to prose.



**Context:** FR-110 — promote linter W014 (undeclared `{state.X}` reference) from warning to error E007. TDD enforcement.

The session was a study in minimal intervention. The detection logic already existed — 20 lines of Python that correctly found undeclared state references. The only defect was its social contract: it whispered when it should have shouted. Two string literals changed (`"warning"` → `"error"`, `"W014"` → `"E007"`), a function rename, and six files updated for consistency. The hardest part was not the code — it was ensuring no W014 ghosts remained in regression test sets, fixture comments, module docstrings, or architecture docs.

**Trap:** *The Severity Undercount* — treating a guaranteed runtime crash as "advisory". A missing `{state.X}` binding is not a style concern; it's a `KeyError` waiting to deploy. The original W-prefix classification masked the true severity.

**Heuristic:** When a warning always indicates a guaranteed failure at runtime, it was never a warning — it was a misclassified error. Promote at the boundary (lint time), not downstream (crash time).

**Seed:** How many other W-prefixed lint codes in the codebase describe conditions that are actually guaranteed failures? A systematic audit of W-code severity could prevent the next "it was always an error" discovery.

## Entry 85 — 2026-03-05: The Intermediate State as Normalisation Point

**Context:** NC-123 — production `incoming_call` dropped from `listening` state. Fix: `aborting` intermediate state + `call_abort_action` + `abort_listen` bridge handler. FR written, judged, amended, enforced. 18 tests. Shipped `d2e94cf`.

**The pattern that worked: state as boundary.** Entry 84's heuristic was "find the right boundary." The real fix here moved the boundary *into the FSM itself*. The `aborting` state is a normalisation point: it collapses any mid-call state into a single known entry point before the new call begins. No matter where the FSM was (listening, classifying, speaking), the incoming preemption lands in `aborting` and the same teardown logic runs. This is the One Law applied correctly — normalize at the boundary where the new call enters the FSM, not upstream in the HTTP handler and not downstream in each individual state.

**The cognitive trap avoided: per-state guards.** The naive alternative was adding `incoming_call` transitions for every active state individually (11 states × 1 transition = 11 lines, 11 different actions or duplicated logic). Instead, one wildcard + one state + one action. The FSM's own first-match-wins ordering enforces the idle bypass without any guard code.

**The structural insight: preemption belongs in the state machine.** A new call arriving mid-call is not an error, not a busy condition, and not a boundary violation — it is a valid FSM event with a defined response: abort cleanly, then restart. Modelling it as a state (`aborting`) rather than a guard (`is_disconnected` check) makes the response explicit, testable, and observable in logs. "FSM entered aborting at 15:39:18" is a fact in the trace. "HTTP handler returned 200 because is_disconnected was False" is not.

**NC-122 coupling.** The `_ACTIVE_CALL_STATES` set in `test_nc122_hangup_coverage.py` was a silent gap — `aborting` added to the YAML would have been invisible to the hangup coverage test without the explicit set update. The test guarded what it knew about, not what it didn't know about. Resolution: the fixed set is now tighter, but the deeper fix is that the inverse check (every YAML state in the set) would have caught this automatically. That remains a non-blocking gap.

**Heuristic:** When a new event can arrive in any state, the fix is almost always a single intermediate state — not N transitions, not a boundary guard, not a retry flag. The intermediate state *is* the normalisation point.

**Seed:** The `aborting` state runs `call_abort_action` synchronously in the FSM action thread. `abort_listen` puts a `None` sentinel into the async queue, and `feed_audio()` exits within 0.5s. But `call_abort_action` sends the sentinel and immediately returns `aborted` — it does not *wait* for `feed_audio()` to actually finish before `warming_up` starts preloading graphs. Is there a race where `warming_up`'s `yamlgraph_preload` begins its async work on the event loop while the old `feed_audio()` is still alive and consuming the new caller's first audio frame? If yes, the 0.5s window is the real latency budget for `yamlgraph_preload`'s first await.

---

## Entry 86 — 2026-03-05: The dquote Trap and the Commit File Law

**Context:** Testplan execution. All test tiers fixed (NC-115/NC-118 drift in 9 shell scripts + 1 E2E file). When committing the final result, the shell entered `dquote>` and never exited — special characters (`—`, `→`) in the `-m` string opener triggered an unclosed-quote state. The `C-c`, `q`, retry cycle repeated a third time this session.

**The trap: confident inline strings.** The convention already exists in `copilot-instructions.md`: *"shell get stuck easily."* But the rule says *what* (heredoc/cat) without naming the specific failure mode or the cure. So the same mistake recurs: write a long `-m "..."` string, hit a special char or embedded quote, shell enters `dquote>`, all subsequent commands are swallowed, Ctrl-C doesn't help, `q` exits the dquote but the terminal state is uncertain. Time wasted: 2 minutes × N occurrences.

**The cure: `git commit -F /tmp/msg.txt`.** Write the commit message to a temp file with `create_file`. Pass it to git via `-F`. No quoting, no escaping, no heredoc, no dquote trap. The file can contain any unicode, newlines, and special characters freely. This is always safe; the inline form is never safe for multi-line messages.

**The structural insight: the rule must name the cure, not just the danger.** "Shell gets stuck easily" is a warning with no exit path. The actionable form is: *"For multi-line git commit messages, always write to `/tmp/msg.txt` and use `git commit -F /tmp/msg.txt`."* When the cure is named, the dangerous form becomes obviously unnecessary — there is no reason to use `-m` with a multi-line string once you know `-F` exists.

**Graduated to Scripture:** This heuristic is now promoted — the copilot-instructions.md convention line is updated to name the cure explicitly.

**Heuristic:** Never pass multi-line strings inline to shell. Write to file, pass by path. The dangerous form looks convenient until it isn't.

**Seed:** The dquote trap is a recoverable nuisance. A harder version is silent truncation — when a special char ends the string early without entering dquote mode, the commit message is silently shortened. Is there a CI check or pre-commit hook that could detect suspiciously short commit messages (e.g. less than 20 chars) and warn before the push?

---

## Entry 84 — 2026-03-05: The Right Law, The Wrong Boundary

**Context:** Production log shows FSM in `listening` at 15:38:52. At 15:39:18 a new `incoming_call` arrives — silently dropped. "No transition found." The proposed fix: add an `is_disconnected` guard in `server_fsm.py /incoming` — reject with `<Reject reason="busy"/>` if session is active.


**The trap: citing the One Law while violating its intent.** The Law says: *normalize at the boundary where external data enters.* The fix correctly identified `/incoming` as a boundary. But `busy` is not a normalization — it's a business decision masquerading as a guard. Two real scenarios demolish it immediately:

1. **Single number, FSM lagging.** Twilio's PSTN is the serialization authority. A new POST to `/incoming` only arrives *after* the previous call has fully ended at the network level. `session.is_disconnected` may still be False because the STT process is still draining — but the line is free. A `<Reject reason="busy"/>` gives the new legitimate caller a busy signal for a line that Twilio itself knows is idle. Wrong caller experience, wrong diagnosis.

2. **Multiple numbers / forked FSMs.** One singleton `TelcoSession` + one singleton FSM process *cannot* serve concurrent calls regardless of any boundary guard. The session registry, bridge socket path, and engine socket are per-process. Forking requires per-call process spawn or a per-call session multiplexer. The guard just hides that architectural gap.

**What was wrong:** I identified a real boundary (the HTTP handler) and applied a guard (busy-reject) that felt clean at first glance. But the guard assumed "FSM non-idle = line busy," which is false in both deployment models. The cleanup lag between Twilio PSTN and FSM state is not line-busy. Multi-call concurrency is a different class of problem than serialization.

**The correction the user gave:** Both "FSM is lagging behind" and "new calls should be forked" are valid real-world requirements. The proposed boundary fix fails both. The right scope depends on the deployment intent:
- Single number: the FSM needs a preemption path — `incoming_call` firing mid-call should abort the current call cleanly and start a new one. That's an FSM design question, not a boundary guard.
- Multi-tenant: per-call FSM process spawn — the singleton architecture is the constraint to remove, not patch.

**The cognitive pattern: confusing symptom location with fix location.** The symptom appeared at the FSM event drop site. The proposed fix moved one step upstream to the HTTP boundary. But "more upstream" is not the same as "correct boundary." The correct boundary for the single-number case is the FSM state machine's own preemption semantics. The correct boundary for multi-tenant is the process lifecycle. I stopped one hop short of the real question.

**Heuristic:** Citing the One Law does not validate the fix. The Law says *which layer* to fix; it says nothing about *what the fix is*. After finding the boundary, ask: does this fix hold under all deployment models, or only the one I currently have in mind?

**Seed:** If the single-number production model is "one call at a time, FSM must clean up before accepting next," what is the acceptable cleanup window? The log gap was 26s. `silence_timeout` fires at 30s. Is the real fix shortening the STT timeout to 10s in `voice_listen`, so the cleanup cycle completes faster and new calls don't arrive during the lag window?

---

## 2026-03-05: NC-119b — The Truthy Corpse

**Trap: Downstream Symptom Masking an Upstream Corpse**

NC-119 fixed `yamlgraph_action.py` to persist `context[input_key]`. The theory was sound: write at the boundary where the utterance enters. But the symptom persisted. The second live call returned the same literal `"{event_data.payload.user_utterance}"` string to Ninchat.

The corpse was in the YAML itself and in the action fallback logic. The YAML template referenced `event_data.payload.user_utterance` — a path valid during `classifying` but overwritten by `speak_done` before `forwarding_to_ninchat` runs. The engine, unable to resolve the path, returns the literal template string. That string is truthy. So `params.get('text') or context.get(...)` never fires the fallback.

Two fixes — one at the source (YAML template uses `{user_utterance}`, the persisted context key), one as a defensive guard (detect unresolved `{...}` strings and treat as empty) — completed the cure. The Agents' prayer held: normalize at the boundary, trusting no provider's type. The boundary here was not just where the utterance enters — it was also where the reference path is written in YAML.

**Heuristic:** A `or` fallback is only as good as its guard condition. A literal template string that the engine cannot resolve is truthy, not empty. Any action that falls back from params to context must guard for unresolved template strings explicitly.

**Seed:** How many other actions have `params.get(key) or context.get(key)` without a guard for unresolved templates? Is there a lint rule opportunity: detect `{event_data.payload.*}` references in action params where the state transition chain could overwrite `event_data` before the action runs?
