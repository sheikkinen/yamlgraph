# Diary — 2026-08-28: The alias boundary moves earlier than you plan it, and map→map needs a barrier

## What happened

Planned FR-896 (a cross-repo pattern/model census, map-mercury/reduce)
end-to-end: judged it (via the sole `scripts/judge.sh` route — never in
the authoring session itself, even though "the author" and "the judge"
were the same chat), folded the five required revisions, then enforced
Phase 0/0.5 by authoring `examples/demos/pattern_model_census/` through
the sole `scripts/author.sh` route.

## Trap: the redaction boundary is a moving target, not a fixed phase

The FR designed the alias mechanism (raw repo name → public-safe alias)
as a Phase 4/6 concern — something that guards the *final* synthesized
brief. Building the Phase 0 scope table (a mechanical `gh repo list`
pull) surfaced raw personal-repo names that were themselves Finnish
health/social-service domain project names — exactly the class of
customer/domain-identifying content the alias mechanism exists to keep
out of a public repo. The FR's own committed text was about to leak the
thing it was designed to prevent, one phase before the phase that was
supposed to catch it. Cure applied: alias at the *first* point raw
external names touch a committed public file, not at the point you
originally designed the gate — `R-4`'s spirit generalizes past its
literal placement in the FR text.

## Finding: a shared census graph's model pin is not runtime-configurable

`corpus_census/graph.yaml` hardcodes `provider`/`model` per node.
Reading `yamlgraph/node_factory/llm_nodes.py` confirmed these resolve
from static YAML at compile time — no state/Jinja templating exists for
them. Wanting a different cost tier (`mercury-2` instead of the shared
graph's `claude-haiku-4-5`) is not a `--var` override; it requires
authoring a structurally-parallel sibling graph through the sole
graph-authoring route. Generalizable rule: **a shared pipeline graph
freezes its model pin as part of its contract** — cost-tier
differentiation between consumers means a new graph, not a config flag.

## Seed (mechanical, from the authoring run's own repair log)

The authoring adapter hit and fixed a real YAMLGraph wiring bug worth
carrying forward: chaining two `type: map` nodes directly over the same
upstream collected list (`extract_items → judge_pattern → judge_model`)
fanned the second map out once *per upstream branch* instead of once
over the fully collected list, and LLM map sub-nodes silently reused a
stale `finding` state key across branches unless `skip_if_exists: false`
was set explicitly. The fix was a deterministic barrier node between
each map stage. **Seed:** should `type: map` chaining insert this
barrier automatically (or at least lint-warn when two map nodes are
adjacent with no barrier between them), the way `graph lint` already
catches other map/state pitfalls?
