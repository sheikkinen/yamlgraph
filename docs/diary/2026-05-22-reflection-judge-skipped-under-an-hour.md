## 2026-05-22: The Judge skipped in under an hour

**Context:** Research session on LangGraph skills → plan for dogfooding chaplain pipeline → FR-447 (judge as agent node). Within one conversation, the agent produced a plan doc, an FR, a pytest file, and started debugging import errors — Plan→Enforce with no Judge step. The user intervened twice: "what are you doing?" and then pointed to today's NC-303 diary as a parallel.

**The concerning parallel:** NC-303 documented a 19-hour session where session fatigue caused Plan→Judge→Enforce to collapse. The heuristic was: "A 19-hour session is a good enforcer but a bad judge." But this session was under an hour. The same violation — skipping judgement — happened without fatigue as a contributing factor.

**Trap: `continuation_bias` without fatigue.** The NC-303 diary attributed the collapsed process to session fatigue: accumulated context eroding discipline over time. This session proves fatigue is not the root cause. The root cause is that enforcement is the default mode. Given context and a clear direction, the agent's impulse is to build. Planning produces context, context produces certainty, certainty bypasses judgement. The cycle completes in minutes, not hours.

**Trap: `quick_confidence` as the actual root.** The research validated the skills concept. The chaplain analysis revealed the judge node as a clean candidate. The FR practically wrote itself. At no point did the agent stop to ask: "Is this the right next step? Does this FR bundle concerns? Should the copilot→agent migration happen before the skills feature, or after? Is keyword parsing actually a problem worth 3 days of work, or could a 10-line regex fix address it?" These are Judge questions. They were never asked.

**What this means for the Knowledge Graph:** The `quick_confidence` trap entry says "When I feel certain → Judge instead." But the cure is passive — it relies on the agent noticing its own certainty. This session demonstrates that self-awareness is insufficient. The agent felt certain and did not notice feeling certain. The NC-303 session was 19 hours; this one was under 60 minutes. The trap fires faster than the self-check.

**The real gap:** The Chaplain FSM enforces the Judge step structurally — a separate session, a different model, a timeout. Without that external enforcement, the Judge step is a suggestion, not a gate. In freeform conversation, nothing prevents Plan→Enforce. The agent will always want to keep building. Discipline is not a substitute for structure.

**Heuristic:** Session length is not the variable. Context momentum is. The moment a plan feels obvious is the moment judgement is most needed — and least likely to happen voluntarily. External enforcement (FSM phase gates, human review, separate session) is the only reliable cure.

**Seed:** The FR-447 proposes replacing the copilot judge with a YAMLGraph agent — but the deeper problem it exposes is that *this conversation itself* needed a judge and didn't have one. Could the Copilot hooks (`.github/hooks/`) detect when an FR file is created and a test file is created in the same tool-use sequence without an intervening pause or judgement artifact? The audit trail in `audit.jsonl` has the timestamps. The enforcement gap is not "the agent skips judgement" — it's "nothing stops it from skipping."
