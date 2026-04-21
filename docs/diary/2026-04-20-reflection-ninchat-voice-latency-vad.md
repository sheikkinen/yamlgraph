# Diary: Ninchat Voice — Listen/Ack/Process/Speak Latency Audit

**Date:** 2026-04-20
**Context:** User reported that calls and LLM processing feel slow and timing varies. Read the VAD + turn-taking pipeline to locate fixed cost vs variance.
**Boundary touched:** `streaming` (real-time constraint exposes implicit assumptions, per the Knowledge Graph).

## The Law applied

> *Streaming as x-ray: the real-time constraint exposes implicit assumptions.*

In a batch system, "the silence timer is 3 seconds" reads as a configuration value. On a live phone call, it reads as **3 seconds of dead air before anything happens**. The same line of YAML means two different things depending on whether you're reading it or hearing it.

## What I found

### There is no acoustic VAD
The system's "VAD" is a transcript-time silence detector: a polling FSM action that measures elapsed wall-clock since the last STT `recognizing` or `transcribed` event. Not a signal on the audio stream — a signal on *text arrival latency*.

This means two silence budgets are stacked serially:
1. Azure STT's internal endpointing (opaque, provider-owned).
2. Our `silence_detector` action (`speech_silence_s: 3.0`, adaptive `min_speech_silence_s: 1.5`).

**Trap — summed budgets:** Each layer believes it's contributing a fraction; the caller pays the full sum. Azure waits for its own endpoint signal before emitting the final transcribed event, then our timer starts counting 3.0s from that moment.

### What works
- **NC-229 ack launch pad** — `ack_speaking` fires TTS then transitions via `set_context` (not `speak_done`), so the filler plays *concurrently* with the LLM call. This is the one place in the pipeline where two waits overlap instead of add.
- **NC-217 STT-during-TTS** — no deaf window; barge-in is an FSM transition, not a stop_event race.
- **yamlgraph_preload** on `warming_up` eliminates first-turn compile cost.
- **Predefined μ-law manifest** hits zero TTS latency for fixed phrases.

### Fixed cost vs variance
| Source | Fixed or variable? | Normalize where? |
|---|---|---|
| Silence timer (1.5–3.0s) | Fixed, per turn | Lower or replace with acoustic VAD |
| Azure endpointing lag | Variable, provider | Cannot — must replace stack |
| LLM round-trip | Variable, long tail | Streaming LLM + streaming TTS |
| TTS TTFB on novel text | Variable | Expand manifest or streaming TTS |
| Adaptive threshold branch | Turn-to-turn jitter | Pick one threshold |

The user complaint "timing varies" resolves to: **every turn pays a large fixed floor (~2–3.5s before ack)** *and* **the LLM's long tail stacks on top of it**. Perceived inconsistency is mostly the LLM long tail exposed against a constant floor.

## Trap catalogue hits

- **downstream_fix**: silence is being *inferred* from text emit cadence (downstream of the actual signal — audio). The right boundary to normalize is the inbound μ-law stream, not the STT event stream. Every `speech_complete` decision currently fires in the wrong layer.
- **framework_costume**: an FSM action polling `time.monotonic()` is performing a real-time DSP job. If <50% of the silence-detection logic benefits from FSM context, it belongs in an audio worker, not in a YAML action.
- **plausible_wrong_answer**: "silence detected at 3.0s" is type-correct and passes shape checks. It is also semantically wrong — it's "STT event silence", not "acoustic silence". The assertion beyond type validation is missing.

## Cures worth judging

**Spec-kill candidate (cheapest bug killed in spec):**
- Lower `speech_silence_s` from 3.0 → 1.2s as the common-case default; keep adaptive 0.8–1.0s for short utterances. No code change, just the YAML threshold. Likely clawback: 1–2s per turn immediately.

**Boundary normalization (normalize where the signal enters):**
- Add acoustic VAD (Silero / WebRTC VAD) on the inbound μ-law stream; emit `speech_complete` from the audio worker, not from STT-event timestamps. The silence_detector becomes a backstop, not the primary signal.

**Streaming the response side:**
- Stream LLM token output straight into streaming TTS. Current flow blocks on full LLM response, *then* sends to TTS. For multi-sentence replies this is pure serial latency. Time-to-first-audio is the perceived metric; the current architecture optimizes total-time.

**Manifest verification:**
- Confirm the `ack_processing.mulaw` manifest entry matches the FSM's literal `"Kiitos. Kirjaan tietoja."` verbatim. If they diverge, the "ack masks LLM" trick silently regresses to paying full ElevenLabs TTFB on every turn.

**Speculative extract (NC-220 diary already exists):**
- Start the LLM call on interim `recognizing` text; cancel and restart if the user keeps speaking. Costs a few wasted tokens, wins full LLM latency on the common case where the interim is close to final.

## Seed

Should `speech_complete` detection be a first-class **audio-pipeline primitive** (acoustic VAD on μ-law frames) rather than an FSM action polling STT event timestamps? The current design is "infer silence from text absence" — a layering inversion. The audio bytes arrive a full turn before the text does. If yes, what is the smallest viable extraction: a Silero VAD worker in `services/` that emits a `speech_complete` FSM event directly, leaving `silence_detector` as the pre-speech / hangup backstop only?

**Companion question:** If streaming LLM→TTS were wired, what would the perceived floor of a turn become? First-token-to-first-audio might dominate everything else — exposing the silence timer as the next bottleneck once the response side stops blocking.
