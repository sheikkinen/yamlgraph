# 2026-08-15 — B→A→D: three cures, one seam lesson, and the gate that turned red into one line

**FRs:** FR-800 (Class B), FR-799 (Class A), FR-801 (Classes C+D) — the
FR-798 dispositions enforced in causal order.

## The enforcement was boring — the Judgement was good

All three fixes landed exactly as judged: one patch-target line plus
assertions (FR-800), one teardown re-import plus a deterministic witness
(FR-799), one conftest plus wiring (FR-801). Zero surprises during
enforcement is the `boring_enforcement` signal: the investigation FR
(FR-798) had already paid the debugging cost, and the judge had already
eaten the ambiguity (marker vs fixture, witness permanence, probe
mechanics). The investigation→fix split (`investigation_before_fix`)
delivered again: enforcement of three FRs took less time than FR-798's
Class A reproduction alone.

## Trap observed: the seam lesson recurred INSIDE its own cure

FR-800's defect was patching the module that no longer resolves the name
(`agent.execute_shell_tool` after FR-660). While writing FR-801's
witnesses I nearly repeated it: the readiness probe does
`from yamlgraph.utils.llm_factory import create_llm` *inside* the
function, so the mockable seam is `yamlgraph.utils.llm_factory.create_llm`
— had the import been module-level in conftest, the same stale-seam class
would have been born in the very tests shipped to witness its cousin's
fix. Heuristic (candidate for graduation if it recurs): **when writing a
mock, name the module that RESOLVES the symbol at call time, and prefer
call-time imports in test infrastructure so the resolving module stays
the defining module.**

## The ideal result, verbatim

FR-801's Ideal Result said: "Provider trouble is visible as
`SKIPPED [provider openai not ready: ...]`". The live verification run
printed `provider openai not ready: RateLimitError/429` four times off
one probe — the artifact matched the ideal sentence byte-for-byte before
any human read it. `ideal_result_backwards` is not ceremony: writing the
end state first made AC-01's skip-reason format a copy, not a design.

## Fixture teardown order is a boundary in miniature

FR-799's one-line fix grew a second line for a reason worth keeping:
the re-import re-runs module-level dotenv loading from *cwd*, so the
teardown must restore cwd BEFORE re-importing and pop the probe env key
AFTER (the re-import may resurrect it). The orphan bug and the dotenv
resurrection (FR-798's `dotenv_resurrects_the_key`) are the same lesson
at two scales: import-time side effects make sequence part of the
contract. A teardown is a boundary; order its operations like one.

**Seed:** the preflight currently knows one provider (openai) because the
frozen inventory named four tests. The anthropic/mistral/deepseek live
tests in `test_providers.py` gate on key presence alone — the same
presence≠readiness gap, currently masked by healthy credentials. When one
of those keys next exhausts, the cure is a one-line
`CREDENTIAL_ENV` entry plus a fixture — should a follow-up FR wire the
whole provider matrix proactively, or does `would_you_use_this` say wait
for the first event?
