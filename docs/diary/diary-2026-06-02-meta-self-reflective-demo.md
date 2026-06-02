# Diary — Meta Self-Reflective Demo (FR-464)

**Date:** 2026-06-02
**FR:** FR-464

## Context

A 2023 Confluence artifact ("OpenAI Prompts for Developers") and Santiago
Valdarrama's `meta.js` trick prompted a reflection: build a typed, traced homage
that applies a natural-language verb to a code artifact — including its own YAML.

## Cognitive Traps Encountered

### 1. `architecture_as_diagram` — the idealized boundary that didn't exist

The original FR sketch declared a project-root-bounded `read_file` Python tool as
if it already existed. It did not. Sibling demos define `read_file` as a shell tool
(`cat {file}`), and FR-463 had *explicitly deferred* path-traversal hardening as
out-of-scope framework work. The Judge step caught this: I verified the claim against
the codebase instead of trusting the plan's prose. The cheapest bug is the one killed
in the spec — the boundary criterion was corrected before any code was written.

### 2. Linter as the real boundary contract

Tests passed GREEN while `graph lint` failed: the E001 rule requires shell-tool
command placeholders to be declared in state, and it only exempts *agent* tools —
not tool-node `variables:` mappings. My first instinct was to declare a phantom
`file: str` state field (the linter's literal suggested fix). Better: rename the
placeholder to `{target}`, which already exists in state. The linter was right that
*something* was undeclared; the honest fix names the real input rather than inventing
a field to satisfy the checker. **Green tests are not green truth — the linter encodes
a constraint the type-shape tests don't.**

### 3. Provider type quirk at the schema boundary

The self-referential run returned `suggested_code: []` (empty list) for a `str`
field. The JSON parser tolerated it; the demo succeeded. This is the recurring
`schema` boundary lesson (FR-059, "the provider's type lie"): an LLM will hand you
the wrong container shape for an empty value. Harmless here, but noted.

## Heuristic

> When type-shape tests pass but a linter fails, the linter usually encodes a
> constraint the tests don't. Fix toward the *real* declared input, not toward a
> phantom field that merely silences the checker.

## Seed

The E001 rule can't see that a tool node supplies command variables via its
`variables:` block — it only exempts agent tools. Should the linter learn that
`type: tool` nodes resolve their own command placeholders, the way it already knows
agent tools get theirs from the LLM? That would let demos name tool placeholders
freely (`{file}`) without phantom state declarations.
