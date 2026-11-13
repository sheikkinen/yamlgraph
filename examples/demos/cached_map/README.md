# Warm-first cached map

This demo reviews four short strings with one `cached_map` node and
Anthropic `claude-haiku-5-5`. Item 0 runs alone and, on a cold provider
cache, writes the shared prompt prefix. Items 1..3 then run together and
read that prefix. All four items still make LLM calls: this is prompt
caching, not a cache of completed answers.

`prompts/review.yaml` puts a deliberately long, stable editorial handbook
in the first `system_segments` block with `cache: true`. Only the user
turn, `{{ item }}`, changes between items. Each answer has a typed
`label` field; the map collects the answers into `answers`.

## Run

Install YAMLGraph with Anthropic support and set `ANTHROPIC_API_KEY`.
From the repository root:

```powershell
yamlgraph graph lint examples\demos\cached_map\graph.yaml
yamlgraph graph run examples\demos\cached_map\graph.yaml --token-usage
```

The graph supplies four default items through graph-level `variables`,
which the CLI merges into initial state, so no `--var` flags are necessary.
The output budget is 16 tokens per call. The single demo run makes four
calls without a separate synthetic warm-up request.

## Expected token usage

On a cold cache, the final `--token-usage` summary should include both
nonzero cache counts, approximately one shared prefix written and three
shared prefixes read:

```text
Token usage: <input> in / <output> out (4 calls), <about 3P> cache read, <about P> cache write
```

This is an illustrative format, not a captured measurement. `P` is the
provider's actual cached prefix token count; exact counts depend on
tokenization and structured-output instructions. Cache reads and writes
are parts of the input token count, not additional tokens to add to it.
An already warm cache can yield all reads instead of a new write.

`demo-output.log` is a real run (2026-11-13). The route log shows
`_map_review_warm` running alone (`fan_out: 1`) and then
`_map_review_sub` with `fan_out: 3`. The summary line was:

```text
Token usage: 35272 in / 44 out (4 calls), 26400 cache read, 8800 cache write
```

That is one 8800-token prefix written and three reads of it. Missing
credentials, provider errors, or zero cache counts do not demonstrate reuse.

Use ordinary `map` when prompts lack an eligible shared cached prefix.
Warm-first ordering adds approximately one worker's latency, and does
not force the provider to cache an ineligible prefix.
