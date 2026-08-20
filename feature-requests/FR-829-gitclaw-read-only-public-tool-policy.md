# Feature Request: FR-829 gitclaw Read-Only Public Tool Policy

**Priority:** HIGH
**Type:** Bug
**Status:** ENFORCED 2026-08-20 — 13/13 ACs satisfied; human-reviewed
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Prior art:** FR-827 created and governs gitclaw's generated-feature pipeline;
FR-828 discovered the policy contradiction through a real cookbook preflight
and is the first blocked consumer. FR-824 supplies bounded public-source and
source-health precedent, not gitclaw policy. FR-425 is a false noun match on
“policy/intelligence” and concerns hook classification. This FR's judgement is
the verdict for this proposal, not separate prior art.
**First consumer / first event:** FR-828, when its preflight is rerun against
the corrected `sheikkinen/gitclaw` template and can state mechanically that a
generated feature may perform bounded, unauthenticated, read-only public HTTP
retrieval without relying on a favorable interpretation by the LLM judge.

## Summary

Replace gitclaw's contradictory generated-feature instructions with one
gitclaw-local policy referenced by plan, judge, enforce, and review. The policy
permits feature-contained tools that perform bounded, unauthenticated,
read-only retrieval from public endpoints frozen in the feature request, while
continuing to forbid new secrets, environment credential access, external
writes, workflow/dependency mutation, and changes outside the generated
feature directory.

Add deterministic tests proving every stage uses the same policy and that the
old “graph plus prompts only” rule cannot reappear unnoticed. This FR changes
gitclaw policy and prompt contracts only; it does not implement FR-828 or add a
runtime gate that rejects tools.

## Value Statement

Gitclaw adopters can request useful public-data automations with contained
tools while planner, judge, enforcer, and reviewer apply one explicit security
boundary instead of contradictory prose.

## Problem

FR-828's preflight found four incompatible descriptions of what a generated
feature may contain:

1. `README.md` says generated feature graphs may declare and use tools because
   that is their purpose.
2. The vendored graph-authoring doctrine defines a complete artifact as graph,
   prompts, optional tools, and validation evidence.
3. `prompts/judge.yaml` requires “YAMLGraph-only artifacts: graph.yaml plus
   prompts/” and rejects “external side effects beyond the commit-back workflow
   layer,” without distinguishing a public GET from an external write.
4. `prompts/enforce.yaml` repeats “YAML-only implementation” and requires only
   graph and prompts, while `prompts/plan.yaml` and `prompts/review.yaml` do not
   state the generated-feature capability boundary.

The runtime already supports contained tools: the diff containment gate allows
any normalized path under `features/<name>/`, the graph authoring contract
supports optional tools, and cron executes generated graphs. The defect is at
the instruction boundary. Today the same public-data request can be rejected,
approved, or incompletely implemented depending on which sentence the model
privileges.

Simply deleting the restrictive lines would create the opposite defect:
“tools allowed” without a read/write, secret, endpoint, timeout, or data
boundary. Because cron executes approved features with `ANTHROPIC_API_KEY` in
the environment, the policy must explicitly forbid generated runtime tools
from reading credentials or performing authenticated/external writes.

## Ideal Result

A prospective feature is evaluated identically at every gitclaw stage. Pure
graph features remain valid. A feature using a contained tool for finite,
unauthenticated GET/HEAD requests to public endpoints named in its frozen FR is
also valid when it bounds time/results, parses structured data, treats remote
content as untrusted data, and persists no credential/private/unbounded raw
body. Requests for new secrets, environment access, external mutation,
dependency/workflow changes, or unrestricted network behavior are rejected.
One deterministic policy-contract test fails if any stage stops referencing
this boundary or restores graph-plus-prompts-only language.

## Proposed Solution

### 1. One gitclaw-local policy

Add `policy/generated-features.md` as the single source of truth for the
artifact and runtime boundary. It is local gitclaw policy, not part of the
vendored YAMLGraph skills snapshot.

The policy governs features created by gitclaw's issue pipeline. Pre-shipped
cron fixtures such as `features/horoscope/` remain valid under their original
fixture contract and are not retroactively required to carry FR, judgement,
review, or authoring-report provenance. Migrating an existing fixture requires
a separate FR; FR-829 changes no fixture.

The policy defines the following classes.

**Required issue-generated artifact:**

- `features/<name>/graph.yaml` and `features/<name>/prompts/*.yaml`;
- `FR.md`, `judgement.md`, `review.md`, and `authoring-report.md` provenance;
- input variable `date` and exactly one non-empty final output candidate.

**Optional contained artifact:**

- tools, tests, fixtures, and concise feature documentation entirely under
  `features/<name>/`;
- standard-library implementation or dependencies already present in the
  unmodified gitclaw cron runtime;
- bounded read-only access to files committed inside the same feature.

**Permitted public retrieval:**

- unauthenticated HTTP `GET` or `HEAD` only;
- only public endpoint origins explicitly named in the frozen FR/judgement;
- finite connect/read timeout, bounded response size or result count, and
  structured parsing appropriate to the response;
- remote text is untrusted data and is never executed or followed as an
  instruction;
- source failure is explicit and follows the feature's judged partial/fail
  behavior rather than silently substituting plausible content.

**Forbidden behavior:**

- requiring or reading new secrets, tokens, credentials, cookies, or arbitrary
  environment values;
- authenticated retrieval or external mutation, including HTTP
  `POST`/`PUT`/`PATCH`/`DELETE`, webhooks, email, social publication, remote
  issue/comment writes, or uploads;
- executing downloaded code/content or interpolating remote content into shell
  commands;
- modifying workflows, dependencies, gitclaw runtime/policy, repository state,
  or any path outside `features/<name>/` during generation;
- persisting credentials, personal profiles, private/local-device data, or
  unbounded raw response bodies;
- claiming that containment or prompt policy prevents a malicious model from
  exfiltrating secrets. README's existing threat-model honesty remains.

The policy distinguishes external **observation** from external **mutation**.
“No external side effects” becomes “no external writes or authenticated access”
rather than an ambiguous ban on all network reads.

### 2. Align all four stage prompts

Each root prompt must name `policy/generated-features.md` explicitly and apply
it within the stage's existing input closure:

| Prompt | Binding responsibility |
|---|---|
| `prompts/plan.yaml` | Produce an FR that names any public origins, data bounds, timeout/failure semantics, parsers, and contained tool surface; reject or defer requests needing forbidden capabilities |
| `prompts/judge.yaml` | Judge against the shared policy; permit compliant read-only public tools; reject new-secret, authenticated, external-write, unbounded, or out-of-feature requirements |
| `prompts/enforce.yaml` | Replace “YAML-only implementation” with graph + prompts + optional contained tools/tests; implement only the origins and behavior frozen by FR/judgement |
| `prompts/review.yaml` | Review every generated feature path, including tools/tests, against the shared network/secret/data boundary and validation evidence |

No stage may duplicate a divergent abbreviated artifact policy such as
“graph.yaml plus prompts only.” Concise stage-specific instructions may restate
responsibilities but cannot redefine allowed or forbidden capability classes.

The existing independent-session boundaries, verdict extraction, remediation
lap, authoring report, containment gate, and workflow permissions remain
unchanged.

### 3. Deterministic policy-contract tests

Add `tests/test_generated_feature_policy.py` using pytest plus Python's standard
library only (`pathlib`, `re`, and ordinary text reads). Gitclaw's test workflow
installs only pytest; FR-829 adds no YAML parser, dependency manifest, or
workflow change. RED must be committed before GREEN.

The tests must prove:

1. `policy/generated-features.md` exists and contains explicit markers for
   optional contained tools, unauthenticated `GET`/`HEAD`, finite timeouts and
   bounds, named origins, forbidden credential/environment access, and
   forbidden external writes;
2. all four prompt YAML files parse and reference the exact shared policy path;
3. judge and enforce contain none of these exact banned strings:
  `YAMLGraph-only artifacts`, `graph.yaml plus prompts/`,
  `YAML-only implementation`, or `graph + prompts only`;
4. plan, judge, enforce, and review each state their stage responsibility from
   the table above;
5. containment accepts representative feature-local tool/test paths and still
   rejects root policy, prompt, workflow, dependency, and sibling-feature
   changes; and
6. the policy contains no promise that it mechanically sandboxes a malicious
   model or secures environment secrets.

These are contract-drift tests, not a semantic source-code security scanner.
Do not add regex that attempts to prove arbitrary generated Python or shell is
safe. Review remains the semantic gate, and README must continue to state its
limitations honestly.

### 4. README alignment

Link `policy/generated-features.md` from the trust-model section and summarize
the allowed read-only public-source class plus the forbidden external-write and
credential classes. Preserve the existing warning that model alignment and the
trusted-operator gate, not containment, are the barriers against deliberate
exfiltration.

Add one limitation: generated public-source tools run in cron with network
access and may break when upstream schemas or availability change; feature
failure must be observable through `.failed.json`.

### 5. FR-828 unblock witness

After gitclaw RED/GREEN tests pass and the correction is pushed, rerun only
FR-828's static preflight against the committed template SHA. The mechanical
unblock witness is the pushed SHA plus captured output from:

```bash
python -m pytest tests/test_generated_feature_policy.py tests/test_contain.py -q
```

The full `python -m pytest tests/ -q` must also pass. Record in FR-828:

- the gitclaw correction commit SHA;
- the shared policy path;
- the four prompt references;
- the policy-contract test command/result; and
- AC-05 checked if the preflight now passes.

Do not create the FR-828 cookbook repository, set its secrets, file its issue,
or implement its feature under FR-829. Those actions remain behind FR-828's
human/public-repo gate.

### 6. Human review gate

After the gitclaw diff and GREEN evidence exist, a human must review FR-829's
final judgement and the complete policy/prompt diff before FR-828 AC-05 may be
marked passed or any public issue is processed under the corrected policy.
Prompt-policy enforcement is itself enforcement infrastructure; generated
approval is advisory until that review is recorded.

The exact allowed YAMLGraph evidence surface is: FR-829 status and
implementation notes, this judgement artifact, FR-828's AC-05/preflight note,
`docs/fr-board.md`, and one diary reflection. No YAMLGraph package, capability,
requirement, example, graph, prompt, hook, CI, runtime, or changelog artifact is
authorized by FR-829.

## Acceptance Criteria

- [x] AC-01: gitclaw contains one local `policy/generated-features.md` governing
  issue-pipeline features, defining required graph/prompt/provenance
  artifacts and optional contained tools/tests/docs, while explicitly
  excluding pre-shipped fixtures from retroactive provenance migration
- [x] AC-02: Policy permits only unauthenticated, bounded HTTP GET/HEAD to
      public origins explicitly frozen in the feature FR/judgement, with finite
      timeouts, bounded data, structured parsing, untrusted-data handling, and
      explicit failure behavior
- [x] AC-03: Policy forbids secret/token/credential/cookie/arbitrary-environment
      access, authenticated retrieval, external writes, downloaded-code
      execution, remote shell interpolation, workflow/dependency/runtime/policy
      mutation, out-of-feature changes, and private/unbounded persistence
- [x] AC-04: `prompts/plan.yaml`, `judge.yaml`, `enforce.yaml`, and `review.yaml`
      all reference the exact shared policy and state their distinct binding
      responsibility
- [x] AC-05: Judge and enforce contain none of the exact banned strings
  `YAMLGraph-only artifacts`, `graph.yaml plus prompts/`,
  `YAML-only implementation`, or `graph + prompts only`
- [x] AC-06: `tests/test_generated_feature_policy.py` uses pytest plus standard
  library only and a RED commit proves it fails against the current
  contradictory prompts before implementation
- [x] AC-07: GREEN commit passes all policy-contract tests and the full gitclaw
      test suite without changing existing ledger, slug, timeout, containment,
      attribution, or workflow behavior
- [x] AC-08: Containment tests explicitly accept representative feature-local
      tool/test paths and reject root policy/prompt/workflow/dependency and
      sibling-feature paths
- [x] AC-09: README links the policy, describes the allowed read-only public
      retrieval class and forbidden classes, preserves security honesty, and
      records upstream source drift as an observable limitation
- [x] AC-10: No static gate rejects a feature merely because it declares tools;
      no arbitrary-code semantic scanner or new runtime sandbox is introduced
- [x] AC-11: No YAMLGraph core/capability/requirement/example, gitclaw workflow,
      dependency, secret, permission, ledger, containment implementation, or
      existing generated feature changes under FR-829
- [x] AC-12: FR-828 static preflight cites the pushed gitclaw SHA and output of
  `python -m pytest tests/test_generated_feature_policy.py
  tests/test_contain.py -q`; FR-828 records policy/prompt references and
  updated AC-05 without creating the cookbook repo or using its secrets
- [x] AC-13: FR-829 records RED/GREEN SHAs, test output, decisions, deviations,
  and exact evidence files; a human reviews the final judgement and complete
  gitclaw policy/prompt diff before FR-828 is unblocked or a public issue is
  processed under the new contract

## Implementation Status (2026-08-20)

**RED:** gitclaw `bba1842` — added standard-library policy-contract tests and
feature-local tool/test containment witnesses. Focused command failed 4 tests:
missing policy, no stage references, missing stage duties, and explicit
tool-excluding language. Containment witnesses passed.

**GREEN:** gitclaw `1854622` — added `policy/generated-features.md`, aligned
plan/judge/enforce/review, and linked the policy plus source-drift limitation
from README.

Validation:

```text
python -m pytest tests/test_generated_feature_policy.py tests/test_contain.py -q
22 passed in 0.03s

python -m pytest tests/ -q
47 passed in 0.09s
```

The static contract check found all four prompt references and zero occurrences
of the four banned strings. Diff review confirmed no workflow, dependency,
secret, permission, ledger, cron, containment implementation, vendored skill,
fixture, or generated-feature change. No deviations from frozen scope.

**Human review:** The operator reviewed and approved gitclaw commit `1854622`
after implementation and remote CI. FR-829 is complete. This approval clears
only FR-828's policy prerequisite; it does not authorize cookbook repo creation,
secret use, issue filing, or feature execution.

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-827 `gitclaw` | Governing implementation and threat model. Preserve trust gate, containment, authoring report, independent judge/review, remediation, cron, and explicit non-sandbox warning; correct only the generated-feature capability contract. |
| FR-828 Oulu cookbook | First blocked consumer and post-fix preflight witness. It does not authorize this policy change and must not be enforced inside FR-829. |
| FR-824 HVA bulletin | Reuse bounded public retrieval, structured parsing, source health, and no-private-data principles. It remains a hand-built satellite, not gitclaw policy. |
| Gitclaw README tool warning | Preserve its honest statement that generated tools execute with secrets in the environment and containment does not stop a malicious model; add a link and capability boundary, not a security claim. |
| Vendored graph-authoring doctrine | Already permits optional tools and evidence. Reference its artifact shape; do not modify the vendored snapshot under this fix. |

## Alternatives Considered

- **Change only `prompts/judge.yaml`:** rejected; enforce would still demand a
  YAML-only implementation, and plan/review would remain policy-blind.
- **Delete restrictive wording and say “tools allowed”:** rejected; it removes
  the contradiction but leaves no credential, write, endpoint, or data bound.
- **Forbid every feature with a `tools:` section:** rejected as directly
  contrary to gitclaw's purpose and the operator's explicit FR-827 correction.
- **Build a static analyzer for generated Python/shell:** rejected; semantic
  safety of arbitrary code cannot be established by a small regex gate, and a
  plausible pass would weaken the existing honest threat model.
- **Add a network sandbox or strip secrets from cron:** potentially valuable but
  separate architecture. FR-829 aligns policy around current runtime behavior;
  it does not claim isolation that does not exist.
- **Implement the Oulu feature directly:** rejected; FR-828 exists specifically
  to prove issue-driven generation in a fresh template instance.

## Related

- `feature-requests/FR-827-gitclaw-forkable-runner.md`
- `feature-requests/FR-828-gitclaw-oulu-civic-intelligence-cookbook.md`
- `feature-requests/FR-828-gitclaw-oulu-civic-intelligence-cookbook.judgement.md`
- `docs/diary/2026-08-20-cookbook-was-a-policy-probe.md`
- `../gitclaw/prompts/plan.yaml`
- `../gitclaw/prompts/judge.yaml`
- `../gitclaw/prompts/enforce.yaml`
- `../gitclaw/prompts/review.yaml`
- `../gitclaw/tools/contain.py`

## Judgement (2026-08-20)

**Verdict:** APPROVED WITH REVISIONS — R-1 through R-4 folded above; human
review remains a gate before implementation authority activates.

| # | Finding | Resolution (binding) |
|---|---|---|
| R-1 | Policy provenance requirements would retroactively invalidate the pre-shipped horoscope fixture | Scoped policy to issue-generated features; fixture migration explicitly excluded |
| R-2 | PyYAML is absent from gitclaw's test workflow and “equivalent” banned prose was untestable | Changed tests to pytest + standard library only and named four exact banned strings |
| R-3 | FR-828 unblock witness and YAMLGraph evidence boundary were vague | Defined the exact pytest command, pushed SHA evidence, and allowed YAMLGraph files |
| R-4 | Prompt-policy changes lacked adversarial human review | Added a human gate over final judgement and complete gitclaw policy/prompt diff |

**Purge list:** Fixture migration; YAMLGraph runtime/core/capability/example/hook/
CI changes; gitclaw workflow/dependency/secret/permission/ledger/cron/containment
implementation changes; runtime sandbox; arbitrary-code scanner; FR-828
cookbook execution.

**Scope frozen:** Yes — one local policy, four prompts, one policy-contract test,
narrow containment test additions, README alignment, and bounded YAMLGraph
evidence only.

### Questions for the human

Human review of the final judgement and gitclaw policy/prompt diff is required
before enforcement and before FR-828 is unblocked.
