# 2026-08-22 — FR-852: the pipeline's own inputs were the last thing it preserved

**FR:** FR-852 (preserve graph-authoring briefs as committed planning
artifacts) — plan, judge, enforce in one morning, triggered by a
five-word operator prompt: "check tmp - graph authoring briefs".

## The provenance system had a gitignored root

The repo enforces provenance obsessively: FRs are the source of truth,
judgements graduate from drafts to committed `.judgement.md`, demo runs
require committed `demo-output.log`. Yet the *input-closure record* of
every sole-route authoring run — the task brief that doctrine itself
declares the ONLY non-repo input — lived in gitignored `tmp/`. Ten FRs
cited `tmp/fr-XXX-authoring-brief.md` as their execution record; every
citation was a dangling pointer awaiting the next tmp cleanup. The
diary had even declared "the brief is code" (FR-789) without noticing
that this code was the only code we didn't keep.

The trap is a cousin of `infrastructure_self_exempt`: the artifact
class that *feeds* the enforcement pipeline was exempted from the
preservation discipline the pipeline enforces on everything else. The
asymmetry was visible for months in plain listings — 34 briefs
accumulated since Aug 4 — but it took an outside question ("should
these be preserved like FRs?") to see it. Inventory by visibility
failed here too: briefs look like scratch because they live next to
scratch.

## The judge killed my glob

My draft FR said `cp tmp/*brief*.md`. The judgement (sole route,
gpt-5.5) refused to authorize a wildcard copy from ignored state and
demanded an exact manifest — old path, new path, governing FR,
rationale, per file. Folding that revision forced the grep pass that
found the real evidence shape: only 10 of my claimed "at least 9" FRs
cite a brief path; FR-771 cites the wrapper without the brief; FR-789
and FR-791 cite the *report*, not the brief. The manifest also
surfaced four gitclaw briefs and two genuinely FR-less briefs I would
have miscounted under the glob. The judge's R-1 was `substance_over_presence`
applied to my own migration plan: "copy the briefs" was presence;
34 rows with named consumers is substance.

Second catch: my draft contained a live contradiction — ideal state
"no FR cites a gitignored path" vs. proposed "no retroactive rewriting
of FR prose". I had written both sentences within minutes and not seen
the collision. The judge saw it cold (R-2). Input closure works in
both directions: the judge couldn't see my chat narrative, so it read
the FR as a text, and the text disagreed with itself.

**Heuristic (first strike):** when an FR proposes migrating N files by
pattern, the pattern is a forecast and the manifest is the measurement
— enumerate before judging, because the enumeration itself falsifies
the FR's evidence claims. Related: `threshold_encodes_forecast`.

**Seed:** the authoring *report* (`tmp/draft-authoring-report.md`) is
still ephemeral — it is overwritten per run and cited by at least two
FRs. FR-852 deliberately deferred it. When a session next needs a
historical validation record that the FR body summarized too thinly,
that is the second strike: give reports the same graduation the
judgement drafts got (`.authoring-report.md` beside the FR, or dated
files under authoring-briefs/). Watch also whether new briefs actually
land in `feature-requests/authoring-briefs/` — review-time enforcement
was chosen over wrapper enforcement as a first strike; drift here is
the trigger for mechanizing.
