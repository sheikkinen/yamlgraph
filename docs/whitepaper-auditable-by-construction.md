# Auditable by Construction

## Per-Run Conformance Evidence Against an Approved Artifact — A Technical Pattern for EU AI Act Record-Keeping, Traceability, and Conformance Evidence in LLM Pipeline Systems

**Whitepaper — 2026-08**
**Status:** draft for review

---

## Abstract

The EU AI Act (Regulation (EU) 2024/1689) requires high-risk AI systems to
automatically record events over their lifetime, to be transparent enough for
deployers to interpret and oversee, and to be documented against an approved
technical design. Current LLM engineering practice answers these requirements
with **observability**: trace trees, span logs, token accounting. This paper
argues that observability is structurally incapable of answering the question
a conformity assessment actually asks — *did this execution stay within the
approved design?* — because in code-authored pipelines there is no approved
design artifact to compare an execution against.

We describe an alternative property, **auditable-by-construction**: the
pipeline's design exists as a declarative, reviewable, versioned artifact;
the design is approved *before* execution through a recorded judgement; every
run emits its decisions in the artifact's own vocabulary; and **control-plane
conformance** is therefore a mechanical diff between the approved artifact
and the run record
— producible per run, at run end, without forensic reconstruction. We present
a reference architecture implementing the property, report an anonymized
production deployment in regulated healthcare that renders a conformance
overlay at the end of every live call, map the mechanism to specific AI Act
articles, and state the property's honest limits: it makes systems
*traceable*, not *explained*.

---

## 1. The Regulator's Question

Every audit of an automated system eventually reduces to one question:

> **"Show me that what the system did is what you approved it to do."**

The question has two halves, and they are not symmetric:

1. *What did the system do?* — an *observability* question.
2. *What was approved?* — a *design governance* question.

Conformance is the intersection: evidence that (1) stayed within (2). An
answer to either half alone is not conformance evidence. A perfect record of
what happened, with no approved design to compare it against, is a diary, not
an audit. A perfectly approved design, with no per-run record in the design's
own terms, is a promise, not an audit.

One scope statement governs everything that follows. What the mechanism in
this paper evidences is **control-plane conformance**: that execution stayed
within the approved routes and topology. It does not evidence that the
content produced within a conforming step was safe, correct, or appropriate
— a run can traverse only approved edges and still produce output that
requires separate content-level controls to assure (§7, note 3). The two
assurances compose; neither substitutes for the other.

Classical software regulation institutionalized a working pattern for the
design half decades ago. IEC 62304 (medical
device software) and ISO 13485 design controls institutionalize **design
transfer**: the design is documented, reviewed, and frozen; verification then
demonstrates that the built and operating system conforms to the frozen
design. The audit trail is design → approval → execution → conformance
evidence, in that order.

LLM systems broke this chain — not because models are stochastic, but
because of an engineering-culture accident: **the design of an LLM pipeline
typically exists only as imperative code.** Prompts are string literals,
routing is `if` statements, the topology is whatever the call graph happens
to be tonight. There is no artifact to approve, so there is nothing to
conform to, so "conformance evidence" degrades into "here are our traces" —
the first half of the question presented as if it answered both.

## 2. What the AI Act Actually Requires

Regulation (EU) 2024/1689 entered into force on 1 August 2024, with staggered
application. Regulation (EU) 2026/1744 (the "Digital Omnibus on AI", 8 July
2026) amended Article 113: the high-risk obligations of Chapter III Sections
1–3 now apply from **2 December 2027** for Article 6(2)/Annex III systems
and from **2 August 2028** for Article 6(1)/Annex I product-embedded
systems. The postponement changes deadlines, not design: the obligations
below are unchanged in substance, and systems being built now will live
their whole production life under them. The obligations relevant
to this paper:

**Article 11 & Annex IV — Technical documentation.** Providers of high-risk
systems must maintain documentation including "the design specifications of
the system," "the general logic of the AI system," and descriptions of what
the system is designed to do and how. The obligation is easiest to satisfy —
and its evidence strongest — when the design *exists as a document* kept up
to date, rather than being reverse-engineered from code on request.

**Article 12 — Record-keeping.** High-risk AI systems "shall technically
allow for the automatic recording of events (logs) over the lifetime of the
system," and the logging must enable identification of situations that may
present risk and facilitate post-market monitoring. Note the phrase
*technically allow*: this is a **system capability requirement**, not an
operations policy. A properly integrated application-level logging subsystem
can satisfy it; framework-level emission provides *stronger and more
uniform* evidence of the capability than application-specific logging that
depends on each implementation remembering to write it.[^1]

**Article 13 — Transparency and provision of information to deployers.**
High-risk systems must be "sufficiently transparent to enable deployers to
interpret a system's output and use it appropriately." The recitals and
guidance around Article 13 speak of *traceability* of the system's
functioning — a system-level property, distinct from model-internal
explainability.

**Article 14 — Human oversight.** Natural persons must be able to
"understand the relevant capacities and limitations" of the system and
"correctly interpret" its output. The mechanism in this paper contributes to
Articles 13–14 by making system-level control flow directly inspectable by
non-authors; it does not by itself establish adequate interpretation of
model-generated content (§7).

**Article 26(6) — Deployer log retention.** Deployers must keep the logs
generated by the high-risk system for a period appropriate to its purpose, at
minimum six months. This creates a *demand side* for Article 12: the logs
must exist in a form a deployer can retain and later produce.

**Articles 72–73 — Post-market monitoring and serious-incident reporting.**
Providers must actively monitor deployed systems and report serious
incidents. Incident analysis of an LLM system without a per-run design-vs-
execution record means reconstructing behavior from raw traces — precisely
the forensic mode these articles are meant to make unnecessary.

Read together, the articles do not prescribe any particular design
representation — no declarative artifact, approval object, or graph diff is
mandated. What they create is a strong engineering incentive for a specific
artifact economy: **an approved design document (Art. 11), automatic per-run
records (Art. 12), records interpretable by non-authors (Arts. 13–14),
retained by deployers (Art. 26), and usable for monitoring and incident
response (Arts. 72–73)** — obligations that become cheap and mechanical
when a machine-comparable relationship exists between documented design and
runtime evidence, and expensive and forensic when it does not. This paper
keeps three layers deliberately distinct: what the Regulation obliges, what
we interpret those obligations to reward as engineering, and what the
mechanism concretely provides. The second and third layers are the authors'
(note 1), not the Regulation's.

## 3. Why Tracing Is Not Conformance

The LLM ecosystem's default answer to Articles 12–13 is a tracing platform:
hierarchical span trees recording every LLM call with inputs, outputs,
latencies, and token counts. These tools are excellent at what they do, and
nothing in this paper argues against deploying them. But three structural
gaps separate a trace tree from conformance evidence:

**Gap 1 — No approved artifact to diff against.** A trace shows the path
taken. It cannot show that the path taken was *within the approved design*,
because in a code-authored pipeline the design is the code, the code changes
continuously, and no frozen, reviewed representation of "the approved routes"
exists. The regulator's question is a set-membership question — *was this
transition in the approved set?* — and a trace tree has no set.

**Gap 2 — Vocabulary mismatch.** Traces speak in spans, function names, and
model identifiers. Design documents (where they exist) speak in states,
decisions, and handoffs. Converting between the two is a manual, per-audit,
error-prone act of interpretation performed by the very engineers whose work
is being audited. Article 13's demand that *deployers* be able to interpret
the record is not met by an artifact only the authoring team can read.

**Gap 3 — Reconstruction instead of emission.** When an incident occurs, the
trace-based workflow is archaeological: pull the traces, correlate the spans,
re-derive what the control flow must have been, compare it by hand against
tribal knowledge of what it *should* have been. Every step of that workflow
is an opportunity for error and dispute. Article 12's "technically allow for
automatic recording" points the other way: the conformance record should be
**emitted by the run itself**, not excavated afterwards.

The distinction in one line: **observability answers "what happened";
conformance answers "did what happened stay within what was approved."** The
second question requires an approval object the first has no concept of.

## 4. Auditable by Construction: Definition

A pipeline system is **auditable by construction** when five properties hold:

**P1 — The design is a declarative artifact.** The pipeline's topology
(nodes, transitions, routing conditions) and its prompts exist as data —
schema-validated, statically lintable without executing application code,
diffable line-by-line, and versioned. Not a serialization dumped from code
(which merely mirrors code and drifts with it), but the *authoring surface
itself*: changing the pipeline means changing the artifact.

**P2 — Approval is a recorded event on the artifact.** Before an artifact
version executes in production, it passes a judgement: a documented review
with acceptance criteria, rendered against the artifact (not against a chat
narrative or a commit message), producing a verdict that is itself versioned.
In practice the judgement gates *changes* — each change request carries its
own review — and deployment pinning binds the running system to a judged
artifact version: the classical design-control pattern of gated change plus
frozen baseline. The artifact-plus-judgement pair is the "approved design"
of Article 11 and the design-transfer input of IEC 62304.[^2]

**P3 — Execution emits decisions in the artifact's vocabulary.** Every
routing decision the running system takes is recorded as a structured event
naming the artifact's own node and edge identifiers — one record per
decision, correlated to a run identity, written automatically by the runtime
(not by application code that might forget). This provides a technical
mechanism addressing Article 12's record-keeping requirement *at the
framework layer*, uniformly, for every pipeline built on it — whether the
record is adequate for a given system remains a function of that system's
purpose and risks.

**P4 — Conformance is a mechanical diff.** Because the design (P1) and the
run record (P3) share a vocabulary, the control-plane conformance check is a
set comparison: overlay the executed transitions on the approved graph. Every
executed transition either exists in the approved artifact or it does not.
The output is renderable as a per-run flowchart — the approved topology with
the actual path highlighted — legible to a deployer, an auditor, or a
clinician, none of whom read code. Deviations are not "anomalies to
investigate"; they are *defects by definition*, detected at run end.[^3]

**P5 — The run record binds itself to the approved version.** P4's diff
proves *executed edge ∈ graph G*; the complete proof chain requires the
record to independently establish *G = approved graph*. Every run record
therefore identifies the exact artifact version — content hash and
approval/judgement reference — so the binding is checked by equality from
the evidence package itself, not inferred from a separate deployment
configuration layer the auditor must additionally trust. The full chain
reads: **design → judgement → identity → execution → conformance**. In the
reference implementation P5 is the one property not yet shipped: today the
binding rests on deployment pinning, and the record-level stamp is a judged,
unimplemented change request (§7).[^5]

Two architectural corollaries make P1–P5 practical for LLM systems:

**Closed routing surface, confined stochastic steps.** Every transition a
run can take is declared in the artifact; within the framework-controlled
routing surface, off-artifact transitions are impossible by construction.
Two boundary statements make that claim honest. First, arbitrary control
flow hidden *inside* node implementations — imperative nodes, agent loops,
dynamically selected tools, retries with side effects — is outside the
claim, and must either be prohibited by the regulated profile or
represented explicitly in the artifact. Second, the property therefore
attaches to a **constrained, enforceable profile** of the framework, not to
the framework wholesale: the regulated profile (§7) admits only declared
transitions over typed state, versioned prompt artifacts, mandatory route
logging, and record-level version binding (P5), and claiming the property
for an artifact means the artifact validates against that profile. Within
the closed surface, two grades of control plane
exist. In the **strong form**, transitions are decided by declared logic
alone — a static transition table, condition expressions over typed state —
with no model in the explanatory path: *"why did the run reach the
escalation state?"* is answerable from the transition table and the event
log, full stop. In the **confined form**, a declared routing step may let
the model select *among the declared edges*: the selection is a typed,
schema-validated output, validated against the closed target set with a
deterministic fallback, so the choice cannot leave the approved set and the
recorded reason for it is the typed output itself. Both grades are
auditable; they are not the same claim, and regulated deployments should
use — as the production pattern in §6 does — the strong form on
safety-relevant paths. In either grade the LLM otherwise operates only
*inside* nodes, as a typed, schema-validated atomic task with a versioned
prompt artifact, its contribution reconstructable from the record (the
exact prompt artifact version, the model configuration, and the recorded
typed output) even though its interior is not explained — and, for
API-backed models, not necessarily *reproducible*, since the provider's
implementation may change beneath a stable identifier (see §7).

**Closed failure surface at authoring time.** Because the artifact is
declarative and schema-bound, the ways an author — human or, increasingly,
LLM agent — can produce an invalid pipeline are *enumerable*, and a static
linter catches them pre-approval with canned remediations: unknown node
types, dangling transitions, unreachable states, references to undeclared
state, missing prompt artifacts. In imperative pipelines the equivalent
defects surface at runtime, in production, as incidents. For an Article 9
risk-management system, an enumerable defect surface with pre-deployment
detection is materially different from an open one.

## 5. Reference Architecture

The property has been implemented on an open-source, self-hosted stack
(declarative YAML graphs compiled onto a state-machine orchestration runtime;
multi-provider LLM access; no mandatory external control plane). The concepts
are stack-independent; the pipeline is:

```
┌──────────────────────────────────────────────────────────────────┐
│ DESIGN TIME                                                      │
│  graph + prompt artifacts (YAML, schema-validated)               │
│    → static lint (topology, reachability, state refs,            │
│      cross-artifact resolution — seconds, no execution, no keys) │
│    → recorded judgement (review artifact, acceptance criteria,   │
│      verdict) — the APPROVAL EVENT                               │
│    → version pinned for deployment                               │
├──────────────────────────────────────────────────────────────────┤
│ RUN TIME                                                         │
│  runtime executes the approved artifact                          │
│    → route log: one structured JSON event per routing decision,  │
│      in artifact vocabulary (node/edge ids), emitted by the      │
│      runtime — on by default in the regulated profile (§7)       │
│    → run identity correlates route log, traces, and outputs      │
│      (OpenTelemetry-compatible)                                  │
├──────────────────────────────────────────────────────────────────┤
│ RUN END                                                          │
│  overlay renderer: approved graph ⊕ route log                    │
│    → per-run conformance flowchart (SVG/PNG/Mermaid)             │
│    → executed path highlighted on approved topology              │
│    → any off-artifact transition = defect, flagged mechanically  │
│    → artifact retained per Art. 26(6)                            │
└──────────────────────────────────────────────────────────────────┘
```

Three properties of the run-time layer deserve emphasis:

- **Uniformity.** The route log is emitted by the framework, below every
  pipeline. No per-application logging code exists to be forgotten, and
  every pipeline in the estate produces evidence in the same format —
  Article 12 as an inherited property. Ordinary artifacts retain explicit
  opt-in; artifacts declaring the shipped regulated evidence profile emit
  to a required per-run sink by default.
- **Self-hosting.** Logs, checkpoints, and overlays are files and databases
  the operator owns. No conformance-relevant record transits a third-party
  platform; data-residency and procurement constraints common in healthcare
  are satisfied by topology, not by contract.
- **Separation from observability.** Trace platforms remain optional and
  complementary; the conformance record does not depend on them. If the
  tracing vendor disappears, the Article 12 record does not.

## 6. Production Pattern (Anonymized)

The architecture is not hypothetical. A production voice-agent deployment in
European regulated healthcare — live telephony, clinical context, its own
formal change-control pipeline of several hundred judged change requests —
operates the full loop today:[^4]

- Pipeline and prompt artifacts are authored declaratively and pass a
  recorded judgement before deployment; the framework version is pinned per
  release.
- The runtime's route-decision hook feeds a per-call event stream,
  correlated by call identifier.
- **At the teardown of every call**, a renderer diffs the call's executed
  path against the approved graph and writes a per-call conformance
  flowchart, guarded by its own regression test.

Two field observations from this deployment generalize:

1. **The evidence layer was pulled by the consumer, not pushed by the
   framework.** The deployment team built the per-call overlay on the
   framework's routing hook because *their* audit obligations demanded it —
   the strongest possible signal that conformance evidence is where
   regulated operators' actual pain lives.
2. **Safety rows become visible.** A late change added a wildcard transition
   (any-state → graceful wrap-up on call-time ceiling). In imperative code
   this class of global safety behavior is invisible until it fires; in the
   artifact it is one reviewable line, present in every subsequent overlay.

## 7. Honest Limits

Claims that overreach invite the audiences best equipped to destroy them.
Three limits are intrinsic and should be stated wherever the property is
claimed:

**Traceable is not explained.** This architecture does *not* provide
model-internal explainability. No attention map, no feature attribution, no
answer to "why did the model produce this token." What it provides: every
stochastic step is confined, typed, schema-validated, and reconstructable
from the record (the exact versioned prompt and the exact typed output are
on record — *reconstructable*, not reproducible: an API-backed model may
not produce the same output later even at fixed parameters), and no
stochastic step can route outside the approved set — where the strong-form
control plane is used, no stochastic step is in the routing path at all.
Under the AI Act this is the right target
— Articles 12–14 demand system-level traceability and interpretability of
*outputs and functioning*, not mechanistic interpretability of weights — but
the words "explainable AI" should never appear in a claim about this
property. Say *traceable*; say *auditable*; do not say *explained*.

**Evidence must be on by default in regulated deployments.** A conformance
capability that is opt-in is a conformance capability that will be found
disabled during the incident that mattered. Regulated deployment profiles
must enable route logging and overlay retention by default, with disabling —
not enabling — as the recorded, justified exception. The profile must also
invert the failure posture: evidence loss must be loud (counted, or fatal in
strict mode), never silently swallowed; each event must carry a timestamp
(Article 12(3) period-of-use recording; Article 73 incident timelines); and
each run record must open with the artifact's content hash and judgement
reference, so the record binds itself to the approved version by equality
instead of relying on deployment state.

The reference implementation now ships that engineering profile: the artifact
must declare a writable route-log directory and judgement reference; each run
writes a content-bound record under its UUIDv7 identity; strict mode fails at
the run boundary on counted evidence loss. This is an evidence-control
mechanism, not a claim of legal compliance, conformity assessment, regulator
acceptance, or sufficient retention policy.

**Uncertainty is not yet surfaced.** The record shows *what* each stochastic
step produced, not how confident the system was. Surfacing calibrated
uncertainty on typed outputs, and routing on it, is the natural next
extension of the artifact vocabulary — and a prerequisite for the stronger
Article 14 claim that overseers can know *when to distrust* the system.

## 8. Adjacent Regimes

The same artifact economy can support evidence obligations under adjacent
regimes:

- **IEC 62304 / ISO 13485 (medical device software).** The pattern extends
  familiar design-control principles into runtime evidence: a reviewed
  design baseline is linked to execution records capable of demonstrating
  control-plane conformity — an analogy and a complementary evidence
  mechanism, not a claim that the standards prescribe or are satisfied by
  per-run overlays.
  Requirement-to-test traceability (each test marked
  with the requirement it witnesses, coverage gated in CI) extends the same
  spine upstream to the specification.
- **GDPR Arts. 13–15 and 22.** Where automated decisions have legal or
  similarly significant effect, the artifact can contribute to providing
  "meaningful information about the logic involved" (Arts. 13(2)(f),
  14(2)(g), 15(1)(h)) *where the routing logic is material to the automated
  decision*, by making workflow-level routing rules and decision points
  inspectable. It does not by itself explain model-level reasoning
  where the consequential judgement happens inside an LLM node, and it does
  not necessarily discharge the transparency obligations on its own.
- **General change control.** Because the artifact is line-diffable, every
  change to system behavior has a minimal reviewable representation — the
  precondition for any change-control regime, regulated or not.

## 9. Adoption Checklist

For a team assessing whether an existing LLM system is auditable by
construction, or specifying a new one:

1. **Artifact.** Does the pipeline's topology and prompt set exist as
   declarative data that is the authoring surface (not a code dump)? Can it
   be schema-validated and linted without executing application code?
2. **Approval.** Is there a recorded judgement, with acceptance criteria,
   rendered against each artifact version before production use? Is the
   approved version pinned in deployment?
3. **Identity.** Does the run record itself identify the executed artifact
   version (content hash) and its approval reference (P5), or must the
   auditor trust a separate configuration layer for the binding?
4. **Emission.** Does the *runtime* (not application code) automatically
   record every routing decision, in the artifact's vocabulary, correlated
   to a run identity?
5. **Diff.** Can a per-run conformance view — executed path over approved
   topology — be produced mechanically at run end? Is it legible to a
   non-author?
6. **Control plane.** Is every transition decided by declared logic over
   typed state, with LLM calls confined to typed, prompt-versioned tasks
   inside nodes?
7. **Defaults.** In regulated profiles, is evidence emission on by default
   and retention aligned with Article 26(6)?
8. **Wording.** Do all claims say *traceable/auditable*, never *explained*?

A system that fails item 1 fails all of them: without the artifact there is
nothing to approve, no vocabulary to emit in, and nothing to diff against.
That is the sense in which the property is *by construction* — it cannot be
retrofitted with tooling onto a code-authored pipeline; it follows from the
decision to make the design a first-class, judgeable artifact.

## 10. Conclusion

The AI Act's record-keeping and transparency articles are widely read as a
logging burden. Taken together, they create a strong engineering incentive
for something more specific: a **machine-comparable relationship between
documented design and runtime evidence** — automatic records that deployers
can interpret, against documentation that reflects the system's actual
logic, usable for monitoring and incident response. The Regulation does not
prescribe how that relationship is established. Auditable-by-construction is
one concrete mechanism for establishing it: declare the
design, judge it, execute it, and let every run testify — mechanically, in
the design's own vocabulary — that it stayed inside the approved lines. The
pattern runs in production, in regulated healthcare, today; every call ends
by drawing its own conformance evidence.

The industry's tracing platforms will tell you what your system did. Only an
approved artifact can tell an auditor what it was *allowed* to do — and only
the diff between the two is conformance.

---

## Implementation Note

The concepts in this paper were not designed on paper and implemented after;
they were extracted from concrete work on **YAMLGraph**, an open-source,
YAML-first pipeline framework (github.com/sheikkinen/yamlgraph, MIT
license), and on a production deployment built with it. The mapping from
the paper's vocabulary to the implementation, for readers who want to
inspect or reproduce the mechanism rather than take it on argument:

| Paper concept | Implementation surface |
|---|---|
| Declarative artifact (P1) | `graph.yaml` + `prompts/*.yaml`, schema-validated |
| Static lint, closed failure surface | `yamlgraph graph lint` |
| Route decision log (P3) | `YAMLGRAPH_ROUTE_LOG` / `observability.route_log` — content-bound run header, timestamped route records, run-end loss count |
| Conformance overlay (P4) | `yamlgraph graph export --overlay <route.jsonl>` — rejects missing or artifact-mismatched headers |
| Run identity correlation | Shared UUIDv7 route/OTel run identity (`yamlgraph[otel]` optional) |
| Version binding (P5) + regulated profile (§7) | `observability.profile: regulated` — required judgement reference and per-run sink; optional strict evidence-loss failure |

The judgement workflow of P2 is the repository's own development process:
every feature enters through a written change request judged against
acceptance criteria before implementation authority is granted — including
the two change requests this paper's §7 identifies as required work. The
framework is cited here for provenance and reproducibility; nothing in the
paper's argument depends on this particular implementation, and §9's
checklist is stated so that any stack can be assessed against it.

---

## Notes and Disclaimers

[^1]: **Regulatory interpretation.** The mapping of the per-run record to
    Article 12 (and the related readings of Articles 11, 13–14, 26, 72–73)
    is the authors' interpretation of the Regulation's text. At the time of
    writing, no notified body, market-surveillance authority, or harmonised
    standard has assessed this specific mechanism. This paper is not legal
    advice; conformity claims for any specific system must be validated with
    qualified counsel under the applicable conformity-assessment procedure.

[^2]: **Approval substance.** The evidentiary strength of the approval event
    is bounded by the competence and independence of the reviewer. Where the
    judgement is machine-assisted, accountability must rest with a named
    natural or legal person; the artifact economy records *that* a review
    occurred and against *what* — it does not by itself certify the
    reviewer's qualification.

[^3]: **Scope of the conformance claim.** The overlay evidences
    *control-plane* conformance: that execution followed approved routes
    through the approved topology. It does not evaluate the content produced
    within a conforming step; content-level quality and safety require
    complementary controls — typed output validation, evaluation suites, and
    human oversight under Article 14 — which this architecture hosts and
    records but does not replace. A run can be fully route-conformant while
    its content requires those separate controls to assure.

[^4]: **Evidence base.** The production pattern describes a single
    deployment, operated within the same engineering practice that produced
    the reference implementation. It demonstrates the pattern's operability
    in live regulated service — not independent third-party adoption, and
    not acceptance of the evidence format by a regulator or auditor. The
    deployment is anonymized stylistically, not contractually, and is
    identified to auditors and prospective customers on request.

[^5]: **Version binding.** The reference implementation's run record carries a
  canonical graph/prompt artifact content hash and optional judgement
  reference. The regulated evidence profile requires the judgement reference,
  so overlay verification checks executed-equals-reviewed binding by hash
  equality rather than inferring it from deployment state. This technical
  binding does not establish legal or regulatory acceptance.

*References: Regulation (EU) 2024/1689 (AI Act), Arts. 9, 11–14, 26, 72–73,
Annexes III–IV, as amended by Regulation (EU) 2026/1744 (application dates,
Art. 113); IEC 62304:2006+A1:2015; ISO 13485:2016; GDPR Arts. 13–15,
22.
Reference implementation: YAMLGraph (see Implementation Note).*
