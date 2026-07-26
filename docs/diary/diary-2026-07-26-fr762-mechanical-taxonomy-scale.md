# 2026-07-26 — When "mechanical" hides an exponent

## What happened

FR-762's core requirement (R-2) reads: "one row per example root... 'Example
root' is defined mechanically: any directory under `examples/` containing a
graph YAML, a Python app/CLI entry point, or a README usage command." The
plan implicit in the FR's prose was a hand-authored table — a handful of
rows, judgement calls per example, done in an afternoon.

Running the mechanical definition literally against the actual repository
produced **112** candidate roots: 32 top-level `examples/*` directories plus
roughly 75 subdirectories under `examples/demos/`. Hand-classifying 112 rows
is not a judgement task anymore — it's a data-entry task with a stale-on-
arrival shelf life, because the very next new demo added under
`examples/demos/` would silently be missing from a hand-written table with
no mechanism to notice.

## The pivot

Rather than accept either horn — do the infeasible manual work, or narrow
the FR's own definition to make it feasible by fiat — I built the thing the
FR's own words already specified: a script that performs the "mechanical"
classification described in the text, instead of a human performing it by
hand from the same rule. `scripts/example_taxonomy_scan.py` discovers roots,
extracts every third-party import per root (reusing FR-761's scanner
internals — `_extract_imports`, `_resolve_distribution`, `_normalize` — not
a second implementation), and classifies each as `extra-backed` or
`externally-provisioned`. `--check` mode makes the committed YAML
self-verifying: a new demo added tomorrow either regenerates correctly or
the check fails, which is a strictly stronger guarantee than any hand-
maintained table could offer.

## The trap under the trap

The first real run of the classifier reported 12 "externally-provisioned"
roots. Reading each one (not trusting the count) surfaced two different
species of the SAME underlying trap, `plausible_wrong_answer`:

1. **Real aliasing gaps** — `tavily` (module name) vs. `tavily-python`
   (PyPI distribution) and `chatterbox` (module name) vs. `chatterbox-tts`
   (distribution) were genuinely declared dependencies that the scanner's
   `IMPORT_TO_DIST` alias table simply didn't know about yet. Both were
   already available via the `tavily`/`chatterbox` extras — the taxonomy
   was accidentally correct about a bug in the underlying scanner it
   inherited, one FR-761 hadn't hit because report-only findings for
   `examples/` were never scrutinized closely enough to notice.
2. **Genuinely local modules** — `tools`, `utils`, `api`, `actions`,
   `canon_tools`, and others were per-example helper packages imported via
   the common `sys.path.insert(0, ...); import tools` fixture idiom. These
   are not third-party at all; they're local siblings that happen to share
   a bare import name with no package prefix. No existing exclusion list
   caught this because FR-761's scanner only excludes a fixed top-level
   `FIRST_PARTY` set (`yamlgraph`, `examples`, `scripts`, `tests`,
   `capabilities`) — it has no notion of "local to THIS particular root."

Fixing #1 was two dictionary entries. Fixing #2 required a genuinely new
idea: `_local_module_names(root)` — walk every `.py` stem and every
subdirectory name anywhere under a root, and treat any bare import
matching one of those names as local. This is not a hack specific to the
taxonomy script; it had to be back-ported into FR-761's own
`direct_import_scan.py` too, because AC-08 required promoting extra-backed
example roots from report-only to core-failure strictness — and the moment
that promotion happened, the same 12 false positives reappeared as
*blocking* failures in the underlying scanner, not just noisy taxonomy
rows. One fix, two call sites, applied identically to keep the boundary
consistent across both tools (`callsite_fix`, but at the SHARED utility
this time, because both call sites reference the exact same filesystem
question — "is this name locally resolvable under this root?" — not two
different questions that happen to look similar).

## Heuristic

**`inventory_by_visibility`'s sibling: a definition that reads as
"mechanical" in prose can still hide combinatorial scope until you actually
run it.** The FR's own words already specified an algorithm; the size of
its output space was invisible until executed. The corrective wasn't to
renegotiate the definition down to something a human could stomach — it was
to notice that "mechanical" is a promise about REPRODUCIBILITY, and a script
honors that promise more completely than a human ever could, precisely
because it doesn't get tired at row 60 and start waving things through.

**Seed:** When an FR's acceptance criterion says "one row per X, defined
mechanically," treat "mechanically" as a literal instruction to write code,
not prose to interpret by hand — and run the discovery step BEFORE
estimating effort, because the exponent is invisible until you count.
