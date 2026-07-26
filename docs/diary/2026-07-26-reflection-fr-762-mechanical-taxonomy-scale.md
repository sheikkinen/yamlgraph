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

## Follow-up: PR #464 review (2026-07-26)

The reviewer's rejection restated the same trap in a sharper form: the
initial enforcement's "top-level plus one demos-flatten" discovery was
ITSELF an unexamined interpretation of "mechanically" — a human-shaped
compromise disguised as an algorithm. The literal FR wording ("any
directory under `examples/`") demanded fully recursive `os.walk`
discovery; anything less was the same convenience-over-literalism drift
the diary above already named. The fix (recursive discovery + README
usage-command gate) grew the root count 112 → 139 and surfaced both
reviewer-cited omissions immediately — confirming that the "count before
estimating" heuristic applies recursively: count again after the first
count, because the first count can itself be an interpretation.

The second finding (`_extras_covering()` preferring full single-extra
coverage over any partial owner) was a `plausible_wrong_answer` case: the
old `_owning_extras()` output looked correct (an extra was named, imports
did resolve) but answered a different question than the one asked — "does
some extra cover this" instead of "which extra IS this example's."
Shape-correct, semantically wrong.

## Follow-up: PR #464 review, round 2 (2026-07-26)

A third instance of the same underlying shape, one level removed: `_root_imports()`
scanned every `*.py` file physically under an example root — a correct
answer to "what does this DIRECTORY import" but the wrong question for
"what does this EXAMPLE require to run." `a2a_call` runs a `type: python`
tool whose implementation is a `module:` reference resolved by YAMLGraph's
own graph loader at runtime, living under `yamlgraph/contrib/`, outside
the example root entirely. `a2a_server`'s runnable surface is two shell
commands documented in prose, backed by a CLI module the example directory
never imports at all. Both are real, load-bearing dependency edges that a
recursive filesystem `.py` scan structurally cannot see, because they
don't live in the filesystem location the scan was looking at — they live
in a YAML string and in Markdown prose.

The trap this names isn't new (`downstream_fix`/`symptom_patch` cousins),
but the specific shape is worth keeping distinct: **the artifact you're
classifying (an "example") is not coextensive with the files sitting in
its directory.** An example's true import surface is defined by what it
*causes to execute* — including other files it references by string
(a module path in YAML, a command in a README) — not by what physically
lives under its path. The fix generalizes cleanly: any place a root
declares "run this other thing" (a tool module, a subprocess command, a
subgraph reference) is a pointer the classifier must follow, the same way
a `from x import y` statement is a pointer the AST walk already follows.

Also recurred independently: the exact same stray-untracked-diary-duplicate
pattern FR-761 hit (a `git mv` rename to the diary-gate filename format
left the old-named file behind, untracked, on disk) was found again here
during this same follow-up — two sibling FRs, same session, same trap,
discovered independently each time rather than checked-for proactively.
That's the actual signal to graduate, not the individual finding: after
any `git mv` rename of a diary file, run `git status --porcelain
docs/diary/` before moving on, every time, as a fixed post-rename ritual —
not something to notice only when writing the follow-up section.

**Seed:** When a classifier walks a directory tree looking for "what does
this thing depend on," ask explicitly: does this artifact reference OTHER
files by string (config keys, prose commands, indirect module paths) that
a pure filesystem walk would never resolve? Building the answer as an
explicit, enumerable "reference-resolution" step (not a growing pile of
special cases) is what let both a2a findings fall to one generalized fix
instead of two hand-coded exceptions.
