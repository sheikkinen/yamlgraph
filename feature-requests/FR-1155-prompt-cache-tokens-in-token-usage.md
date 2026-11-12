# Feature Request: FR-1155 `--token-usage` counts prompt-cache reads and writes

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Requested:** 2026-11-12

**First consumer / first event:** game-engine's cost records, brief 441 (P0).
- `run.py`, `chapter_music.py` and `character_map.PRICE` parse the printed `📊 Token usage: N in / M out` line and
  price all of `N` at the full input rate.
- Brief 441 plans to move shared chapter material into cached `system_segments`. That change cannot be priced, and
  cannot even be checked to have worked, until the line splits `N` into reads and writes.
- The first event is the first game-engine run after this merges with a cached segment: its cost record shows
  `cache read` > 0.

**Research:**
- Desk research: [docs/research-prompt-caching-2026-11-12.md](../docs/research-prompt-caching-2026-11-12.md),
  recommendations R0 and R1.
- Live spike record: [FR-1155.research.md](FR-1155.research.md). It covers 26 single calls and 72 calls made in the
  shape of a map fan-out, on `claude-haiku-5-5` and `claude-sonnet-5-5`, with the raw `usage_metadata` quoted.

**Prior art:**
- [FR-1152-thinking-tokens-in-token-usage.md](FR-1152-thinking-tokens-in-token-usage.md) uses the same pattern for
  thinking tokens: one more `usage_metadata` field summed, and a `, N thinking` suffix on the printed line. This FR
  follows it exactly.
- [FR-1055-anthropic-prompt-cache-blocks-never-reach-api.md](FR-1055-anthropic-prompt-cache-blocks-never-reach-api.md)
  made `cache_control` reach the API. It recorded its live hit verification as blocked; this FR's live witness closes
  that gap.
- [FR-276](FR-276.md) added `system_segments` and CAP-131.
- REQ-YG-064 (CAP-17) is the tracker's requirement.
- No rejected FR covers this area.

## Summary

`TokenUsageCallbackHandler` also sums the cache tokens that LangChain normalises into
`usage_metadata["input_token_details"]`.
- `summary()` gains `total_cache_read_tokens` and `total_cache_write_tokens`.
- The `--token-usage` line appends `, R cache read` and `, W cache write`, each only when greater than 0.

Both counts are **parts of** `input_tokens`, never added to it. `langchain_anthropic` reports `input_tokens` as
uncached + read + write; the spike shows raw `input_tokens` 11 becoming normalised 2938 = 11 + 2927.

## Value Statement

Graph authors using `system_segments` can see whether the cache hit, and can price input honestly. A read costs 0.1×
on Haiku 5.5 and 0.05× on Sonnet 5.5; a write costs 1.25×. Today `--token-usage` prints the same 2938 for a write and
for a read.

## Problem

1. `token_tracker.py` reads `input_tokens`, `output_tokens` and `output_token_details.reasoning`. It ignores
   `input_token_details`.
2. **The write count is not where its name says.** In `langchain-anthropic` 1.7.0, when Anthropic sends the per-TTL
   breakdown, `input_token_details.cache_creation` is **0** and the written tokens are in
   `ephemeral_5m_input_tokens` or `ephemeral_1h_input_tokens`. The spike's write call shows:
   `{cache_read: 0, cache_creation: 0, ephemeral_5m_input_tokens: 2927, ephemeral_1h_input_tokens: 0}`, while the raw
   `cache_creation_input_tokens` is 2927. A meter that summed `cache_creation` would report that nothing was ever
   written. The rule must be fixed at this boundary, not in the consumers.
3. Caching can also cost money and nobody can see it:
   - a breakpoint on a varying segment writes every time and never reads (spike case C);
   - automatic top-level caching on a single-shot node does the same (case F);
   - a cold parallel map writes once per concurrent branch (map spike).

   Without meters, none of these can be seen.

## Ideal Result

`yamlgraph graph run … --token-usage` on a two-call run whose second call hits prints:

`📊 Token usage: 5876 in / 64 out (2 calls), 64 thinking, 2927 cache read, 2927 cache write`

- `summary()["total_cache_read_tokens"] == 2927` and `summary()["total_cache_write_tokens"] == 2927`.
- A provider that reports no cache details adds 0.
- A run with no cache activity prints a line identical, character for character, to today's.
- One live test proves the cache hit through yamlgraph's own `system_segments` path.

## Planned Operations

```yaml
probes:
  - "fake usage_metadata with input_token_details in each of the three observed shapes (offline)"
  - "one live two-call Haiku 5.5 run through _build_system_message_from_segments (the AC-08 witness)"
branches:
  - "a provider reports cache_creation AND an ephemeral breakdown that disagree -> max() rule, recorded, not summed"
delegations:
  - "judge.sh: 1 run (JUDGE_BACKEND=claude)"
waits: ["judge", "CI", "the operator's merge decision"]
commands:
  - JUDGE_BACKEND=claude bash scripts/judge.sh feature-requests/FR-1155-prompt-cache-tokens-in-token-usage.md
  - pytest -q --no-cov tests/unit/test_fr027_execution_safety.py tests/unit/test_fr1152_thinking_tokens.py tests/unit/test_fr1155_cache_tokens.py
  - pytest -q --no-cov tests/integration/test_fr1155_cache_read_live.py
  - PYTHONUTF8=1 pre-commit run --files <changed files>
```

## Proposed Solution

1. **`yamlgraph/utils/token_tracker.py`:**
   - Add `total_cache_read_tokens` and `total_cache_write_tokens`. Both are summed in `on_llm_end` from
     `d = usage.get("input_token_details") or {}`, where a `None` value counts as 0:
     - read = `d.get("cache_read") or 0`
     - write = `max(d.get("cache_creation") or 0, (d.get("ephemeral_5m_input_tokens") or 0) + (d.get("ephemeral_1h_input_tokens") or 0))`
   - **Why `max`:**
     - 1.7.0 zeroes `cache_creation` when the breakdown is present.
     - A version or provider without the breakdown reports `cache_creation` alone.
     - A future version that filled both would be counted twice by a sum, and once by `max`.
   - `summary()` adds both keys. This changes the dict's contract: the two exact-dict assertions in
     `tests/unit/test_fr027_execution_safety.py` (L1133 and L1149 area) gain both keys as 0.
   - The docstring states that both counts are parts of the input count, never added to it.
2. **`yamlgraph/cli/graph_run_helpers.py`:** the printed line appends `, {R} cache read` when R > 0, then
   `, {W} cache write` when W > 0, after the FR-1152 thinking suffix. With both at 0 the line is unchanged.
3. **REQ-YG-064 and CAP-17:**
   - REQ-YG-064's description names the cache read and write counts, the `max` rule, and that both are parts of the
     input.
   - CAP-17's `fr:` reads `legacy, FR-027, FR-1152, FR-1155`.
   - `ARCHITECTURE.md` is regenerated.
4. **The live witness:** `tests/integration/test_fr1155_cache_read_live.py::test_anthropic_system_segment_cache_read_live`.
   - It is skipped when there is no `ANTHROPIC_API_KEY`, and carries `@pytest.mark.req("REQ-YG-064")` and
     `@pytest.mark.req("REQ-YG-289")`.
   - It makes two `claude-haiku-5-5` calls with `max_tokens=32`. Both use the same nonce-prefixed segment of more
     than 2,000 tokens with `cache: true`, built by `_build_system_message_from_segments`, and a different user line.
   - It asserts that the tracker's write count is > 0 after call 1 and its read count is > 0 after call 2.
   - Cost: under a cent.
5. **Housekeeping:** a changelog fragment with `type: feat` and `req: REQ-YG-064`, and a diary entry.

## Alternatives Considered

**is_this_a_graph:** no. It adds two more fields to a callback.

| # | Solution class | Precedent | Disposition |
|---|---|---|---|
| A | **Sum the normalised `input_token_details`, with the `max` write rule** (chosen) | FR-1152 | Provider-independent: OpenAI's `cache_read` is counted too |
| B | Sum `cache_creation` only | — | Rejected: the spike shows it is 0 on every write in 1.7.0 |
| C | Sum `cache_creation` + the ephemeral fields | — | Rejected: counts twice if a version fills both |
| D | Read Anthropic's raw `response_metadata.usage` | — | Rejected: provider-specific, at a boundary LangChain already normalises |
| E | Rewrite the line as `N in (R read, W write) / M out` (R0's draft) | — | Rejected: breaks the consumers' `N in / M out` regexes |
| F | Print dollars | — | Rejected: no price sheet in yamlgraph; consumers price the tokens themselves |

## Out of scope

- `--json` output, `yamlgraph bench` and the async run path. All three are excluded for the same reasons as in
  FR-1152.
- Lint warnings for caching (research R2) and the documentation (R6).
- `ttl: 1h` and user-message breakpoints (R5). The spike shows both work through LangChain, but no consumer has
  asked for them.
- FR-381 batch mode (R3) and the FR-032 node cache (R4).
- Map warm-first. This is a follow-up; see below.

## Follow-up: warm-first map dispatch (not this FR)

The map spike ([FR-1155.research.md § Map fan-out spike](FR-1155.research.md)) shows that with a cached shared
segment, a cold parallel map pays one 1.25× write per concurrent branch:

| | Writes | Reads | Input cost vs no caching |
|---|---|---|---|
| Today, cold `par8` (12 items) | 8 | 4 | 0.87 (Haiku), 0.85 (Sonnet) |
| One item first, then fan out | 1 | 11 | 0.20 (Haiku), 0.15 (Sonnet) |

Some numbers for reading the table:
- At the default width W = 8, caching is a **net loss** for N ≤ about 10. The break-even is
  $N > W(1.25-r)/(1-r)$, where $r$ is the read multiplier.
- Warming first saves $(W-1)(1.25-r)$ prefix-equivalents per run, whatever N is.
- The price is one call's latency, measured at 0.7 to 1.8 s. Making the first real item the warmer adds no tokens.

A follow-up FR should decide between two designs:
1. **An explicit map option**, for example `warm_first: true` on the map node.
2. **Automatic**, triggered when the sub-node's prompt has a `cache: true` segment, the provider is Anthropic,
   N ≥ 2, and the shared prefix is at least the model's cache minimum. A minimum size is a possible extra condition.

The follow-up FR also needs to settle:
- **Mechanism:** branches with index > 0 wait on index 0's LLM call inside the same dispatch superstep. Splitting
  into two supersteps would touch FR-1073's dispatch token and `MapVerdict`, so it is avoided. If item 0 fails, the
  others proceed cold.
- **Unmeasured:** whether the cache becomes readable at the first streamed token rather than at the end of the
  response, and confirmation through a real `type: map` graph rather than the semaphore imitation.
- **Dependency:** it needs this FR's meters to prove the saving in real runs.
- **First consumer:** game-engine's library describe map, 9 to 140 items. Without warming, it loses money at the
  small end (about 1.12× at N = 9).

## Acceptance Criteria

- [ ] AC-01: Two fake results give summed totals:
  - result 1: `{cache_read: 0, cache_creation: 0, ephemeral_5m_input_tokens: 2927, ephemeral_1h_input_tokens: 0}`;
  - result 2: `{cache_read: 2927, cache_creation: 0, ephemeral_5m_input_tokens: 0, ephemeral_1h_input_tokens: 0}`;
  - expected: `summary()["total_cache_write_tokens"] == 2927` and `summary()["total_cache_read_tokens"] == 2927`;
  - input, output and call counts are unchanged.
- [ ] AC-02: The write rule:
  - `{cache_creation: 500}` with no breakdown counts 500;
  - `{ephemeral_1h_input_tokens: 700}` counts 700;
  - `{cache_creation: 900, ephemeral_5m_input_tokens: 900}` counts 900, not 1800.
- [ ] AC-03: Each of these adds 0 to both counts and does not raise:
  - a result without `input_token_details`;
  - one with an empty dict;
  - one whose values are `None`.
- [ ] AC-04: `total_tokens` stays input + output when the cache counts are > 0. The handler docstring states that
  the cache counts are parts of the input.
- [ ] AC-05: The printed line:
  - with read and write tokens, it ends `(2 calls), 2927 cache read, 2927 cache write`;
  - with thinking as well, it ends `, 64 thinking, 2927 cache read, 2927 cache write`;
  - with no cache activity, the full line equals today's literal string.
- [ ] AC-06: The tests are in `tests/unit/test_fr1155_cache_tokens.py`.
  - Each carries a `@pytest.mark.req("REQ-YG-064")` decorator.
  - They are committed failing (RED) before the code (GREEN), and the RED output is pasted into this FR.
- [ ] AC-07: The `tests/unit/test_fr027_execution_safety.py` exact-dict expectations gain both keys as 0. The rest of
  that file is unmodified.
- [ ] AC-08: The live witness from Proposed Solution 4 passes, and its printed counts are pasted into this FR. If it
  cannot run, the AC is recorded as **owed** with the blocker named. No simulated transcript.
- [ ] AC-09: The registry and housekeeping:
  - REQ-YG-064's description is updated and CAP-17's `fr:` gains FR-1155;
  - `ARCHITECTURE.md` is regenerated;
  - `python scripts/req_coverage.py --strict` exits 0;
  - there is a changelog fragment with `type: feat` and `req: REQ-YG-064`;
  - there is a diary entry with a **Seed:**.
- [ ] AC-10: `pre-commit run --files <changed files>` passes. Any `SKIP=pytest` is recorded with its commit. No
  `--no-verify` and no `Co-authored-by` trailer.
