# Diary — FR-798: Four Reds, Four Boundaries, Zero Product Bugs

**Date:** 2026-08-15
**Context:** FR-798 investigation — classify the four non-subgraph failure
classes from the FR-796 validation run before anyone fixes anything.

## The central insight

One full-suite command produced four reds; every one lived at a *different*
boundary: test-isolation (`sys.modules` orphaning), refactor-orphaned mock
seam (FR-660 moved the symbol), provider unavailability surfaced correctly
but read at the wrong field, and credential presence mistaken for readiness.
Not one required a production change. The repository's boundary rule —
name the boundary before proposing the fix — is what kept four unrelated
defects from being absorbed into one franken-fix.

## Traps encountered

**attribute_orphan_after_pop.** `sys.modules.pop("yamlgraph.config")` does
not remove the `config` attribute from the `yamlgraph` package object.
A later `from yamlgraph import config` happily returns the orphan, and
`importlib.reload()` then raises `ImportError: not in sys.modules`. The
intermittency was pure xdist scheduling: any sibling test whose
`from yamlgraph.config import X` re-imports the module *heals* the orphan,
so serial runs (where runpod's registration tests precede the reload test)
never fail. The deterministic witness was two modules in one process —
cheaper than 20 full-suite runs, found by grepping for `sys.modules` writes
first (`changelog_first_diagnostic` generalized: enumerate mutators before
reproducing schedules).

**dotenv_resurrects_the_key.** `env -u OPENAI_API_KEY python ...` still hit
a 429 with the account's credit message: `yamlgraph.config`'s module-level
`load_dotenv()` re-supplied the key from the developer's `.env`. An
"absent-key" test lane that unsets env vars is not absent at all. The
empty-string override survives (dotenv doesn't override existing vars).
This is the `state` boundary of the one_law wearing a `.env` costume —
normalization happens at config import, so disabling must happen *below*
that boundary, not above it.

**key_presence_is_not_readiness.** Confirmed exactly as the FR predicted:
the readiness probe (one `invoke`) cleanly separates absent / exhausted /
healthy — anthropic returned `ok`, openai returned 429 `insufficient_quota`
with the same key that gates test *selection*. Every `skipif(not KEY)` in a
live-provider test asserts the wrong predicate.

**the_tests_read_the_wrong_field.** The multi-turn "failures" asserted the
empty `response` and never printed `errors` — where a perfectly typed
`PipelineError(llm_error, node=respond, retryable=true)` sat the whole
time, with a healthy checkpoint pointing at `wait_for_user`. The error
surfacing worked; the assertion's failure message hid it. Reading the raw
state dict (read_raw_output_first, state edition) classified the whole
class in one probe run.

## What worked

- Hypothesis-first hunting: grep for `sys.modules` mutators → one suspect →
  two-module deterministic witness, before running the 20× statistical
  matrix. The matrix became confirmation, not discovery.
- The FR-761 constrained env earned its keep on first use: classes A and B
  reproduced byte-identically under 3.12.11, killing the Python-3.14
  hypothesis in two commands.
- Investigation-only authority (C-1) made every finding a disposition
  instead of a temptation — four one-line fixes are now specified with
  their regression witnesses, none smuggled in.

## Seed

**Seed:** The healing-import effect means *test order silently repairs
isolation bugs* — a green serial suite can hide any number of sys.modules
orphans that only xdist scheduling exposes. Could a conftest hook assert,
at each test teardown, that every `yamlgraph.*` module in `sys.modules` is
identical to the corresponding package attribute — turning orphaning into
an immediate, attributed failure at the offending test instead of a
scheduling lottery two files away?
