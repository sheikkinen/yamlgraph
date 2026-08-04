# Feature Request: FR-770 — Vision Demo Consumes the Tool Manifest (FR-768 Smoke)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-04
**Prior art:** FR-768 (tool manifests, Enforced core) defines the `manifest:` mechanism this FR consumes — no overlap, this is its first committed consumer. FR-769 (shared vision tool, Enforced) shipped the demo this FR migrates; its judgement froze the demo to an inline `type: python` declaration because the freeze predated FR-768's implementation. FR-769's own text ("once FR-768 lands, it becomes a manifest-declared shared capability") is the deferred promise this FR redeems.
**First consumer / first event:** FR-768 itself — the moment anyone asks "show me a graph that uses `manifest:`" there is currently **no answer outside the unit test suite**. The shared-vision-tool demo was implicitly the manifest smoke test and is currently failing that role: it declares the tool inline.

## Summary

Migrate the FR-769 demo to declare the shared vision tool via a FR-768
manifest: add `examples/shared/describe_image.tool.yaml` and switch
`examples/demos/shared-vision-tool/graph.yaml` from the inline declaration
to a `manifest:` reference. One small diff turns the demo into the manifest
feature's living, executed showcase.

## Value Statement

FR-768 gains its first committed, smoke-run consumer; FR-769's demo gains
the declaration style its own FR promised; the docs can point at a real
graph instead of a synthetic test fixture.

## Problem

FR-768 and FR-769 shipped in the same arc without touching:

- The demo graph declares `describe_image` inline
  (`type: python` / `module:` / `function:` / `description:`) — the exact
  4-line block the manifest feature exists to eliminate.
- FR-768's `manifest:` key has **zero consumers** in committed graphs; its
  only exercisers are `tests/unit/test_tool_manifest.py` tmp_path fixtures.
  Every consumer named in FR-768 (chaplain trio, novel_fandom,
  examples/shared) is still on inline declarations.
- The inline `describe_image` declaration in the demo is additionally
  decorative (lint W001 unused: the node calls the `describe_demo_image`
  wrapper) — a manifest reference carries the same documentation value with
  a declaration that is actually shared.

The chaplain trio migration (FR-768 AC-09) remains deferred and human-review
gated; it is explicitly **not** in this FR's scope.

## Ideal Result

`grep -r "manifest:" examples/` returns a real, lint-clean, smoke-run demo.
A reader of the FR-768 docs section can open one committed graph and one
committed manifest file and see the round trip: manifest resolved relative
to the graph, `module:` runtime translated, tool executed against a live
provider, output in `demo-output.log`.

## Proposed Solution

1. **Manifest** — `examples/shared/describe_image.tool.yaml`:

```yaml
name: describe_image
description: "Describe an image: title, description, tags"
runtime:
  type: python
  module: examples.shared.vision_tool
  function: describe_image
```

2. **Demo graph** — replace the inline block in
   `examples/demos/shared-vision-tool/graph.yaml`:

```yaml
tools:
  describe_image:
    manifest: ../../shared/describe_image.tool.yaml
  describe_demo_image:
    type: python
    path: nodes/demo.py
    function: describe_demo_image
    description: Call the shared vision tool with the demo instruction
```

3. **Governed-path discipline**: the graph edit goes through the
   graph-authoring sole route (`scripts/author.sh`), producing lint + smoke
   evidence and a refreshed `demo-output.log`.

4. **Docs**: `examples/shared/README.md` vision section shows the
   `manifest:` declaration alongside (or instead of) the inline form;
   FR-768's reference section gains a pointer to the demo as the committed
   example.

No changes to `yamlgraph/tools/manifest.py`, `vision_tool.py`, core code,
the chaplain trio, or any other consumer.

## Acceptance Criteria

- [ ] AC-01: `examples/shared/describe_image.tool.yaml` exists and validates
      as a `ToolManifest` (python `module` runtime).
- [ ] AC-02: The demo graph's `describe_image` entry contains only the
      `manifest:` key; the manifest path resolves from the demo directory.
- [ ] AC-03: `yamlgraph graph lint examples/demos/shared-vision-tool/graph.yaml`
      passes with no new errors.
- [ ] AC-04: Smoke run (`--var image=.../fixture.png --full`) succeeds against
      a live provider; refreshed `demo-output.log` committed with success
      marker.
- [ ] AC-05: A unit test loads the committed demo graph and asserts the
      translated `describe_image` config equals the previous inline form
      (module/function/description) — the manifest round-trip pinned on a
      real repo artifact, not a tmp_path fixture (REQ-YG-574 marker).
- [ ] AC-06: `examples/shared/README.md` and the FR-768 docs section
      reference the demo as the committed manifest example.
- [ ] AC-07: Changelog fragment added.

## Alternatives Considered

- **Wait for the chaplain trio migration (FR-768 AC-09)** to be the first
  consumer: rejected as the *only* path — it is human-review gated and
  larger; this FR is a 30-minute consumer that unblocks the "show me one"
  question immediately, and does not replace AC-09.
- **Manifest for `describe_demo_image` too**: rejected — it is graph-local
  glue with exactly one consumer; manifests are for shared tools.
- **Also migrate `websearch` consumers**: deferred — two more graphs would
  join the diff and both are governed demo paths; keep this FR one-artifact
  small, fold websearch into the AC-09 follow-up if wanted.

## Related

- [FR-768-tool-manifest-declaration-reuse.md](FR-768-tool-manifest-declaration-reuse.md) — the feature under smoke
- [FR-769-shared-vision-tool.md](FR-769-shared-vision-tool.md) — the demo being migrated
- [diary-2026-08-04-the-verdict-i-almost-shipped-without-measuring.md](../docs/diary/diary-2026-08-04-the-verdict-i-almost-shipped-without-measuring.md) — the arc that produced the gap
