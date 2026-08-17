# Call From Chat — Outbound Phone Calls, Controlled From Discord

**One typed message becomes speech on a live phone call. No headset, no audio, no new telephony stack.**

---

## The Pitch

Operators already live in chat. Phone calls shouldn't drag them out of it.

**Call From Chat** lets an authorized operator place a real PSTN call with one
slash command, read the remote party's words as live transcript messages, and
reply by typing — or by pressing an approved one-click voice macro. The system
speaks; the operator never touches audio.

```
/call start number:+358...
  → 📞 dialing… ringing… connected
  → 🗣 "Voitteko soittaa huomenna uudelleen?"
  → operator types: "Hetkinen, tarkistan asian."  → spoken to the caller
  → /call hangup  → ✅ duration, outcome, audit summary
```

## Why It Wins

| | |
|---|---|
| **Zero new audio work** | Reuses the production-proven telephony and speech runtime: Twilio Media Streams, streaming STT/TTS, echo suppression, call isolation — all battle-tested on live traffic. |
| **Chat is just a skin** | Discord is an adapter over a channel-neutral Call Hub. Teams or Slack plug into the *same* command and event contracts — no changes to telephony, speech, or call-state logic. |
| **Safe by construction** | Role-restricted commands, allowlisted destinations, one thread bound to one call, idempotent commands (a Discord retry can never repeat speech or hang up the wrong call), fail-closed routing, redacted logs, full audit trail. |
| **Human stays in charge** | No autonomous LLM replies. Every spoken word is typed or explicitly approved as a server-defined macro. |

## How It Works (30 seconds)

A Discord thread is bound to exactly one call. The Call Hub authorizes and
deduplicates every command, a call-control state machine serializes speech, and
the existing voice runtime does the talking. Events flow back as ordered,
sequenced messages — dial, ring, connect, transcript, spoken, ended.

**Operator surface:** `/call start · say · macro · status · hangup` + macro and
hang-up buttons, all inside one auto-created thread per call.

## Proof Plan, Not Promises

Five gated phases: contracts with fake everything → deterministic mock voice
loop → full Discord flow against mocks → two-call isolation and restart
recovery → **one** explicitly approved live call on an allowlisted number.
No provider credentials until the routing and idempotency tests pass; no
billable call without a human sign-off.

## Deliberately Not Doing

Inbound calls, conferencing, operator microphone audio, autonomous replies,
arbitrary dialing, WhatsApp onboarding. First proof = one internal operator,
one call, end to end.

---

*Full plan: [plan-chat-initiated-outbound-calls.md](plan-chat-initiated-outbound-calls.md)*
