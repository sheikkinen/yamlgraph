# Devil's Advocate: Why the Voice Product Should Potentially Be Abandoned (2026-03-27)

## Purpose
This document is a deliberate counter-position to the current migration momentum.
It assumes technical execution is possible and asks a harder question:
should this be built as a product at all?

## Executive Position
The strongest strategic argument is:
- Voice transport and speech orchestration are commodity infrastructure domains.
- The real moat is domain logic and care workflows.
- If we keep investing disproportionately in runtime plumbing, we are drifting into an infrastructure company posture while competing against incumbents with larger scale, better procurement leverage, and mature operational tooling.

In that framing, full product abandonment (or radical de-scope) is a rational option, not failure.

## What Is Commodity vs Differentiated

### Commodity (Necessary, but not moat)
- WebSocket and telephony transport handling
- TTS and STT provider abstraction and failover
- Audio encoding, buffering, timing, and mark synchronization
- Runtime retries, circuit breakers, and queue behavior
- Provider cost optimization and deployment mechanics

These are expensive to maintain and easy for larger platform vendors to do better.

### Differentiated (Potential moat)
- Navigation and intent/risk taxonomy for care contexts
- Crisis override and escalation policy
- Strong authentication policy and identity confidence gating
- Questionnaire sequencing, recap behavior, and scoring interpretation
- Clinical workflow branching and handoff correctness
- Multi-channel care result delivery policy

This is where domain knowledge compounds and where mistakes have the highest consequence.

## Competing Product Reality
A buy-oriented baseline now exists in multiple ecosystems (managed contact center, managed conversational voice, managed telephony + bot stacks).
They already provide:
- Production concurrency at scale
- Reliability SLOs and operational maturity
- Integrated routing, transfer, and queue controls
- Mature audit, retention, and compliance support
- Provider ecosystem leverage and lower unit economics over time

If our architecture focus remains on transport/runtime internals, we are choosing to compete where we are least likely to win.

## Why Existing voice_runtime Can Be a Trap
The presence of a capable bridge can create sunk-cost bias:
- We already have runtime components, so we keep extending them.
- Extension work appears incremental, but aggregate complexity grows nonlinearly.
- Every new care feature (crisis, booking, multilingual, reroute) increases safety and governance burden faster than transport code value.

Conclusion:
- Existing runtime should be treated as an execution substrate, not the product core.
- If runtime work dominates roadmap capacity, strategic drift is already occurring.

## Cost Driver Reality: Older Azure Speech Models
Cost pressure is real and valid.
However, low model cost is not sufficient justification for platform ownership.

Key point:
- Speech model choice is an optimization variable.
- Product strategy should not be dictated by whichever model is currently cheapest.

If cheaper speech models reduce comprehension or repeat prompts in safety-critical interactions, total cost can increase through:
- Longer calls
- More handoffs and escalations
- Higher failure and abandonment rates
- Higher clinical and reputational risk

## Why Navigation + Intent + Strong Auth Are the Core
The highest-value control plane is not audio.
It is policy.

### Navigation and intent detection
- Determines where the caller goes
- Determines whether crisis pathways trigger
- Determines whether rerouting is appropriate
- Directly affects care outcome and operational load

### Strong authentication
- Determines what is allowed to happen next
- Controls access to sensitive data and actions
- Provides legal and safety boundary enforcement

Without strong auth, advanced workflow capabilities are fragile or non-compliant by design.

## Steelman Case for Full Abandonment
Abandon custom voice productization if this is true:
- We are fundamentally building and operating voice infrastructure rather than improving care outcomes.
- Domain logic progress is slower than runtime/integration maintenance.
- The reliability/compliance burden is outpacing team capacity.
- Managed platforms can deliver equivalent or better baseline call quality and operations at lower total ownership cost.

Under these conditions, continuing custom product build is strategic misallocation.

## Viable Alternatives to Full Build

### Alternative A: Buy substrate, keep domain brain
- Keep intent/routing/auth/workflow logic as first-party assets.
- Run them on managed voice/contact infrastructure.
- Reduce in-house scope to adapters and policy engines.

### Alternative B: Channel-priority strategy
- Move high-complexity navigation to lower-latency-sensitive channels first.
- Keep voice for constrained, high-value use cases.
- Expand only when safety and auth metrics are stable.

### Alternative C: Static entry routing first
- Use number-based entry points for deterministic first routing.
- Add dynamic navigator behavior only after auth and crisis gating are proven.

## Decision Framework (Kill or Continue)
Use hard gates rather than optimism:

### Continue only if all are true
- Domain outcomes improve measurably (not just technical metrics)
- Auth and crisis pathways are validated under realistic conditions
- Runtime reliability is consistently within target
- Total cost trajectory is competitive with managed alternatives
- Roadmap share for domain logic exceeds roadmap share for infrastructure maintenance

### Abandon (or de-scope aggressively) if any persist
- Safety-critical misroutes remain non-trivial
- Auth confidence is insufficient for required actions
- Runtime complexity dominates delivery capacity
- Cost reductions require quality compromises in critical flows
- Comparable managed stack can deliver faster with lower operational risk

## Recommended Strategic Stance
Treat voice runtime as replaceable infrastructure.
Treat navigation, intent policy, auth gating, and care workflows as the product.

If the organization cannot enforce that boundary in roadmap allocation, full abandonment of custom voice product development is the rational choice.

## Immediate Next Actions
- Write a formal feature request that compares Build vs Buy vs Hybrid with explicit 12-month TCO and safety gates.
- Add a mandatory auth architecture decision before enabling booking or sensitive result delivery paths.
- Define objective stop criteria and commit to executing them if unmet.
- Rebalance roadmap ownership so domain-policy work is the majority investment.
