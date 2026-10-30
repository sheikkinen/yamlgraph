# Reflection: FR-1154 — the axis the allowlist never named

**Date:** 2026-10-30
**FR:** FR-1154 (omit Anthropic sampling parameters under API version 2026-10-21)

## What happened

deviant-daily's nightly run died on its describe step with a 400 from Anthropic: "temperature: Extra inputs are not
permitted". Nothing in deviant-daily or yamlgraph had changed. The consumer's CI installs `yamlgraph` without pins.
langchain-anthropic 1.7.7 dropped its `anthropic<2` cap. pip took anthropic 2.3.0, which sends
`anthropic-version: 2026-10-21`, and that API version removed temperature, top_p and top_k on every model.

yamlgraph already had a rule for this, FR-1146: keep temperature only for a named list of older models. The rule was
correct when written. It assumed one axis (which model) while the API had a second (which version header). On that
second axis `claude-haiku-4-5`, the model most firmly on the "keeps temperature" list, rejected it. A probe matrix
with the header overridden showed this in four calls.

## Root cause

A per-model allowlist encoded a vendor fact as if the model were the only variable. The vendor's breaking change
then arrived through a transitive dependency's cap removal, not through any repository's diff. `recent_changes_blindness`
pointed at the wrong place: `git log` in both repos was empty. The change was in the resolver, not the tree.

## Heuristic

**When a rule is keyed by one identifier of an external system, list the other identifiers that system versions
by.** Model, API version, SDK major and endpoint each version independently. An allowlist on one of them is a
forecast that the others hold still.

Second: **an unpinned consumer turns an upstream cap removal into your outage.** The probe that found this was
`pip install` in a clean venv with the consumer's exact command, not a read of either repo.

## Corrective actions

- `create_llm` reads the SDK's own `anthropic-version` default once. At or after 2026-10-21 it omits temperature
  for every Anthropic model, thinking included, and logs why. Before that version, FR-1146 runs unchanged.
- An SDK-2 live witness (haiku-4-5, with and without thinking, both 200) is recorded in the FR.
- deviant-daily moves its describe step to `claude-haiku-5-5`, which already omits temperature on either header.

**Seed:** Should yamlgraph run a nightly "consumer-resolution" job that runs `pip install yamlgraph` in a clean venv
and makes one live call per provider? Upstream cap drops would then surface here, as a red build, before they become
a consumer's outage.
