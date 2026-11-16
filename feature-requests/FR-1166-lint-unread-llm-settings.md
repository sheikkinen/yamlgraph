# Feature Request: FR-1166 Lint LLM settings written where yamlgraph never reads them

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS 2026-11-16
([judgement](FR-1166-lint-unread-llm-settings.judgement.md)); R-1..R-5 folded
(see [Judgement fold](#judgement-fold-2026-11-16))
**Capability:** CAP-305 / REQ-YG-730
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

The four tuning settings `thinking_budget`, `temperature`, `max_tokens` and
`effort` produce a `yamlgraph graph lint` warning when written in graph
`metadata:` or in the `metadata:` of a prompt a node references. Any key other
than `provider` / `model` on a `race` or router-race candidate does too. Each
warning names its location and a fix that is true for that key on that path.
The setting names are declared once, in `yamlgraph/constants.py`; the lint
check and the regular-LLM and direct-race resolution sites read them from
there. `metadata:` stays free-form for every other key. (Narrowed by R-2: this
FR does not promise that every written setting is applied or diagnosed
everywhere.)

## Planned Operations

```yaml
probes:
  - "lint-imports after adding LLMSetting to yamlgraph/constants.py and importing it from yamlgraph/linter — must pass with no contract edit (R-3)"
  - "wc -l yamlgraph/node_factory/race_node.py (450, the size-gate max) and llm_nodes.py (448) — the name-sharing edits must not add lines"
  - "yamlgraph graph lint on every graph.yaml under examples/ and graphs/, before and after — any new W072/W073 is listed by path and key"
  - "read-only yamlgraph graph lint on csap a60fb2b9 graphs/flex_navigator/graph.yaml, graphs/flex_navigator/graph_v2.yaml, graphs/post_call/graph.yaml"
branches:
  - "a shipped example carries a metadata tuning key → fix it through scripts/author.sh (governed path), or keep it with a recorded rationale"
  - "a size-gate overflow in race_node.py → move a literal-free line, never split the module under this FR"
  - "csap a60fb2b9 unavailable → committed self-contained reproducer, labelled as such (R-5)"
delegations:
  - "research.sh: 4 runs (3 reducer rejections, 1 accepted)"
  - "judge.sh: 1 run (APPROVED WITH REVISIONS)"
  - "author.sh: 1 run only if the shipped-example branch fires"
waits:
  - "judge"
commands:
  - scripts/research.sh feature-requests/research-briefs/lint-unread-llm-keys.md
  - scripts/judge.sh feature-requests/FR-1166-lint-unread-llm-settings.md
  - yamlgraph graph lint
  - lint-imports
  - pytest tests/unit/test_fr1166_lint_unread_llm_settings.py -q --no-cov
  - pytest tests/unit/ -q --no-cov -m "not slow" -n 4
  - python scripts/req_coverage.py --strict
```

## Proposed Solution

1. **One declaration (R-3).** `yamlgraph/constants.py` gains
   `class LLMSetting(StrEnum)` with `TEMPERATURE`, `MAX_TOKENS`,
   `THINKING_BUDGET` and `EFFORT`, following the `NodeType` pattern. The
   module is pure (stdlib only), so the linter imports it without reaching
   any runtime module or touching `.importlinter`. A StrEnum member is
   equal to and hashes like its string, so the resolution sites swap only
   the literal: `llm_nodes.py` (all four) and `race_node.py` (temperature
   and thinking budget). Each site keeps its own semantics, which this FR
   does not change:

   | Site | Setting | Resolution kept as is |
   |---|---|---|
   | regular LLM (`llm_nodes.py`) | `temperature` | node, else defaults, else 0.7; null inherits |
   | regular LLM | `max_tokens` | `node_config.get(key, defaults.get(key))`; explicit node null suppresses the default |
   | regular LLM | `thinking_budget`, `effort` | `node_or_default`; null inherits |
   | direct race (`race_node.py`) | `temperature` | node, else defaults, else 0.7 |
   | direct race | `thinking_budget` | node, else defaults; null inherits |
   | direct and router race | `max_tokens`, `effort` | **not forwarded** to candidates (unchanged; parked) |
   | router race (`router_race_node.py`) | `temperature`, `thinking_budget` | read from the regular-LLM config (unchanged) |

2. **W072, a tuning key in `metadata:` (warning).** Implemented in
   `yamlgraph/linter/checks_providers.py` and registered in `graph_linter.py`.
   It checks each `LLMSetting` key, by presence rather than truthiness, in:
   - graph top-level `metadata:`;
   - the top-level `metadata:` of each existing prompt that a node references,
     resolved with the existing `resolve_prompts_dir` and `get_prompt_path`
     helpers. Each prompt is reported once. A missing prompt stays E004's
     job.

   The message names the location and the key. The fix names
   `defaults.<key>` (or the node), and for `max_tokens` / `effort` adds that
   race and router-race nodes do not apply it.
   ```
   W072 graph metadata: 'thinking_budget' is not read from metadata
        fix: move it to defaults.thinking_budget (or onto the node)
   ```
3. **W073, an extra key on a race candidate (warning).** Same module and
   registration. It runs for `type: race` and for any node with
   `candidates:`, which covers the FR-272 router race. It reports one issue
   per extra key, naming the node and the zero-based candidate index. The
   fix depends on the key (R-4):
   - `temperature`, `thinking_budget`: move it onto the node or under
     `defaults:`; it then applies to every candidate.
   - `max_tokens`, `effort`: race nodes do not apply this setting today;
     remove it.
   - any other key: candidates take only `provider` and `model`; remove it.
4. **Docs.** `docs/demos/linter.md` lists W072/W073. `reference/graph-yaml.md`
   states that `metadata:` is not read for LLM settings, and that race
   candidates take only `provider` and `model`.

No runtime behaviour changes, no load refusal, and nothing starts reading
`metadata:`.

## Acceptance Criteria

The binding criteria are the judgement's AC-01..AC-11
([judgement](FR-1166-lint-unread-llm-settings.judgement.md#revised-acceptance-criteria)),
restated here:

- [ ] AC-01: Through `lint_graph` and a CLI witness, each of the four keys in
      graph `metadata:` gives W072 naming the location, the key and
      `defaults.<key>`; values `0` and `null` are detected.
- [ ] AC-02: Each key in a referenced prompt's `metadata:` gives W072, both for
      a graph-relative `prompts_dir` and for project-root resolution.
- [ ] AC-03: Non-setting `metadata:` keys, prompt top-level `provider` /
      `model`, and missing prompts produce no W072/W073.
- [ ] AC-04: Direct race and router race emit W073 for every extra key
      (`thinking_budget`, `temperature`, `max_tokens`, `effort`, arbitrary),
      with node and index; provider-only, model-only, and provider+model
      candidates produce none.
- [ ] AC-05: Fix wording per R-4; both codes are warnings; no load refusal.
- [ ] AC-06: `LLMSetting` drives lint membership and the named resolution
      sites. Behaviour witnesses cover all four regular-LLM settings and
      temperature/thinking_budget through the direct and router race.
      Absent/default/node/null/zero semantics are unchanged, and nothing new
      is forwarded to candidates.
- [ ] AC-07: Defect-specific RED is committed before GREEN; all new tests
      carry `REQ-YG-730`; CAP-305 exists; `req_coverage.py --strict` passes.
- [ ] AC-08: `lint-imports` passes with no contract edit; the focused pytest,
      the unit suite at `-n 4`, `req_coverage --strict`, and ruff check/format
      on touched Python all pass.
- [ ] AC-09: Before/after lint census of `examples/` and `graphs/`, with each
      new W072/W073 recorded by path and key.
- [ ] AC-10: Read-only lint of csap `a60fb2b9` (the three graphs named in
      Planned Operations) shows W072, or a labelled reproducer is used
      instead.
- [ ] AC-11: Docs, changelog fragment, the FR implementation record, and a
      Distill entry with **Seed:**.

Tests: `tests/unit/test_fr1166_lint_unread_llm_settings.py` holds the lint
witnesses. Preservation witnesses go in the existing LLM, direct-race and
router-race test files.

## Alternatives Considered

The five solution classes in the research record
([FR-1166.research.md](FR-1166.research.md)), dispositioned per R-1.
Persona convergence labels (`convergent x3`) are not counted as independent
classes.

| Class | Research rows (verbatim persona) | Decision | Committed precedent |
|---|---|---|---|
| A. Shared declarative names + narrow lint warnings | os-infra-primitivist ("allowlist constant … in `llm_factory.py`") and data-process ("canonical LLM settings registry", codes W027/E028), merged | **Adopt**, with two disagreements resolved. The declaration lives in `yamlgraph/constants.py`, not `llm_factory.py`, because the linter may not import factory or executor modules (`.importlinter:16-33`; `llm_nodes.py:15`). The codes are W072/W073, beside the W071 provider-settings family (`yamlgraph/linter/checks_providers.py:28`), not W027/E028; E028 would be an error, contradicting the warning-only freeze (R-2). | `yamlgraph/constants.py:15` (`NodeType` StrEnum pattern); FR-1165 (removed an unapplied key) |
| B. Source introspection at lint time | yamlgraph-native-planner | **Reject.** Parsing `llm_factory.py` / `race_node.py` source at lint time is fragile, and class A gets the same freedom from drift with one declaration. Its `is_this_a_graph: none` answer is right: this extends a deterministic analyzer, not an LLM orchestration graph. | `yamlgraph/linter/checks_providers.py:45-51` (raw-YAML key checks, no introspection) |
| C. csap-only migration, no new check | subtractionist | **Reject.** FR-1144 named the migration in prose on 2026-09-30 (`FR-1144-race-node-thinking-budget.md:244-246`) and none of the 18 files changed. The row's advice to put tuning "as top-level race-candidate dict keys" is **wrong**: candidates are read only for `provider` and `model` (`yamlgraph/node_factory/race_node.py:201-206`). Its `is_this_a_graph: Yes` answer is also wrong: that metadata is a tree of keys does not make a lint check a graph. | `FR-1144-race-node-thinking-budget.md:244-251` |
| D. Location-schema unknown-key validation (actionlint style) | librarian | **Partly adopt.** The location-scoped idea is used for candidates only: W073 flags every key outside `{provider, model}`. Broad unknown-key validation of graph or prompt YAML is rejected; `metadata:` is user-owned, so only `LLMSetting` names are flagged there. The actionlint URL is cited as an analogy, not as verified implementation evidence. Its `is_this_a_graph: Yes` answer is wrong for the same reason as class C. | `yamlgraph/models/node_schema.py:384-396` (candidate contract) |
| E. Load-time refusal (FR-1165 shape) | not in research; added by the author | **Reject for this FR (R-2).** It changes loading behaviour beyond a lint-only fix. "No known csap user" does not prove that no other consumer has extra candidate keys. | FR-1165 (`feature-requests/FR-1165-config-max-tokens-refused.md:78-107`), applicable to framework-owned documented keys |

Also rejected: reading `thinking_budget` from `metadata:` at runtime. FR-1144
already rejected it as a separate framework-wide change.

## Judgement fold (2026-11-16)

- **R-1** folded into the Alternatives table above (five classes, with
  research errors corrected).
- **R-2** folded: both codes are warnings; the prompt-deferral and
  load-refusal branches are removed; the Ideal Result is narrowed.
- **R-3** folded: `LLMSetting` lives in `yamlgraph/constants.py`; the scope
  inventory table is in Proposed Solution §1.
- **R-4** folded: key-specific fix wording is in Proposed Solution §2-3.
- **R-5** folded: the doc targets are named; CAP-305 / REQ-YG-730 are
  recorded; the test file is named; the csap revision `a60fb2b9` and its
  three graphs are named; the census is per graph.

## Out of Scope

- csap migration of the 18 files and the pin bump (csap-side work).
- Per-candidate LLM settings (FR-1144 C-6).
- **Parked finding:** direct and router races do not forward `max_tokens` or
  `effort` to candidates (`race_node.py:201-206`). That is a separate FR if
  wanted; W072/W073 messages state it truthfully instead.
- `reasoning_effort` for Azure/OpenAI and `thinking_level` for Gemini 3.x.
- Standalone or unreferenced prompt lint; top-level prompt tuning keys.

## Related

- `yamlgraph/node_factory/race_node.py:189` (`_build_candidate_llms`), `:347`
  (budget resolution)
- `yamlgraph/linter/checks_providers.py` (W071 family; same check scope)
- `yamlgraph/models/node_schema.py:384` (race candidate validation)
- `yamlgraph/executor_base.py` (`_resolve_provider_and_model`: prompt
  top-level `provider`/`model` only)
