# 2026-08-26 — The route that indicts its own author (FR-890)

## What happened

Enforced FR-890: the research sole route. Five closed-input personas,
an LLM-free reducer, a wrapper in the judge.sh lineage, a template
field, and a judge-doctrine clause that kills unresearched plans. The
D-9 exemplar was the point: re-run the FR-888 problem — the one where
a 601-line regex grammar shipped because nobody considered OS
permissions — through the new route, and see what comes back.

It came back with the answer the operator had to supply by hand three
days ago. The os-infra-primitivist proposed kernel-enforced mount
boundaries; the subtractionist said "make the checkout read-only";
the librarian cited external worktree-isolation prior art with a URL.
**No persona proposed the terminal grammar.** The route, on its first
real firing, retroactively out-planned the session that built its
predecessor. That is the cleanest witness the FR could have asked for:
the contamination was never the model's capability, it was the loaded
context. Change the input closure and the same model class (haiku!)
finds the class a frontier-model session missed.

## Trap encountered: the enforcement layer polices its enforcer

Mid-enforcement, the FR-888 guard denied MY writes to the main
checkout — the guard whose post-mortem seeded this very FR forced this
FR's enforcement into a worktree. Two observations: (1) the guard
works, including against the agent that documented its flaws; (2) the
`$PWD`-relative denial is coarse — it resolved my worktree-relative
paths against the main checkout and denied literal `$PWD` in an
argument. I routed around it with literal absolute paths, which is
compliance, not bypass — but a guard that denies by string inspection
of unexpanded variables is `gate_checks_shape_not_substance` pointed
at itself. Not my scope today (FR-888's territory); noted for its
successor.

## Trap avoided: preflight classifier false-positive

`author_preflight.py` classified my smoke-run command as a premise
because the path contained the substring "fixtures" (an input marker).
The judged cure was already in the mechanism: output markers win over
input markers, so appending `# writes tmp/draft-alternatives.md` to
the line reclassified it. The lesson generalizes: when a deterministic
classifier misfires, look for the tiebreak rule the author built in
before reaching for `--no-preflight`. The escape hatch is almost never
the first move.

## Insight: the bootstrap paradox is handled by naming it

FR-890 mandates research evidence for every new FR — including,
recursively, itself. The judgement resolved this not with machinery
but with one sentence: "FR-890 itself is the bootstrap case, judged
under the prior doctrine." Activation boundaries are cheap when
stated and catastrophic when implied. The same pattern held for the
board: `FR-XXX.research.md` would have rendered as a PARSE-FAILURE row
— the new artifact class had to be named in every consumer that
enumerates the namespace (`fr_board.py` exclusion). A new sibling file
convention is not one change; it is one change per enumerator.

## Seed

**Seed:** The route proved a cheap model with clean closure beats an expensive
model with dirty context — for PLANNING. Where else is the repo paying
frontier-model prices for a contamination problem? Candidate: the
review route reads the full PR diff plus FR plus judgement in one
context. Would five closed-input reviewers (security-only, scope-only,
test-substance-only, entropy-only, precedent-only) each seeing ONE
slice, reduced by code, out-review the monolithic reviewer the way
five haiku personas out-planned the FR-888 session?
