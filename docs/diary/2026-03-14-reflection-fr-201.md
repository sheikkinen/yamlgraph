# FR-201 Horoscope Demo — Reflection

**Date:** 2026-03-14
**FR:** FR-201
**Type:** Feature (Demo)

## Cognitive Process

The horoscope demo was a clean, well-scoped FR — static list, known domain, zero Python. The challenge was not complexity but discipline: following existing patterns precisely.

## Traps Encountered

### Pattern Conformity Over Invention
**Trap:** Temptation to add Jinja2 loops in the assemble prompt (like the map demo's summarize prompt uses `{% raw %}{% for item in expansions %}{% endraw %}`). The FR specified simple `{readings}` substitution, which is sufficient since the assembler LLM formats the output. Conforming to the FR spec rather than over-engineering.

### Audit Test Discovery
**Trap:** `test_examples_readme_audit.py` enforces that every demo directory appears in `examples/README.md` and has a `README.md` file. This was not in the FR's acceptance criteria but was caught by running the full test suite. Lesson: always run the full test suite, not just targeted tests.

## Insight

Static `over:` lists in map nodes are the ideal pattern for demos — they remove the need for a "generate list" node, making the pipeline shorter and the parallelism more visible. The zodiac is a perfect teaching example: universally known, exactly 12 items, naturally parallel.

## Heuristic

> **Run the full test suite even for "simple" changes** — audit tests catch cross-cutting concerns (READMEs, naming, structure) that targeted tests miss.

**Seed:** Could YAMLGraph auto-generate a demo skeleton from a `yamlgraph demo init` CLI command, pre-populating graph.yaml, prompts/, README.md, and the demo.sh registration?
