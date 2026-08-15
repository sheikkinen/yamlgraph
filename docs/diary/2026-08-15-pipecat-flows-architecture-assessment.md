# Pipecat Flows Architecture Assessment

**Date:** 2026-08-15
**FR:** FR-803
**Verdict:** **THREAT-DORMANT**

Pipecat Flows is a credible structured-conversation library and is now built
directly into Pipecat, but it cannot replace ninchat_voice's deterministic FSM
control plane without moving the missing FSM semantics into ordinary Python.
The deciding failures are **static diffable transitions** and **deterministic
non-LLM dispatch**. Recheck if either property becomes first-class.

## Pinned Corpus

- Live repository: <https://github.com/pipecat-ai/pipecat>
- Commit: `a5bb7867e1a08595dac1a778948bbdb49e0549b2`
- Frozen predecessor: <https://github.com/pipecat-ai/pipecat-flows>
- Predecessor commit: `96223f4e9ea6f84651e379978be6560cf3ae50c8`
- Immutable predecessor release checked: `v1.0.0`, commit
  `119e0af8aa3dfaf3ddf07379d6ba8959575b1565`

The standalone repository says Flows moved into `pipecat/flows` and is frozen.
This assessment therefore uses the live integrated Pipecat commit as deciding
evidence, with the predecessor changelog only to establish the static-flow
removal history.

## Raw Examples Read First

These files were read end-to-end from the pinned live commit before relying on
documentation prose:

1. [`examples/flows/food_ordering.py`](https://github.com/pipecat-ai/pipecat/blob/a5bb7867e1a08595dac1a778948bbdb49e0549b2/examples/flows/food_ordering.py)
   (371 lines). Surprising detail: the apparent graph has no edge table.
   `choose_pizza`, `choose_sushi`, `complete_order`, and `revise_order` are
   LLM-advertised Python functions whose return value contains the next
   `NodeConfig`; even the confirmation-to-start loop is hidden in a function
   body.
2. [`examples/flows/patient_intake.py`](https://github.com/pipecat-ai/pipecat/blob/a5bb7867e1a08595dac1a778948bbdb49e0549b2/examples/flows/patient_intake.py)
   (424 lines). Surprising detail: `verify_birthday` calculates
   `verified=False` for a wrong birthday but still returns the prescriptions
   node. The branch condition is prompt intent, not an enforced FSM guard.
   `RESET_WITH_SUMMARY` also invokes an LLM while changing conversation state.
3. [`examples/flows/multi_worker_handoff.py`](https://github.com/pipecat-ai/pipecat/blob/a5bb7867e1a08595dac1a778948bbdb49e0549b2/examples/flows/multi_worker_handoff.py)
   (511 lines). Surprising detail: the general router is itself a free-form
   `LLMWorker`; an LLM tool call transfers control into the structured
   reservation worker, and another LLM-callable function transfers back. The
   state boundary is operationally useful but not deterministic.

Deciding source was also read in
[`src/pipecat/flows/manager.py`](https://github.com/pipecat-ai/pipecat/blob/a5bb7867e1a08595dac1a778948bbdb49e0549b2/src/pipecat/flows/manager.py)
and
[`src/pipecat/flows/types.py`](https://github.com/pipecat-ai/pipecat/blob/a5bb7867e1a08595dac1a778948bbdb49e0549b2/src/pipecat/flows/types.py).
`FlowManager._create_function_schema()` advertises handlers to the LLM as
tools. `_create_transition_func()` executes whichever tool the LLM selected,
stores the handler-returned next node, and `_execute_transition()` applies it.
The transition application is deterministic only *after* stochastic edge
selection.

The predecessor's pinned `v1.0.0` changelog records the key architecture
decision: `FlowConfig`, `flow_config`, `transition_to`, and
`transition_callback` were removed; dynamic Python flows are the supported
model.

## Source FSM Fragment

Source artifact:
[`projects/ninchat_voice/config/voice_coordinator_navigator.yaml`](../../projects/ninchat_voice/config/voice_coordinator_navigator.yaml),
the navigator graph-loop, recovery, and safety cluster. The complete machine
has 18 states; this bounded probe uses these 10:

| State | Event | Next state | Required semantics |
|---|---|---|---|
| `graph_processing` | `graph_continue` | `graph_speaking` | deterministic result dispatch |
| `graph_processing` | `graph_switch` | `graph_switching` | change active reasoning graph |
| `graph_switching` | `switched` | `graph_processing` | resume graph loop |
| `graph_speaking` | `speak_done` | `graph_listening` | media completion event |
| `graph_speaking` | `transcribed` or `recognizing` | `graph_listening` | barge-in |
| `graph_listening` | `transcribed`, `recognizing`, or `speak_done` | `graph_listening` | self-loop and timeout reset |
| `graph_listening` | `speech_complete` | `ack_speaking` | deterministic acknowledgement |
| `ack_speaking` | `ack_done` | `graph_processing` | immediate passthrough |
| `graph_processing`, `graph_speaking`, `graph_listening`, or `ack_speaking` | `crisis_detected` | `crisis_handoff` | safety event from every loop state |
| `graph_processing`, `graph_speaking`, `graph_switching`, or `ack_speaking` | timeout or provider failure | `speaking_error` | timed/error recovery |
| `graph_listening` | `timeout(15)` | `stt_recovery` | STT liveness |
| `stt_recovery` | `transcribed` or `recognizing` | `graph_listening` | recovery |
| `stt_recovery` | `stt_error` or `timeout(60)` | `speaking_error` | recovery exhausted |
| `graph_processing` | `safety_refusal` | `crisis_fallback` | pinned safety response |
| `crisis_fallback`, `crisis_handoff`, or `speaking_error` | completion, hangup, error, or timeout | `closing` | bounded closure |

This fragment exercises properties absent from the happy-path examples:
external events, wildcard-like safety coverage, self-loops, timeouts, barge-in,
and deterministic failure routing.

## Paper Translation

A faithful Flows-shaped representation would need Python factories and handlers
rather than one transition artifact:

```python
def graph_listening_node() -> NodeConfig:
    return NodeConfig(
        name="graph_listening",
        task_messages=[...],
        functions=[speech_complete, crisis_detected, graph_switch],
    )

async def speech_complete(flow_manager: FlowManager, text: str):
    flow_manager.state["accumulated_utterance"] = text
    return {"accepted": True}, ack_speaking_node()

# Non-LLM events require an external processor/controller:
async def on_stt_timeout():
    await flow_manager.set_node_from_config(stt_recovery_node())
```

That pseudocode can represent named nodes and actions, but it does not translate
the FSM. It splits the transition relation across tool registration, handler
returns, prompts/docstrings, and external Pipecat callbacks. A separate
deterministic dispatcher could restore the missing semantics, but then that
dispatcher, not Flows, is the control plane.

## Construct Mapping

| ninchat_voice construct | Pipecat Flows representation | Result | Evidence |
|---|---|---|---|
| Named state | `NodeConfig(name=...)` | PASS | `NodeConfig` and `FlowManager.current_node` are first-class. |
| Static transition row | Python handler returns `(result, next_node)` | FAIL | No complete edge table exists; static `FlowConfig` was removed in v1.0. |
| Event-driven dispatch | LLM tool call invokes handler | FAIL | Functions become LLM tools in `_create_function_schema`; LLM selection precedes deterministic application. |
| Guard | Python conditional inside handler | PARTIAL | Arbitrary logic works, but guards are not declarative, lintable, or enumerable independently of code paths. |
| Entry/exit action | `pre_actions` / `post_actions`, custom handlers | PASS | `NodeConfig` and `ActionManager` support built-in and custom actions. |
| Timeout transition | External timer/callback calling `set_node_from_config()` | PARTIAL | Possible in Pipecat Python, not represented by the Flows transition model. |
| Wildcard safety transition | Repeat function on every node or external dispatcher | FAIL | No machine-level wildcard/event table; omission is easy and not mechanically visible. |
| Self-loop | Handler returns the same/fresh node config | PARTIAL | Expressible in code, but resets and edge identity are not a static artifact. |
| Shared context | `FlowManager.state` plus context strategies | PASS | Persistent dict and APPEND/RESET strategies are first-class. |
| Worker handoff | `activate_worker()` / `NO_RESPONSE` | PASS | The multi-worker example proves router/reservation handoff, but the router is LLM-controlled. |

## Required-Property Verdicts

| Required property | Result | Deciding evidence |
|---|---|---|
| Static diffable transitions | **FAIL** | v1.0 removed static flows; live examples distribute edges through Python handlers returning `NodeConfig`. |
| Deterministic non-LLM dispatch | **FAIL** | `FlowManager` registers edge handlers as LLM tools; the LLM chooses the function before deterministic transition application. |
| Guard/action semantics | **PARTIAL** | Actions and arbitrary Python guards are powerful, but guards, timeouts, and wildcard safety rules are not a mechanically inspectable machine artifact. |
| Self-hosted execution | **PASS** | Examples support local SmallWebRTC and text-only eval transports; `PipelineWorker`, `WorkerRunner`, and `FlowManager` run without Pipecat Cloud. Cloud is a compatible deployment target, not a runtime requirement. |

## Verdict: THREAT-DORMANT

The deciding rows are the two **FAIL** results above. Pipecat Flows can encode a
large conversation as Python node factories and tool handlers, but today it
cannot encode the load-bearing contract of the voice control plane: all allowed
transitions visible in one static artifact and all runtime events dispatched
without an LLM in the control path.

Flows is still a serious adjacent capability. It combines media transport,
workers, context, actions, and structured conversation nodes in one self-hosted
runtime. If it regains a static flow schema or adds a deterministic event
dispatcher whose complete transition relation is exportable and lintable, the
threat becomes live immediately.

**Concrete recheck trigger:** Pipecat ships either (1) a first-class static
transition/event schema after the v1.0 removal, or (2) an export API that emits
the complete dynamic transition relation, including guards, wildcard events,
timeouts, and actions, without executing LLM-selected handlers.

## FR-359 Disposition: COMPOSES

FR-359's `YAMLGraphProcessor` distribution-channel position still composes with
this result. Pipecat remains a strong self-hosted media and worker runtime, and
a processor can delegate bounded typed reasoning to YAMLGraph. Flows overlaps
with questionnaire sequencing, but it does not replace the deterministic FSM;
the viable architecture remains Pipecat media/workers + statemachine-engine
control + YAMLGraph reasoning. FR-359 is neither superseded nor required to be
implemented by this assessment.

## Reflection

The April assessment was right about Pipecat's media plane but wrong to stop at
framework boundaries. Reading the live source at the architecture boundary
revealed a sharper distinction than feature lists: Pipecat Flows has states and
transitions, yet its supported transition relation is Python assembled and
LLM-entered. "Has an FSM" and "has an auditable deterministic FSM artifact" are
not equivalent claims.

**Heuristic:** Evaluate control planes by who selects the edge and where the
complete transition relation can be inspected, not by whether the API uses
state-machine vocabulary.

**Seed:** Could a static analyzer safely extract a conservative transition
superset from Flows handlers, or does dynamic `NodeConfig` construction make
the missing artifact irreducible without changing the API?
