# Diary: Call Me Maybe

**Date:** 2026-05-07
**Context:** Skills export reflection — the outcaller-yamlgraph escalation

## The Vision

Install `outcaller-yamlgraph` as a system-level service. Export its graphs as user-level Copilot skills (`~/.copilot/skills/outcaller/SKILL.md`). Result: any Copilot session, in any workspace, gains the ability to make phone calls.

```
User: "Call +358401234567 and ask about their prescription refill status"
Copilot: [activates outcaller skill → yamlgraph graph run → Twilio → ElevenLabs → live call]
```

The agent becomes a telephone operator. Not by reasoning about telephony. By delegating to infrastructure it cannot replicate.

## Why This Is Different

The failed experiments (code-analysis, reflexion) taught us: **skills that describe are ignored, skills that constrain are adopted.** But there's a third category we missed:

**Skills that *extend* — granting capabilities the agent provably lacks.**

| Category | Agent Response | Activation |
|---|---|---|
| Describes (what it already can do) | "I can do this myself" | Ignored |
| Constrains (discipline it should follow) | "I'll follow this process" | Adopted |
| **Extends (what it physically cannot do)** | "I cannot do this alone" | **Must activate** |

The outcaller skill isn't a constraint. It's a **capability grant**. The agent gains telephony, TTS/STT, real-time audio — things that don't exist in its architecture.

## The Architecture

```
~/.copilot/skills/
├── outcaller/SKILL.md          ← "Make outbound calls via Twilio + ElevenLabs"
├── incaller/SKILL.md           ← "Answer inbound calls, run voice questionnaires"
└── voice-navigator/SKILL.md    ← "Route callers through healthcare navigation"

~/.local/bin/yamlgraph           ← System-level installation
~/.config/yamlgraph/
├── env                          ← TWILIO_SID, ELEVENLABS_KEY, etc.
└── graphs → ~/src/outcaller-yamlgraph/graphs/
```

The skill SKILL.md would read:

```markdown
---
name: outcaller
description: 'Make outbound phone calls with AI voice. Use when: user asks to call someone,
  conduct a phone interview, collect information by phone, or run a voice questionnaire.
  You CANNOT do this yourself — telephony requires Twilio, ElevenLabs TTS/STT, and
  real-time WebSocket audio streaming that exists outside your architecture.'
---
```

## The Implication

This collapses the boundary between "coding assistant" and "operations agent." Copilot stops being something that helps you write code about phone calls. It becomes something that *makes* phone calls.

The Skills standard was designed for "teach an agent a procedure." We're using it for "give an agent a body." The graph is the body. The skill is the nerve ending that connects agent intention to physical world action.

## Trap Awareness

- **Security boundary:** A user-level skill that can spend money (Twilio calls cost) and contact humans needs explicit consent gates. The skill should require confirmation before dialing.
- **Scope creep:** This is an application deployment pattern, not a framework feature. YAMLGraph provides the plumbing (`skill export`). The outcaller project owns the deployment.
- **Testing:** How do you test that a skill activates correctly without actually making calls? Mock mode in the graph + a `--dry-run` flag in run.sh.

## Seed

> If Skills are capability grants and graphs are the body — what happens when an agent can compose skills? "Call the pharmacy, check my prescription status, then email me the result." Three skills chained by agent reasoning. No graph orchestrates the composition — the agent IS the graph. Is that the ceiling of Skills, or the floor of something else?
