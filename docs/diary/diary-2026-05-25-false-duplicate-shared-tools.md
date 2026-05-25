# Diary: False Duplicate — Should Judge Tools Be Shared?

**Date:** 2026-05-25
**FRs:** FR-452
**Context:** Eval harness session, post-amendment reflection

## Summary

After amending FR-452 (standalone planner demo), noticed that the planner
graph would need 4 of the same 5 tools as the judge demo: `read_file`,
`search`, `list_dir`, `git_log`. The instinct was to extract shared tool
definitions. Investigation killed the instinct.

## The False Duplicate

Four demos define `read_file` as a shell tool. Surface similarity is high —
all wrap a shell command that reads a file. But the implementations diverge:

| Demo | `read_file` command | Purpose |
|------|---------------------|---------|
| judge | `cat {file}` | Full file — judge must see complete FR |
| research-agent | `head -80 {file}` | Truncated — research scans many files |
| verified-search | similar truncated | Scan pattern |
| philosopher_book | Python tool | Different mechanism entirely |

The descriptions diverge more. Judge's `search` description includes
`--glob 'ARCHITECTURE.md'`, `--glob 'capabilities/*.yaml'` — LLM steering
tuned to the judge's domain. A shared tool would either lose this guidance
or need per-consumer overrides, which is worse than inline definitions.

## Trap: `false_duplicate`

> Syntactic similarity ≠ semantic equivalence.

The Scripture already names this trap. The tools *look* the same because they
solve adjacent problems (file access for LLM agents), but they serve
different optimization targets:

- **Judge tools** optimize for completeness (read everything, miss nothing)
- **Research tools** optimize for breadth (scan many files, truncate each)
- **Planner tools** will optimize for generation (read templates, write files)

Extracting a shared `tools_file:` mechanism would cost: new schema field,
parser changes, loader changes, tests, docs, a new FR. Benefit: saving ~15
lines of YAML per demo. The abstraction is more expensive than the
duplication.

## Heuristic

**When duplication feels wrong, check the descriptions.** If tool
descriptions need per-consumer tuning (because they steer LLM behavior),
the tools are not true duplicates — they are domain-specific instruments
that happen to share a command shape. Inline them.

**Threshold for extraction:** 5+ consumers with *identical* commands AND
*identical* descriptions. Below that, the abstraction costs more than the
copy.

## Seed

If YAMLGraph grows a tool marketplace (shared tool libraries across
projects), the unit of sharing should be the *tool + description + parse
config* triple, not just the command. A tool without its description is a
function without its docstring — technically reusable, practically
dangerous because the LLM loses steering.
