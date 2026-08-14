# Diary: FR-794 Shared Python Tool Manifest Root Confinement Fix

**Date:** 2026-08-14
**FR:** FR-794
**Duration:** ~70 min

## What happened

While authoring FR-788 (platform-confirm), the shared `curl_probe`
Python-runtime tool manifest failed to load with "escapes graph root."
Reproducing the same command against the already-merged, "Enforced"
FR-785 `endpoint-probe` graph showed the identical failure — this
wasn't a new-graph problem, it was a load-bearing composition bug
between two independently-shipped, independently-tested features
(FR-445's graph-root confinement, FR-768's manifest-relative path
resolution) that had never been exercised together with a real
cross-directory manifest until now.

## Trap encountered: fixing one bug unmasks a second, unrelated one

After relocating confinement to the manifest's own declaration root,
`load_and_compile` on the SAME endpoint-probe graph got further and hit
a completely different, pre-existing defect: `probe.yaml`'s `schema:`
block mixed the native "fields:" dialect's top-level key with
JSON-Schema-style content (`type: list` + nested `items:`), which the
native loader has never supported. FR-785's "19/19 tests green" claim
covered only structural YAML assertions — the graph had literally never
been through a real `load_and_compile`.

## Trap encountered: human-directed scope expansion overridden by the judge

Asked the human how to handle AC-05 given the second bug; they chose
"expand FR-794 to fix probe.yaml too, since it's what makes AC-05 true
as worded." I folded that in and re-judged — the judge returned **SPLIT**,
not APPROVED: the two defects have different execution routes (a
framework Python-file edit vs. a `prompts/*.yaml` edit gated by the
graph-authoring sole route), and doctrine forbids collapsing them into
one implementation authority even when the human directing the session
wants it that way. This is the judge doing exactly its designed job —
catching scope drift the requesting session is too close to see,
including drift the human explicitly asked for. Reverted to the
framework-only scope FR-794 was originally judged for; filed FR-795 for
the prompt repair separately.

## Insight: "N tests green" is not evidence a graph compiles

FR-785 and (implicitly, before this session) reviewers treated passing
structural pytest assertions (file exists, YAML has expected keys) as
proof of a working graph. Neither the manifest bug nor the schema-dialect
bug would ever be caught by that test style — both are only visible to
an actual `yamlgraph.compile.graph_loader.load_and_compile()` call. Every
example-graph FR test suite should include at least one compile-or-invoke
level assertion, not just YAML-shape assertions.

## Heuristic

When a framework composition bug is found via one example, always test
it against every OTHER known consumer before scoping the fix — the
sibling that looked unrelated (FR-785, already merged) turned out to be
equally broken. "Fixed for the graph I'm authoring right now" and "fixed
for the framework primitive" are different claims; only test the latter
if multiple consumers exist.

## Seed

Should `load_and_compile` (or a lighter "dry-compile" CLI/lint mode) be
part of the mandatory graph-authoring validation gate for ANY graph that
declares `tools:` with a `manifest:` reference or an inline schema block?
`yamlgraph graph lint` currently checks structural/style rules but this
session's two bugs both slipped past lint and only surfaced at compile
time — is there a cheap way to fold a real (mocked-LLM) compile-and-invoke
smoke into `graph lint` itself, closing the gap between "lints clean" and
"actually runs"?
