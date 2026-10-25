# Judgement: FR-1148 `thinking_budget: 0` Turns Anthropic Thinking Off

**Prior art:** [FR-1148-anthropic-thinking-off.md](FR-1148-anthropic-thinking-off.md) — the FR this judgement rules on, not precedent; dismissed; its own Prior art line dispositions FR-071, FR-1056, FR-230, FR-1144 and FR-1146. (Added by the FR author at promotion to satisfy the FR-738 gate; not judge output. Backend: `JUDGE_BACKEND=claude scripts/judge.sh`, 2026-10-25, round 1.)

**Verdict:** APPROVED WITH REVISIONS — the defect is real and probe-proven, the chosen rule is right on all 14 probed ids, and the change is one branch at one boundary; but the evidence stops at the raw Anthropic SDK while the code ships through `ChatAnthropic`, the acceptance criteria assert a constructor attribute instead of the request payload, one existing FR-071 test asserts the opposite contract, and the registry/doc surfaces that describe REQ-YG-083 are left stale. Authority activates when R-1 … R-9 are folded into the FR file; no implementation commit before then.

**Reviewed against:**
`feature-requests/FR-1148-anthropic-thinking-off.md` ·
`feature-requests/evidence/FR-1148-thinking-off-probe.md` ·
prior art cited by the FR: `feature-requests/FR-071-thinking-budget-graph-level.md`,
`feature-requests/FR-1056-deepseek-thinking-off.md` (+ its judgement),
`feature-requests/FR-230-google-vertex-thinking-budget.md` (referenced, not re-read in full),
`feature-requests/FR-1144-race-node-thinking-budget.md`,
`feature-requests/FR-1146-anthropic-temperature-deprecated.md` (referenced) ·
code: `yamlgraph/utils/llm_providers.py` (443 lines; `_create_anthropic_llm` L28–46,
`_THINKING_PROVIDERS` L331–335, `dispatch_provider` L355–376, FR-998 block L379–443),
`yamlgraph/utils/llm_factory.py` (291 lines; `THINKING_PROVIDERS` L39,
`ANTHROPIC_SAMPLING_MODEL_PREFIXES` L44–51, `create_llm` L98–242),
`yamlgraph/linter/checks_providers.py`, `yamlgraph/config.py` (anthropic default
`claude-haiku-4-5`), `scripts/check_changelog_req.py` ·
tests: `tests/unit/test_thinking_budget.py`, `tests/integration/test_thinking_budget_integration.py` ·
registry/doc: `capabilities/CAP-28-graph-level-thinking-budget.yaml`,
`capabilities/CAP-273-deepseek-non-thinking.yaml`, `ARCHITECTURE.md` (L362, L912),
`reference/graph-yaml.md` (L84, L94, L278, L1032),
`examples/demos/thinking/graph.yaml` + `README.md`,
`examples/demos/image-that-speaks/FR-1144-No-Thinking.yaml` ·
third-party contract read at the boundary: `.venv/Lib/site-packages/langchain_anthropic/chat_models.py`
(`thinking` field L1180, `_default_params` L1363–1367,
`_assert_valid_model_configuration` L1495–1538, `_get_request_payload` L1540–1548) ·
doctrine: `.github/skills/judge-fr/doctrine.md`, `.github/copilot-instructions.md`, `CLAUDE.md`.

Input closure held: no chat transcript, no working notes, no sibling-repo content
(the game-engine commit `0d7a9b8b` cited in the Problem section is **outside** this
repo and was not consulted — see R-8).

## What is sound

1. **The defect is witnessed, not argued.** Probe B is the strongest part of the
   FR: four runs, two per form, `stop=max_tokens blocks=['thinking'] out=1500
   text_chars=0` twice with `thinking` absent, and `end_turn / ['text'] / 2491
   and 2265` chars with `between_tools`. That is a reproduction, not a theory,
   and it survives `read_raw_output_first` — the raw console output is committed,
   unedited, with the scripts attached so the probe is re-runnable.
2. **The rule is derived from an exhaustive enumeration, not a guess.** Probe A
   covers every id `models.list` returns (14) × three forms (42 calls). I checked
   the proposed prefix rules against all 42 lines myself: `claude-sonnet-5-5` →
   `between_tools` ✅; `claude-opus-5-5`, `claude-fable-5-1`, `claude-fable-5` →
   raise ✅ (all three refuse both forms); the remaining ten → `disabled` ✅,
   including the near-miss pairs `claude-opus-5-5` vs `claude-opus-5` and
   `claude-sonnet-5-5` vs `claude-sonnet-5`, which the `startswith` ordering gets
   right. The "14/14" claim is true.
3. **The right alternative was killed by the right probe.** Alternative A
   (`disabled` everywhere) is the shape that was actually pushed to `main` on
   2026-10-25, and the FR retires it with the 400 that names `between_tools` on
   the first consumer's own model. Preserving the author's own failed approach in
   the table is `forced_opposite` done honestly, and it satisfies the FR-889
   research-substance bar: seven solution classes, each with a probe line, the
   `is_this_a_graph` answer stated and correct (a deterministic constructor rule
   is not a graph).
4. **Raise beats pretend on the three models that cannot comply** (Alternative
   G). Mapping `0` to `adaptive`+`effort` would be `plausible_wrong_answer` —
   "less thinking" sold as "off". Deferring the `effort` surface to its own FR is
   correct scoping.
5. **The blast radius is genuinely one branch.** `thinking_budget` already rides
   the cache key (`llm_factory.py` L216–225), already reaches
   `_create_anthropic_llm` through `dispatch_provider` (`anthropic` is in
   `_THINKING_PROVIDERS`), and the linter's W071 family is gated on
   `thinking_budget > 0`, so `0` trips nothing. The FR's claim that no cache,
   dispatch, schema or linter change is needed is verified.
6. **The premise about the current tree is verified.** `_create_anthropic_llm`
   (L38) still has only the `>= 1024` branch, and `grep -r "between_tools\|
   anthropic_thinking"` across the repo matches only the FR and its evidence
   file: nothing from the direct pushes survives in the tree, so the enforcer
   starts from a clean base and this FR is a genuine redo, not a patch over
   residue.
7. **Origin is disclosed rather than laundered.** An FR that opens by naming its
   own gate-skipping provenance is the behaviour doctrine wants.

## Required revisions

### R-1: Assert the request payload, not the constructor attribute

AC-01/02/04/05 assert `llm.thinking`, which only proves the value survived
Pydantic field assignment. The boundary that matters is the request, and
`langchain_anthropic` runs model-specific validation there:
`_assert_valid_model_configuration` (chat_models.py L1495–1538) raises on
`claude-opus-5*` + `{"type": "enabled"}` and on `claude-opus-5*` +
`{"type": "disabled"}` with `effort` in `{xhigh, max}`. `llm.thinking` never
executes that code; `_get_request_payload` does.

Rewrite AC-01/02/04/05 to assert on
`llm._get_request_payload([HumanMessage("hi")])["thinking"]` (and, for the
omitted case, that `"thinking"` is absent from the payload), exactly as FR-1056
AC-01…AC-03 did for DeepSeek. Keep an `llm.thinking` assertion only as a
secondary line if the author wants it.

### R-2: Pin the model in every test and fix the test that asserts the old contract

Two concrete hazards, both mechanical:

- `tests/unit/test_thinking_budget.py:110` `test_thinking_budget_zero_no_thinking`
  calls `create_llm(provider="anthropic", thinking_budget=0)` and documents
  "thinking_budget=0 does not enable thinking". Under this FR that call must set
  `thinking` to something. The FR's Planned Operations calls the FR-071 tests
  "the regression floor" — they are not; this one contradicts the new contract
  and must be amended, not preserved. Name it in the FR as an edit, with its new
  assertion.
- That same call resolves the model from `ANTHROPIC_MODEL` or the
  `yamlgraph/config.py` default `claude-haiku-4-5`. With the new rule, an
  operator whose `.env` sets `ANTHROPIC_MODEL=claude-opus-5-5` turns that test
  from pass into `ValueError`. Add to the FR: **every** test touching the new
  rule passes `model=` explicitly, and the suite's outcome must not depend on
  `ANTHROPIC_MODEL`.

### R-3: Turn the Probe A table into a test

The whole correctness claim is "the three prefix rules are right on all 14
listed ids". Add an acceptance criterion for a parametrised test over those 14
ids asserting the mapping (`between_tools` / `disabled` / raises) exactly as the
evidence file records it. This is offline, keyless and cheap, and it makes the
evidence file falsifiable by CI instead of by memory.

### R-4: Update the registry text this FR makes stale

The FR reuses REQ-YG-083 but leaves its definition describing the old contract.
`capabilities/CAP-28-graph-level-thinking-budget.yaml` L12–16 (and therefore
`ARCHITECTURE.md` L912) says `thinking_budget` is "validated as `0` or `≥ 1024`;
passed as `thinking={"type":"enabled","budget_tokens":N}`" — after this change
that is false for `0`. Add an acceptance criterion: update the REQ-YG-083
description to state the three outcomes of `0` (per-model form, raise on the
three models that cannot comply, unchanged `None` and `≥ 1024` behaviour), add
`yamlgraph/utils/anthropic_thinking.py` and
`yamlgraph/utils/llm_providers.py` to the CAP's `modules`, and regenerate
`ARCHITECTURE.md` with `scripts/aggregate_capabilities.py`.

Reuse of REQ-YG-083 (rather than a new CAP/REQ as FR-1056 did) is accepted: it
is the same YAML field's contract, CAP-28 stays single-REQ, and
`scripts/check_changelog_req.py` therefore passes the fragment mechanically.

### R-5: Name all four documentation sites, not "both tables"

AC-09 says "both tables". `reference/graph-yaml.md` carries the field in **three**
tables plus an example comment: L94 (defaults), L278 (node fields), L1032 (race
node, FR-1144) and the inline comment at L84. The `create_llm` docstring
(`llm_factory.py` L120–127) also states "For Anthropic: 0 or ≥1024, forces
temperature=1", which becomes wrong for `0` (constraint 3 of this FR says `0`
changes no temperature). List all five sites in the criterion; FR-1056's AC-09
set the precedent of including the docstring.

### R-6: Make the new module unconditional and rename the constant

- `yamlgraph/utils/llm_providers.py` is already **443 lines** — 7 from the gate.
  The Planned Operations branch "llm_providers.py over 450 lines → move the rule
  to `anthropic_thinking.py`" is therefore not a branch but the plan. State the
  new module as a deliverable. (It cannot live beside
  `ANTHROPIC_SAMPLING_MODEL_PREFIXES` in `llm_factory.py`: `llm_factory` imports
  `dispatch_provider` from `llm_providers`, so the reverse import would cycle.
  Record that one-line reason so the next author does not "fix" the placement.)
- `_THINKING_ALWAYS_ON` is factually wrong as a name. Probe A line 19 shows
  `claude-opus-5-5` answering with `blocks=['text']` and no thinking block when
  `thinking` is absent — thinking is not always on there; what is true is that
  neither off-form is accepted. Rename to something that says that (e.g.
  `_THINKING_OFF_UNSUPPORTED`) so the constant cannot teach a false fact.

### R-7: State where the raise happens, and what the message says

The Ideal Result promises "a load-time `ValueError`" and "fails at client
construction ... never with a 400 mid-run". `create_llm` is called when the node
builds its client, which for an `llm` node is during the run, not at graph load.
Replace "load-time" with the accurate boundary ("at `create_llm`, before the
first request is sent — a `ValueError` naming the model instead of an API 400").
Also fix the message sketch's `...`: specify that it names the model id, says
thinking cannot be turned off on it, and names the remedy (omit
`thinking_budget`, or use a model that accepts an off form). AC-03 must also
assert no client is cached by the failed call (a second identical call raises
identically).

### R-8: Repair the Origin section's two unlanded citations

- `docs/diary/diary-2026-10-25-reflection-fr-1148-the-push-that-skipped-the-gates.md`
  does not exist in the tree (`docs/diary/` holds nothing dated 2026-10-25). The
  Origin section cites it in the present tense as an existing record while AC-11
  asks for it to be written. State it as a deliverable of this FR with that exact
  filename, and keep AC-11.
- The first-consumer witness (game-engine commit `0d7a9b8b`) is in another
  repository and cannot be verified from here. Keep it as context, but mark it
  explicitly as an out-of-repo report; the in-repo evidence that carries the FR
  is Probe B.
- Add the one line FR-737 asks for: the five REJECTED FRs in
  `feature-requests/` (FR-084, FR-702, FR-737, FR-1091, FR-1145) are unrelated to
  Anthropic thinking, so no rejected precedent stands against this proposal.

### R-9: Add a live witness through `ChatAnthropic`

Both probes used the raw `anthropic` SDK. The code under change constructs a
`ChatAnthropic`, and the wrapper has its own model-specific validation layer
(R-1). Nothing in the FR proves `{"type": "between_tools"}` survives the
LangChain boundary — this is exactly `the_one_law` read in reverse: the evidence
was gathered at a boundary the product does not cross. Add an acceptance
criterion requiring one executed call —
`create_llm(provider="anthropic", model="claude-sonnet-5-5", thinking_budget=0,
max_tokens=1500).invoke(<Probe B prompt>)` — with `stop_reason`, block types and
text length recorded verbatim in the FR's Implementation Status, asserting
`text` is non-empty and no thinking block is returned. Guarded-integration
placement (`tests/integration/test_thinking_budget_integration.py` is the
existing home) is acceptable; the recorded output in the FR is the witness.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/utils/anthropic_thinking.py` — new; the prefix tables and the one mapping function |
| D-2 | `yamlgraph/utils/llm_providers.py` — the `thinking_budget == 0` branch in `_create_anthropic_llm` only |
| D-3 | `tests/unit/test_thinking_budget.py` (amend the contradicting case) and/or `tests/unit/test_fr1148_anthropic_thinking.py` — payload-level + 14-id table tests |
| D-4 | `tests/integration/test_thinking_budget_integration.py` — the guarded live case (R-9) |
| D-5 | `capabilities/CAP-28-graph-level-thinking-budget.yaml` + regenerated `ARCHITECTURE.md` |
| D-6 | `reference/graph-yaml.md` (L84, L94, L278, L1032) + `create_llm` docstring |
| D-7 | `changelog/unreleased/fr-1148-anthropic-thinking-off.md` |
| D-8 | `docs/diary/diary-2026-10-25-reflection-fr-1148-the-push-that-skipped-the-gates.md` |
| D-9 | This FR file — folded revisions, Implementation Status, deviations |

**Not authorized:**

- Any `effort` / `adaptive` / `output_config` surface, in YAML or in Python —
  Alternative G is parked for its own FR.
- Any change to the `>= 1024` path, the FR-071 `temperature=1` override, the
  `None` path, or the cache key.
- Any change to the DeepSeek, Google, Vertex or any other provider branch, to
  `llm_factory.THINKING_PROVIDERS`, to `_THINKING_PROVIDERS`, or to
  `dispatch_provider`.
- Any new YAML field, schema change, or new lint code. A `graph lint` check that
  would catch `thinking_budget: 0` + an off-incapable model before the run is a
  good idea and a **separate FR** — note it in Out of scope, do not build it.
- Any network call, `models.list` query, or 400-retry at construction
  (Alternatives E and F stay rejected).
- Any rewrite, force-push, or history scrub of `main`. The direct-push incident
  is closed by D-8 and this FR; it is not re-opened here.
- Any edit to `examples/demos/thinking/graph.yaml`, its README, or
  `examples/demos/image-that-speaks/FR-1144-No-Thinking.yaml`. (`examples/demos/
  thinking/graph.yaml:28` is `provider: anthropic` + `thinking_budget: 0` with no
  model, so it silently changes behaviour under this FR — verifying it still
  lints and runs is AC-14; changing it is not authorized.)

## Revised acceptance criteria

- [ ] AC-01: `create_llm(provider="anthropic", model="claude-sonnet-5-5", thinking_budget=0)` → `llm._get_request_payload([HumanMessage("hi")])["thinking"] == {"type": "between_tools"}`; cache cleared in setup.
- [ ] AC-02: same call with `model="claude-haiku-5-5"` → payload `thinking == {"type": "disabled"}`.
- [ ] AC-03: `model="claude-opus-5-5"` and `model="claude-fable-5-1"` with `thinking_budget=0` raise `ValueError` from `create_llm` matching `cannot be turned off`; the message contains the model id; a second identical call raises identically (nothing cached).
- [ ] AC-04: `thinking_budget=None` with a pinned model → `llm.thinking is None` and `"thinking"` is absent from the request payload.
- [ ] AC-05: `thinking_budget=2048` with a pinned `claude-haiku-4-5` → payload `thinking == {"type": "enabled", "budget_tokens": 2048}` and `llm.temperature == 1` (FR-071 unchanged).
- [ ] AC-06: a parametrised test over the 14 model ids of `evidence/FR-1148-thinking-off-probe.md` asserts the mapping recorded there (1 × `between_tools`, 3 × raise, 10 × `disabled`).
- [ ] AC-07: `tests/unit/test_thinking_budget.py::TestCreateLLMThinking::test_thinking_budget_zero_no_thinking` is amended to the new contract with an explicit `model=`; no test in the file resolves its model from `ANTHROPIC_MODEL`.
- [ ] AC-08: `yamlgraph/utils/anthropic_thinking.py` exists and holds the rule; `yamlgraph/utils/llm_providers.py` ≤ 450 lines; `lint-imports` passes; `pre-commit run --files <changed files>` passes.
- [ ] AC-09: every new test carries `@pytest.mark.req("REQ-YG-083")` (class marker); the RED commit precedes the GREEN commit in `git log`.
- [ ] AC-10: `capabilities/CAP-28-graph-level-thinking-budget.yaml` REQ-YG-083 description states the `0` contract and lists the two provider modules; `ARCHITECTURE.md` regenerated via `scripts/aggregate_capabilities.py`; `python scripts/req_coverage.py --strict` exits 0.
- [ ] AC-11: `reference/graph-yaml.md` L84 comment, L94 defaults table, L278 node table and L1032 race table, plus the `create_llm` docstring, all state what `0` does per model and that `0` does not force `temperature=1`.
- [ ] AC-12: `changelog/unreleased/fr-1148-anthropic-thinking-off.md` with `type: fix`, `scope: llm`, `req: REQ-YG-083`.
- [ ] AC-13: the FR's Implementation Status records one executed `create_llm(..., model="claude-sonnet-5-5", thinking_budget=0, max_tokens=1500).invoke(...)` with `stop_reason`, block types and text length; text length > 0 and no thinking block.
- [ ] AC-14: `yamlgraph graph lint examples/demos/thinking/graph.yaml` is clean and the graph compiles unchanged (no edit to the demo).
- [ ] AC-15: `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` passes.
- [ ] AC-16: `docs/diary/diary-2026-10-25-reflection-fr-1148-the-push-that-skipped-the-gates.md` exists, names the trap behind the gate-skipping push, and carries a **Seed:**.
- [ ] AC-17: no commit on the branch carries a `Co-authored-by` trailer and none used `--no-verify`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 … R-9 are folded into the FR file and committed **before** the first implementation commit. The folded FR is the authority; this judgement is not. | GATE |
| C-2 | No network call, SDK capability query, or 400-retry in the construction path. The rule is a static table. | GATE |
| C-3 | If any prefix rule changes, the probe is re-run and `evidence/FR-1148-thinking-off-probe.md` is updated **in the same commit** as the rule and the AC-06 table. Rules and evidence never drift apart. | GATE |
| C-4 | RED commit (failing tests, `SKIP=pytest`) precedes GREEN; `git log` is the proof trail. | GATE |
| C-5 | Nothing outside the D-1 … D-9 surfaces is touched. In particular no `effort` surface, no other provider branch, no lint code, no demo edit, no `main` history operation. | GATE |
| C-6 | AC-13's live witness is executed and recorded before the PR is marked ready. A unit-only landing of this change is not acceptable: both probes crossed the raw SDK boundary, not the `ChatAnthropic` one. | GATE |
| C-7 | This FR follows the normal route end to end — branch, PR, required checks, human merge. Given its origin, the enforcer must not self-certify; supervision and merge are the human's. | GATE |

**Questions for the human (not absorbed by this judgement):**

1. **Behaviour change, loud.** Today `thinking_budget: 0` on `claude-opus-5-5` /
   `claude-fable-5.x` runs fine (a silent no-op). After this FR it raises. The FR
   argues for the raise (Alternative G, "Raise instead of pretending") and I
   concur, but it is a product call: confirm loud failure over warn-and-omit.
2. **Spend.** AC-13 costs one ~1500-token Sonnet 5.5 call; AC-14 is lint-only. If
   live calls are off-budget in this session, say so and AC-13 becomes owed work
   recorded in the FR rather than a merge blocker.

Authority granted: after R-1 … R-9 are folded and committed, the enforcer may
implement the `thinking_budget == 0` branch for the Anthropic provider — a new
`yamlgraph/utils/anthropic_thinking.py` holding the three static prefix rules
derived from Probe A, one call to it from `_create_anthropic_llm`, the tests of
AC-01 … AC-07 and AC-13, and the registry, documentation, changelog and diary
artifacts of D-5 … D-9. Nothing else.
