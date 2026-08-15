# Auditable by Construction

## Per-Run Conformance Evidence Against an Approved Artifact — Meeting the EU AI Act's Record-Keeping and Traceability Requirements in LLM Pipeline Systems

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
run emits its decisions in the artifact's own vocabulary; and conformance is
therefore a mechanical diff between the approved artifact and the run record
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

Classical software regulation solved this decades ago. IEC 62304 (medical
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

Regulation (EU) 2024/1689 entered into force on 1 August 2024; the bulk of
high-risk obligations apply from 2 August 2026 (Annex III systems), with
Annex I product-embedded systems following in 2027. The obligations relevant
to this paper:

**Article 11 & Annex IV — Technical documentation.** Providers of high-risk
systems must maintain documentation including "the design specifications of
the system," "the general logic of the AI system," and descriptions of what
the system is designed to do and how. This presumes a design that *exists as
a document* — kept up to date, not reverse-engineered from code on request.

**Article 12 — Record-keeping.** High-risk AI systems "shall technically
allow for the automatic recording of events (logs) over the lifetime of the
system," and the logging must enable identification of situations that may
present risk and facilitate post-market monitoring. Note the phrase
*technically allow*: this is a **system capability requirement**, not an
operations policy. A system whose logging is a bolt-on script does not
technically allow it; a system that emits its run record by construction
does.[^1]

**Article 13 — Transparency and provision of information to deployers.**
High-risk systems must be "sufficiently transparent to enable deployers to
interpret a system's output and use it appropriately." The recitals and
guidance around Article 13 speak of *traceability* of the system's
functioning — a system-level property, distinct from model-internal
explainability.

**Article 14 — Human oversight.** Natural persons must be able to
"understand the relevant capacities and limitations" of the system and
"correctly interpret" its output. Oversight of a pipeline whose routing logic
is opaque code is oversight in name only.

**Article 26(6) — Deployer log retention.** Deployers must keep the logs
generated by the high-risk system for a period appropriate to its purpose, at
minimum six months. This creates a *demand side* for Article 12: the logs
must exist in a form a deployer can retain and later produce.

**Articles 72–73 — Post-market monitoring and serious-incident reporting.**
Providers must actively monitor deployed systems and report serious
incidents. Incident analysis of an LLM system without a per-run design-vs-
execution record means reconstructing behavior from raw traces — precisely
the forensic mode these articles are meant to make unnecessary.

Read together, the articles describe a specific artifact economy: **an
approved design document (Art. 11), automatic per-run records (Art. 12),
records interpretable by non-authors (Arts. 13–14), retained by deployers
(Art. 26), and usable for monitoring and incident response (Arts. 72–73).**

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

A pipeline system is **auditable by construction** when four properties hold:

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
The artifact-plus-judgement pair is the "approved design" of Article 11 and
the design-transfer input of IEC 62304.[^2]

**P3 — Execution emits decisions in the artifact's vocabulary.** Every
routing decision the running system takes is recorded as a structured event
naming the artifact's own node and edge identifiers — one record per
decision, correlated to a run identity, written automatically by the runtime
(not by application code that might forget). This is Article 12 satisfied *by
the framework layer*, uniformly, for every pipeline built on it.

**P4 — Conformance is a mechanical diff.** Because the design (P1) and the
run record (P3) share a vocabulary, the conformance check is a set
comparison: overlay the executed transitions on the approved graph. Every
executed transition either exists in the approved artifact or it does not.
The output is renderable as a per-run flowchart — the approved topology with
the actual path highlighted — legible to a deployer, an auditor, or a
clinician, none of whom read code. Deviations are not "anomalies to
investigate"; they are *defects by definition*, detected at run end.[^3]

Two architectural corollaries make P1–P4 practical for LLM systems:

**Deterministic control plane, confined stochastic steps.** The transitions
between pipeline stages are decided by the declared artifact — a static
transition table, condition expressions over typed state — never by
free-form model output. The LLM operates only *inside* nodes, as a typed,
schema-validated atomic task with a versioned prompt artifact. The
consequence for audit: *"why did the run reach the escalation state?"* is
answerable from the transition table and the event log alone, with no model
in the explanatory path. The model's contribution to any decision is
reproducible (exact prompt version + typed output), even though its interior
is not explained (see §7).

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
│      in artifact vocabulary (node/edge ids), auto-emitted        │
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
  Article 12 as an inherited property.
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
stochastic step is confined, typed, schema-validated, and reproducible (the
exact versioned prompt and the exact typed output are on record), and no
stochastic step controls routing. Under the AI Act this is the right target
— Articles 12–14 demand system-level traceability and interpretability of
*outputs and functioning*, not mechanistic interpretability of weights — but
the words "explainable AI" should never appear in a claim about this
property. Say *traceable*; say *auditable*; do not say *explained*.

**Evidence must be on by default in regulated deployments.** A conformance
capability that is opt-in is a conformance capability that will be found
disabled during the incident that mattered. Regulated deployment profiles
must enable route logging and overlay retention by default, with disabling —
not enabling — as the recorded, justified exception.

**Uncertainty is not yet surfaced.** The record shows *what* each stochastic
step produced, not how confident the system was. Surfacing calibrated
uncertainty on typed outputs, and routing on it, is the natural next
extension of the artifact vocabulary — and a prerequisite for the stronger
Article 14 claim that overseers can know *when to distrust* the system.

## 8. Adjacent Regimes

The same artifact economy discharges obligations beyond the AI Act:

- **IEC 62304 / ISO 13485 (medical device software).** The judged artifact
  is the design output; the per-run overlay is continuous design-transfer
  verification — evidence, on every run, that the operating system conforms
  to the approved design. Requirement-to-test traceability (each test marked
  with the requirement it witnesses, coverage gated in CI) extends the same
  spine upstream to the specification.
- **GDPR Article 22.** Where automated decisions have legal or similarly
  significant effect, the deterministic control plane provides the
  "meaningful information about the logic involved" that a black-box
  pipeline cannot: the logic *is* the artifact.
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
3. **Emission.** Does the *runtime* (not application code) automatically
   record every routing decision, in the artifact's vocabulary, correlated
   to a run identity?
4. **Diff.** Can a per-run conformance view — executed path over approved
   topology — be produced mechanically at run end? Is it legible to a
   non-author?
5. **Control plane.** Is every transition decided by declared logic over
   typed state, with LLM calls confined to typed, prompt-versioned tasks
   inside nodes?
6. **Defaults.** In regulated profiles, is evidence emission on by default
   and retention aligned with Article 26(6)?
7. **Wording.** Do all claims say *traceable/auditable*, never *explained*?

A system that fails item 1 fails all of them: without the artifact there is
nothing to approve, no vocabulary to emit in, and nothing to diff against.
That is the sense in which the property is *by construction* — it cannot be
retrofitted with tooling onto a code-authored pipeline; it follows from the
decision to make the design a first-class, judgeable artifact.

## 10. Conclusion

The AI Act's record-keeping and transparency articles are widely read as a
logging burden. They are better read as a **design-artifact requirement in
disguise**: automatic records that deployers can interpret, against
documentation that reflects the system's actual logic, usable for monitoring
and incident response — none of it is satisfiable at reasonable cost unless
the system's design exists as an approved, machine-comparable artifact and
the runtime emits its decisions in that artifact's terms.

Auditable-by-construction is that reading made operational: declare the
design, judge it, execute it, and let every run testify — mechanically, in
the design's own vocabulary — that it stayed inside the approved lines. The
pattern runs in production, in regulated healthcare, today; every call ends
by drawing its own conformance evidence.

The industry's tracing platforms will tell you what your system did. Only an
approved artifact can tell an auditor what it was *allowed* to do — and only
the diff between the two is conformance.

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
    not acceptance of the evidence format by a regulator or auditor.

*References: Regulation (EU) 2024/1689 (AI Act), Arts. 9, 11–14, 26, 72–73,
Annexes III–IV; IEC 62304:2006+A1:2015; ISO 13485:2016; GDPR Art. 22.
Reference implementation: open-source YAML-first pipeline framework with
static graph lint, route-decision logging, run-identity correlation
(OpenTelemetry), and authored-vs-executed overlay export.*
