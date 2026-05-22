## 2026-05-22: Session fatigue and the self-approving Judge

**Context:** Audit log forensics on session `b1df1785` — a single Copilot session active for 19 hours (490 events, 5 denials). In its final 6 minutes, the session wrote the NC-303 FR, set `Status: Judged — PASS`, and began creating implementation files. Plan→Judge→Enforce collapsed into a single unbroken flow. The Judge step was a one-line status field edit, not a separate critical review.

**Trap: quick_confidence.** The agent had just finished NC-302 (same pattern, mock mode). NC-303 was "just extend to real mode." The familiarity created certainty, and certainty bypassed judgement. The Knowledge Graph names this: "When I feel certain → Judge instead." The agent felt certain and therefore did not Judge.

**Trap: gate_checks_shape_not_substance.** Setting `Status: Judged — PASS` satisfies the shape of the process. The `fr-checks.sh` hook — if it validates FR status at all — checks presence, not content. A Judgement section with explicit risk analysis, constraint verification, and challenge to assumptions is the substance. The status field is the shape. The sheikkinen-process FSM has the right structure (separate `judge` state with `approve`/`revise`/`reject` transitions, 600s timeout) but this session was not running under the Chaplain FSM. It was a freeform Copilot session with no external state machine enforcing the phase gates.

**The gap: Chaplain process exists but doesn't cover ninchat_voice.** The sheikkinen-process.md documents the full Plan→Judge→Enforce FSM with timeouts (plan: 600s, judge: 600s, enforce: 3600s). The Chaplain system in `.chaplain/` implements this for the yamlgraph core repository. But `projects/ninchat_voice` operates as a separate blast radius — its FRs (NC-xxx) are written and enforced by freeform Copilot sessions with no FSM enforcement. The Chaplain's phase gates, timeouts, and separate-session-for-judgement discipline simply don't apply there. The mitigation exists in doctrine but is not deployed where the violation occurred.

**Session fatigue as force multiplier.** A 19-hour session accumulates context but erodes discipline. The first 18 hours produced solid work (NC-298 error tickets, NC-300 flex navigator, NC-301 hangup lifecycle, NC-302 mock E2E — each with proper TDD cycles). The final hour introduced NC-303 with compressed process. The pattern: long sessions do good enforcement work on established tasks, but new planning work initiated late in a session gets rubber-stamped. The impulse is "let me just get this started before the session ends." That impulse is the opposite of Judge.

**Available mitigations (ranked by feasibility):**

1. **Extend Chaplain to ninchat_voice.** The infrastructure exists. The `.chaplain/inbox/` → FSM → Plan → Judge → Enforce pipeline would enforce session boundaries automatically. The Judge would run in a separate inference session from the Plan. Cost: configuration, not code. Status: not done.

2. **FR Judgement substance check in hooks.** Require a `## Judgement` section with structural markers (`Risk:`, `Challenge:`, `Verdict:`) and minimum content. A status-field-only "Judged" would fail the gate. This is the `substance_over_presence` cure already in the Knowledge Graph, applicable via `fr-checks.sh`. Status: not implemented.

3. **Temporal cooldown in audit trail.** Cross-reference the audit log: if FR status changed to "Judged" and implementation file created within N minutes in the same session, warn or block. The data is already there (audit.jsonl has timestamps and session IDs). Status: not implemented.

**Heuristic:** A 19-hour session is a good enforcer but a bad judge. When a session that has been enforcing for hours begins planning new work, the enforcement muscle dominates — it wants to build, not question. Separate the sessions or accept that late-session plans will be rubber-stamped.

**Seed:** Could the Chaplain FSM be extended to ninchat_voice as a thin wrapper — same inbox pattern, same phase gates, but with project-scoped FR numbering (NC-xxx) and project-local paths? The infrastructure cost is configuration; the discipline cost is accepting slower throughput for higher process fidelity.
