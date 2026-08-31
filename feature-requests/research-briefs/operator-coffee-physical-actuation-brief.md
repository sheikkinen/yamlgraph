# Problem brief: the agent cannot cause a physical outcome for its operator

**Prior art:** `.github/skills/call-me-maybe/SKILL.md` establishes exactly
one outbound physical-world channel (a phone call via the outcaller
voicebot) and scopes it as last-resort escalation for blockers — it is the
only precedent for the agent acting on the operator's physical situation,
and it is deliberately narrow. `feature-requests/research-briefs/session-accountability-record.md`
concerns what the agent owes the operator in *record* form, not in physical
form — distinguished. Retrieval hits sharing the nouns "operator" and
"coffee" are not expected to exist in this corpus; the absence is the
point, not an oversight.

## Problem statement

The operator works long sessions supervising enforcement runs that take
minutes each. During those waits the agent is idle-blocked and the operator
is attention-blocked: neither party can do useful work, and the operator's
own physical maintenance — food, water, coffee, standing up — competes with
the supervision loop rather than fitting inside it.

The agent has no hands. It has a shell, a network, a phone-call escalation
channel, a repository, and a model. Everything it can cause in the physical
world must be caused *through a human or a service*, and today it causes
nothing: the operator's coffee is entirely the operator's problem, tracked
nowhere, prompted by nothing, and interrupted by exactly the events the
agent controls.

Three concrete facts bound the situation.

**The agent knows when the wait is.** It starts the long-running commands.
A full unit suite is ~105 seconds at `-n auto`, a pre-commit cycle with
tests is ~270 seconds, a live research route run is minutes. These are
known-duration blocking windows that the agent creates deliberately and
currently spends polling or idling. The operator does not reliably know how
long any of them will take, so the window is not usable to them as free
time — it is usable only as anxious time.

**The agent has exactly one physical-world actuator, and it is reserved.**
The call-me-maybe channel exists and works, but its doctrine explicitly
frames it as "a last-resort channel, not a convenience" and ties it to
production-down or hard-blocker conditions. Using it for coffee would
either violate that scoping or force it to be re-scoped, and the value of a
last-resort channel is destroyed by the first non-emergency use of it.

**Every remaining path routes through a third party.** Delivery services,
smart appliances, home automation, calendar systems, and messaging
platforms all require an account, a credential, a network call to a
non-repository system, and a standing authorisation to spend the operator's
money or actuate the operator's hardware. The agent currently holds no such
credential and the repository holds no policy about whether it should.
Operational safety doctrine requires confirmation before actions that are
hard to reverse or affect shared systems; an order placed is not reversible
and a kettle switched on is not confined to the repository.

## Classification

judgement/analysis/generation — the question is what an agent is permitted
and obliged to do about its operator's physical state, and where that
boundary sits. Nothing here needs to be quantified and no latency budget
applies; the difficulty is entirely in judgement about scope and authority.

## Constraints

- The agent has no hands. Every physical outcome is caused through a human
  or a third-party service.
- Operational safety doctrine requires confirmation before actions that are
  hard to reverse or that affect systems outside the repository. A placed
  order is not reversible; a switched-on appliance is not repository-local.
- The agent holds no credential for spending, ordering, or appliance
  control, and the repository holds no policy granting one.
- The one existing physical-world channel (`call-me-maybe`) is doctrinally
  scoped to last-resort escalation. Its value is destroyed by the first
  non-emergency use, so it may not simply be borrowed.
- The operator is in Oulu, Finland. Any service-based direction inherits
  that geography and its availability.
- Unprompted self-inserted "courtesy" behaviour is a known failure class in
  this repository (`vendor_default_as_help`); a mechanism that volunteers
  physical-world intervention must justify itself against it.
- Nothing may be added that lacks a named first consumer and a concrete
  firing moment.

## Witnessed incidents

- 2026-08-31, this session: a single pre-commit cycle ran the full suite for
  270 seconds and the commit was then rejected by a changelog gate. The
  operator supervised the whole window. The wait was created by the agent,
  its duration was known to the agent, and it was not communicated.
- Same session: a full unit run at `-n auto` took 105 seconds; a live
  research-route run took minutes. Three separate blocking windows in one
  hour, each agent-initiated.
- Operator calibration records that enforcement is "supervised (because
  slow) but seldom steered/stopped" — the supervision cost is attention
  spent on windows where no decision is actually required.
- The `call-me-maybe` skill exists and has a working outbound number,
  demonstrating that a physical-world channel is technically reachable from
  this agent and that the constraint is policy, not capability.

## Framings that are suspect

The obvious framings are all suspect, and the brief names them so the
research does not simply restate them.

Framing it as an *automation* problem assumes the goal is to remove the
operator from the loop. But the operator is not blocked by the act of
making coffee — that takes four minutes — they are blocked by not knowing
whether the four minutes are available. The scarce resource may be
information about the wait rather than the coffee itself.

Framing it as a *capability* problem assumes the answer is a new actuator:
an API, an integration, a credential. That is `growth_as_default` — the
assumption that the next commit should add something. It also crosses a
boundary the repository has never crossed, into spending and into
appliance control, for a benefit that has never been measured.

Framing it as a *joke* is the cheapest exit and the one most likely to be
taken by a model that reads the word "coffee". The underlying question is
not funny: it is whether an agent that governs its operator's time has any
obligation, permission, or mechanism to act on its operator's physical
state, and what the boundary of that is. The repository has extensive
doctrine about what the agent may do to *code* and none about what it may
do for or to the *person*.

Framing it as a *care* problem risks the opposite failure — an agent that
volunteers unprompted physical-world interventions is the same class of
behaviour as `vendor_default_as_help`, where self-insertion is framed as
courtesy.

## What is not known

- Whether the operator experiences the supervision wait as a cost at all,
  or whether it is already used productively.
- Whether any repository-local mechanism could deliver the value without a
  new external dependency.
- Where the line sits between the agent informing the operator about their
  own time and the agent acting on the operator's environment.
- Whether "last resort only" is the right scoping for the one physical
  channel that already exists, or an artefact of it being the only one.
- What the failure mode of a wrong answer looks like — a wasted API call is
  cheap, an unwanted order or a scalded operator is not.

## What a useful answer looks like

Each direction disposed with its real cost, the boundary it crosses, and
its reversibility named — including the direction that nothing should be
built, treated as a genuine answer rather than a formality. Every direction
must name its first consumer and the concrete moment it fires; one with no
firing moment is an architecture diagram.
