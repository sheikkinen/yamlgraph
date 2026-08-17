# Reflection: The Planning Session That Left the Framework Behind

**Date:** 2026-08-17
**Trigger:** A full evening of Discord + voice_runtime + PSTN architecture
planning — five approaches compared, transport ownership debated, AudioMixer
internals reviewed, transliteration positioned — and at the end, the
realization that none of it is about YAMLGraph.

## What Happened

The session started from three threads: the chat-initiated outbound-calls
plan, the FR-812 Discord bot PoC, and a question about extending
voice_runtime for Discord calls and transliteration. It evolved into a
thorough architectural comparison of five operator-voice approaches (A–E),
discovered that voice_runtime already has speaker output via AudioMixer, and
converged on a clean recommendation: Discord for chat, voice_runtime for all
audio, Call Hub for coordination.

The work is sound. The plans are honest. The research doc is grounded in
evidence. But YAMLGraph — the framework this repository exists to build — is
barely present in any of it.

## The Trap: Infrastructure Gravity

The codebase hosts `projects/voice_runtime/` and
`docs/plan-chat-initiated-outbound-calls.md` because they grew here
organically. The voice runtime was extracted from ninchat_voice. The outbound
calls plan references the Discord PoC that lives in `examples/`. The diary
and doctrine that govern this repo's quality also govern these sibling
projects.

But the gravitational pull is real: voice transport architecture, PSTN
bridging, codec transcoding, echo suppression, operator console UX — these
are telephony and real-time audio problems. YAMLGraph's role in the outbound
calls plan is explicitly described as "optional for the first proof." The
framework contributes typed reasoning *after* final transcripts, not before.
It is a passenger in an architecture it didn't shape.

This is `working_system_inertia` applied to a repository: because the tools
and discipline are here, work migrates here, even when the work's center of
gravity is elsewhere.

## The Honest Inventory

What YAMLGraph actually contributes to the voice/Discord architecture:

- **Graph execution seam** — FR-812 proved `run_graph_async` behind a Discord
  slash command. Real, but a 30-line adapter.
- **Typed reasoning post-transcript** — call summaries, disposition coding,
  response suggestions. Valuable, but downstream of the hard audio problems.
- **Prompt/schema management** — YAML prompts for whatever the voicebot says.
  Natural fit, but not load-bearing.

What YAMLGraph does *not* contribute:

- Audio transport, codec, echo, or mixing
- Call-control FSM or session lifecycle
- Discord voice protocol or DAVE
- Transliteration (ICU/CLDR, not LLM)
- Operator console UX

The framework is relevant to ~20% of the evening's planning output. The
other 80% belongs to voice_runtime, a hypothetical Call Hub, and Discord
adapter code.

## The Question This Raises

Is this repo the right home for the outbound-calls plan and voice-Discord
research? The doctrine is valuable. The discipline transfers. But planning
documents about Twilio codec bridging and Discord DAVE encryption live here
only because the author works here, not because the framework serves them.

Counter-argument: the three-layer pattern (presentation / logic / side
effects) *is* YAMLGraph's architecture, and the voice/Discord stack follows
it cleanly — Discord is presentation, YAMLGraph graphs are logic, voice_runtime
is side effects. The framework's value is the pattern, not just the code.

Resolution: the plans can stay as long as they are honest about what is
framework work and what is infrastructure work. The risk is not that they
live here — it is that they consume sessions that could advance the framework
itself.

## Heuristic

**`infrastructure_gravity`** — when a repository's discipline and tooling are
strong, unrelated work migrates there because the environment is productive,
not because the work belongs. The symptom is a planning session that produces
valuable architecture but advances none of the repository's core capabilities.
The cure is not to reject the work but to name it: "this session advanced
voice_runtime and the Call Hub, not YAMLGraph" — and to balance the next
session accordingly.

## Seed

If the framework's contribution to voice/Discord is "typed reasoning after
final transcripts," is the real product opportunity a lightweight
post-transcript analysis service rather than an operator console — and does
that service need voice_runtime at all, or just an STT webhook?
