# Problem brief: consuming calibrated decision models in yamlgraph graphs

**Prior art:** FR-998 (structured-output provider policy,
`yamlgraph/utils/structured_output.py` — one policy surface, no forks);
FR-059 (normalize the provider's type lie at the schema boundary);
FR-464 (structured-output fallback); FR-761 (dependency governance);
FR-767 (graph artifacts authored only via the sole route);
`reference/patterns/corpus-map-reduce.md` (census cost model);
docs/2026-11-02-research-typesafe-system-one-jev.md (committed research
note: vendor claims, examples census, feasibility check).

## Problem statement

A new vendor model class ("System One"; first model Jev, TypeSafe AI)
answers typed questions against a state blob — choose from a list, score
on a rubric, judge a statement true/false — in one parallel call,
returning typed answers with probability distributions and calibrated
confidence. It generates no text. The native model is early-access
gated, but the request/response contract is public and a pip-installable
package (`system-one-adapter`, by the vendor) implements the same
contract backed by OpenAI/Anthropic/Gemini chat LLMs, so the interface
is exercisable today.

yamlgraph cannot consume this model class. There is no way to (a)
express a decision-only question in graph YAML, (b) execute it against a
decision provider rather than a chat model, (c) receive probabilities
and confidence as first-class state values that conditions can branch
on, or (d) verify a provider's calibration claim empirically before any
graph trusts its confidence for routing. Meanwhile the examples corpus
is full of decision-shaped nodes paying chat-LLM latency and cost:
routers, guard classifiers, census map phases, judge verdicts — nearly
all hybrids whose schemas carry self-reported, uncalibrated confidence
integers next to the decision enum.

The question: what is the smallest yamlgraph surface that lets a graph
ask an atomic decision question, branch on calibrated confidence, and
prove the calibration claim empirically first — demonstrated at
hello-demo scale, runnable today without native Jev access?

## Classification

judgement/analysis/generation

## Constraints

- No provider-specific imports in node code; factory-mediated provider
  access only (the `create_llm` precedent).
- The chat call shape (`messages` + schema) and the decision call shape
  (`state` + named questions) differ structurally; whatever bridges them
  must not fork FR-998's single structured-output policy surface into a
  second ad-hoc one.
- Calibration is verified empirically on our own harness before any
  graph branches on confidence (Commandment 9, `read_raw_output_first`);
  vendor evals are not evidence.
- Native Jev access is waitlist-gated: every test and demo must run
  without it — unit tests without network, demos against a non-gated
  backing.
- Any new dependency passes FR-761 governance (constraints artifact,
  pip-audit, direct-import scan).
- Graph and prompt artifacts are authored via the sole route
  (`scripts/author.sh`, FR-767 sentinel); demos must lint and smoke.
- The native model caps choice cardinality at 255; question design in
  examples must respect it.
- Pydantic at every boundary (Commandment 5): decision answers enter
  state typed, never as raw dicts.

## Witnessed incidents

- 2026-11-02 research note (branch `feat/research-typesafe-jev`, commits
  33625aec..54263903): census of `examples/` found the decision-shaped
  corpus — `examples/cost-router` spends a full chat-LLM classifier call
  to decide routing, so the router can cost more than it saves;
  `examples/demos/corpus_census/prompts/judge_item.yaml` hand-rolls an
  abstain protocol with a self-reported integer confidence that has no
  calibration evidence; `examples/demos/hook_classifier` classifies tool
  intent on a 1–5 danger scale for a latency-bounded PreToolUse
  consumer that chat-LLM latency effectively bars from production use.
- 2026-11-02 fetch of <https://docs.typesafe.ai/introduction>: public
  contract — Choice / Score / Noul question types, one request carries
  state plus a dict of named questions, all evaluated in parallel and in
  isolation; answers carry probabilities, some types confidence.
- 2026-11-02 fetch of
  <https://github.com/typesafe-ai/system-one-adapter-python>: public
  `SystemOneAdapterClient.system_one(state, questions)` backed by
  OpenAI/Anthropic/Gemini with structured-output mode, corrective
  retries, and a full attempt debug trail; response is a
  `typesafe_sdk.SystemOneResponse` subclass.
- 2026-09-28 FR-1137 full run (witnessed in
  `feature-requests/research-briefs/fr1140-bare-list-structured-output-brief.md`):
  545 chat-LLM map branches for one classification census — the cost
  shape the decision-model class claims to collapse by two orders of
  magnitude.
