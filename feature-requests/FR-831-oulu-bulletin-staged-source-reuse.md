# Feature Request: FR-831 Oulu Bulletin Staged Source Reuse

**Priority:** HIGH
**Type:** Process / Feature decomposition
**Status:** Enforced 2026-08-20 — Task 1 complete; 12/12 ACs satisfied and
human-reviewed; Tasks 2-7 remain separately judged
**Effort:** 0.5 day for Task 1; follow-up work separately judged
**Requested:** 2026-08-20
**Depends on:** FR-827, FR-828, FR-829, FR-830
**Blocks:** Any further FR-828 intake retry or manual repair
**Prior art:** FR-828 is the failed monolithic Oulu cookbook attempt; FR-829
defines the public read-only generated-feature policy; FR-830 repaired copied
ledger identity. The private `sheikkinen/control-plane` repository already
contains the relevant source research and probes. This FR reconstructs their
contracts and provenance before any new implementation issue is filed.
**First consumer / first event:** The operator planning the next Oulu bulletin
issue series, when a private `sheikkinen/control-plane` GitHub issue records a
reviewed source-asset inventory and a public-safe transfer packet without
starting a GitClaw intake run.

## Summary

Replace FR-828's single overloaded `Oulu Civic Intelligence Daily` issue with a
sequence of bounded tasks. The first task does not implement the bulletin. It
reconstructs the existing Oulu, Digitraffic Marine, Hilma, and municipal
decision research from the private `sheikkinen/control-plane` repository into
one durable private GitHub issue, classifies which probe behavior is reusable,
and produces a redacted transfer packet for later public GitClaw issues.

The original issue required one Copilot enforcement call to discover three
source contracts, implement three retrieval paths, define partial-failure
semantics, author a YAMLGraph feature, and prove the result. The corrected
template reached `judged_approved`, then the `enforce` node timed out after 900
seconds in run `32332927531`. That is an abstraction-span failure, not evidence
that the timeout should simply be raised.

## Value Statement

The next GitClaw worker receives closed, reviewed, public-safe source contracts
instead of rediscovering sources that have already been investigated and
probed. Each later issue performs one implementation judgement and can be
validated independently.

## Evidence and Root Cause

The fresh FR-828 replacement repository proved FR-829 and FR-830:

- repository: `sheikkinen/gitclaw-oulu-civic-intelligence`;
- initial corrected-template commit: `b7e0bcf`;
- tests run `32332856441`: green;
- Copilot authentication run `32332872063`: green;
- intake run `32332927531`: failed;
- ledger path reached `seen -> planned -> judged_approved` under repository
  identity `sheikkinen/gitclaw-oulu-civic-intelligence`;
- `enforce` then consumed its complete 900-second node allowance; and
- issue #1 remains open in an intentionally interrupted, non-terminal state.

The task mixed at least six levels: source discovery, private prior-art recall,
transport implementation, source-specific normalization, cross-source failure
policy, and bulletin graph authoring. Rewording the same issue or increasing its
timeout preserves that overload.

## Existing Assets to Reconstruct

Task 1 uses private repository `sheikkinen/control-plane` at frozen commit
`6cadb00cc77d6f110a5342b2cbd9dff830a4ac6d`. The issue must inspect and classify
at least these assets:

| Asset | Relevant established behavior | Initial disposition |
|---|---|---|
| `probes/digitraffic-marine-probe.sh` | Public no-auth port-call endpoint, `FIOUL`, gzip, bounded result count, earliest berth ETA, vessel-type hint, cargo caveat, common JSON envelope | Reuse contract; port implementation later |
| `probes/hilma-probe.sh` | Public eForms search, bounded `$top`, publication ordering, notice deduplication, stable detail URL construction, SPA detail limitation | Reuse contract; narrow Oulu matching later |
| `probes/config/municipalities.csv` | Oulu code `564`, Triplan platform, `https://asiakirjat.ouka.fi/ktwebscr` | Reuse configuration facts |
| `probes/municipality-kit.sh` | Hilma municipality search and Oulu KTweb public-notice route | Treat as exploratory prior art, not production code |
| `docs/municipality-probe-kit.md` | National/municipal source split, KTweb endpoint map, Oulu working-platform evidence, structured identifiers | Reuse reviewed research claims with verification dates |
| `docs/use-cases.md` | Municipal decision, procurement, and transport attention model | Background only; do not import product claims as source facts |

The inventory may add directly relevant assets discovered at the frozen commit,
but it must explain each addition. It must not broaden into unrelated private
device, address, company, profile, messaging, browser-history, defence, or
personal-data probes.

## Ideal Result

The private control-plane issue contains a reviewed source-asset inventory and
a redacted public transfer packet. A later public GitClaw issue can quote one
reviewed packet section as a closed input without private repository access,
memory of an earlier run, or source rediscovery.

## Task 1: Private Provenance Reconstruction Issue

Create exactly one issue in private repository `sheikkinen/control-plane`.
Creating this issue must not touch the public cookbook repository and therefore
must not trigger GitClaw.

**Title:** `Oulu bulletin source assets: provenance and public transfer packet`

**Required body:**

> Reconstruct the existing source research and probe contracts needed by the
> Oulu civic bulletin. This is an inventory and transfer task, not a new probe
> implementation.
>
> Freeze evidence at control-plane commit
> `6cadb00cc77d6f110a5342b2cbd9dff830a4ac6d`. Inspect every asset in this
> checklist:
>
> - [ ] `probes/digitraffic-marine-probe.sh`
> - [ ] `probes/hilma-probe.sh`
> - [ ] `probes/config/municipalities.csv`
> - [ ] `probes/municipality-kit.sh`
> - [ ] `docs/municipality-probe-kit.md`
> - [ ] `docs/use-cases.md`
>
> For each relevant asset, record: path, purpose, public origin, request method,
> authentication requirement, query bounds, timeout behavior, parser and
> encoding assumptions, normalized fields, stable identity, source URL rule,
> known failure modes, inference caveats, test or live evidence, and one of
> `reuse`, `adapt`, `reference-only`, or `reject`.
>
> End with a section named `Public transfer packet`. It must contain only the
> minimum public source contracts and behavioral invariants needed by later
> GitClaw issues. It may name public origins and generic probe behavior. It must
> not contain credentials, environment values, private outputs, personal or
> local-device data, unrelated probe inventory, raw response bodies, or claims
> unsupported by the inspected assets.
>
> Explicitly identify stale or unsafe behavior rather than copying it. In
> particular, replacement-character decoding, unbounded response retention,
> primary regex parsing of structured responses, commodity claims inferred
> from vessel type, and substring-only Oulu relevance are not reusable
> contracts.
>
> Do not write or modify probe code, bulletin code, YAMLGraph graphs, workflows,
> secrets, or the public Oulu repository. Do not open downstream implementation
> issues. Return the issue checklist and public transfer packet for human review.

The issue is an operator/research record. It is not labelled `gitclaw`, and no
automation is added to execute its prose. The operator reviews its source-path
citations and redaction before any part is copied to a public repository.

## Public Transfer Contract

Task 1 is complete only when the private issue contains a bounded `Public
transfer packet` with three independent source sections:

1. **Harbour:** exact public origin and query, `FIOUL`, response/result bounds,
   earliest future ETA rule, normalized fields, and explicit vessel/cargo
   inference boundary.
2. **Procurement:** exact public Hilma origin and query shape, bounded ordering,
   deduplication identity, normalized fields, stable detail-link rule, Oulu
   relevance evidence, and SPA/detail limitation.
3. **Municipal decisions:** Oulu's official KTweb base and selected endpoint
   family, response and item bounds, lossless charset rule, structured HTML
   parsing expectation, normalized fields, stable identity, and bounded-index
   removal caveat.

Every source section must distinguish:

- facts established by existing assets;
- behavior that must be reverified against the live public source;
- behavior condemned and not transferable; and
- missing decisions reserved for its source-specific implementation FR.

The packet is evidence input, not executable code. Later public issue bodies
must quote only reviewed packet sections and the public URLs they require. They
must not grant a public runner access to the private repository or rely on the
runner remembering a previous issue.

## Follow-up Issue and FR Sequence

Only Task 1 is in FR-831's enforcement scope. Its reviewed packet feeds this
ordered queue, with one separately planned and judged FR/issue active at a time:

| Order | Bounded judgement | Deliverable | Stop gate |
|---|---|---|---|
| 1 | Reconstruct prior art and public-safe contracts | Private provenance issue and reviewed transfer packet | Human confirms completeness and redaction |
| 2 | Encode Digitraffic Marine retrieval | Tested, contained harbour adapter/fixture contract | Live and fixture validation pass |
| 3 | Encode Hilma retrieval and Oulu relevance | Tested, contained procurement adapter/fixture contract | False-positive and source-link tests pass |
| 4 | Encode Oulu KTweb retrieval | Tested, lossless municipal adapter/fixture contract | Charset and bounded-index tests pass |
| 5 | Decide shared reuse/composition boundary | Separate GitClaw platform FR if cross-feature assets remain forbidden | No adapter duplication is approved |
| 6 | Compose verified source snapshots | Deterministic source-health and partial/all-failure assembly | No LLM or publication work included |
| 7 | Condense and publish the daily bulletin | One bounded synthesis graph, cron output, cookbook evidence | Dispatch and scheduled witnesses pass |

Tasks 2-4 must not independently rediscover their source. Each receives exactly
one reviewed transfer-packet section as a closed input. Task 5 is mandatory
because current `policy/generated-features.md` permits a generated feature to
read bounded files inside its own directory, while `tools/contain.py` confines
each issue to its new `features/<slug>/` path. The plan must not claim that
separate generated features are automatically a reusable library.

## Interrupted Attempt Disposition

The existing public issue #1 and run `32332927531` remain immutable failed
evidence. FR-831 does not:

- increase the 900-second node timeout;
- rerun or relabel issue #1;
- append a synthetic terminal ledger state;
- manually edit generated implementation files;
- delete or recreate the repository;
- open issues #2 onward; or
- modify GitClaw runtime, policy, prompts, workflows, or containment.

Recovery or abandonment semantics for interrupted GitClaw issues require a
separate platform FR if existing policy is insufficient.

Before any Task 2-7 issue is opened, FR-828's implementation/status record must
identify the fresh replacement repository, initial commit `b7e0bcf`, intake run
`32332927531`, the `judged_approved -> enforce timeout` outcome, and FR-831's
decision to stop and decompose the work.

## Acceptance Criteria

- [x] AC-01: FR-831 contains an explicit Ideal Result stating the reviewed
  private inventory and public-safe transfer packet as the end state
- [x] AC-02: One private `sheikkinen/control-plane` issue exists with the exact
      Task 1 title and all required body constraints
- [x] AC-03: The issue freezes repository commit `6cadb00c` and contains the
  self-contained checklist naming every required repository-relative path
- [x] AC-04: Every cited asset records public origin, request/auth contract,
      bounds, parser/encoding assumptions, normalized identity and fields,
      failure modes, caveats, evidence, and disposition
- [x] AC-05: The issue contains one `Public transfer packet` with
      separate Harbour, Procurement, and Municipal decisions sections
- [x] AC-06: Facts, live-reverification needs, condemned behavior, and deferred
      decisions are visibly distinguished for every source
- [x] AC-07: Human review confirms the transfer packet contains no credential,
      environment value, private output, personal/local-device data, unrelated
      probe inventory, or unbounded raw response
- [x] AC-08: No probe, graph, workflow, runtime, policy, prompt, secret, public
      cookbook repository, public issue, or generated feature is created or
      modified under Task 1
- [x] AC-09: FR-828 issue #1 and run `32332927531` remain preserved as failed,
      interrupted evidence without rerun, timeout increase, ledger repair, or
      manual implementation edit
- [x] AC-10: FR-828's implementation/status record identifies the second
  attempt repository, initial SHA, intake run, timeout outcome, and FR-831
  stop decision
- [x] AC-11: The downstream queue records Tasks 2-7 as separate judgements, one
      active at a time, with source reuse and composition stop gates
- [x] AC-12: No downstream task is filed until the Task 1 issue URL, human
  redaction review URL, and FR-828 status-update reference are recorded in
  this FR's implementation status

## Implementation Status (2026-08-20)

Human enforcement approval authorized Task 1 only. Private control-plane issue
`https://github.com/sheikkinen/control-plane/issues/1` was created with the
exact frozen title, no labels, and no workflow trigger. It records all six
required assets at control-plane commit
`6cadb00cc77d6f110a5342b2cbd9dff830a4ac6d`, classifies each as `reuse`, `adapt`,
or `reference-only`, and contains separate Harbour, Procurement, and Municipal
decisions transfer sections.

Bounded live evidence was recorded without raw response retention:

- Digitraffic Marine: five `FIOUL` items, two upcoming, no probe errors;
- Hilma: five deduplicated Oulu-search candidates with stable detail links and
  no probe errors; and
- Oulu KTweb public notices: HTTP 200, `text/html`, 26,479 bytes, with no
  detected charset declaration.

The issue explicitly condemns replacement decoding, response retention without
a byte cap, substring-only Oulu relevance, unconditional Latin-1, primary regex
HTML parsing, cargo inference, and bounded-index removal inference. Sensitive
terms occur only in prohibitions; no credential value, environment value,
private output, raw response body, or unrelated probe inventory was copied.

Control-plane and GitClaw worktrees remained clean, no control-plane workflow
ran, and public cookbook issue #1 remained open and unchanged. The operator
approved all five redaction/completeness checks in review comment
`https://github.com/sheikkinen/control-plane/issues/1#issuecomment-5351771445`.

For authorized control-plane readers, the issue now links all six source assets
through private GitHub permalinks pinned to commit `6cadb00c`. Later public
GitClaw issues receive only the reviewed `Public transfer packet`; they neither
receive nor depend on private-repository visibility. No Task 2-7 issue was
filed. The private issue was closed as `COMPLETED`; closing comment:
`https://github.com/sheikkinen/control-plane/issues/1#issuecomment-5351775218`.
Tasks 2-7 remain behind their separately judged FRs.

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-828 | Preserve both failed attempts and its product intent; replace its monolithic implementation issue, not its evidence |
| FR-829 | Preserve bounded read-only public retrieval policy; do not broaden tools or origins |
| FR-830 | Preserve repository-scoped ledger identity; the corrected retry proved it works |
| Control-plane probes | Treat as private prior art to inspect and selectively reconstruct, not code to rediscover or copy blindly |
| HVA bulletin source adapters | Reference their transport-boundary and event-safety lessons; do not migrate HVA product scope |

## Alternatives Rejected

- **Raise the enforcement timeout:** preserves the overloaded judgement and
  increases cost without making failures resumable.
- **Retry the same issue with a shorter prompt:** source knowledge remains
  implicit and the worker still changes abstraction levels repeatedly.
- **Copy all control-plane probes into the public repository:** leaks unrelated
  scope and imports exploratory assumptions without review.
- **Let each source issue rediscover its API:** duplicates validated research
  and makes source behavior drift between features.
- **Assume separate feature directories compose:** contradicted by current
  generated-feature policy and containment boundaries.
- **Manually finish the timed-out feature:** violates the cookbook witness and
  erases the platform failure being measured.

## Related

- `feature-requests/FR-828-gitclaw-oulu-civic-intelligence-cookbook.md`
- `feature-requests/FR-829-gitclaw-read-only-public-tool-policy.md`
- `feature-requests/FR-830-gitclaw-repository-scoped-ledger.md`
- `../gitclaw/policy/generated-features.md`
- `../gitclaw/tools/contain.py`
- `../gitclaw/tools/cron_run.py`
- `../control-plane/probes/digitraffic-marine-probe.sh`
- `../control-plane/probes/hilma-probe.sh`
- `../control-plane/probes/municipality-kit.sh`
- `../control-plane/docs/municipality-probe-kit.md`

## Scope Fence

FR-831 authorizes one private provenance issue and its human redaction review.
It does not authorize code implementation, public issue intake, secrets,
workflow changes, retries, timeout changes, or bulletin publication. Any such
work requires the corresponding separately judged follow-up FR.
