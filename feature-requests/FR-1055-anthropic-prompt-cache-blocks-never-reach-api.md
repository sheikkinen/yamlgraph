# Feature Request: Anthropic prompt-cache blocks never reach the API (and the system prompt is dropped with them)

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-09-23
**First consumer / first event:** `yamlgraph-visual-novel` FR-008, Pass C —
the first of 14 per-character calls that each re-send an identical ~70k-token
book prefix. That FR was written around prompt caching (~$2.94 -> ~$0.53 per
run) and cannot be built on `system_segments` until this is fixed.
**Research:** in-body dispositioned alternatives table (FR-889 style), below.
Every row is a probe that was executed, not a position argued.
**Prior art:**
- [FR-276.md](FR-276.md) — implemented `system_segments` + `cache: true`. This
  FR fixes the defect in that implementation; it does not re-litigate the
  design, which is right.
- [FR-219.md](FR-219.md) — the caching demo. Its AC "Second LLM call benefits
  from Anthropic prompt cache" was checked off while its own Next Steps line
  still read "Verify cache hits in Anthropic usage logs (if accessible)". That
  gap is the subject here.
- [FR-382-prompt-caching-chaplain-system-prompts.md](FR-382-prompt-caching-chaplain-system-prompts.md)
  — a consumer of the feature. If it uses `system_segments` with
  `provider: anthropic`, **its system prompts are currently empty**; it needs
  re-verification after the fix, not just a version bump.
- [FR-381-batch-llm-node-anthropic-messages-batch-api.md](FR-381-batch-llm-node-anthropic-messages-batch-api.md)
  — mentions `cache_control` for the batch path; same construction, so likely
  the same defect. Distinguished: this FR fixes the shared builder only.
- [FR-449-agent-structured-output-anthropic-bugfix.md](FR-449-agent-structured-output-anthropic-bugfix.md)
  — also an Anthropic message-shape bugfix, but in structured output, not the
  system message. No overlap.

## Summary

`_build_system_message_from_segments()` stores Anthropic content blocks in
`SystemMessage.additional_kwargs["content"]`. `langchain_anthropic` reads only
`SystemMessage.content`, which yamlgraph sets to `""`. The blocks are silently
discarded. The consequence is not merely "caching is off" — **the entire system
prompt is dropped**, and the model receives only the user message. No error, no
warning.

## Value Statement

Graph authors who ask for prompt caching get it — and, more urgently, stop
silently losing their system prompt on every Anthropic call that uses
`system_segments`.

## Problem

### What the code does

`yamlgraph/executor_base.py:334-337`:

```python
# Create SystemMessage with content blocks in additional_kwargs
return SystemMessage(
    content="",  # Empty content, actual content in additional_kwargs
    additional_kwargs={"content": content_blocks},
)
```

`langchain_anthropic/chat_models.py:_format_messages` handles system messages
with `system = _format_system_content(message.content)`. It never consults
`additional_kwargs`. With `content=""` the result is `system=''`.

### Executed probe (no network)

Both real code paths, composed:

```python
msg = _build_system_message_from_segments(
    [{"content": "BOOK TEXT ...", "cache": True},
     {"content": "You extract characters.", "cache": False}],
    {}, None, "anthropic")
system, formatted = _format_messages([msg, HumanMessage(content="...")],
                                     model="claude-sonnet-4-5")
```

Observed:

```
yamlgraph SystemMessage.content = ''
yamlgraph additional_kwargs     = {'content': [{'type': 'text', 'text': 'BOOK TEXT ...',
                                   'cache_control': {'type': 'ephemeral'}}, ...]}

=> what langchain sends as `system`: ''
=> messages: [{'role': 'user', 'content': '...'}]

cache_control reaches API?  False
system prompt survives?     False
```

yamlgraph builds the blocks **correctly**. They are then thrown away one layer
down.

### Why eight passing tests did not catch it

`tests/unit/test_prompt_caching_fr276.py` asserts the producer's own output
shape on every Anthropic case:

```python
assert cache_blocks[0].get("cache_control") == {"type": "ephemeral"}
#      ^ read back out of system_msg.additional_kwargs
```

No test calls `_format_messages`. The suite verifies that yamlgraph wrote into
a box; nothing verifies that the consumer opens that box. An unexercised link
passes every test of the chain. Two artifacts agreeing that the feature works
(the tests and FR-219's checked AC) are one assumption copied, not two
observations — both consult the same side of the seam.

Whether this *ever* worked is unverified: no test crossed the seam, so a
regression from a `langchain-anthropic` upgrade and a defect present since
FR-276 are indistinguishable from inside this repo. The defect is **not
version-gated within the declared range**: `pyproject.toml` declares
`langchain-anthropic>=1.5.1` with no upper bound, and the probe above
reproduces on this repo's resolved **1.5.2** — the floor of that range. An
upgrade is therefore not the suspect, and the version pin is not the cure.

### Blast radius

- Any prompt using `system_segments` with `provider: anthropic` -> **empty
  system prompt**.
- Any prompt using the `system:`-as-list form with `provider: anthropic` ->
  same, it routes through the same builder (`executor_base.py:253`, `:273`).
- Scalar `system:` (the overwhelmingly common form, 213 files per FR-219) is
  **unaffected** — it takes the `SystemMessage(content=system_text)` branch.
  Anthropic passes string system content through uncached by design, so scalar
  users lose nothing except the ability to cache.

Nothing in yamlgraph reads `additional_kwargs["content"]` back; the three
matches in the package are all at the construction site. So the field has no
other consumer to break.

In-repo consumers, enumerated (`grep -rln system_segments --include='*.yaml'`):
`examples/demos/prompt-caching/` is the **only** one, and it is a *shipped
demo* — `graph.yaml:13` sets `provider: anthropic` and both
`prompts/analyze.yaml` and `prompts/reflect.yaml` use `system_segments`. The
demo is therefore running today with an empty system prompt, and its committed
`demo-output.log` is a record of the broken behaviour, not of the feature.
This makes the demo the cheapest in-repo witness for the fix.

## Ideal Result

A `cache: true` segment produces a real `cache_control` breakpoint on the wire,
the system prompt arrives intact, and a test fails the moment either stops
being true — regardless of which side of the yamlgraph/LangChain seam causes
it.

## Proposed Solution

Pass the blocks where the consumer looks. One line:

```python
# yamlgraph/executor_base.py, _build_system_message_from_segments
if provider == "anthropic":
    content_blocks = [...]
    return SystemMessage(content=content_blocks)   # was: content="", additional_kwargs=...
```

Verified by execution — same probe, with the blocks in `content`:

```
system = [{'type': 'text', 'text': 'BOOK TEXT ...',
           'cache_control': {'type': 'ephemeral'}},
          {'type': 'text', 'text': 'You extract characters.'}]

cache_control reaches API? True
system prompt survives?    True
```

`_format_system_content` maps a list through `_format_text_block` per element,
preserving `cache_control`. Its docstring notes string content is deliberately
passed through unpromoted "to avoid invalidating existing callers' prompt
caches" — so the list form is the supported route, not a workaround.

### The test that should have existed

A seam test, not another producer-shape assertion:

```python
def test_cached_segments_reach_langchain_as_cache_control_blocks():
    """Walks producer -> consumer. Turns red if either side changes shape."""
    msg = _build_system_message_from_segments(
        [{"content": "STABLE", "cache": True}], {}, None, "anthropic")
    system, _ = _format_messages([msg, HumanMessage(content="x")],
                                 model="claude-sonnet-4-5")
    assert system, "system prompt must survive the seam"
    assert system[0]["cache_control"] == {"type": "ephemeral"}
```

This is also a drift detector: it passes today and turns red on the next
`langchain-anthropic` message-handling change, which is the failure mode that
produced this FR.

Note the existing Anthropic assertions in `test_prompt_caching_fr276.py`
(lines ~198, ~230, ~345) **encode the bug** — they assert `additional_kwargs`.
They must be rewritten against `.content`, not merely kept green.

## Acceptance Criteria

- [ ] `_build_system_message_from_segments` returns blocks in
      `SystemMessage.content` for `provider == "anthropic"`
- [ ] A test composes `_build_system_message_from_segments` with
      `langchain_anthropic._format_messages` and asserts both that the system
      prompt is non-empty and that `cache_control` survives
- [ ] The existing Anthropic tests asserting `additional_kwargs` are rewritten
      to assert `.content`
- [ ] Non-Anthropic providers still flatten to a single string (unchanged);
      scalar `system:` behaviour unchanged
- [ ] One live Anthropic run records non-zero `cache_read_input_tokens` on a
      second call sharing the prefix — the measurement FR-219 deferred. The
      number is pasted into this FR; "cache hints are present" is not evidence
      of a cache hit
- [ ] `examples/demos/prompt-caching` re-run after the fix; its regenerated
      `demo-output.log` replaces the log produced under the empty-system-prompt
      defect
- [ ] `langchain-anthropic` gains an upper bound, or the seam test is
      explicitly accepted as the drift guard in its place
- [ ] FR-382's chaplain prompts re-verified to have non-empty system prompts
- [ ] Documentation updated
- [ ] Released so `yamlgraph-visual-novel` FR-008 can pin it

## Alternatives Considered

| # | Alternative | Probe executed | Disposition |
|---|---|---|---|
| A | Blocks in `SystemMessage.content` | Ran both code paths composed; `cache_control: True`, system survives | **Chosen.** One line, uses the documented list form |
| B | Leave as-is, document `system_segments` as Anthropic-only-broken | — | Rejected. Silent loss of the system prompt is a correctness bug, not a caching shortfall |
| C | Subclass/patch `ChatAnthropic` to read `additional_kwargs` | Not run | Rejected. Forks a vendor message contract to preserve a field no consumer wants; A is strictly smaller |
| D | Consumers avoid `system_segments`, use scalar `system:` | Confirmed scalar path is correct and uncached | Rejected as a fix, accepted as the **interim workaround** for consumers on <=0.5.25. Forfeits caching entirely — Anthropic has no implicit-cache fallback; `cache_control` breakpoints are required |
| E | Drop to a cheaper model instead of caching | Costed for the first consumer: cached Sonnet ~$0.53 < uncached Haiku ~$0.98 | Rejected. Caching saves more than the model downgrade **and** costs no capability |

## Related

- `yamlgraph/executor_base.py:289-341` — `_build_system_message_from_segments`
- `yamlgraph/executor_base.py:211-275` — both routes into that builder
- `tests/unit/test_prompt_caching_fr276.py` — the tests that pass regardless
- `langchain_anthropic/chat_models.py` — `_format_messages`,
  `_format_system_content`
- Consumer: `yamlgraph-visual-novel` FR-008 (whole-book character extraction)
- Reproduced against yamlgraph 0.5.23 (installed in the consumer) and confirmed
  identical on `main` at 0.5.25
