# Feature Request: Anthropic prompt-cache blocks never reach the API (and the system prompt is dropped with them)

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced except AC-10 (live cache measurement blocked on credentials)
**Effort:** 0.5 days
**Requested:** 2026-09-23
**First consumer / first event:** `yamlgraph-visual-novel` FR-008, Pass C —
the first of 14 per-character calls that each re-send an identical ~70k-token
book prefix. That FR was written around prompt caching (~$2.94 -> ~$0.53 per
run) and cannot be built on `system_segments` until this is fixed.
**Research:** in-body dispositioned alternatives table (FR-889 style), below.
Every row is a probe that was executed, not a position argued.

**`is_this_a_graph`?** **No.** This is one deterministic provider-boundary
assignment plus focused Python tests. There is no per-item model operation, no
multi-stage LLM pipeline, and no subagent fan-out; `yamlgraph graph list` holds
no graph that is a better execution vehicle for a one-line message-construction
fix. (The paid verification in R-4 *runs* a graph —
`examples/demos/prompt-caching` — but as the witness, not as the implementation
route.)
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
`langchain-anthropic>=1.5.1` with no upper bound; the local venv resolves
**1.5.2** and CI resolves a later 1.7.x, and the probe above reproduces at the
floor. An upgrade is therefore not the suspect, and the version pin is not the
cure.

The range is not uniform, though, and the seam test found it: `_format_messages`
gained a **required** `model` keyword partway through 1.5.x -> 1.7.x. The test
detects the parameter and spans both. This is the drift-detection value arriving
before the feature even merged \u2014 the first CI run on a machine that resolved a
different version inside the declared range turned the test red.

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

## Operator decision (R-4)

**Question:** Approve one paid Anthropic verification run, with the raw second-
call usage record committed to `examples/demos/prompt-caching/demo-output.log`
and copied into this FR?

**Answer (2026-09-23, operator):** **Approved.** The run must show the second
call's exact non-zero cache-read field and value. The existing log's prose
`Cache hit!` (`demo-output.log:13-14`) is a claim, not a measurement, and does
not satisfy AC-10. A success-shaped log must never be synthesized.

## Implementation Status (2026-09-23)

**Enforced except AC-10.** Commits on `feat/fr-1055-anthropic-prompt-cache`:

| Commit | Content |
|---|---|
| `ccec1e77` | RED — seam test fails with `assert ''`: the system prompt is dropped, not merely uncached |
| `2af5cf90` | GREEN — blocks moved to `SystemMessage.content`; three producer assertions rewritten off `additional_kwargs` |

- AC-01..AC-07: **met.** `pytest tests/unit/test_prompt_caching_fr276.py -q
  --no-cov` \u2192 16 passed. Full fast suite \u2192 6893 passed, 61 skipped, 1 xfailed.
  `scripts/req_coverage.py --strict` \u2192 exit 0.
- AC-08: **met** \u2014 no public contract change (above).
- AC-09: fragment `changelog/unreleased/fr-1055-anthropic-system-segments.md`;
  Distill entry pending.
- AC-10: **BLOCKED \u2014 not met, and not claimed.** See below.

### AC-10: live verification blocked (no measured cache hit is claimed)

The operator approved the paid run (R-4). It did not complete. Two findings,
both recorded rather than worked around:

**1. Credentials rejected.** The witness reached the API and was refused:

```
anthropic.AuthenticationError: Error code: 401 -
{'type': 'error', 'error': {'type': 'authentication_error',
 'message': 'API key is invalid.'}, 'request_id': None}
```

The key in `.env` is well-formed (`sk-ant-` prefix, 108 chars), so this is a
revoked/expired credential, not a missing one. Per C-3 and R-4 this FR
therefore records the deferred decision and **makes no claim of a measured
cache hit**. The existing `demo-output.log` is left untouched.

**2. The demo could never have cached anything anyway.** Anthropic's minimum
cacheable prefix is 1024 tokens (Sonnet) / 2048 (Haiku).
`examples/demos/prompt-caching/prompts/analyze.yaml` is 1298 **bytes** \u2014 on the
order of 300 tokens. Its committed log line `\u2713 Cache hit! Shared system segment
reused from analyze step` (`demo-output.log:13-14`) is authored narration, not
a reading: the demo is below the floor at which a `cache_control` breakpoint
does anything, and always was. This is a second, independent defect of the same
class as the one this FR fixes \u2014 a success-shaped artifact standing in for a
measurement \u2014 and needs its own FR.

**What the live path did verify.** Run through the shipping entry point
(`prepare_messages` \u2192 `create_llm`, a ~2.3k-token stable prefix):

```
[call-1] system message type=list
[call-1] blocks=2 first_keys=['cache_control', 'text', 'type']
[call-1] cache_control={'type': 'ephemeral'}
```

Before the fix the same probe printed `type=str` (empty string). So the repair
is confirmed end-to-end up to the network boundary; only the round-trip cache
number remains unmeasured.

## Acceptance Criteria

Superseded by the judgement's revised criteria; reproduced here as the working
list (`FR-1055-....judgement.md`).

- [ ] AC-01: A RED test tagged `@pytest.mark.req("REQ-YG-289")` demonstrates
      that `_build_system_message_from_segments([{"content": "STABLE",
      "cache": True}], {}, None, "anthropic")` does not deliver a non-empty
      system block through `langchain_anthropic._format_messages`
- [ ] AC-02: After the production change, the Anthropic `SystemMessage.content`
      equals a list containing the rendered text block and
      `{"cache_control": {"type": "ephemeral"}}`; `additional_kwargs` does not
      carry a duplicate `content` payload
- [ ] AC-03: The seam test composes `_build_system_message_from_segments` with
      `langchain_anthropic._format_messages` and asserts the exact rendered
      text `"STABLE"` plus the exact ephemeral cache-control object, not mere
      truthiness
- [ ] AC-04: The Anthropic producer assertions at
      `tests/unit/test_prompt_caching_fr276.py:199`, `:230`, `:345` read
      `.content`; the non-Anthropic assertion at `:277` remains valid and
      non-Anthropic providers still receive one flattened string
- [ ] AC-05: Existing scalar `system:` tests remain green, demonstrating the
      branch at `executor_base.py:266-270` is unchanged
- [ ] AC-06: `pytest tests/unit/test_prompt_caching_fr276.py -q --no-cov` passes
- [ ] AC-07: `python scripts/req_coverage.py --strict` passes and the seam test
      is linked to REQ-YG-289
- [ ] AC-08: The FR records that the public prompt contract needs no edit, or
      names and verifies the exact documentation correction
- [ ] AC-09: A valid FR-1055 fix fragment exists under `changelog/unreleased/`,
      and a Distill entry with a `Seed:` exists under `docs/diary/`
- [ ] AC-10: The second call's raw non-zero cache-read field and value appear
      in both `examples/demos/prompt-caching/demo-output.log` and this FR
      (operator approved the paid run in R-4)

### Documentation (AC-08)

**No public contract change.** `reference/prompt-yaml.md:67-97` already states
the intended behaviour verbatim — "**Anthropic**: `cache: true` segments get
cache_control metadata for cost reduction" and "**Other providers**: Cache
flags are ignored; segments are flattened to single system message". Both
sentences become *true* after this fix; neither is inaccurate as a statement of
the contract. Nothing to correct.

### Descoped by the judgement

- FR-382 chaplain prompt re-verification — historical downstream evidence, not
  a named current witness; belongs to its own FR
- Release / version bump / tag so the consumer can pin — a later lifecycle
  action, not this repair
- A `langchain-anthropic` upper bound — **resolved in favour of the seam test**
  (R-3). The declared floor 1.5.1 reproduces the bug, so a pin is not the cure;
  the seam test is the selected dependency-drift guard. Any upper-bound policy
  needs a separate FR naming a version.

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
