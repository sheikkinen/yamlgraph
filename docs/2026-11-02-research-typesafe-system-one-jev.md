# Research: TypeSafe AI "System One Models" & Jev — Structured-Decision Models

**Date:** 2026-11-02
**Status:** Research note (no FR attached; seeds at the end)
**Method:** Primary source fetched 2026-11-02 —
<https://typesafe.ai/blog/introducing-system-one-models-and-jev>
(published 2026-09-15, author Diogo Almeida, founder, ex-OpenAI RLHF).
Vendor claims are reported as claims; nothing here is independently
measured. Early-access product — API not yet publicly verifiable.

## Question

TypeSafe AI announces a new model class ("System One Models") and a first
model ("Jev") that gives up free-text generation entirely in exchange for
typed, calibrated, parallel-sampled structured decisions. What is it, how
credible are the claims, and what does it mean for YAMLGraph — a framework
whose whole premise is LLM nodes constrained by Pydantic schemas?

## Answer in one paragraph

Jev is positioned as a "frontier-intelligence function call": unstructured
state in, type-safe probabilistic decisions out — no string generation at
all, so type errors are impossible by construction and every answer carries
a calibrated probability. Claimed economics are dramatic: $0.042/MTok input,
free output tokens, 70–500 ms end-to-end (vendor headline: ~194x faster,
~445x cheaper than LLM workflows). The declared use cases — smart
if-statements, classify/route/score/extract, map-reduce over large corpora,
judging/verifying LLM outputs — overlap almost exactly with what YAMLGraph's
schema-constrained LLM nodes, map nodes, and judge graphs do today. If the
claims hold, this is a candidate *provider class* (decision provider, not
chat provider) that would slot under existing `schema:` nodes; it is not a
replacement for generation nodes, since Jev cannot produce strings.

## What they built (vendor description)

- **Model class:** "System One Models" (after Kahneman's fast/intuitive
  System 1) — frontier models for fast, structured decisions consumed
  directly by software.
- **Training method:** "Reinforcement Learning for Calibrated Decisions"
  (RLCD) — optimizes for epistemically honest probabilities rather than
  human preference (RLHF) or verifiable rewards (RLVR).
- **Sampling:** parallel, not autoregressive — all outputs of a query are
  produced in a single pass; output tokens are free ("too cheap to meter").
- **Contract:** output space is declared in advance (schema/enumerated
  decisions, cardinality up to 255 per choice; higher cardinality handled
  by a two-stage score-then-choose system). The model "never makes type
  errors" — guaranteed by construction (schema matching, not an empirical
  0%).
- **Confidence:** every output carries a calibrated probability; vendor
  claims higher confidence correlates with higher accuracy and that similar
  inputs yield similar answers (consistency).
- **First model:** Jev (after William Stanley Jevons — the Jevons-paradox
  bet: each order-of-magnitude cost drop unlocks orders of magnitude more
  use cases). Early access only as of the post.

## Claimed numbers

| Axis | Existing LLMs (vendor's framing) | Jev (vendor claim) |
|------|----------------------------------|--------------------|
| Input cost | $0.20–$10 / MTok | $0.042 / MTok |
| Output cost | ~5x input | Free |
| Latency | 3–329 s end-to-end (frontier) | 70–500 ms |
| Speedup | — | 40x–200x at comparable intelligence; 193.6x headline |
| Type errors | nonzero, always | 0% by construction |
| Confidence | overconfident, inconsistent | calibrated, consistent |

## Evidence quality (their own nuance sections, summarized)

The post is unusually candid about its evidence limits:

- **Workflow evals** (<https://evals.typesafe.ai/>): a fixed compute graph
  ("workflow" represented in code) is run across models; the reference
  answer is the *average of GPT-6 Astra and Fable 5.1 predictions*, not
  ground truth. This biases toward OpenAI/Anthropic agreement and is a
  consensus benchmark, not correctness.
- Workflows were authored by TypeSafe's own capabilities team — admitted
  possible bias despite "not deliberately constructed to look good".
- LLM baselines run through TypeSafe's own `system-one-adapter-python`
  wrapper (<https://github.com/typesafe-ai/system-one-adapter-python>),
  which they note is slower/costlier than unconstrained decisions.
- Hallucination comparison numbers come from OpenRouter aggregate data —
  routing bias acknowledged.
- Pricing sustainability explicitly unproven ("can't prove it isn't
  subsidized").
- The side-by-side demo input was chosen to flatter parallel sampling
  (short dense input, readable keys).
- Comparison target: GPT-5.6 Terra at default reasoning, which they found
  most comparable in intelligence to Jev on System One tasks.

Credibility read: the mechanism claims (parallel sampling, schema-guaranteed
outputs, latency, pricing) are cheap to verify once access exists; the
*intelligence-parity* claim rests on a consensus-against-frontier-LLMs
methodology that cannot distinguish "as smart as" from "agrees with".

## Demos (what the shape of the product is)

- **Doom bot:** 10 decisions/second against structured game state (text,
  not pixels) at ~$7/hour — real-time inference in a control loop.
- **Wikiracing:** high-cardinality link choice (hundreds–thousands of
  options per step); showcases compounding value of non-hallucinated
  choices; smaller speedups vs non-reasoning LLM modes.

Both demos are *decision loops embedded in ordinary code* — exactly the
"logic layer" position YAMLGraph assigns to YAML graphs.

## What this means for YAMLGraph (the analysis, not the inventory)

1. **Same thesis, different layer.** YAMLGraph's premise is that LLM calls
   become reliable when constrained by schemas at the boundary
   (Commandment 5; `schema:` in prompt YAML). TypeSafe pushes the same
   normalization *into the model*: the schema is the output space, so the
   boundary validation becomes a no-op. This is `the_one_law` implemented
   in weights instead of Pydantic.
2. **Candidate provider class, not provider.** Jev cannot generate strings,
   so it can never back a generation node. It maps to a hypothetical
   *decision node*: nodes whose schema is pure enums/bools/scores
   (classify, route, judge verdicts, map-phase scoring). Today those run
   on chat LLMs via `create_llm()` + structured output — the expensive,
   slow path TypeSafe is attacking.
3. **Corpus map-reduce is their declared sweet spot.** "Map-reducing over
   big data" at $0.042/MTok with free output is 1–2 orders of magnitude
   below the cheap-map pricing assumed in corpus-map-reduce cost estimates
   (`reference/patterns/corpus-map-reduce.md`). If real, the
   census-affordability threshold (`map_reduce_the_corpus`) drops to
   near-zero for classification-shaped map phases.
4. **Calibrated probabilities are a new primitive.** YAMLGraph judges emit
   discrete verdicts; the post argues reliable workflows branch on
   *probabilities* with domain-specific thresholds. That is expressible
   today in graph condition logic, but no current provider returns
   trustworthy confidence. A calibrated score would let judge graphs
   encode "escalate below 0.9" instead of binary verdicts — directly
   relevant to the `two_strike_split` / `threshold_encodes_forecast`
   lessons.
5. **Guardrails/verification as a use case** ("verify everything: score,
   judge, guardrail, detect jailbreaks") overlaps with the judge-fr and
   review-pr pipelines — though those judge *prose artifacts* against
   doctrine, which needs reading comprehension plus generation of a
   rationale; only the verdict extraction is System One shaped.
6. **Caution flags.** Early access; no public API; intelligence parity
   unproven (consensus benchmark); 255-cardinality cap per choice; no
   image/multimodal input yet; a two-model architecture (LLM composes,
   Jev decides) adds integration surface. Per `vendor_default_as_help` and
   `model_as_trusted_peer`, any future adoption in enforcement pipelines
   (judges, gates) would require adversarial review regardless of the
   no-hallucination claim — calibrated ≠ aligned.

## Census: System One–shaped nodes in `examples/` (2026-11-02 reflection)

First Seed answered by a quick scan (grep for `enum:`, `type: bool`,
`condition`-routing graphs; schemas read for ~10 representative examples).

**Headline finding: pure System One nodes are rare — hybrids dominate.**
Nearly every decision-shaped schema pairs its enum/bool/score with a
free-text `reasoning` or `evidence_span` field. That is deliberate doctrine
(`read_raw_output_first`, auditability, verbatim-quote evidence in
`cwe-classifier`), but it means few nodes could move to Jev wholesale. The
reasoning field is partly a *poor man's calibration* — it exists so humans
can inspect decision quality. A provider with genuinely calibrated
confidence changes the economics: justify lazily, only when confidence is
low or the decision is contested, instead of generating a rationale on
every call.

### Candidate inventory (by fit)

| Example | Decision shape | Jev fit |
|---------|---------------|---------|
| `cost-router` (`classify_complexity`) | enum {simple, medium, complex} | **Pure.** The router call itself costs an LLM round-trip — self-defeating today. A ~100 ms near-free router is the canonical "smart if-statement". |
| `fsm-router`, `demos/router`, `demos/promptfoo-router`, `demos/router-race-candidates`, `demos/salvage_classify` | route enums | **Pure** (reasoning field droppable). Same routing family. |
| `demos/hook_classifier` (`classify-tool-intent`) | intent enum + danger 1–5 + category enum | **Pure + latency-critical.** A PreToolUse hook adding seconds per tool call is unusable; 70–500 ms makes real-time hook classification viable. TypeSafe's "guardrail / detect jailbreaks" case verbatim. |
| `demos/safety-guards`, `demos/enforcer` | bool gates | Pure. Same guardrail family. |
| `demos/corpus_census` (`judge_item`) + census family (`session-shapes`, `cap_journey_census`, `pattern_model_census`, `person_profile_census`) | rubric enum + confidence + abstain + evidence_span | **Hybrid.** Judgement/confidence/abstain are Jev-shaped (calibrated abstain is *better* than self-reported `confidence: int`); `evidence_span` is string extraction Jev cannot do. Map phase would split: Jev judges, LLM extracts evidence only for non-abstained or low-confidence rows. |
| `cwe-classifier` (`reason_cluster`) | match/partial_match per weakness in cluster | **Hybrid, high-cardinality.** Cluster-of-weaknesses choice mirrors the Wikiracing demo (score-then-choose); verbatim-quote evidence stays with an LLM. |
| `demos/judge` (`JudgeVerdict`) | APPROVE/AMEND + per-criterion `passed: bool` | **Partial.** Verdict and criteria bools are System One shaped; the rationale is the product. Also the one place `model_as_trusted_peer` bars silent substitution. |
| `npc` (`encounter_decide`, `npc_behavior`), `dungeon_master` (`turn_direct`) | in-game decisions, bools | **Pure + real-time.** The Doom-demo analog: structured game state in, decision out, 10/sec affordable. |
| `booking`, `questionnaire` | branch-on-extracted-state | Hybrid (extraction is generative; branching decision is not). |

### Proposed Jev use cases, ranked

1. **Model/cost routing** (`cost-router` shape). Today the classifier can
   cost more than the saving it enables; a two-orders-cheaper router makes
   tiered routing default-on for every graph. First candidate for a
   `decision provider` behind `create_llm()`.
2. **Real-time guardrails** (`hook_classifier`, `safety-guards`,
   `enforcer`). The PreToolUse hook budget is milliseconds, which is why
   today's hooks are regex/shell; a calibrated intent classifier at 100 ms
   would upgrade them without the latency tax. Caveat: an enforcement
   surface — adversarial review applies (`model_as_trusted_peer`).
3. **Census map phases** (corpus-map-reduce family). The biggest cost
   lever: N-item map phases are classification-shaped, and calibrated
   abstain directly replaces the hand-rolled abstain/confidence protocol
   in `judge_item`. Evidence spans force a hybrid map (judge cheap,
   extract selectively).
4. **High-cardinality coding** (`cwe-classifier`). Cluster verdicts are
   repeated bounded choices over hundreds of codes — the exact shape the
   vendor's two-stage scoring targets.
5. **Judge/review verdict extraction only.** Keep the LLM rationale;
   let a calibrated verdict flag "the judge is unsure" — turning
   `threshold_encodes_forecast` ambiguity into a measurable signal rather
   than a forecast.
6. **Interactive/game loops** (`npc`, `dungeon_master`). Decisions per
   second instead of per scene; generation nodes stay LLM.

### Reflection

The census confirms the provider-class framing: Jev would not replace any
node; it would split the hybrid nodes this repo already writes. The
doctrine-relevant insight is that YAMLGraph's ubiquitous `reasoning` field
conflates two needs — decision quality and audit trail — that calibration
decouples. Whether to decouple is an FR-sized question, not a research
note's.

## Proposed Jev-native samples

The census above covers retrofits. These are *native* samples — each is
pointless on a chat LLM and exists only because of a System One property
(parallel sampling, calibrated probability, free output, ~100 ms latency).
Proposals only: building any of them goes through the graph-authoring
route (`scripts/author.sh`), and since Jev is early-access, each would
ship against a **mock decision provider** (same pattern as the existing
mock-LLM test fixtures: fixed decisions + synthetic confidence), so the
graphs run today and swap in a real provider later.

1. **`demos/smart-if`** — the hello-world. One decision node as a fuzzy
   if-statement in ordinary control flow: classify an inbound message,
   branch on the enum. Property demoed: decision-as-function-call; the
   whole graph is `decide → branch → act`, no prompt engineering, no
   parsing. The decision-provider analog of `demos/hello`.
2. **`demos/confidence-ladder`** — branch on *probability*, not verdict.
   High confidence → auto-act; mid → cheap LLM generates a justification;
   low → `interrupt` to a human. Property demoed: calibration as a routing
   signal — the lazy-justification Seed made runnable, composing the
   existing interrupt/human-in-loop machinery.
3. **`demos/parallel-intake`** — the side-by-side-demo shape: one state
   blob (support ticket), N independent questions (urgency, sentiment,
   category, churn risk, language, PII present) answered in a *single
   parallel query*. Property demoed: free output tokens kill the
   question-per-call economics; today this is either one brittle mega-
   schema call or N calls.
4. **`demos/stream-gate`** — real-time guardrail: score every chunk of a
   streaming LLM output (or every tool call) at 10 decisions/sec; trip a
   circuit breaker on a hostile score. Property demoed: latency — the
   gate is faster than the stream it guards, which no chat-LLM judge can
   claim. Builds on `hook_classifier` and the streaming layer.
5. **`demos/calibration-audit`** — the skeptic's sample, most repo-native.
   Run N labeled decisions, bucket by reported confidence, emit a
   reliability table (confidence vs observed accuracy). Property demoed:
   *testing the vendor's central claim* instead of trusting it
   (`read_raw_output_first`, Commandment 9). This graph is the acceptance
   gate any real decision provider must pass before use cases 1–4 are
   allowed to trust confidence; against the mock provider it demos the
   harness with planted miscalibration.
6. **`demos/reflex-npc`** — the Doom analog on existing assets: the `npc`
   encounter loop re-timed to a decision per game tick instead of per
   scene, generation reserved for dialogue only. Property demoed:
   interactive-rate intelligence in a control loop (~$7/hr at 10/sec per
   vendor pricing).
7. **`demos/census-ab`** — side-by-side census map: the same
   `corpus_census` rubric run with (a) chat-LLM structured output and
   (b) the decision provider, reducing to one cost/latency/agreement
   table. Property demoed: the map-reduce economics claim, measured on
   this repo's own census harness rather than vendor evals.

Suggested order: 5 before everything (the gate), then 1–2 (primitives),
then 3–4 (native shapes), 6–7 (showcases). Each sample is also the witness
for one claim in the vendor table above — the suite doubles as our
independent verification checklist once API access exists.

## Integration feasibility (checked 2026-11-02)

Follow-up check of <https://docs.typesafe.ai/introduction> and
<https://github.com/typesafe-ai/system-one-adapter-python> — both public,
updating the "API not publicly verifiable" caveat above:

- **Public API surface.** Three primitives: **Choice** (pick from list →
  `choice` + probabilities + confidence), **Score** (rubric score +
  probabilities + confidence), **Noul** (is this statement true? → 0–1).
  One call = `state` (text/JSON) + a dict of named questions, all evaluated
  in parallel and in isolation; adding questions barely changes latency and
  avoids context-rot. Doctrine-adjacent guidance: decompose into atomic
  questions, combine with code ("change a coefficient, not a prompt").
- **Public adapter = usable today without Jev access.** The
  `system-one-adapter` package implements the same `system_one(state,
  questions)` call and `SystemOneResponse` shape backed by
  OpenAI/Anthropic/Gemini (structured-output mode, corrective retries,
  full attempt debug trail). It exists so people can benchmark LLMs vs
  Jev — which makes it a *better* mock than a hand-rolled one: a real,
  provider-agnostic reference implementation of the interface.
- **Jev itself remains access-gated** (waitlist/early access): pricing,
  latency, and calibration claims still unverifiable first-hand.

**Feasibility verdict:** integrating *Jev the model* — not feasible now
(no API key without early access). Integrating the *System One interface*
— feasible now: build the decision-node primitive against the public
adapter, run `demos/calibration-audit` against it, and the eventual Jev
adoption becomes a client swap. The schema mapping is clean: `enum` field
→ Choice, `bool` field → Noul, bounded `int` → Score; free-text fields
stay on the LLM path (the hybrid split above). The real integration cost
is architectural, not vendor-side: YAMLGraph nodes assume a chat-model
call shape (`messages` + schema via `create_llm()`), while System One is
`state` + questions — a new node/provider class, not a provider swap.
Dependency additions go through FR-761 governance; the work is FR-sized.

## Seeds

- **Seed:** Can a hybrid node be split declaratively — one schema, decision
  fields routed to a decision provider and justification fields generated
  lazily (only below a confidence threshold)? That would adopt calibration
  without surrendering the audit trail.
- **Seed:** Should the graph schema distinguish *decision nodes* from
  *generation nodes*? Even without Jev, the distinction would let the
  linter flag free-text schemas used where an enum would do
  (`plausible_wrong_answer` prevention at spec time).
- **Seed:** If a provider ever returns calibrated confidence, where does it
  live in state? A convention (e.g. `<state_key>_confidence`) would need
  to exist before conditions can branch on it.
