# 2026-07-26 — The gate that found its own bug

## What happened

Building the FR-761 direct-import scanner, the first live run against the
real repository reported 31 "undeclared core direct imports" — but 24 of
them were `langchain_anthropic`, `langchain_azure_ai`, `langchain_openai`,
`langchain_google_genai`, `langchain_mistralai`, `langchain_litellm`: every
one of these distributions is already declared in `pyproject.toml`, right
there in `[project.dependencies]`. The scanner was lying about the exact
thing it exists to catch honestly.

The cause: Python import names use underscores (`langchain_anthropic`);
PyPI distribution names conventionally use hyphens (`langchain-anthropic`).
My first-draft comparison did a literal string match between the resolved
"distribution" and the parsed `pyproject.toml` dependency names, with no
normalization. Any package whose PyPI name contains a hyphen and whose
import name uses an underscore in the same position (a *majority* of the
`langchain-*` family, plus others) would always fail the check, regardless
of whether it was declared.

## Why this recurred rather than surprised

This is the same shape as `plausible_wrong_answer` from the Scripture: the
scanner's output had the correct *shape* — a list of file:line findings
with a distribution name and a "not declared" message — but was
semantically wrong for roughly three-quarters of its own first real-world
run. A shape check (does it run, does it print, does it exit non-zero on
`--strict`) would have passed this version and shipped it straight into a
blocking pre-commit gate that would then have failed on every single
commit touching `yamlgraph/utils/llm_providers.py` — which is nearly every
provider-related change in the repo.

## The catch

`read_raw_output_first`: before writing a single test, I ran
`python scripts/direct_import_scan.py --detail` against the live repo and
*read* the findings list rather than trusting the summary counts. The
summary said "31 core failures" — a number that could plausibly mean "the
scanner works and there really are 31 gaps." Only reading the actual
distribution names line by line surfaced that most of them were
already-declared dependencies wearing an underscore disguise.

## The fix

Added a `_normalize()` helper applying PEP 503-style normalization
(`re.sub(r"[-_.]+", "-", name).lower()`) to both sides of the comparison —
the resolved import distribution and every declared `pyproject.toml`
dependency name — before checking set membership. Re-running the scan
after the fix: core failures dropped from 31 to 0 (with 24 correctly
becoming non-findings and the remaining ~7 all being the genuinely
undeclared `langchain_core` — itself pending on FR-760, not yet merged at
authoring time — and FR-762's frozen `litellm`/`starlette`/`protobuf`
table). Two packages I had provisionally flagged as "new gaps needing
disposition" during design (`httpx`, `uvicorn`) turned out to already be
declared elsewhere in `pyproject.toml` once normalization was correct —
they were never real gaps, just victims of the same bug.

## Heuristic

**Any string-based "is this declared?" check that compares an import name
to a PyPI distribution name must normalize both sides (PEP 503: hyphens,
underscores, and dots are equivalent, case-insensitive) before the first
real run, not after the first failure report is misread as ground truth.**
This is narrower than the general `read_raw_output_first` cure but
specific enough to save the next person writing an import-to-dependency
mapper from re-discovering it the hard way — the underscore/hyphen split
is systemic across the `langchain-*` ecosystem specifically, so any tool
that walks LangChain-based imports will hit this immediately.

**Seed:** The ownership model this scanner settled on — "satisfied if
declared *anywhere* in pyproject.toml, not tied to which directory the
importing file lives in" — was a deliberate simplification of FR-761's
frozen per-surface ownership table. It works today because no two extras
currently declare *conflicting* version constraints for the same
distribution. What happens the day two optional extras need incompatible
version ranges of the same package, and the scanner's "declared anywhere"
check silently passes a core file that's actually importing the wrong
range? Is there a cheaper structural signal (dependency graph solve
failure, `pip check`) that would catch that specific class before a
scanner rewrite would be needed?

## Follow-up (same day, PR #463 review)

The seed above fired within hours. PR review flagged exactly this: a new
required core import would silently pass if its distribution happened to
be declared under an unrelated extra (`booking`, `digest`, `redis-simple`,
`a2a`, …) — the flattened "declared anywhere" set doesn't distinguish
"this file's owner" from "any owner at all." Concrete instance found by
the reviewer's probe: `yamlgraph/contrib/a2a_client.py` unconditionally
imports `httpx` at module scope, but `httpx` was declared only under
`booking`/`digest`/`npc` — unrelated extras — and the flattened check let
it through.

Fix: split classification by import *site*, not just by directory.
Module-level (unconditional) imports in `yamlgraph/` now require the
distribution in core `[project.dependencies]`, unless the file matches an
explicit `PATH_PREFIX_OWNERS` table entry (a small, auditable list of
recognized optional feature surfaces — `storage/simple_redis.py` →
`redis-simple`, `contrib/a2a_client.py` and `a2a/` → `a2a`, etc.), in
which case the owning extra(s) also count. Nested/lazy imports (inside a
function, method, or try/except — the genuine multi-provider-factory
pattern in `llm_providers.py`) keep the permissive "declared anywhere"
check, because that's the one case where per-file ownership really would
be impractical (a single factory file legitimately imports a different
provider SDK per branch). `httpx` was added explicitly to the `a2a` extra
(it's already a transitive dependency of `a2a-sdk`, but FR-761's own
direct-import philosophy requires an explicit declaration, not a
transitive one).

The seed's harder question (conflicting version ranges across extras for
the same distribution) remains open — this fix narrows the blast radius
(only module-level imports in unmapped files are now strict) but doesn't
solve version-range conflicts. Left for the next person who hits it.
