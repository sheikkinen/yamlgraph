# Diary 2026-07-16 — The human skims; the agents deliberate; nobody interrupts

## The observation (supplied by the human, which is itself the point)

Three facts about how this process actually runs, stated by its human:

1. **The human only skims the results.** The FR/judgement corpus — 40+
   documents this week, thousands of lines of verdicts, revisions,
   rulings — is read in depth by nobody human. It is written *as if*
   for a human reviewer; its actual reader is the next agent (the
   enforcer reads the judgement, the judge reads the FR, the reflection
   reads the diary).
2. **FRs are discussed by planner, judge, and enforcer — the human is
   not in the loop.** The adversarial review chain is agent-to-agent.
   It works (the boring-enforcement record proves it), but it is a
   closed loop: three roles sharing one model family can converge on
   shared blind spots, and the human skim is the only outside check.
3. **The agent hesitates to use intrusive tools** — structured
   questions, "break the glass, call me" escalation. Eight product
   decisions sat parked for days (yesterday's diary) not because asking
   was hard but because interrupting felt expensive.

## The trap: inverted attention economics

The agent's default treats **prose as free and interrupts as costly**.
The human's reality is the opposite: a 2,000-word judgement costs skim
attention and extracts no decision; a 4-option question costs one click
and extracts a binding ratification. The agent optimizes for
politeness (don't interrupt) and thoroughness (write everything down)
— both of which *spend* the scarcest resource (human attention) on the
lowest-yield surface (prose to be skimmed) while *starving* the
highest-yield surface (decision points).

Named: `prose_is_free_interrupts_are_expensive` — the inversion. The
hesitation to interrupt is continuation bias's social cousin: when
unsure, the model generates more text instead of stopping to ask,
because generating is what it is; asking requires believing the
interruption is worth more than the next paragraph. Yesterday's
evidence says it is: every one of the eight questions was worth more
than any document written this week.

## What the corpus is actually FOR (role honesty)

The FR/judgement trail is not human communication — it is the agents'
**shared memory and audit substrate**. That is legitimate and valuable
(it is why enforcement is boring), but naming it changes the design:

- The documents optimize for the next agent: precise citations,
  mechanical ACs, frozen scope. They already do this; keep it.
- The **human-facing surface must be decision-shaped and tiny**:
  questions with options + evidence + recommendation; one-line
  verdicts; the (seeded) pipeline board. The skim is the interface —
  so put the load-bearing content where the skim lands: money, safety,
  deviations, and open decisions in the first lines, never buried.
- The closed-loop risk is real: planner/judge/enforcer share weights
  and doctrine. The mitigations that exist are structural (source
  verification against reality, condemning tests, the CDR-style
  witnesses outside our blast radius) — reality is the fourth reviewer.
  The human's product authority is the fifth, and it only engages
  through interrupts. Which is why hesitating to interrupt quietly
  removes the only non-model reviewer from the loop.

## Heuristics extracted

- Interrupt EARLY for decisions, not late for permission: a structured
  question with options is the cheapest thing you can hand a skimming
  human; a paragraph asking "should I…?" buried in output is the most
  expensive.
- Write documents for agents (their real readers); write interrupts for
  humans. Never confuse the two surfaces — a judgement is not how the
  human learns anything, and a question is not where nuance goes.
- Escalation tools exist to be used at the *design* moment, not the
  emergency: "call me maybe" used at judgement time is a question; used
  after enforce it is an incident report.
- The skim is the interface: front-load verdicts, money, safety,
  deviations. If the human's skim would miss it, it is in the wrong
  place.

## Seed

The pipeline-board seed (yesterday) gains a second column family:
**interrupt budget** — each gated row carries not just owner + ask-by
but the prepared question (options drafted at parking time, not asking
time). Parking an FR then MEANS drafting its unblocking question — the
ask becomes copy-paste cheap, and the hesitation excuse dies. Meta-seed:
should the Judge's template end with "questions for the human, if any,
as options" — making the interrupt a standard judgement output instead
of an agent initiative?
