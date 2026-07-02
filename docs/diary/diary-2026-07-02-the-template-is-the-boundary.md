# Diary: 2026-07-02 — The Template Is the Boundary

**FR:** FR-656 (Tighten Genesis Prompt)
**Trap:** downstream_fix × instruction_boundary_uncrossed
**Duration:** ~45 min investigation, 15 min fix

## What Happened

After FR-655 produced structurally valid canon, the `retrieve_window` tests
failed because the LLM's free-text output didn't match the Pydantic schema's
type expectations — `goals` as comma-separated string instead of `list[str]`,
`relationships` missing `valence`, `consequences` as prose paragraph. The
prompt didn't specify types; the schema silently accepted whatever passed
Pydantic coercion.

## The Jinja2 Collision

The real trap: when I wrote `{to, kind, valence}` in the prompt's descriptive
text to document the relationship structure, Jinja2 parsed it as a set literal.
The error was `KeyError: 'to'` — Jinja2 tried to resolve `to` as a template
variable. The fix was trivial: use "objects with keys: to, kind, valence"
instead of curly braces.

**This is a boundary problem.** The prompt YAML file sits at the intersection
of three grammars: YAML (structure), Jinja2 (templating), and English
(instruction). Bare curly braces are valid in all three but mean different
things. The collision is invisible until runtime.

## The Non-Deterministic ID Problem

Each genesis run produces different entity IDs. The LLM chose `hilde` this
run, `hilde_aschenwulf` last run. Tests that hardcode IDs break on every
re-run. The current fix (update tests to match latest run) is fragile. The
proper fix is tests that read actual IDs from canon files rather than
asserting specific strings — but that changes the test from "correct output"
to "structurally valid output", which is a different claim.

## Heuristic

**template_grammar_collision**: When a file is processed by multiple parsers
in sequence (YAML → Jinja2 → LLM), any syntax valid in more than one grammar
is a collision risk. The error manifests in the last parser that touches it,
not the one that misinterprets it. Avoid ambiguous syntax; prefer natural
language over symbolic notation in multi-grammar files.

## Seed

Can we lint prompt YAML files for Jinja2 collision risks — scan for bare
`{...}` outside `{{ }}` blocks and warn before runtime?
