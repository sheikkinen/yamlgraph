# Judgement: FR-1152 `--token-usage` counts thinking tokens

**Prior art:** [FR-1152-thinking-tokens-in-token-usage.md](FR-1152-thinking-tokens-in-token-usage.md) — the FR this judgement rules on, not precedent; dismissed; its own Prior art line dispositions FR-231, FR-1151 and FR-1148. (Added by the FR author at promotion to satisfy the FR-738 gate; not judge output. Backend: `JUDGE_BACKEND=claude scripts/judge.sh`, 2026-10-25, round 1.)

**Verdict:** APPROVED WITH REVISIONS — the mechanism is real and verified in the installed dependency, and the scope is genuinely one field; but the FR does not account for two existing exact-dict assertions its change breaks, never states that thinking tokens are a *decomposition* of `output_tokens` rather than an addition to them, and cites no raw sample in which the count is non-zero. Authority activates when R-1..R-8 are folded into the FR file.

**Reviewed against:** `feature-requests/FR-1152-thinking-tokens-in-token-usage.md`; `yamlgraph/utils/token_tracker.py`; `yamlgraph/cli/graph_run_helpers.py` (L246-278, L75-86, L346-371); `yamlgraph/cli/bench_commands.py` (L189-228); `tests/unit/test_fr027_execution_safety.py` (L1044-1161); `capabilities/CAP-17-execution-safety-guards.yaml`; `ARCHITECTURE.md` L825; `capabilities/CAP-08-*.yaml`, `CAP-03-*.yaml` (`fr:` list form); the cited prior art `feature-requests/FR-1151-anthropic-effort.md` (incl. its judgement fold and CI addendum), `FR-231-model-provider-timing-comparison.md`, `FR-1148-anthropic-thinking-off.md`; the cited dependency evidence `.venv/Lib/site-packages/langchain_anthropic/chat_models.py` L2967-3002 and `.venv/Lib/site-packages/langchain_core/messages/ai.py` L83-153; `.github/skills/judge-fr/doctrine.md`; `.github/copilot-instructions.md`; `reference/getting-started.md` L110. No judgement file exists for this FR — this is round 1 (FR-1022 sentinel not armed). No author transcript or working notes were consumed.

## What is sound

- **The mechanism is verified, not asserted.** The FR's central claim checks out against the installed package: `langchain_anthropic/chat_models.py:2974-3000` builds `output_token_details = {"reasoning": getattr(getattr(anthropic_usage, "output_tokens_details", None), "thinking_tokens", None)}` and attaches it to `UsageMetadata` when not `None`. The normalised key name (`output_token_details`, singular "token") and the `reasoning: int` member are confirmed in `langchain_core/messages/ai.py:96,153`. The FR's quoted comment is the real one.
- **The boundary choice is the right one.** Alternative B (reading Anthropic's raw `response_metadata.usage.output_tokens_details.thinking_tokens`) is rejected for exactly the reason doctrine gives: normalise where external data enters, and LangChain already owns that boundary. The chosen field also carries OpenAI/DeepSeek reasoning counts for free, which keeps the handler's own docstring claim ("provider-independent") true.
- **Scope is minimal and the alternatives table earns its place.** Four solution classes with real dispositions, `is_this_a_graph` answered ("no — one more field summed in a callback") and correct. Alternative D (print `0 thinking` always) is rejected on the right ground, and that rejection is what keeps existing output stable.
- **Prior art is dispositioned.** FR-231, FR-1151 and FR-1148 are each distinguished with a reason, and FR-1148's subtraction estimate is named as the thing being replaced — the value statement is not hypothetical. The claim "no rejected FR covers this territory" holds: of the six FRs carrying `Status: Rejected`, none concerns token accounting.
- **The first consumer is named with an event**, not a hope: game-engine stage 5, one Opus 5.5 plan call at effort `low`, run on merge.

## Required revisions

### R-1: Account for the two existing exact-dict assertions this change breaks

`summary()` is asserted by *equality*, not by membership, in two places:

- `tests/unit/test_fr027_execution_safety.py:1128-1133` — `assert summary == {"total_input_tokens": 100, "total_output_tokens": 50, "total_tokens": 150, "total_calls": 1}`
- `tests/unit/test_fr027_execution_safety.py:1143-1148` — the all-zeros twin

Adding `total_reasoning_tokens` turns both red. The FR lists this test file in its `commands:` block but no AC, no Proposed Solution step and no deviation note says the assertions change. Fold into Proposed Solution: both assertions gain `"total_reasoning_tokens": 0`, the two tests are named by file and line, and the FR states plainly that `summary()`'s returned dict gains a key — a contract change for any consumer comparing the dict whole (the game-engine runner included). Nothing else in that file may be touched.

### R-2: State that thinking tokens decompose `output_tokens` and do not add to it

`chat_models.py:2974` is explicit: "Reasoning (thinking) tokens are a decomposition of `output_tokens` (not additive)". The FR's Problem 3 knows this ("billed inside `output_tokens`") but neither the Ideal Result, the Proposed Solution nor any AC forbids folding the new count into `total_tokens`. An enforcer reading only the Proposed Solution could plausibly double-count. Fold: `summary()["total_tokens"]` stays `total_input_tokens + total_output_tokens` exactly as today; the handler docstring and REQ-YG-064's description say the thinking count is a subset of the output count; add the AC in the revised list below.

### R-3: Coerce a `None` reasoning value to 0 at the boundary

Proposed Solution 1 reads `(usage.get("output_token_details") or {}).get("reasoning", 0)`. `langchain_anthropic` filters `None` out before constructing `OutputTokenDetails` (`chat_models.py:2994-2997`), but nothing in the normalised contract obliges another provider's integration to do the same — `reasoning` is a plain `NotRequired[int]`, and a present-but-`None` value makes `self.total_reasoning_tokens += None` raise `TypeError` inside a callback, aborting a paid run. Fold the trailing `or 0` into the Proposed Solution expression and add the AC below. This is the One Law applied to the same boundary the FR already chose; it costs three characters.

### R-4: One raw witness in which the count is non-zero — run, or recorded as owed

Every cited sample has thinking at zero. The only live evidence in the FR is FR-1151's call, quoted in Problem 2: `'output_tokens_details': {'thinking_tokens': 0}` — and that is the *raw* Anthropic field, not the normalised `usage_metadata` this FR actually sums. The FR therefore has no record of the path it implements producing a non-zero number, and all six ACs are satisfiable by hand-built fakes. That is the shape `plausible_wrong_answer` warns about: the suite goes green and the first consumer's cost record reports `0 thinking` forever, indistinguishable from "this model did not think".

Fold an AC requiring one live call whose `message.usage_metadata` dict is pasted verbatim into the FR, showing `output_token_details` with `reasoning` greater than zero — or the AC recorded as **owed** in both the FR and the PR body with its blocker named, exactly as FR-1151's AC-11 was framed by R-7 of its judgement. No simulated or reconstructed transcript. Note for the enforcer: FR-1151's effort-`low` Opus call returned `thinking_tokens: 0`, so reaching a non-zero count will need a different effort level or a `thinking_budget` model — see the spend question below.

### R-5: Record the dependency version the normalisation was observed in, and the degradation rule

FR-1151's CI addendum is the precedent: local `langchain-anthropic` 1.7.0 and CI's 1.7.6 disagreed about `thinking`, and the FR had to be amended after CI. The same exposure exists here — `pyproject.toml`'s floor is `langchain-anthropic>=1.5.1`, and this FR depends on a normalisation whose presence the FR has only checked in one installed version. Fold: the FR names the version in which `chat_models.py:2974-3000` was observed, states that providers or versions that omit `output_tokens_details` simply contribute 0 (the AC-02 path, not an error), and states that no dependency floor is raised by this FR.

### R-6: Name the surfaces this does not reach, and name the surface the first consumer reads

The FR has no **Out of scope** section. Three adjacent surfaces carry token data and are silently untouched:

- `--json` mode prints **no** token usage at all today — `_print_json_result(result, tally)` (`graph_run_helpers.py:75-86`) carries only `_error_count` and `_tolerated_error_count`; the tracker never reaches it.
- `bench` sums `total_input_tokens` and `total_output_tokens` only (`bench_commands.py:225-227`) and will not report thinking.
- the async run path.

Fold an **Out of scope** section naming all three, and state in the first-consumer paragraph which surface the game-engine runner actually reads — the printed line, `summary()` in Python, or `--json`. If the answer is `--json`, this FR delivers nothing to its stated first consumer and must be amended before enforcement (see Conditions).

### R-7: Make the registry bookkeeping exact

Proposed Solution 3 is under-specified in two ways:

- The printed line lives in `yamlgraph/cli/graph_run_helpers.py`, which appears in neither REQ-YG-064's `modules:` (`cli/graph_commands`, `cli/__init__`, `utils/token_tracker`) nor CAP-17's module list. Fold: both gain `cli/graph_run_helpers`.
- CAP-17's `fr:` is the scalar `legacy`, not a list. Fold the precedent form explicitly: `fr: legacy, FR-1152`, as `CAP-08-error-handling.yaml:45` (`legacy, FR-1124`) and `CAP-03-node-execution.yaml:81` already do. The changelog fragment's `req: REQ-YG-064` depends on this edit landing with it.

### R-8: Record the naming rule

The dict key is `total_reasoning_tokens`, the printed word is `thinking`, and the FR title says "thinking tokens". That is defensible — LangChain's normalised field is `reasoning`, the provider's and the user's word is `thinking` — but it is nowhere stated, so the next contributor will "fix" one of them. Fold one sentence into the Summary recording the rule: the public dict key follows LangChain's normalised field name; the human-facing label follows the provider's term.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/utils/token_tracker.py` — `total_reasoning_tokens` attribute, the `on_llm_end` sum, the `summary()` key, docstring |
| D-2 | `yamlgraph/cli/graph_run_helpers.py` L262-269 — the `, {N} thinking` suffix, emitted only when the count is greater than zero |
| D-3 | `tests/unit/test_fr1152_thinking_tokens.py` (new) and the two equality assertions at `tests/unit/test_fr027_execution_safety.py:1128,1143` — nothing else in that file |
| D-4 | `capabilities/CAP-17-execution-safety-guards.yaml` (REQ-YG-064 description, both module lists, `fr:`); `ARCHITECTURE.md` regenerated |
| D-5 | `changelog/unreleased/` fragment; a `docs/diary/` entry with a **Seed:** |

**Not authorized by this FR:** token usage in `--json` output; thinking tokens in `bench` results; any dollar/cost computation or price table; any new CLI flag or env var; any change to `total_tokens`'s definition; reading Anthropic's raw `response_metadata` (Alternative B); printing the count when it is zero (Alternative D); any change to `timing_tracker.py`; any change to the async executor path; raising the `langchain-anthropic` floor; refactoring `token_tracker.py` beyond the added field; touching any test in `test_fr027_execution_safety.py` other than the two named assertions.

## Revised acceptance criteria

- [ ] AC-01: two fake LLM results with `output_token_details: {reasoning: 30}` and `{reasoning: 12}` give `summary()["total_reasoning_tokens"] == 42`; input, output and call counts unchanged.
- [ ] AC-02: a result without `output_token_details`, and one with `output_token_details` lacking `reasoning`, each add 0 and do not raise.
- [ ] AC-03: the printed line with reasoning tokens ends `(2 calls), 42 thinking`; with a zero count the full line equals today's string character for character (assert the literal, not a prefix).
- [ ] AC-04: tests in `tests/unit/test_fr1152_thinking_tokens.py`, each carrying a `@pytest.mark.req("REQ-YG-064")` **decorator** (module-level `pytestmark` is not counted by `scripts/req_coverage.py`); committed failing (RED) before the code (GREEN), the RED output pasted into the FR.
- [ ] AC-05: REQ-YG-064's description names the thinking count and says it is part of the output count; REQ-YG-064's `modules:` and CAP-17's `modules:` both include `cli/graph_run_helpers`; CAP-17's `fr:` reads `legacy, FR-1152`; `ARCHITECTURE.md` regenerated; `python scripts/req_coverage.py --strict` exits 0; changelog fragment `type: feat`, `req: REQ-YG-064`; diary with a **Seed:**.
- [ ] AC-06: `pre-commit run --files <changed files>` passes apart from any `SKIP=pytest`, recorded with its commit and reason in the PR body; no `--no-verify`; no `Co-authored-by` trailer.
- [ ] AC-07 (R-1): `tests/unit/test_fr027_execution_safety.py:1128` and `:1143` include `"total_reasoning_tokens": 0` in their expected dicts and pass; the rest of the file is unmodified; the FR records that `summary()` gained a key.
- [ ] AC-08 (R-2): with `reasoning: 30` and `output_tokens: 80` on one result, `summary()["total_tokens"] == summary()["total_input_tokens"] + 80` — the thinking count is not added to the total; the handler docstring states the decomposition.
- [ ] AC-09 (R-3): a result whose `output_token_details` is `{"reasoning": None}` adds 0 and does not raise.
- [ ] AC-10 (R-4): one live call whose `message.usage_metadata` is pasted verbatim into the FR with `output_token_details["reasoning"] > 0`, and whose printed `--token-usage` line is pasted with it — or the AC recorded as **owed** in the FR and the PR body with the blocker named. No simulated transcript.
- [ ] AC-11 (R-5): the FR names the `langchain-anthropic` version in which `chat_models.py`'s reasoning normalisation was observed, states that versions or providers omitting `output_tokens_details` contribute 0, and states that no dependency floor changes.
- [ ] AC-12 (R-6): the FR carries an **Out of scope** section naming `--json`, `bench`, and the async path, and its first-consumer paragraph names the surface the game-engine runner reads.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | A run with no reasoning tokens prints the current line unchanged, character for character | GATE |
| C-2 | `summary()["total_tokens"]` remains `input + output`; the thinking count is never added into it | GATE |
| C-3 | RED commit (failing tests, `SKIP=pytest`) precedes the GREEN commit; both in `git log` | GATE |
| C-4 | No edit to `--json` output, `bench_commands.py`, `timing_tracker.py`, or the async path | GATE |
| C-5 | AC-10 is either run and pasted verbatim, or recorded as **owed** with its blocker; never reconstructed | GATE |
| C-6 | Edits to `test_fr027_execution_safety.py` are confined to the two expected dicts at L1128 and L1143 | GATE |
| C-7 | If the first consumer's surface (R-6) turns out to be `--json`, enforcement stops and the FR returns to plan | GATE |

**Questions for the human — not absorbed into this judgement:**

1. **Spend.** AC-10 needs a call that actually thinks. FR-1151's effort-`low` Opus 5.5 call returned `thinking_tokens: 0`, so the witness will cost more than that run's ~$0.01 (a higher effort level, or a `thinking_budget` model). Approve the spend, or direct that AC-10 be recorded as owed.
2. **Reader hazard in the printed line.** `📊 Token usage: 1200 in / 800 out (1 call), 650 thinking` invites a reader to add 650 to 800, when the 650 is inside the 800. The FR's format is accepted as written; if the line should mark the subset (e.g. placing the count beside `out`), that is a product decision to make before D-2 is written, not after.
3. **Dollar figures.** The first consumer wants "tokens, thinking tokens and dollars per step". This FR delivers the first two; the dollars are computed outside yamlgraph and are not authorized here. Confirm that is the intent.

**Research note (FR-890):** the in-body table is accepted on substance — four genuine solution classes, real dispositions, `is_this_a_graph` answered and correct. It is thin at the edges: classes B and D carry no precedent line. Sufficient for a change of this size; not a pattern to lean on for a larger one.

Authority granted: once R-1..R-8 are folded into the FR file, the enforcer may add `total_reasoning_tokens` to `TokenUsageCallbackHandler` and its `summary()`, append the `, N thinking` suffix to the `--token-usage` line when that count is greater than zero, write the new test file, update the two named equality assertions, and land the REQ/CAP/changelog/diary bookkeeping — nothing else.
