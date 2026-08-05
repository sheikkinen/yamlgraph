# Was the Manifest Worth It? — Auditing FR-768 Through Its Own PoC

**Date:** 2026-08-05
**Context:** Post-enforcement reflection on FR-773..776 (book-summary demo),
which served as the proof-of-concept consumer for FR-768 tool manifests.
Three questions asked, answered from the repo, not from memory:
was the feature used, was it beneficial, does the example demo it.

## 1. Was it used? Yes — and the negative space is the finding

Census: 3 manifests exist (`describe_image`, `split_document`,
`render_page`), 2 committed consumer graphs (book-summary consumes two,
shared-vision-tool consumes one). Inside book-summary: **2 of 13 tools are
manifest-referenced; 11 are inline `path: tools.py`**. That 2/13 split is
not underuse — it is the fit boundary drawn correctly. Every
manifest-backed tool lives in `examples/shared/` with a second consumer
real or imminent; every inline tool is demo-local with exactly one caller.
A manifest for `gate_render` would be `junk_drawer` indirection. The PoC's
most useful output is this ratio: manifests earn their file when the tool
crosses a directory boundary, and not before.

## 2. Was it beneficial? Modestly — but not for the reason the FR implied

Checking `python_tool.py` deflated my assumption: inline tools **already
support `module:`** — `type: python, module: examples.shared.render_page,
function: render_page` expresses the identical wiring in three lines. The
manifest added no capability. What it added is *location of truth*: the
contract comment (args, defaults, raise behavior, C-7 warning) lives once
at the tool, validated `extra=forbid` at the load boundary, and FR-776
consumed `split_document.tool.yaml` unchanged — zero re-declaration, zero
drift risk between two graphs' descriptions of the same tool. That is
`the_one_law` applied to declarations: normalize the tool contract at the
tool, not downstream in each consumer. Real, but small; the honest
counterfactual is "three inline lines plus a docstring."

## 3. Does the example demo the feature? One third of it

FR-768 shipped three runtime types: python, shell, graph. Committed
manifest consumers exercise **python only**. Shell and graph manifest
runtimes have zero consumers — capability shipped, witness absent. This is
the `demo_vs_test` gap wearing a manifest costume: unit tests prove the
translation, but no committed graph proves the abstraction is worth having
for shell or graph runtimes. Two releases of silence there is a signal —
either a consumer appears or the runtime variants were speculative
(`would_you_use_this` was never answered for them).

## The meta-trap

I nearly answered "yes, beneficial" from narrative memory — the manifests
felt load-bearing because I had just written one. The census took four
greps and reversed the emphasis: the feature's value is documentary, not
functional, and a third of its surface is unwitnessed. Reflection questions
about one's own recent work are exactly where `quick_confidence` bites
hardest; the repo is the only calibrated witness.

**Seed:** should `would_you_use_this` become mechanical for capability
surfaces — a periodic sweep that lists shipped runtime variants / enum
members / config options with zero committed consumers, so speculative
surface area is retired (FR-465/466 style) instead of silently maintained?
