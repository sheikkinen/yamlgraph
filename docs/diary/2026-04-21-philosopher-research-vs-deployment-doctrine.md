# Philosopher Reflection — Research Fork vs Deployment Fork

**Date:** 2026-04-21
**Author:** The Philosopher
**Scope:** Reframe of yesterday's twin-repo analysis after the user supplied the intended topology.
**Related:** [2026-04-21-philosopher-nv-csap-twins.md](2026-04-21-philosopher-nv-csap-twins.md)

---

## The Frame That Was Missing

> nv = research with multiple attempts.
> csap = first deployment.

That single sentence reframes the prior reflection. What I catalogued as "drift" is **the intended topology**, not a defect. A two-track R&D pipeline looks exactly like this: a messy upstream sandbox and a zero-entropy downstream product.

The real question is not "how do we unify them" but **"is the pipeline between them working, and where does it leak?"**

## Clean Separation of Concerns

| Property | nv (research) | csap (deployment) |
|---|---|---|
| Cost of being wrong | a bad experiment | a bad patient call |
| Acceptable churn | high — 5 coordinators, ad-hoc scripts, stale comments | low — Phase J–N killed 25 test files to reach "golden" |
| Optimal cadence | daily NC-* (NC-240 to 4 coordinators in one session) | gated by staging + Confluence + Terveystalo review |
| Tolerates | 5 modes, stale `OC-012` comment, dangling fn for weeks | nothing unused, no lying comments, single coordinator |
| Failure mode | entropy accumulates | deployment goes stale — research outpaces production |

Research needs a **mess budget**. Deployment needs a **zero-entropy posture**. Forcing one doctrine on both corrupts both.

## Retraction of Yesterday's Submodule Proposal

Yesterday I proposed extracting `graphs/_common/` + `graphs/navigator/` + `graphs/interrai_ca/scoring/` into a shared submodule.

**That proposal is withdrawn.** A submodule would import deployment's zero-entropy constraint back into research — revoking exactly the freedom that makes research work (rename, fork, delete, re-experiment on shared primitives without review gates). The byte-identical subtrees are identical today *because* research hasn't needed to diverge there yet, not because they are a true shared invariant.

## The Deeper Trap I Missed Yesterday

Not `quick_confidence` — **doctrine leakage**.

Yesterday I treated both repos under the same Scripture. That Scripture was written for a production codebase. Applied to a research sandbox, its gates become obstacles, its entropy-kill rule becomes churn-suppression, its "no comments that lie" rule flags abandoned experiments as defects.

The 2026-04-21 diff audit is Exhibit A. It flagged nv's stale `OC-012` comment as a 🟡 issue. Under research doctrine, that comment is **not a defect** — it is an artifact of an abandoned experiment, cost-free to leave. It *becomes* a defect if and only if it graduates to csap.

## Generalized One Law (Candidate)

The Scripture's **One Law** says:

> Normalize at the boundary where external data enters, not downstream where it manifests.

Its unstated generalization:

> **Normalize defects at the doctrine boundary, not before.**

A stale comment is not a defect in research. It becomes a defect at the research → deployment crossing. Applying zero-entropy upstream is as wrong as failing to apply it downstream.

## The Actual Pipeline Today

**Manual cherry-pick by the human.** No tooling. No declared promotion criteria. No staleness signal. Evidence from the last 7 days:

- `farewell_wait` landed in csap first (production incident) → ported to nv 5 coordinators one-by-one (NC-240).
- NC-232 split landed in nv first → csap port pending.
- The 2026-04-21 audit was itself a manual drift report.

The pipeline lives in the human's head. Fine today at ~1 promotion/week. Won't stay fine.

## Alternative Processes — Ordered by Invasiveness

### Tier A — zero cost, do now

**1. `DOCTRINE.md` in each repo.** One paragraph declaring research vs deployment posture. Changes how both humans and the Philosopher classify findings.

**2. `graduation-log.md` in nv; `adoption-log.md` in csap.** Schema:

```
## NC-232 extract/probe split
- Graduated from nv: 2026-04-20 @ 744ffb9
- Acceptance gate: ≥20 calls with split-phase histograms
- Status in csap: pending FR
- Ported to csap: <date/SHA or —>
```

Forces the graduation criterion to be named **before** the port. Biggest single win relative to effort.

**3. Amend [docs/letter-to-the-philosopher.md](../letter-to-the-philosopher.md)** with a warning about doctrine leakage as a distinct trap.

### Tier B — when a second drift incident appears

**4. Nightly capability-parity script.** Compares a thin semantic-capability manifest between repos and emits a markdown diff. Signal, not gate.

**5. `promote:csap` trailer convention.** Human marks nv commits ready to port. No bot yet — just a named signal.

### Tier C — defer until volume justifies

**6. Automated promotion PR bot.** When volume exceeds ~5 promotions/week.

**7. Shared package or submodule.** Rejected yesterday, still rejected. It imports deployment doctrine into research.

## What This Reveals About the Scripture

The Scripture's gates (changelog-gate, diary-gate, demo-gate, no-verify-ban) assume deployment doctrine. Applied to a research repo with daily throwaway commits, they become friction that suppresses the experiment rate.

nv has `.chaplain/` tooling; csap does not. That asymmetry is correct under this frame — the research repo needs the Chaplain/Inquisitor loop *more* than deployment does, because deployment has fewer degrees of freedom to audit. But the enforcement thresholds should differ:
- Research: advisory gates, fast iteration, entropy tolerated within the mess budget.
- Deployment: blocking gates, zero entropy, every comment must be true.

**Candidate heuristic (new, seed):**
> Doctrine is contextual. A lint gate that makes sense in deployment can corrupt research. Before flagging a finding, ask: "Under which doctrine does this repo operate, and does the finding violate *that* doctrine?"

Two diary entries now reference doctrine-contextuality. Not yet graduated to Scripture — awaiting a third instance that confirms recurrence.

## Seed

> If research and deployment need different doctrines, do they also need different *Scriptures*? Or is one Scripture correct — and we have been applying it at the wrong boundary?

Corollary seed:
> Is the two-repo split itself the doctrine boundary? Is that why it feels correct to have two repos rather than one with branches?

## References

- [2026-04-21-philosopher-nv-csap-twins.md](2026-04-21-philosopher-nv-csap-twins.md) — prior reflection, partially superseded by this one
- [projects/ninchat_voice/docs/2026-04-21-graph-diff-vs-csap.md](../../projects/ninchat_voice/docs/2026-04-21-graph-diff-vs-csap.md) — the audit re-judged
- [customer-service-agent-platform/docs/clean-up.md](../../../customer-service-agent-platform/docs/clean-up.md) — evidence of deployment doctrine (Phase J–N purge)
- [.github/copilot-instructions.md](../../.github/copilot-instructions.md) — Scripture assumed universal; this reflection argues it is contextual
