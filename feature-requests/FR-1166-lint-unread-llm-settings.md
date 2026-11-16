# Feature Request: FR-1166 Lint LLM settings written where yamlgraph never reads them

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Requested:** 2026-11-16
**First consumer / first event:** csap (customer-service-agent-platform). After
this FR, the first `yamlgraph graph lint` run on `graphs/flex_navigator/graph_v2.yaml`
reports that the graph's `thinking_budget: 0` sits in `metadata:`, which
nothing reads, and names `defaults.thinking_budget` as the fix. The same
finding appears for each of the 14 prompt files. Today that lint run prints
26 warnings and none of them is this one.
**Research:** [FR-1166.research.md](FR-1166.research.md)
(brief: `research-briefs/lint-unread-llm-keys.md`)
**Prior art:** [FR-1144](FR-1144-race-node-thinking-budget.md) made race
nodes read `thinking_budget` and recorded csap's `metadata:` placement only
as a prose follow-up; its judgement (C-4, C-6) forbade linter changes and
asked for this separate FR. [FR-1165](FR-1165-config-max-tokens-refused.md)
refused an unapplied key at load. That key, `config.max_tokens`, was a
framework-owned key documented as working. Graph and prompt `metadata:` are
user-owned free-form blocks, so this FR warns instead of refusing (see
Alternatives). FR-071 / FR-230 own the W071 family, which inspects only
`defaults:` and node configs; this FR adds new codes and leaves W071 alone.
FR-232 / FR-272 define race and router-race `candidates` as `{provider, model}`.
Retrieval hits FR-1124, FR-1050, FR-1073 and FR-1122 share only the nouns
`lint`, `llm` and `keys` and are dismissed.

## Summary

yamlgraph reads LLM settings (`thinking_budget`, `temperature`, `max_tokens`,
`effort`) only from a node and from graph `defaults:`. A prompt file
contributes only its top-level `provider` and `model`. A setting written in
graph `metadata:`, prompt `metadata:`, or as an extra key on a race candidate
loads cleanly, passes lint, and does nothing. Add lint warnings for these
three placements, driven by one list of setting names that the runtime
resolution also uses.

## Value Statement

Graph authors who put an LLM setting in a place yamlgraph never reads find
out when they lint, not weeks later from a latency chart.

## Problem

- **csap, every file.** At csap `a60fb2b9` (2026-11-16), all 18 YAML files that
  set `thinking_budget` set it under `metadata:`. That is 4 graphs
  (`flex_navigator/graph.yaml`, `flex_navigator/graph_v2.yaml`,
  `post_call/graph.yaml`, `persona_judge/graph.yaml`) and 14 prompts. None set
  it under `defaults:`.
- **The runtime never sees it.** On yamlgraph `ad5db794`, loading the
  flex_navigator and post_call graphs gives `defaults.thinking_budget = None`,
  while the raw YAML has `metadata = {'thinking_budget': 0}`.
- **Lint passes.** `yamlgraph graph lint graphs/post_call/graph.yaml` reports
  "No issues found". `graph_v2.yaml` reports 26 warnings (W002, W012×12, W017,
  W022, W803×14, W804×2), none about `thinking_budget` or `metadata`.
- **The cost.** All 12 csap LLM nodes are race nodes between Vertex
  `gemini-2.5-flash` and Azure `aaa-gpt-5.4-mini`. Gemini runs with its default
  thinking, and Azure wins about 95% of races (operator report, 2026-11-16).
  That report blamed the 0.5.25 race node alone (fixed by FR-1144 in v0.6.3)
  and missed the `metadata:` placement. Upgrading yamlgraph alone would leave
  Gemini thinking.
- **The prose note failed.** FR-1144 named this placement on 2026-09-30.
  Seven weeks later all 18 files are unchanged. A note in an FR body reaches no
  author at write time; a lint finding does.
- **Race candidates drop extra keys.** `_build_candidate_llms` passes only
  `candidate.get("provider")` and `candidate.get("model")` to `create_llm`.
  Schema validation (`yamlgraph/models/node_schema.py`) checks only that one
  of those two is present, so `{provider: vertex, model: x, thinking_budget: 0}`
  is accepted and the third key is discarded. The same operator report
  considered exactly this form as a workaround.

## Ideal Result

Every LLM setting a graph author writes is either applied or reported by
`yamlgraph graph lint` with its location and the place it should go. The list
of setting names exists once, and the lint check and node-level resolution
both use it, so a new setting (as `effort` was in FR-1151) is covered without
editing the linter. `metadata:` stays free-form for every key that is not an
LLM setting.

## Planned Operations

```yaml
probes:
  - "grep every node_config.get / defaults.get of an LLM setting in yamlgraph/node_factory/ — the union decides the setting list; a setting read in only one node type is listed with that scope"
  - "lint-imports with the linter importing the new constant's module — a contract violation moves the constant to a module both layers may import"
  - "read yamlgraph/linter/checks_prompts.py prompt discovery — decides whether prompt metadata is reachable from lint_graph or needs prompt-file lint"
  - "yamlgraph graph lint on every graph under examples/ and graphs/ before and after — any new W072/W073 finding in a shipped example is a real defect to list, not to suppress"
  - "yamlgraph graph lint on the 3 csap graphs read-only — must show the new findings (csap is not edited)"
branches:
  - "a shipped example carries a metadata LLM setting → fix it in this FR's PR as a witness, through scripts/author.sh (governed graph path)"
  - "prompt metadata not reachable from lint_graph → cover graph metadata and candidates only; prompt metadata returns as its own FR"
  - "judge prefers load refusal for candidate extra keys (FR-1165 shape) → W073 becomes a schema error; metadata stays a warning"
delegations:
  - "research.sh: 4 runs (3 reducer rejections, 1 accepted)"
  - "judge.sh: 1 run, 2 if revisions are disputed"
  - "author.sh: 1 run only if the shipped-example branch fires"
waits:
  - "judge"
commands:
  - scripts/research.sh feature-requests/research-briefs/lint-unread-llm-keys.md
  - scripts/judge.sh feature-requests/FR-1166-lint-unread-llm-settings.md
  - yamlgraph graph lint
  - lint-imports
  - pytest tests/unit/ -q --no-cov -m "not slow" -n auto
  - python scripts/req_coverage.py --strict
```

## Proposed Solution

1. **One list.** Add a module-level constant naming the node-level LLM
   settings (initially `thinking_budget`, `temperature`, `max_tokens`,
   `effort`) next to the node-level resolution in `yamlgraph/node_factory/`.
   `llm_nodes.py` and `race_node.py` use it where they resolve node-then-defaults,
   and the linter imports it. Where the constant lives is set by the
   `lint-imports` probe.
2. **W072 — LLM setting in `metadata:`.** Flag any key from that list found in
   graph `metadata:` or in a referenced prompt file's `metadata:`. Other
   `metadata:` keys stay silent.
   ```
   W072 graph metadata: thinking_budget is not read from metadata
        fix: move it to defaults.thinking_budget (or onto the node)
   ```
3. **W073 — unread key on a race candidate.** Flag any key other than
   `provider` or `model` on a `race` or router-race candidate.
   ```
   W073 node 'classify': candidate 0 key 'thinking_budget' is ignored
        fix: race candidates take only provider and model; set
        thinking_budget on the node or under defaults
   ```
4. **Docs.** Add W072/W073 to the lint-code reference. In `reference/graph-yaml.md`,
   add one line saying `metadata:` is not read for LLM settings.

No runtime behaviour changes, and nothing starts reading `metadata:`
(FR-1144 rejected that).

## Acceptance Criteria

- [ ] `yamlgraph graph lint` emits W072 for an LLM-setting key in graph
      `metadata:` and its message names `defaults.<key>`. Witness test.
- [ ] W072 fires for the same key in a referenced prompt's `metadata:`, unless
      the prompt-reachability branch fires (then recorded as deferred).
- [ ] W072 stays silent for non-setting keys in `metadata:` (e.g. `owner`,
      `description`), and for top-level prompt `provider` / `model`. Witness test.
- [ ] W073 fires for an extra key on a `race` candidate and on a router-race
      candidate, and stays silent for `{provider, model}`. Witness tests.
- [ ] The setting list exists once. A test asserts that each listed name is
      resolved by `llm_nodes.py`, so a rename breaks the test, not the lint.
- [ ] `lint-imports` passes.
- [ ] Every graph under `examples/` and `graphs/` is linted. Any new
      W072/W073 is listed in this FR as fixed or dispositioned.
- [ ] Read-only lint of csap's `flex_navigator/graph_v2.yaml` shows W072,
      recorded in Implementation Status.
- [ ] New REQ ID in `ARCHITECTURE.md`; tests carry `@pytest.mark.req`;
      `python scripts/req_coverage.py --strict` passes.
- [ ] Changelog fragment in `changelog/unreleased/`.

## Alternatives Considered

Research rows from [FR-1166.research.md](FR-1166.research.md):

| Row | Disposition |
|---|---|
| os-infra: allowlist constant shared with the factory | **Adopted** as step 1. The constant sits next to the node-level resolution rather than in `llm_factory.py`, because `create_llm` also takes `provider` / `model`, which prompts legitimately supply. |
| data-process: canonical settings registry | **Adopted**; same as above. Its proposed codes W027/E028 are not taken: these warnings belong beside the W071 provider-settings family. |
| yamlgraph-native: introspect `llm_factory.py` / `race_node.py` at lint time | **Rejected.** Introspecting source at lint time is fragile, and a shared constant gets the same freedom from drift. |
| subtractionist: keep `metadata:` uninspected; migrate csap only | **Rejected.** That migration was named in FR-1144's prose seven weeks ago and has not happened in any of the 18 files. With no check, the next project repeats it. |
| librarian: actionlint-style unknown-key-by-location schema | **Partly adopted.** It is the right pattern for candidates (W073 flags every key outside `{provider, model}`). Not adopted for `metadata:`, which is user-owned, so only listed setting names are flagged there. |

Not from research:

- **Refuse at load (FR-1165 shape).** Right for framework-owned keys; wrong
  for `metadata:`, where it would stop csap loading the day it upgrades instead
  of telling the author. For candidates, this is a judge question (see below).
- **Read `thinking_budget` from `metadata:`.** Rejected by FR-1144 as a
  separate framework-wide change, and it would make `metadata:` a second
  config block.

## Questions for the judge

- **W073 severity:** keep it a lint warning, or make candidate extra keys a
  schema error at load (FR-1165 shape)? Candidates are framework-owned, which
  favours an error. A csap search found no candidate with extra keys today, so
  an error would break no known graph. Recommended default: warning, the
  smaller change.

## Out of Scope

- csap migration of the 18 files and the pin bump (csap-side work).
- Per-candidate LLM settings (FR-1144 C-6; a separate FR if wanted).
- `reasoning_effort` for Azure/OpenAI and `thinking_level` for Gemini 3.x.

## Related

- `yamlgraph/node_factory/race_node.py:189` (`_build_candidate_llms`), `:347`
  (budget resolution)
- `yamlgraph/linter/checks_providers.py` (W071 family; same check scope)
- `yamlgraph/models/node_schema.py:384` (race candidate validation)
- `yamlgraph/executor_base.py` (`_resolve_provider_and_model`: prompt
  top-level `provider`/`model` only)
