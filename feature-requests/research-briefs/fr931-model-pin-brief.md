# Problem brief: the model pin behind the judge and review sole routes

**Prior art:** filename-noun hits share only the generic tokens "model",
"pin", and "brief": `corpus-census-skeleton-reuse.md`,
`census-human-readable-tail.md`, and
`corpus-map-reduce-reference-contract.md` are corpus/census pipeline
briefs; `session-accountability-record.md` concerns session receipts;
`fr-891-web-research-fail-open.md` concerns web-search failure policy in
the research route. None addresses which model executes a governed
route. The genuine prior art is FR-758 / CAP-211 (the sole-route
wrapper and adapter contract being edited) and FR-928 (in-flight, holds
the same pin constant) — both dispositioned in the FR.

## Problem statement

The judge sole route (`.github/skills/judge-fr/adapters/graph.yaml`) and
the review sole route (`.github/skills/review-pr/adapters/graph.yaml`)
both pin `cli_flags.model: gpt-5.5` on their single `copilot` node. That
pin was chosen when gpt-5.5 was the strongest reasoning model available
to the Copilot CLI. It no longer is: `gpt-5.6-sol` is now offered by the
same CLI (verified 2026-08-30, CLI 1.0.82, a non-interactive `-p` probe
with `--model gpt-5.6-sol` completed and billed), is a later generation,
carries a larger default context window (272k prompt tokens vs 200k),
and is priced lower per token in the same billing sheet (input 200 vs
500, output 1000 vs 3000 credits per 1M — `feature-requests/FR-900-evidence.md`).

The two routes are the repository's only authority-granting and
merge-advising surfaces. Every FR in the repo passes through the judge
pin; every PR review passes through the review pin. The question is what
the correct decision procedure is for changing that pin — the model
identifier is one literal line in each of two YAML files, but the
verdict quality it produces is the thing the whole plan-judge-enforce-
review spine rests on, and there is no committed record of how a pin
change should be evidenced, staged, or reverted.

Two properties of the current situation make the decision non-trivial.
First, the routes are unverified against any model other than the pinned
one: no test, gate, or artifact records that a verdict rendered by a
different model still satisfies the frozen output contract that
`scripts/judge.sh` and `scripts/review.sh` enforce (`tmp/draft-judgement.md`
with a `**Verdict:**` line; the review artifact equivalent). Second, the
pin is duplicated across two adapters (three, counting the authoring
route, which is outside the immediate ask but shares the literal), so
any change has a consistency dimension the repo currently handles by
copy-paste.

## Classification

judgement/analysis/generation

## Constraints

- The judge and review routes are the SOLE execution routes for their
  respective doctrines; any change must keep `scripts/judge.sh` and
  `scripts/review.sh` as the only entry points and must not weaken the
  artifact contracts they verify (verdict line present, artifact
  non-empty, verified by artifact never by exit code).
- The copilot node's model resolution chain is already implemented and
  must not be re-designed: `cli_flags.model` > node-level `model` >
  graph `defaults.model` > omit (`yamlgraph/node_factory/copilot_node.py`,
  FR-266). Omitting the pin entirely is out of bounds — an unpinned node
  inherits the CLI ambient default and becomes an unbilled drift surface
  (diary 2026-08-25).
- Configuration is truth (Commandment 3): the model belongs in YAML, in
  the repo, visible in a diff. No environment-variable-only selection
  that leaves the effective model absent from git.
- Governed spend is the cheap spend and must stay that way: the three
  sole routes together were ~5% of the 2026-08 invoice. A change must not
  move a governed route onto a more expensive model without an explicit
  cost line in the record.
- Model availability is a vendor surface outside our control. Whatever is
  decided must degrade legibly if the identifier stops being served —
  the failure must be visible, not silently re-routed.
- Whatever is decided applies to two adapters that are near-identical by
  construction; divergence between them must be either impossible or
  deliberate and recorded.

## Witnessed incidents

- 2026-08-30 (this session): `copilot -p "reply with exactly: OK"
  --model gpt-5.6-sol --allow-all-tools` completed on CLI 1.0.82 and
  billed 7.55 AI credits — the identifier is accepted by the same binary
  the adapters shell out to. No equivalent verification exists in the
  repo for any model other than gpt-5.5.
- 2026-08-25 (`docs/diary/diary-2026-08-25-the-invoice-audits-the-doctrine.md`):
  the invoice-as-coverage-report reflection found gpt-5.5 pinned in all
  three sole routes at $296.82, and identified unpinned copilot nodes as
  "the drift surface nobody bills to a diff". The same entry recorded a
  concrete repoint lever for `validate-session.yaml` (Opus 4.6 →
  cheaper) that was never executed — evidence that model-pin changes are
  proposed and then stall for want of a procedure.
- 2026-08-25 (`docs/analysis-fr888-post-mortem-2026-08-25.md:17`): five
  consecutive review rounds under the gpt-5.5 pin all returned "Not
  approved" until the operator merged manually — a witnessed case where
  the pinned model's verdict behaviour on the review route was itself
  the operational problem.
- 2026-08-28 (`feature-requests/FR-928-cloud-judge-github-actions.md:227`,
  and its judgement at :17): an in-flight FR moves the judge route into
  GitHub Actions and explicitly names "same model pin (gpt-5.5)" as the
  invariant it holds constant to isolate cloud variance. Two changes to
  the same literal are in motion at once.
- 2026-08-04 (`docs/diary/diary-2026-08-04-the-verdict-i-almost-shipped-without-measuring.md:28`):
  a verdict from the pinned judge was classified and nearly shipped
  without measurement — the record shows verdict quality from this route
  has failed observably before, with no model-attribution data captured.
