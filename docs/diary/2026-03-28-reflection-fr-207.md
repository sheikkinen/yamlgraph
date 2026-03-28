# Reflection: FR-207 Standalone Scripture Methodology Repository

**Date:** 2026-03-28
**FR:** FR-207 (standalone scripture template)
**Trap:** Framework entanglement

## Context

Extracted YAMLGraph's governance methodology — the Scripture, diary discipline, changelog fragments, pre-commit hooks, CI workflows — into a standalone template repository under `projects/scripture-dev/`. The core challenge was separating framework-agnostic governance principles from framework-specific enforcement wiring.

## Insight

The Judge's note about the re-rendering contradiction (Option A vs in-place rendering) was the critical design decision. Keeping `_templates/` as source of truth makes the system idempotent: `render.sh` always reads from templates, so re-rendering after config changes works naturally. This mirrors the Cookiecutter/Copier pattern without adding dependencies.

The `__PLACEHOLDER__` format avoided three collision domains simultaneously: Jinja2 `{{ }}`, shell `$VAR`, and YAML syntax. Double-underscore delimiters are ugly but unambiguous — a property worth preserving.

## Heuristic

*Extraction over extension* — When governance is the reusable asset, extract it into a standalone template rather than parameterizing it inside the framework. The extraction forces you to identify and eliminate framework-specific assumptions, producing cleaner doctrine.

## Seed

Could a `scripture upgrade` command pull new traps/cures/seeds from an upstream template while preserving local customizations? The `_templates/` pattern enables a merge strategy: upstream templates provide new markers, local `scripture.yaml` provides values, and `render.sh` reconciles them.
