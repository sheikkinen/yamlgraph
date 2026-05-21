# Reflection: FR-430 Linter Rule W024

**Date:** 2026-05-21
**FR:** FR-430 Linter Rule W024 Mixed Template Syntax
**Author:** copilot enforce pass

## Trap

`plausible_wrong_answer` - prompts can render without crashing yet still carry semantically broken placeholders when mixed template syntaxes are used.

## What Happened

YAMLGraph supports simple substitution (`{var}`) and Jinja2 (`{{ var }}`, `{% ... %}`), but mixed usage in one prompt file can silently degrade rendering quality. FR-430 added linter warning `W024` so the problem appears at lint time instead of runtime.

## Root Cause

The engine auto-detects Jinja2 by syntax presence, so a file containing both styles can be interpreted entirely as Jinja2 while simple placeholders remain unrendered or misinterpreted.

## What Worked

- Rule placement in linter gives one enforcement point for CLI, CI, and hooks.
- Shared extraction utility was reused, but only after stripping Jinja2 constructs to avoid Jinja-only false positives.
- Focused tests covered mixed warning, pure simple clean, pure Jinja2 clean, and missing prompt skip.

## Seed

Seed: Should lint rules around prompt semantics move to a dedicated prompt AST pass so syntax-family checks, variable anchoring, and escape diagnostics share one parser boundary instead of layered string heuristics?
