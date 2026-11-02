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

## Seeds

- **Seed:** Which existing YAMLGraph nodes are already System One shaped?
  A census over `examples/` and production graphs — nodes whose schema is
  pure enum/bool/score with no free-text field — would quantify the
  addressable surface before any provider work is considered.
- **Seed:** Should the graph schema distinguish *decision nodes* from
  *generation nodes*? Even without Jev, the distinction would let the
  linter flag free-text schemas used where an enum would do
  (`plausible_wrong_answer` prevention at spec time).
- **Seed:** If a provider ever returns calibrated confidence, where does it
  live in state? A convention (e.g. `<state_key>_confidence`) would need
  to exist before conditions can branch on it.
