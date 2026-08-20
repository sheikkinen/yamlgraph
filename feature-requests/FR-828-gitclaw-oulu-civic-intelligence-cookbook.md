# Feature Request: FR-828 gitclaw Oulu Civic Intelligence Daily Cookbook

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged — APPROVED WITH REVISIONS folded; human review pending;
BLOCKED pending a separate judged gitclaw policy correction and human approval
for public repo creation
**Effort:** 1 day
**Requested:** 2026-08-20
**Prior art:** FR-827 is the direct gitclaw platform dependency; FR-824 is the
bounded civic-source/source-health precedent; FR-819 and FR-826 are the public
satellite and scheduled-publication precedents, all reused and distinguished in
the table below. FR-425 is a false noun match on “intelligence” (hook daemon,
not civic data or a cookbook). This FR's judgement is the verdict artifact for
this same proposal, not separate prior art.
**First consumer / first event:** A prospective gitclaw adopter, opening a
public cookbook repository after the first scheduled run and following the
same template -> keys -> issue cycle to obtain a source-linked daily civic
brief without editing code. The operator is the first witness, on the first
clean template instantiation that reaches a committed cron output using only
the documented steps.

## Summary

Create a fresh public repository from the `sheikkinen/gitclaw` template and
use one owner-authored issue to generate **Oulu Civic Intelligence Daily**: a
daily Markdown brief combining Oulu harbour traffic, public procurement, and
municipal decision signals from unauthenticated Finnish public sources.

The resulting repository is both a useful live publication and the canonical
gitclaw cookbook. Its committed evidence must show the complete adopter path:
template instantiation, two repository secrets, verbatim issue, autonomous
plan/judge/enforce/review, generated feature provenance, scheduled execution,
and published output. No implementation file may be edited manually after the
template is instantiated.

## Value Statement

A gitclaw adopter gets one copyable, independently witnessed example proving
that a natural-language issue can become a useful multi-source, tool-using,
scheduled automation using only a GitHub repository and two secrets.

## Problem

FR-827 proved gitclaw itself and generated small daily text features, but the
current examples do not prove the strongest intended use case:

1. a clean adopter starts from the public template rather than the maintainer's
   working repository;
2. the generated feature uses real tools and live external data;
3. the output distinguishes source facts, inference, and unavailable data;
4. the first scheduled run succeeds without a maintainer editing generated
   code; and
5. another adopter can reproduce the entire cycle from one bounded document.

The recent satellite repositories (`yamlgraph-daily-digest`,
`hva-weekly-bulletin`, and `deviant-daily`) prove unattended GitHub-native
publication, but each was hand-built. A cookbook that bypasses gitclaw's issue
pipeline would repeat that pattern rather than test the factory.

`../control-plane` contains 55+ public-data source investigations alongside
private-device probes. Copying that toolkit would be unsafe and would hide the
gitclaw test beneath a large migration. This FR takes only three public,
no-auth source contracts and leaves all local-device, profile, messaging,
browser-history, and personal-data probes outside the repository.

## Ideal Result

A reader opens a public `gitclaw-oulu-civic-intelligence` repository and sees a
dated Oulu brief committed by GitHub Actions. The README shows exactly how the
empty template became that publication: create from template, add
`COPILOT_CLI_TOKEN` and `ANTHROPIC_API_KEY`, file the reproduced issue, observe
the generated feature and its plan/judgement/review/authoring evidence, then
observe cron commit the first source-linked output. The reader can repeat the
process in a new repository without consulting yamlgraph internals, copying
control-plane, or editing generated code.

## Proposed Solution

### 1. Gitclaw public-source policy preflight

Before creating the cookbook repository or filing its issue, verify that the
current public gitclaw template permits generated features to perform bounded,
read-only, unauthenticated HTTP retrieval without new secrets. Inspect the
actual judge/review/authoring contracts used by the template; README prose is
not sufficient evidence.

**Preflight result, 2026-08-20: FAILED/BLOCKED.** The current README says
generated feature graphs may declare and use tools, and the vendored graph
authoring doctrine permits optional tools. However,
`sheikkinen/gitclaw/prompts/judge.yaml` requires generated features to be
“YAMLGraph-only artifacts: graph.yaml plus prompts/” and says they must not
require “external side effects beyond the commit-back workflow layer.” A
read-only public HTTP fetch is not explicitly distinguished from a forbidden
external side effect. The cookbook must not rely on a favorable model
interpretation of contradictory policy.

Enforcement stops before public repo creation. A separate judged gitclaw policy
FR must define bounded read-only public retrieval as permitted, align the
judge/review/authoring contracts, and retain the prohibition on new secrets and
external writes. FR-828 may resume only after that correction is committed and
its template SHA is recorded. FR-828 must not patch gitclaw, bypass its judge,
or hand-repair a rejected generated feature.

### 2. Fresh public template instance

Create `sheikkinen/gitclaw-oulu-civic-intelligence` through GitHub's **Use this
template** path from `sheikkinen/gitclaw`. It must be a new repository with one
template-derived initial history, not a fork network member, nested checkout,
submodule, or copy inside the yamlgraph working tree.

Before filing the issue:

1. enable GitHub Actions if the platform requires it;
2. set repository Actions secrets `COPILOT_CLI_TOKEN` and
   `ANTHROPIC_API_KEY` using the cookbook commands;
3. record only secret names and successful probe results, never values; and
4. run the existing Copilot spike workflow as the authentication witness.

The built-in `GITHUB_TOKEN` supplies repository `contents: write` and
`issues: write`. No PAT, deployment key, cloud account, database, or
source-specific API key is permitted.

### 3. Verbatim issue contract

File this owner-authored issue without manually adding files or labels:

**Title:** `Oulu Civic Intelligence Daily`

**Body:**

> Each day, publish one concise Markdown civic-intelligence brief for Oulu,
> Finland, using only unauthenticated public sources.
>
> Include exactly three sections:
>
> 1. **Harbour:** the next upcoming vessel call at Oulu (`FIOUL`) from the
>    Digitraffic Marine Port Call API. Report vessel name, ETA, previous port,
>    next port, berth when available, and vessel-type hint. Never state an
>    inferred cargo commodity as fact.
> 2. **Procurement:** up to five recent public procurement notices relevant to
>    Oulu from Hilma's public notice data. Report title, contracting authority,
>    publication date, deadline when available, and source URL.
> 3. **Municipal decisions:** up to five recent Oulu municipal decisions,
>    agendas, or public notices from an official City of Oulu public source.
>    Report title, governing body or notice type, date, and source URL.
>
> Every item must carry a clickable source URL. Begin with the UTC generation
> date. End with a **Source health** table showing `ok`, `unavailable`, or
> `invalid` for each source. If one source fails or returns invalid data, keep
> the other verified sections and state that source's failure explicitly;
> never invent replacement facts. If all three sources fail, fail the feature
> rather than publish a plausible empty brief. Keep source retrieval and
> deterministic field selection in tools; use the LLM only to condense verified
> records and label inference. Output only the final Markdown brief.
>
> Retrieval constraints are part of this issue contract: use finite connect
> and read timeouts, cap every source to the smallest result window needed for
> the output, and parse structured JSON, XML, RSS, or HTML with an appropriate
> parser rather than primary regex extraction. Do not commit raw unbounded
> source responses, credentials, environment values, personal profiles, or
> local-device data. Tests must prove that one unavailable source still yields
> a brief from the other verified sources with that source marked
> `unavailable`, while all three sources failing yields no Markdown brief and a
> recorded feature failure.

The issue intentionally names public contracts and output invariants while
leaving implementation details to gitclaw. It is a cookbook input, not a hidden
maintainer prompt.

### 4. Bounded source scope

The generated feature may implement exactly these source families:

| Source | Required public contract | Required behavior |
|---|---|---|
| Digitraffic Marine | `https://meri.digitraffic.fi/api/port-call/v1/port-calls?locode=FIOUL` | Select the earliest future ETA; preserve vessel-type inference as a labelled hint |
| Hilma | Official public Hilma notice data/API | Filter to notices whose structured authority/location or returned text establishes Oulu relevance; do not imply completeness beyond the query window |
| City of Oulu | One official public decision, agenda, or notice feed selected and cited by the generated feature | Bound the fetch, preserve source dates/URLs, and report source unavailability honestly |

The generated feature must use structured JSON/XML/RSS/HTML parsing appropriate
to the selected source. Ad hoc regex may not be the primary parser for
structured responses. Retrieval must use finite connect/read timeouts and
bounded result counts. Raw unbounded response bodies, credentials, and personal
profiles must never be committed.

No cross-day deduplication, notification delivery, semantic thread linking,
company enrichment, prediction, scoring, or full control-plane probe migration
belongs in this FR. Daily snapshots are sufficient for the cookbook.

### 5. Generated feature contract

The issue pipeline must generate one contained feature under the slug selected
by gitclaw, expected to be:

```text
features/oulu-civic-intelligence-daily/
├── FR.md
├── judgement.md
├── review.md
├── authoring-report.md
├── graph.yaml
├── prompts/
└── tools/                    # optional shape; source retrieval belongs here
```

The feature graph must lint and smoke through gitclaw's authoring route. Its
final state must expose exactly one non-empty Markdown output candidate so
`tools.cron_run.extract_output()` cannot select ambiguously. The feature may
declare and execute tools; tool use is the point of this acceptance case.

The pipeline must reach the ledger terminal state `closed` and close the issue
with a post-rebase commit SHA. A judge or reviewer rejection is a legitimate
pipeline outcome but does not satisfy this FR's positive acceptance witness.

### 6. Cookbook as evidence, not reconstruction

After the issue pipeline and first cron run complete, add a README section
`Reproduce this cookbook` containing:

1. the source template URL and template commit SHA;
2. the GitHub repository creation path;
3. exact secret-setting commands using stdin without printing values;
4. the existing spike workflow dispatch and expected success marker;
5. the verbatim issue title/body above;
6. links to the issue, intake Actions run, generated feature commit, closed
   ledger record, cron Actions run, and first output;
7. elapsed wall-clock times for intake and cron;
8. the explicit statement: `No implementation files were edited manually
   after template instantiation`; and
9. a troubleshooting table for missing Copilot access, missing Anthropic key,
   interrupted ledger state, source timeout, and cron `.failed.json` output.

README evidence updates may be committed after the run because they document
the witness. They must not alter the generated feature, gitclaw runtime,
workflows, prompts, or tools. If the generated implementation requires a manual
repair, the attempt is recorded as failed and a fresh template instance or a
new issue-driven repair must produce the final witness.

### 7. Acceptance validation

Validation has four layers:

1. **Instantiation:** repository ancestry/layout matches the public template;
   only the two documented secrets exist; the Copilot spike is green.
2. **Issue pipeline:** the owner-authored issue runs plan -> judge -> enforce ->
   review, commits governed provenance, reaches `closed`, and cites the pushed
   feature SHA.
3. **Feature behavior:** a dispatch cron run and one actual scheduled cron run
   both commit a Markdown brief; all emitted civic items have source links and
   source-health statuses.
4. **Fault witness:** in tests or a temporary fixture, one source failure still
   renders the other verified sections with `unavailable`; three failures cause
   a recorded feature failure and no plausible brief.

## Acceptance Criteria

- [x] AC-01: The current gitclaw policy preflight was performed against actual
      template contracts; its README/judge-prompt contradiction is recorded and
      enforcement is blocked pending a separate judged policy correction
- [ ] AC-02: Public `sheikkinen/gitclaw-oulu-civic-intelligence` exists as a
      fresh `sheikkinen/gitclaw` template instance outside all existing working
      trees, with source template URL and commit SHA recorded
- [ ] AC-03: The repo has exactly the two adopter-supplied Actions secrets
      `COPILOT_CLI_TOKEN` and `ANTHROPIC_API_KEY`; secret values appear in no
      git object, issue, Actions log, output, provenance artifact, or uploaded
      artifact
- [ ] AC-04: The Copilot spike workflow completes green before issue intake and
      its run URL is recorded in the cookbook
- [ ] AC-05: Corrected gitclaw policy explicitly permits bounded, read-only,
      unauthenticated public HTTP retrieval without new secrets; otherwise
      FR-828 remains stopped without manual repair
- [ ] AC-06: The owner files the exact revised issue contract without adding
      implementation files or an auto-triggering label; the issue carries the
      timeout, result-bound, structured-parser, raw-body, credential/profile,
      and one-source/three-source failure constraints
- [ ] AC-07: Intake completes through plan, independent judge, enforce, review,
      push, and close; `state/issues.jsonl` contains the terminal path and the
      issue comment cites the post-rebase generated feature commit
- [ ] AC-08: The generated feature contains `FR.md`, `judgement.md`,
      `review.md`, `authoring-report.md`, lint-clean `graph.yaml`, prompts, and
      any required contained tools
- [ ] AC-09: `authoring-report.md` contains substantive lint and smoke evidence,
      `scripts/author-report.sh` accepts the feature, retrieval uses finite
      timeouts/bounds/structured parsing, and no raw unbounded response body is
      committed
- [ ] AC-10: A manual cron dispatch commits one non-empty attributed Markdown
      output with UTC date, Harbour, Procurement, Municipal decisions, and
      Source health sections; final state has exactly one output candidate
- [ ] AC-11: Every emitted civic item has a clickable official source URL;
      vessel/cargo inference is labelled and unavailable data is not presented
      as fact
- [ ] AC-12: Tests prove one-source failure yields an honest partial brief while
      three-source failure yields `.failed.json`, non-zero cron status, and no
      plausible Markdown brief
- [ ] AC-13: A second same-day cron run remains green and creates no path or
      commit conflict, regardless of live source changes
- [ ] AC-14: At least one actual `schedule` event completes green and commits a
      dated output without human runner access; dispatch does not substitute
- [ ] AC-15: The cookbook README records source/template SHA, stdin-safe setup
      commands, verbatim issue, issue/run/commit/ledger/output links, elapsed
      times, troubleshooting, and the no-manual-implementation-edits statement
- [ ] AC-16: Full git-history, tracked-file, Actions-log, issue/comment, output,
      and artifact scans find no token, key, private control-plane artifact,
      local-device data, personal profile, or unbounded raw source body
- [ ] AC-17: No YAMLGraph core/capability/requirement/example or gitclaw
      runtime/template/workflow/prompt/policy change is made under FR-828; any
      such need stops for a separate judged FR
- [ ] AC-18: Implementation status, witness links, decisions, deviations, and
      failed attempts are recorded in FR-828; required changelog and diary
      evidence close the YAMLGraph-side work

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-819 `yamlgraph-daily-digest` | Reuse the public satellite, PyPI consumption, cron/dispatch, commit-back, and live scheduled witness pattern. Distinguish: FR-828 must be generated through a clean gitclaw issue cycle and serves as a reproducible cookbook. |
| FR-824 `hva-weekly-bulletin` | Reuse public/private source separation, provenance, bounded retrieval, and source-health honesty. Distinguish: FR-828 is a daily snapshot of exactly three Oulu source families, not a typed longitudinal event ledger or cross-HVA thread engine. |
| FR-826 `deviant-daily` | Reuse the full public repo + secrets + scheduled publisher witness. Distinguish: FR-828 publishes Markdown to git only and requires no third-party publication secret. |
| FR-827 `gitclaw` | Direct platform dependency. FR-828 validates the external adopter path and tool-using feature generation without modifying gitclaw runtime. |
| `../control-plane` public probes | Research evidence for Digitraffic, Hilma, and municipal source feasibility only. No code or data is copied wholesale; all private-device and personal-data surfaces are excluded. |
| FR-827 canonical gitclaw run and `gitclaw-fork-witness` | FR-827 witnessed issue intake and cron on the canonical gitclaw repo, and separately witnessed that a template-created repo contained the full layout/workflows. It did not witness the full issue -> generated feature -> closed ledger -> dispatch cron -> scheduled cron chain under the template instance's own Actions history. FR-828 adds exactly that fresh-repo chain; prior gitclaw run identities cannot substitute. |

## Alternatives Considered

- **Add the feature directly to `sheikkinen/gitclaw`:** rejected because it
  tests maintainer editing, not template adoption or repository creation.
- **Copy the full control-plane civic stack:** rejected because it obscures the
  issue-to-feature claim, imports unrelated private-data risk, and exceeds the
  daily snapshot need.
- **Use only Digitraffic:** cheaper but too weak; it proves one API call, not a
  multi-source tool-using feature with honest partial failure.
- **Require HVA/TED/thread reconstruction:** deferred; those need persistent
  normalized state and belong to the existing weekly-bulletin class.
- **Publish a written tutorial without a live fork:** rejected; generated prose
  could claim steps that were never witnessed. The cookbook must carry run and
  artifact identities.
- **Permit manual repair after generation:** rejected because it would convert
  the acceptance test into another hand-built satellite. Failed generation is
  evidence about gitclaw and must remain visible.

## Related

- `feature-requests/FR-819-github-native-digest-poc-repo.md`
- `feature-requests/FR-824-hva-weekly-bulletin-new-repo.md`
- `feature-requests/FR-826-deviantart-daily-repo.md`
- `feature-requests/FR-827-gitclaw-forkable-runner.md`
- `docs/diary/2026-08-20-weeks-repos-are-the-acceptance-suite.md`
- `../control-plane/docs/acceptance-test-questions.md`
- `../control-plane/docs/use-cases.md`
- `../control-plane/probes/digitraffic-marine-probe.sh`

## Judgement (2026-08-20)

**Verdict:** APPROVED WITH REVISIONS — R-1 through R-3 folded above;
enforcement remains blocked by the failed public-source policy preflight and
requires human approval before public repository creation.

| # | Finding | Resolution (binding) |
|---|---|---|
| R-1 | Current gitclaw policy does not clearly permit read-only public HTTP tools | Added an actual contract preflight, recorded its failed result, and stopped for a separate judged gitclaw policy correction |
| R-2 | Safety constraints lived outside the issue visible to gitclaw | Moved finite timeouts, bounded results, structured parsing, raw-body/privacy boundaries, and partial/total failure semantics into the verbatim issue |
| R-3 | Prior fork witness distinction overstated | Corrected the disposition: FR-827 proved canonical-repo intake/cron and template layout separately; FR-828 requires the whole chain in the fresh cookbook repo |

**Purge list:** YAMLGraph core/runtime/capability/example changes; gitclaw policy
changes inside FR-828; manual generated-feature repair; control-plane migration;
private-device/profile sources; source-specific secrets; cross-day state,
notification, enrichment, scoring, and product surfaces.

**Scope frozen:** Yes, subject to the policy dependency and human public-repo
approval gates.

### Questions for the human

Approve or reject public cookbook repository creation only after the separate
gitclaw policy correction is judged and merged. No approval is requested in
this planning turn.
