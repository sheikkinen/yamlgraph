# 2026-08-20 — gitclaw as a feature, gitclaw as promo

**Context:** Reflection on FR-827 after enforcement. Not a defect
post-mortem (that entry exists) — a strategic read: what gitclaw *is*
to yamlgraph, beyond one more shipped FR.

## As a feature: the first true external consumer

Every prior validation of yamlgraph lived inside its own repo —
examples/, demos/, tests that import the package from the working
tree. gitclaw is the first artifact that consumes yamlgraph the way a
stranger would: `pip install yamlgraph` on a bare Actions runner, one
graph, four prompts, four small Python tools. Nothing else. The
framework's core claim — 60–80% of an AI workflow definable in YAML —
was finally tested at the product boundary rather than the source
boundary, and it held: the entire plan→judge→enforce→review
orchestrator is one YAML file; Python appears only where the doctrine
says it must (ledger legality, diff containment, slug sanitation —
side effects and invariants, never orchestration).

Consumption from outside also produced the sharpest feedback yamlgraph
has received in one day: the silent-failure semantics of LLM nodes
(exit 0, error only in state) forced the verify-artifacts-not-exit-codes
posture; `--json` proved to be the integration surface that matters;
folded-scalar quoting was the recurring authoring papercut. A
framework learns more from one real tenant than from fifty resident
demos. `does_the_tool_fit_or_merely_exist` — gitclaw answers it with
a named, recurring, external consumer.

## As promo: the repo is the demo

The persuasion mechanics are unusual and worth naming:

1. **Self-demonstrating artifact.** A visitor does not read about the
   pipeline — they file an issue and watch an LLM plan, judge,
   implement, review, and commit working code in five minutes, with
   every verdict and ledger transition inspectable in git history.
   No README paragraph competes with a closed issue that says
   "Implemented in 3d3d559".
2. **Doctrine, miniaturized and portable.** gitclaw is the Chaplain's
   pocket edition: the Scripture's plan-judge-enforce-review arc
   compressed from an FSM runtime into one graph, a JSONL ledger, and
   two workflows — small enough to fork, complete enough to be
   governed. The compression ratio is itself the advertisement, the
   same way 216 lines of Scripture governing 21k lines of Python is.
   What we export is not the code but the constraint system; the code
   is regenerable, and gitclaw *proves* it by regenerating features
   on demand.
3. **Thesis made concrete.** "The primary consumers of software are
   no longer humans" — in gitclaw the human API is a one-line issue;
   everything downstream is agents judging agents. It is the thesis
   as a runnable repo rather than a slide.
4. **Witnessed claims only.** Every README assertion maps to a run ID
   or a commit SHA. Promo built from witnesses inherits the
   credibility of the test suite. The generated aphorism — "The craft
   of software is knowing which cracks are load-bearing" — is more
   quotable than anything we would have written for a landing page,
   and it cost nothing because the product made it.

The honest limits are also promo, stated as limits: Copilot
subscription + provider key required, ~5-minute latency, trust model
deliberately closed to strangers. gitclaw demonstrates *governance of
generation*, not scale — and that is the differentiator worth
advertising, because ungoverned generation is the commodity.

## The trap avoided (barely): demo drift

The risk named by `growth_as_default`: gitclaw could accrete features
until it becomes a second product demanding its own maintenance
budget. Its value is inversely proportional to its size — the moment
it needs a doc site, it stops being a pocket edition. The containment
gate applies to scope, not just diffs: features/ may grow (that is
the product working); tools/ and the graph should approach
frozen.

**Seed:** Promo without a funnel is a diary entry with a URL. The
repo now emits daily outputs — a visible pulse. Should the cron also
maintain a gallery README of latest outputs (cheap, self-updating
storefront)? And AC-05's pending observation doubles as the first
stranger-detector: the day an untrusted issue arrives and is
correctly skipped, we learn both that the gate works *and that
someone found the repo*. What is the cheapest instrument that tells
us a fork actually ran its own first issue?
