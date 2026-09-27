# Feature Request: ramp_rtm as the FR-1125 showcase — the refused shape and the filled one

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented (2026-09-27) — docs PR pending merge (see [Implementation record](#implementation-record))
**Effort:** 0.5 day
**Requested:** 2026-09-27
**First consumer / first event:** a reader of
`examples/demos/ramp_rtm/README.md` after FR-1125 who asks "how do I use
Anthropic now?", at the moment they want to *see* rather than read: one
command that shows what constrained decoding refuses (no tokens spent)
and one that shows the declared form filled (two cheap calls on a
committed fixture). Second consumer: `tests/unit`, so the before/after
pair cannot rot as the demo evolves.
**Research:** FR-890 route **not run** (the operator's rite for this FR
named judge, enforce, PR, outsider, merge). Substitute, per the
TEMPLATE's equivalent-record clause and the FR-1083 precedent: the live
spike [docs/spikes/constrained-object-2026-09-27/README.md](../docs/spikes/constrained-object-2026-09-27/README.md)
(the mechanism), today's live proof of this very demo after the retype (commit
`0cc2c3ff57a5fe635ad669477476504929ef9066` on #734: the 2026-09-27
`anthropic/claude-haiku-4-5` run; the `demo-output.log` on `main` at filing
time is still the 2026-08-23 DeepSeek run), the CI capture of the
E017 refusal on this demo's `derive/node` before the retype (run
36339774208), and the in-body [Alternatives Considered](#alternatives-considered)
with an `is_this_a_graph` answer.
**Prior art:** [FR-1125](FR-1125-refuse-unconstrained-objects-anthropic.md)
made the rule and migrated this demo's prompt; this FR adds no rule and
edits no governed artifact, it adds the demonstration surface
Commandment 2 asks for ("never explain abstractly; show working code").
FR-866 created `ramp_rtm`; this FR keeps its purpose and adds one README
section. [FR-1113](FR-1113-meta-map-demo.md) is the precedent for a demo
that deliberately shows a failure class beside the working path
(poison inputs); this FR does the same with the refused schema form,
but reproduces the failure through lint at zero cost instead of a paid
run. FR-1054 (`output_schema` nested objects) is the form shown.
[FR-1123](FR-1123-untyped-subschema-constrained-decoding-gate.md) owns
the sibling E016 class; not shown here, one class is enough for a
showcase. No REJECTED FR in this territory.

## Summary

After FR-1125, no example is labelled as the demonstration of how
Anthropic structured output now works: `ramp_rtm` proves the working
form (fixture-driven, Anthropic by default, live log committed today)
but shows nothing of the refusal, and the reference explains the rule
to readers who would rather run something. This FR makes `ramp_rtm` the
showcase: a README section that shows the refused form and the filled
form side by side, a zero-token way to reproduce the E017 refusal, the
live command, and a deterministic test that keeps the pair honest.

## Value Statement

A reader gets the whole FR-1125 story from one demo directory in two
commands, one of which costs nothing, and the repository gets a
witness that the showcase's "before" is still refused and its "after"
still fills.

## Problem

- The quickstart (`examples/demos/hello`) uses three strings; it cannot
  show an object.
- `ramp_rtm`, `fr-atlas` and `req_witness_audit` now use `output_schema`
  on Anthropic with live proofs, but none says so; a reader would not
  know which to open.
- The refusal is documented (`reference/prompt-yaml.md`, E017) but never
  demonstrated; its message is the most useful artifact FR-1125 produced
  and nobody sees it until they hit it.
- A README alone rots: the next edit to the demo's prompt could silently
  make the "before" text wrong.

## Ideal Result

`examples/demos/ramp_rtm/README.md` carries a section a newcomer can
follow top to bottom: the schema before FR-1125 and after, the exact
E017 message, one lint command on a scratch copy that reproduces it
without a token, the live run command, and the committed proof. A unit
test asserts the section exists, the before-form is refused by lint with
that message, the committed demo lints clean, and the committed prompt's
transformed item schema keeps its five fields. No prompt or graph
changes; no new demo directory.

## Proposed Solution

### S-1: README section

`examples/demos/ramp_rtm/README.md` gains, after "## Output":

```markdown
## Anthropic and open objects (FR-1125)

This demo runs on Anthropic by the framework's built-in default and is
the showcase for FR-1125. Its `entries` field was `list[dict]` until
2026-09-27. Anthropic's constrained decoding cannot express an object
with unknown keys: the API refuses `additionalProperties: true`, so the
SDK rewrites the object to `properties: {}` and the model can only answer
`[]`. YAMLGraph now refuses that shape before any call:

    ❌ [E017] Prompt 'derive_reqs' (node 'derive/node', model 'provider default'):
    field 'entries.items' is an object with no declared properties; Anthropic
    constrained decoding reduces it to {} and the model can only answer empty.
    Declare its properties with the output_schema form ...

Before (`fields` form) / after (`output_schema` form): <the two-line
schema excerpts, verbatim from git history and the committed prompt>.

Reproduce the refusal without spending a token: copy the demo to
`tmp/`, put `type: list[dict]` back in the copy's `prompts/derive_reqs.yaml`
under a `schema:` block, run
`PROVIDER=anthropic yamlgraph graph lint tmp/ramp_rtm/graph.yaml`
(the provider is set explicitly; the resolver reads `PROVIDER` before its
built-in default, and a host `.env` can change the classification).

Run the filled form: `PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5
yamlgraph graph run examples/demos/ramp_rtm/graph.yaml --var
target=tests/fixtures/ramp_target --full` (two calls; both variables are
set explicitly because the model is an environment-overridable default); the committed `demo-output.log` is
that run from 2026-09-27, every entry carrying `req_id`, `statement`,
`witness_tests`, `confidence`, `status`. Reference:
[Unconstrainable schema fields on Anthropic](../../../reference/prompt-yaml.md).
```

Exact wording is the enforcer's; the elements are frozen: rule in two
sentences, the **complete** E017 diagnostic (`[E017] ` plus the linter's
message, never truncated), before/after excerpts, zero-token
reproduction with `PROVIDER=anthropic`, live command with
`PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5`, proof pointer,
reference link.

### S-2: The witness

`tests/unit/test_fr1126_ramp_rtm_showcase.py` (process mark; REQ-YG-712).
An autouse fixture sets `PROVIDER=anthropic` for every test (R-1, C-2):

- README contains the section heading, the code `E017`, the strings
  `list[dict]`, `output_schema` and `demo-output.log`.
- **Before is refused:** the test builds a temp copy of the demo
  directory, rewrites the copy's `prompts/derive_reqs.yaml` to the
  pre-FR-1125 `fields` form (the schema text lives in the test as a
  string; no open-object prompt is committed under `examples/`), and
  asserts `lint_graph` reports exactly one `E017` naming `derive/node`
  and `entries.items`.
- **After is clean and full:** the committed demo lints with no
  E016/E017/W028/W029, and the committed prompt's model, passed through
  the public `anthropic.transform_schema`, keeps exactly the five item
  properties and requires all five.
- The README's E017 diagnostic, after whitespace normalisation, **equals**
  `[E017] ` plus the sole before-copy `LintIssue.message` (R-3): no
  prefix, no ellipsis, so the README cannot drift from the code.

RED: the README assertions fail before S-1; the before/after assertions
pass already and stay as the rot guard.

### S-3: Proof and records (R-2)

No new paid run. The Anthropic proof is commit
`0cc2c3ff57a5fe635ad669477476504929ef9066` on #734 (2026-09-27,
`anthropic/claude-haiku-4-5`, two branches, every entry carrying the five
fields); the `demo-output.log` on `main` at filing time is the 2026-08-23
DeepSeek run and is not that proof. The implementation PR carries the
exact successful Anthropic log in its own diff: cherry-picked from
`0cc2c3ff` if #734 has not merged, or, if #734 lands first, the same
file with at most a provenance-header line naming it as the FR-1126
reused proof and the raw run body preserved. This is what the
repository's demo-proof gate requires for any README change under a
demo. The implementation record states #734's final disposition. FR
record and Distill diary entry with a `**Seed:**`; no changelog fragment
(C-7).

### Not in scope

- A new minimal demo directory (deferred; the FR-1125 diary's seed).
- Any edit to `graph.yaml` or `prompts/*.yaml` (none needed; the demo is
  already in the working form).
- Framework or linter changes; E016 demonstration.

## Acceptance Criteria

The judgement's revised list is binding; it replaces the original
AC-01..AC-06.

- [ ] AC-01: The README contains the heading `## Anthropic and open objects (FR-1125)` and all seven frozen elements: the two-sentence rule, complete E017 diagnostic, before/after schema excerpts, zero-token reproduction, live command, proof pointer, and reference link.
- [ ] AC-02 (RED first): A commit before the README implementation adds the focused test and fails only its README assertions; a later GREEN commit adds the section. The FR records both SHAs.
- [ ] AC-03: With `PROVIDER=anthropic` explicitly set, a temporary copy using the pre-FR-1125 `schema:` / `entries: list[dict]` form produces exactly one E017 whose message names `derive/node` and `entries.items`; no open-object prompt is committed under `examples/`.
- [ ] AC-04: With `PROVIDER=anthropic` explicitly set, the committed demo has none of E016, E017, W028, or W029. Passing its prompt model through public `anthropic.transform_schema` preserves exactly `req_id`, `statement`, `witness_tests`, `confidence`, and `status`, requires all five, and yields `additionalProperties: false`.
- [ ] AC-05: After whitespace normalization, the README's complete E017 diagnostic equals `[E017] ` plus the sole before-copy E017 `LintIssue.message`; prefix-only and ellipsis-truncated comparisons fail.
- [ ] AC-06: The README's refusal command sets `PROVIDER=anthropic`. Its live command sets `PROVIDER=anthropic` and either sets `ANTHROPIC_MODEL=claude-haiku-4-5` or omits any fixed-model claim.
- [ ] AC-07: The implementation diff contains a semantically valid `examples/demos/ramp_rtm/demo-output.log` from commit `0cc2c3ff`; it identifies Anthropic/`claude-haiku-4-5`, a successful two-branch run, and populated entries carrying all five declared fields. The demo-proof gate passes without a new paid run.
- [ ] AC-08: Every test carries `@pytest.mark.req("REQ-YG-712")`; the focused FR-1126 test and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-09: The FR implementation record states the final #734 disposition, RED/GREEN SHAs, and exact validation results; a Distill diary entry with `**Seed:**` is present.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| A new minimal demo `structured-output-anthropic` | Deferred. Best long-term teaching surface, but a new directory needs its own graph, prompts, proof and README; `ramp_rtm` already has all four. Seeded in the FR-1125 diary. |
| README section only, no test | Rejected. The "before" text rots the first time the prompt changes; the pair must be witnessed. |
| Commit the before-prompt as a second prompt file under the demo | Rejected. An open-object prompt on an Anthropic-bound demo trips lint and the FR-1125 census; the before form lives in the test as a string. |
| Demonstrate the refusal with a paid run of the before-form | Rejected. Lint reproduces it at zero cost and shows the same message the compile and bind refusals use. |
| Show E016 (untyped) too | Rejected here. One class is enough for a showcase; FR-1123 owns E016. |

`is_this_a_graph`: no; a README and a test.

## Judgement fold (2026-09-27)

[Judgement](FR-1126-ramp-rtm-fr1125-showcase.judgement.md): APPROVED WITH
REVISIONS. Folded the same day:

- **R-1** → S-1, S-2: `PROVIDER=anthropic` on the refusal command and in
  the test's autouse fixture; the live command sets
  `ANTHROPIC_MODEL=claude-haiku-4-5` explicitly.
- **R-2** → Research, S-3: the proof is commit `0cc2c3ff` on #734, not
  the DeepSeek log on `main`; the implementation diff carries it.
- **R-3** → S-1, S-2: the README quotes the complete diagnostic and the
  test asserts equality after whitespace normalisation.

Scope frozen to the judgement's D-1..D-5; conditions C-1..C-7 are gates.
Judge rendered from the author's session via the sole route, as recorded
for FR-1121..FR-1125.

## Related

- `examples/demos/ramp_rtm/` (FR-866), `demo-output.log` (#734).
- `reference/prompt-yaml.md` § Unconstrainable schema fields on Anthropic.
- `yamlgraph/linter/checks_schema.py` (E017), `docs/spikes/constrained-object-2026-09-27/`.

## Implementation record

**Enforced 2026-09-27**, branch `docs/fr1126-ramp-rtm-showcase` (worktree).

| Step | Commit | Evidence |
|---|---|---|
| RED | `c59c3787` | `tests/unit/test_fr1126_ramp_rtm_showcase.py`: the two README assertions fail (no section, no diagnostic); the before-copy E017, the clean committed demo and the five-field transformed schema pass from the start, with `PROVIDER=anthropic` set by an autouse fixture. |
| GREEN | `12661284` | README section with the seven frozen elements; the complete diagnostic quoted in a text block and asserted equal to the linter's message after whitespace normalisation. |
| Test correction | `d0b9c303` | the ellipsis guard forbids a truncated end only; the diagnostic's own `{...}` is legitimate text. |
| Proof (R-2) | `4fa01089` + header commit | `0cc2c3ff` cherry-picked from #734 before it merged; #734 then merged as `c33fe6a0`, so the log received one provenance header line naming it as the FR-1126 reused proof, run body unchanged; the fr-atlas log was reset to `main`'s (D-3 is ramp only). Validated with `validate_demo_output_log_file`. |

#734 disposition: merged (`c33fe6a0`, 2026-09-27 19:15Z); this PR depends
on nothing from it beyond the identical proof body.

Validation: focused test 5 passed with `PROVIDER=anthropic`; ruff clean;
`python scripts/req_coverage.py --strict` passes; no governed artifact,
framework, capability, fragment or paid run (C-6, C-7). The E017 text
the README quotes was captured from the linter on the before-copy on
2026-09-27 and is byte-equal after normalisation.
