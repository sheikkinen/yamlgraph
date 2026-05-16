# 2026-05-16 FR-404 Philosopher's Book

**FR:** FR-404
**Type:** Implementation reflection

## What was built

A YAMLGraph pipeline that generates a 21-chapter philosophical work — one chapter per cognitive trap from the Knowledge Graph. The pipeline uses `copilot` nodes with diary search tools so the Philosopher actively researches primary source material during generation.

## Cognitive traps encountered

**continuation_bias** — Nearly implemented without tests first. Caught it before coding tools.py. TDD red-green refactor enforced the right order.

**downstream_fix** — The initial design wanted to pre-load diary excerpts in a Python tool and pass them as state. This would have added a pre-processing layer. The FR correctly identifies this as downstream fixing: instead, give the Philosopher tools and let it search at generation time (boundary: the copilot node).

**working_system_inertia** — The ebook pipeline pattern works well for 7 chapters. For 21 it needed `sequential: true` to avoid rate limiting. The temptation was to copy the ebook pattern exactly without examining fit.

## Insights

The hardcoded trap list in tools.py is the right call. The 21 traps are stable, well-defined data. Parsing them from copilot-instructions dynamically would add fragile parsing logic that would break if the comment format changed — a false sophistication.

The `read_file` allowed-paths validation is the One Law in action: normalize at the boundary where user-controlled path data enters, not downstream in some error handler.

## Heuristic

**Stable enumerations deserve hardcoding.** When a list has 21 items with stable names and definitions, a hardcoded data structure is more reliable than dynamic parsing. Reserve parsing for truly dynamic content.

## Seed

Can the book-generation pipeline be extended with a write→judge→amend loop per chapter (v2), and what would the cost difference look like in a cost_estimate tool?
