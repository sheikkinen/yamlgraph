# The Chaplain as Compiler

**Date:** 2026-04-20
**Author:** Philosopher
**Theme:** Architectural naming analysis — mapping pipeline stages to compiler passes

## Observation

The convergence pattern across this session's proposals (Research step, acceptance tests, Inquisitor migration, finalize_merge automation, early worktree) revealed a deeper structure: the Chaplain pipeline is a compiler. Naming the passes precisely exposes which are missing.

## The Pass Inventory

| Compiler Pass | Chaplain Stage | Purpose | Status |
|---|---|---|---|
| Lexer | watch.sh inbox poll | Tokenize raw input into processable unit | ✅ |
| Preprocessor | GitHub issue import + author allowlist | Normalize, sanitize, gate untrusted input | ✅ (FR-251) |
| Parser | `plan` node | Transform freeform proposal into structured FR (the AST) | ✅ |
| Semantic Analysis | `research` node | Resolve references — existing abstractions, competitors, diary precedents | ✅ (FR-257) |
| Type Checking | `judge` node | Verify AST is internally consistent, feasible, minimal | ✅ |
| IR Generation | acceptance test step | Convert spec to verifiable intermediate form (failing tests) | 🔴 (#138) |
| Dead Code Elimination | Inquisitor | Find unreachable code, unused abstractions, entropy | ⚠️ Disconnected (#139) |
| Constant Folding | Research "existing abstractions" | Reuse what exists instead of reinventing | ✅ (in research prompt) |
| Inlining | *absent* | Fast path for trivial changes — skip full pipeline | 🔴 |
| Code Generation | `implement` node | Emit code that satisfies the IR (tests) | ✅ |
| Linking | `test_and_demo` node | Verify generated code integrates with existing codebase | ✅ |
| Static Analysis | `critique_and_distill` node | Post-codegen review against spec + diary reflection | ✅ |
| Assembler | `finalize` node | Pre-commit, commit, push, PR — produce final artifact | ✅ |
| Loader | CI (GitHub Actions) | Load into target environment, run in real context | ✅ |
| Runtime | merge + finalize_merge.sh | Deploy: changelog, FR status, diary stub | ⚠️ Manual (#137) |
| Profiler | pipeline metrics | Measure pass durations, detect regressions | ✅ (FR-256) |
| LTO | Philosopher | Cross-module optimization — patterns across compilation units | ⚠️ Dormant |

## Three Gaps Revealed by Naming

1. **IR Generation** (#138): Without intermediate representation (failing tests), enforce does parse-and-codegen in one pass. No compiler does this — the IR is what makes optimization possible and correctness verifiable.

2. **Inlining**: Micro-fixes (rename, typo, version bump) run through the full pipeline. This is like compiling `x = x + 0` with full optimization. Need a severity-based fast path: trivial changes → direct commit with pre-commit only.

3. **Link-Time Optimization** (Philosopher): Cross-FR pattern detection is dormant. Without LTO, each FR is optimized in isolation and systemic patterns never surface.

## The Structured Output Gradient

The naming also reveals an output-typing problem:

- Plan: markdown file (unstructured)
- Research: brief in session (unstructured)
- Judge: verdict embedded in FR — grep for "Approved/Rejected" (semi-structured)
- Enforce: code + tests + PR (structured)

Quality increases with structure moving downstream. The IR step (#138) is the inflection point — where natural language becomes machine-verifiable contract.

## Trap

**`anthropomorphic_naming`** — "Plan," "Judge," "Enforce" are roles, not functions. Roles invite interpretation; passes have contracts. A pass that can't declare its output type is suspect.

## Insight

The convergence of all proposals toward watch.sh isn't simplification — it's recognizing the pipeline is a compiler and should have a single driver. `gcc` doesn't run its linker from a post-commit hook.

## Seed

If passes have typed input/output contracts, the pipeline becomes composable. You could swap the Judge for a different evaluator (human review, automated scoring). You could run two Research passes in parallel and merge. You could skip passes for known-good patterns. The compiler framing isn't metaphor — it's architecture. What would a `--dump-ir` flag for the Chaplain look like?
