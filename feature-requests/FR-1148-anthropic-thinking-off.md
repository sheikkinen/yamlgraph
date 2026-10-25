# Feature Request: FR-1148 `thinking_budget: 0` Turns Anthropic Thinking Off

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Requested:** 2026-10-25
**First consumer / first event:** the game-engine repository's
*Voyage to Arcturus* chapter-text graph (`workflows/chapter-text/text.yaml`,
`adapt` and `extract` nodes on `claude-sonnet-5-5`, `max_tokens: 32000`).
On 2026-10-25 its chapter I `adapt` call spent the whole 32 000-token
answer on thinking and returned no usable text. The first event is that
graph's next chapter run with `thinking_budget: 0` on both nodes.
**Research:** in-body dispositioned [Alternatives Considered](#alternatives-considered)
table (FR-889 style); every row rests on the probe in
[evidence/FR-1148-thinking-off-probe.md](evidence/FR-1148-thinking-off-probe.md)
or a code read of `00742bd4`.
**Prior art:** [FR-071-thinking-budget-graph-level.md](FR-071-thinking-budget-graph-level.md)
— introduced `thinking_budget` and its `0 or >= 1024` validation, but `0`
was a no-op for Anthropic; this FR gives `0` its meaning;
[FR-1056-deepseek-thinking-off.md](FR-1056-deepseek-thinking-off.md)
— the same "0 turns thinking off" contract for `deepseek`; this FR mirrors
it for `anthropic` and does not touch the DeepSeek branch;
[FR-230-google-vertex-thinking-budget.md](FR-230-google-vertex-thinking-budget.md)
— Google/Vertex budget plumbing; dismissed, other provider;
[FR-1144-race-node-thinking-budget.md](FR-1144-race-node-thinking-budget.md)
— passes `thinking_budget` through race nodes; this FR changes what the
Anthropic constructor does with the value, not how it arrives;
[FR-1146-anthropic-temperature-deprecated.md](FR-1146-anthropic-temperature-deprecated.md)
— same model generation, sampling parameters; its Out of scope recorded
the thinking-shape split this FR handles for the *off* case only.

## Origin (process record)

This change first reached `main` as three direct pushes on 2026-10-25
(`aa1589d7`, `8366d6c7`, merge `3a911ae2`), past the required checks and
carrying `Co-Authored-By:` trailers. The check-only PR #756 was rejected,
and the force-push scrub of `main` was refused by branch protection. This
FR redoes the change through the normal route. The diary entry
`docs/diary/diary-2026-10-25-reflection-fr-1148-the-push-that-skipped-the-gates.md`
records the corrective actions.

## Summary

`thinking_budget: 0` on an Anthropic node sends nothing today, so a model
that thinks by default keeps thinking. Make `0` turn thinking off, in the
form each model accepts: `{"type": "between_tools"}` on Claude Sonnet 5.5,
`{"type": "disabled"}` on the other listed models, and a load-time
`ValueError` on the models that cannot turn thinking off (Opus 5.5,
Fable 5.x).

## Value Statement

Graph authors on Claude Sonnet 5.5 get their whole `max_tokens` for the
answer, instead of an empty or cut-off answer after the model spent it on
thinking.

## Problem

Code read at `00742bd4`:

- `yamlgraph/utils/llm_providers.py` `_create_anthropic_llm` sets
  `thinking` only when `thinking_budget >= 1024`. A `0` falls through:
  no `thinking` field is sent, and the model's own default stands.
- `reference/graph-yaml.md` documents `anthropic: 0 or >= 1024`, which
  reads as if `0` were a setting. It is a no-op.

Witnessed:

1. **The empty answer (first consumer).** game-engine chapter I, 2026-10-25
   (game-engine commit `0d7a9b8b`): Sonnet 5.5 "thinks by default and spent
   chapter I's whole 32000-token adapt answer on it". The earlier run
   (`45e066da`) found both `adapt` answers unparseable.
2. **Probe B, reproduced on demand**
   ([evidence](evidence/FR-1148-thinking-off-probe.md)): one prompt,
   `max_tokens=1500`, `claude-sonnet-5-5`, two runs per form:

   | `thinking` sent | stop | blocks | output tokens | text chars |
   |---|---|---|---|---|
   | absent (today's `0`) | `max_tokens` | `['thinking']` | 1500 | 0 |
   | absent (today's `0`) | `max_tokens` | `['thinking']` | 1500 | 0 |
   | `between_tools` | `end_turn` | `['text']` | 1084 | 2491 |
   | `between_tools` | `end_turn` | `['text']` | 884 | 2265 |

3. **Probe A — the off switch is not one shape.** Every id `models.list`
   returns (14), three forms each. `disabled` on Sonnet 5.5 returns 400:
   `To turn thinking off on this model, send "thinking": {"type":
   "between_tools"} instead of {"type": "disabled"}.` The split:

   | Model ids | `disabled` | `between_tools` |
   |---|---|---|
   | `claude-sonnet-5-5` | 400 (names `between_tools`) | OK |
   | `claude-opus-5-5`, `claude-fable-5-1`, `claude-fable-5` | 400 (`use adaptive + effort`) | 400 |
   | `claude-haiku-5-5`, `claude-sonnet-5`, `claude-opus-5`, `claude-opus-4-8`, `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-opus-4-6`, `claude-opus-4-5-20251101`, `claude-haiku-4-5-20251001`, `claude-sonnet-4-5-20250929` | OK | 400 |

   No model accepts both forms; three accept neither.

## Ideal Result

`thinking_budget: 0` on an Anthropic node means "no thinking before the
answer" on every model that can express it, in the one form that model
accepts; on a model that cannot, the graph fails at client construction
with a message naming the model, never with a 400 mid-run. Omitting
`thinking_budget` leaves the request exactly as today, and `>= 1024`
behaves exactly as today.

## Planned Operations

```yaml
probes:
  - "Probe A over every models.list id x {absent, disabled, between_tools} — decides the prefix rules (done, evidence file)"
  - "Probe B on claude-sonnet-5-5, absent vs between_tools — decides whether the bug is real (done, evidence file)"
  - "wc -l yamlgraph/utils/llm_providers.py after the edit — over the size gate's 450 means the rule lives in its own module"
  - "pytest tests/unit/test_thinking_budget.py before edit — the FR-071 tests are the regression floor"
branches:
  - "a listed id contradicts the prefix rules → change the rules and the evidence, never add a runtime models.list call"
  - "llm_providers.py over 450 lines → move the rule to yamlgraph/utils/anthropic_thinking.py"
delegations:
  - "judge.sh: 1 run (JUDGE_BACKEND=claude)"
waits:
  - "judge"
  - "CI"
commands:
  - JUDGE_BACKEND=claude scripts/judge.sh feature-requests/FR-1148-anthropic-thinking-off.md
  - pytest tests/unit/test_thinking_budget.py -q --no-cov
  - pytest tests/unit/ -q --no-cov -m "not slow" -n auto
  - python scripts/req_coverage.py --strict
  - pre-commit run --files <changed files>
```

## Proposed Solution

One rule at the Anthropic constructor boundary, in its own small module
so `llm_providers.py` stays under the size gate:

```python
# yamlgraph/utils/anthropic_thinking.py
_THINKING_ALWAYS_ON = ("claude-opus-5-5", "claude-fable-5")  # Probe A

def anthropic_thinking_off(model: str) -> dict:
    if model.startswith(_THINKING_ALWAYS_ON):
        raise ValueError(f"thinking_budget=0: thinking cannot be turned off on {model}; ...")
    if model.startswith("claude-sonnet-5-5"):
        return {"type": "between_tools"}
    return {"type": "disabled"}
```

```python
# _create_anthropic_llm
if thinking_budget == 0:
    anthropic_kwargs["thinking"] = anthropic_thinking_off(model)
elif thinking_budget is not None and thinking_budget >= 1024:
    ...  # unchanged
```

```yaml
# graph usage
nodes:
  adapt:
    type: llm
    provider: anthropic
    max_tokens: 32000
    thinking_budget: 0   # Sonnet 5.5 → between_tools
```

Constraints:

1. `None` (omitted) sends no `thinking` field — unchanged.
2. `>= 1024` sends `{"type": "enabled", "budget_tokens": N}` and keeps the
   FR-071 `temperature=1` override — unchanged. (That this form is itself
   refused by the 5.x generation is FR-1146's recorded follow-up, not this
   FR.)
3. `0` changes no temperature: thinking off has no temperature rule.
4. The cache key already includes `thinking_budget`; no change.
5. `reference/graph-yaml.md` documents the three outcomes of `0` in both
   tables (defaults and node fields).

## Acceptance Criteria

- [ ] AC-01: `create_llm(provider="anthropic", model="claude-sonnet-5-5", thinking_budget=0)` → `llm.thinking == {"type": "between_tools"}`.
- [ ] AC-02: `claude-haiku-5-5` (a listed id that accepts `disabled`) with `thinking_budget=0` → `{"type": "disabled"}`.
- [ ] AC-03: `claude-opus-5-5` and `claude-fable-5-1` with `thinking_budget=0` raise `ValueError` matching `cannot be turned off` at `create_llm`.
- [ ] AC-04: `thinking_budget=None` → `llm.thinking is None`.
- [ ] AC-05: `thinking_budget=2048` → `{"type": "enabled", "budget_tokens": 2048}`.
- [ ] AC-06: Every new test carries `@pytest.mark.req("REQ-YG-083")` (class marker); the RED commit precedes the GREEN commit.
- [ ] AC-07: `yamlgraph/utils/llm_providers.py` ≤ 450 lines; `pre-commit run --files` on every changed file passes.
- [ ] AC-08: `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-09: `reference/graph-yaml.md` documents `0` as thinking off per model in both tables.
- [ ] AC-10: `changelog/unreleased/fr-1148-anthropic-thinking-off.md` with `type: fix`, `scope: llm`, `req: REQ-YG-083`.
- [ ] AC-11: Diary reflection for FR-1148 with the corrective actions and a **Seed:**.
- [ ] AC-12: No commit on the branch carries a `Co-authored-by` trailer.

## Alternatives Considered

**is_this_a_graph:** no — a deterministic constructor rule at the provider
boundary; no per-item model judgement.

| # | Alternative | Probe / evidence | Disposition |
|---|---|---|---|
| A | Send `{"type": "disabled"}` for every model (the first direct push, `aa1589d7`) | Probe A: 400 on Sonnet 5.5 — the first consumer's model | Rejected — fails exactly where the bug is |
| B | **Per-model form by prefix rules** (chosen) | Probe A: 14/14 listed ids match the three rules | Chosen — the smallest rule that is right on every listed id |
| C | Omit `thinking` and lower `max_tokens` / raise it to fit the thinking | Probe B: thinking took all 1500 tokens; game-engine took all 32 000 | Rejected — no ceiling is safe when the model decides how long it thinks |
| D | Send `between_tools` only, for Sonnet 5.5, and ignore `0` elsewhere | Probe A: `claude-opus-5` returned a thinking block with no `thinking` field, and none with `disabled` | Rejected — `0` would stay a silent no-op on models that do think by default |
| E | Catch the 400 and retry with the other form | Probe A messages are stable text | Rejected — `downstream_fix`; a wasted call per node, every run |
| F | Query `models.list` capabilities at construction | FR-1146 Probe 3: no documented field for the off form | Rejected — network call in the constructor, undocumented contract |
| G | Map `0` on Opus 5.5 / Fable 5.x to `adaptive` with low effort | Probe A: they refuse both off forms; the API names `output_config.effort` | Rejected for this FR — that is "less thinking", not "off"; a new config surface (effort) belongs in its own FR. Raise instead of pretending |

## Out of scope

- `effort` / adaptive thinking as a graph field (the only lever on Opus 5.5
  and Fable 5.x).
- `thinking_budget >= 1024` on the 5.x generation (FR-1146 follow-up).
- Unknown future ids default to `disabled`; a new model that refuses it
  fails with the API's 400, which names the form to use. Widening the rule
  then needs a probe folded into this FR's successor.

## Related

- `yamlgraph/utils/llm_providers.py` — `_create_anthropic_llm`
- `yamlgraph/utils/anthropic_thinking.py` — new, the rule
- `tests/unit/test_thinking_budget.py` — FR-071 tests, extended
- `reference/graph-yaml.md` — `thinking_budget` rows
- [evidence/FR-1148-thinking-off-probe.md](evidence/FR-1148-thinking-off-probe.md)
- PR #756 (rejected check-only PR for the direct pushes)
