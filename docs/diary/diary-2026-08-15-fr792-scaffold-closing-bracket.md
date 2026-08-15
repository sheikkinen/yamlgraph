# 2026-08-15 — FR-792: extracting the pattern the same day it was proven

**FR:** FR-792 (investigation scaffold) — the arc's closing bracket: the
API discovery family became a template hours after its capstone shipped.

## The judge's R-1 gate aged perfectly

When FR-792 was judged (2026-08-13), its premise was false: the FR
claimed the pattern was "proven by FR-783..FR-791" while every cited
sibling was still Proposed. The judge's R-1 — gate extraction on an
enforced source instance — looked like bureaucracy then; today it read
as simple accuracy. By the time enforcement began, FR-791's live smokes
had made the claim true, and the fold could cite commit fd36b773 with
raw-log evidence instead of aspiration. `growth_as_default`'s cure is
sometimes just sequencing: the same FR text, enforced two days later, is
honest instead of speculative.

## TDD on a generator is pleasantly mechanical

Twelve witnesses written against a nonexistent script (RED committed
7a72503a with three gate-corrections: ruff-format reflow, phantom-REQ
registry ordering — CAP must exist before tests may cite its REQ — and
fr-board drift). GREEN was one script and one witness repair: I invoked
an uncompiled `StateGraph`; `.compile()` first (test_fr794 had the
precedent I didn't read — the day's third argument-shape stumble, same
lesson: grep the signature before writing the call).

Template mechanics note worth keeping: `string.Template` `$`-substitution
is the right tool for generating YAML that itself contains `{state.*}`
runtime placeholders and `{{ jinja }}` prompt syntax — three brace
dialects coexist in one generated file, and only `$` stays out of all
their ways. The FR-787 adapter learned the brace-collision lesson inside
prompts; the scaffold inherits it structurally.

## The arc in one line each

787 recon (route's repair loop is its argument) → 789 browser-sniff
(the brief is code; premises must be dry-run) → 790 schema-extract
(dry-run heuristic's first save; on_error: fail as truth policy) →
791 orchestrator (budgets are premises too; steps_tried must be rendered
from evidence, not inferred) → 792 scaffold (extract only what is
enforced). Five FRs, five sole-route authoring runs (two resumed), zero
manual authoring escapes, every gate that fired was either satisfied or
taught something that got recorded.

**Seed:** the scaffold generates TODO skip-condition edges, but FR-791's
deviation showed the real constraint: edge expressions cannot see into
tool_call wrapper JSON, so skip logic must key on state the router can
address. Should the scaffold's orchestrator template generate a
candidate-hints pattern (a routing-visible llm output consumed by
conditions) instead of bare TODO comments — encoding the deviation's
lesson so the second pipeline doesn't rediscover it?
