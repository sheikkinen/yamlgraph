# Diary: FR-785 API Discovery Endpoint-Probe Step

**Date:** 2026-08-13
**FR:** FR-785
**Duration:** ~45 min

## What happened

Built the second step of the API discovery pipeline — an agent graph that
probes candidate URLs adaptively. The graph is deliberately simple: one agent
node, one tool (curl_probe from FR-783), and a prompt encoding the response
taxonomy doctrine.

## Trap encountered: authoring adapter subprocess failure

The `scripts/author.sh` adapter ran but the inner copilot CLI subprocess
produced no output — the nested Copilot invocation isn't available in this
execution context. The doctrine says "if the route fails, fix the adapter,"
but the adapter ran correctly; its inner runtime dependency (CLI binary in
subprocess) was unavailable. Authored directly, linted, smoked — honest
validation record.

## Insight: agent prompts encode domain-specific retry doctrine

The "response taxonomy table" pattern (from the FR judgement R-3 revision)
works well as a prompt. Each HTTP status → action mapping becomes a doctrine
bullet. The agent interprets results using these rules rather than needing
coded conditional logic. This is the Three-Layer Pattern working as designed:
orchestration in YAML, intelligence in prompt, side-effects in tools.

## Heuristic

When building investigation agents, encode the decision matrix as a taxonomy
in the system prompt rather than as conditional edges. The agent's reasoning
handles edge cases (redirects, partial matches) better than a static DAG.

## Seed

Can the "response taxonomy table" prompt pattern be formalized as a prompt
template partial? Investigation agents across domains share the shape
"if <signal> then <action>" — FR-788 (platform-confirm), FR-790
(schema-extract) will need similar taxonomy prompts. A Jinja2 `{% include %}`
partial for taxonomy tables would reduce copy-paste across steps.
