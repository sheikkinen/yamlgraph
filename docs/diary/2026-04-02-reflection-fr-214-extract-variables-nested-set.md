# FR-214: Reflection — extract_variables nested set false positive

**Date:** 2026-04-02
**FR:** FR-214
**Scope:** `yamlgraph/utils/template.py` — `extract_variables()`

---

## What happened

`extract_variables()` relied entirely on Jinja2's `meta.find_undeclared_variables()` to determine which variables a template requires as input. This function handles top-level `{% raw %}{% set x = y %}{% endraw %}` correctly (reports `y`, excludes `x`), but silently fails for `{% raw %}{% set %}{% endraw %}` targets that appear inside nested `{% raw %}{% for %}{% endraw %}`/`{% raw %}{% if %}{% endraw %}` blocks — it reports them as undeclared inputs even though they are loop-local assignments.

The symptom: a template like

```jinja2
{% raw %}{% for i in items %}{% if i %}{% set x = i %}{{ x }}{% endif %}{% endfor %}{% endraw %}
```

returned `{'items', 'x'}` instead of `{'items'}`. Any caller validating required inputs would demand `x` from the user, which is never needed.

---

## Root cause

`find_undeclared_variables` is a static analyser that tracks scope. Its scope-tracking for `{% raw %}{% set %}{% endraw %}` is shallow — it works at the top level but does not propagate the assignment into the set of "declared" names when the set node is nested inside loop/conditional bodies. This is a known limitation of the Jinja2 meta module, not a YAMLGraph bug per se.

---

## Fix

Walk the full AST with `ast.find_all(jinja_nodes.Assign)` to collect every `{% raw %}{% set %}{% endraw %}` target at any depth, then subtract the resulting set from the undeclared variables. This is O(n) in AST nodes and adds no dependencies.

```python
set_targets = {
    node.target.name
    for node in ast.find_all(jinja_nodes.Assign)
    if isinstance(node.target, jinja_nodes.Name)
}
variables -= set_targets
```

The subtraction is safe because `find_undeclared_variables` already excludes top-level set targets; subtracting them again is a no-op.

---

## Cognitive trap

**downstream_fix** — my first instinct was to add a guard at the callsite (e.g., filter variables in `validate_variables`). But the correct boundary is `extract_variables` itself, which is where external AST data enters our system. Normalise at the boundary; don't patch downstream.

## Heuristic

> When a Jinja2 meta utility gives a wrong answer, walk the AST yourself rather than patching callers.

---

**Seed:** Could a property-based test (hypothesis) generate random Jinja2 templates with arbitrary `{% raw %}{% set %}{% endraw %}` nesting and assert that no set target ever appears in `extract_variables` output? That would catch entire classes of scope-tracking regressions automatically.
