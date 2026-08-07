# Diary — 2026-08-07 — Two Providers Became Twelve

**FR:** FR-780 (research-agent toolbelt conversion), same-day successor to FR-779

## What happened

The research-agent demo converted from inline tool variants (`head -80`
reads, py-only capped grep) to the shared toolbelt manifests. The witness
run quantified the fidelity claim: asked "which LLM providers does
create_llm support?", the truncated tools (FR-779-era run) confirmed 2
providers and honestly listed the rest as gaps; the canonical `cat`-based
tools found all 12 with `confidence: high` and zero gaps. Same graph
topology, same iteration caps, same model — the only variable was tool
fidelity.

## Insight: iteration caps price context starvation

The 2026-08-06 dogfood failure (10 iterations, empty findings) looked
like an agent-budget problem, and raising `max_iterations` was the
tempting fix — the judgement explicitly forbade it (AC-09). Correctly:
an agent reading 80-line fragments through a py-only grep needs *more
calls* to assemble the same evidence, so truncating tools convert
directly into iteration spend. Tool fidelity and iteration budget are
the same resource viewed from opposite ends; fixing the tools is buying
context wholesale instead of retail.

## Trap witnessed: the sweep caught what the brief missed

My authoring brief listed graph.yaml and two prompts. The RED sweep test
(`test_no_legacy_names_anywhere_in_demo`, rglob over the whole demo dir)
failed the adapter's first validation pass because README.md still named
`search_code`/`list_files` — a surface neither I nor the judgement had
enumerated. `partial_remediation` prevented not by more careful listing
but by writing the assertion over the *set* ("anywhere under the demo")
instead of the enumeration. Enumerations rot; quantifiers don't.

## Also: the adapter healed its own smoke

The adapter's first smoke run terminated on the low-confidence route
(over-exploring out of scope) — the FR-779 gate it was required to
preserve is what told it its own prompts were weak. It tightened the
scope-translation instructions and reran green. A guard installed by the
previous FR acted as the test harness for the next one, unprompted.

**Seed:** the scope-translation contract lives in prompt prose ("pass
scope as glob prefix"). Per `two_strike_split`, if a future run silently
searches the whole repo despite a scope, the second strike means this
belongs in code — e.g. a `scope`-aware wrapper tool or a glob-prefix
default in the manifest args. Where is the boundary for argument
defaulting in tool manifests?
