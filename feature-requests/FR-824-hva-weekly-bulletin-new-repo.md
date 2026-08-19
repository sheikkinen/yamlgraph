# Feature Request: HVA Weekly Governance and Procurement Bulletin — New Repository

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 4–6 days
**Requested:** 2026-08-19
**First consumer / first event:** The operator, Monday morning, opening
`bulletins/<ISO-week>.md` in the public `hva-weekly-bulletin` repository to see
which Finnish wellbeing-services county governance and procurement threads
appeared, advanced, or became disputed during the prior week — without running
`control-plane` locally or reading source systems one by one.

**Prior art:** FR-819 proved an unattended YAMLGraph publication in a separate
public GitHub repository with committed state; FR-821 proved weekly scheduled
publication, substantive no-op behavior, and automation delivery; the
`control-plane` HVA orchestrator and probes prove source access but only produce
single-run snapshots. `../control-plane/docs/github-runner-weekly-recap-research.md`
provides the source-cadence and runner analysis behind this FR.

## Summary

Create a new public repository, working name `hva-weekly-bulletin`, that
collects public HVA governance, Hilma/TED procurement, and Market Court (MAO)
procurement-dispute data on GitHub-hosted runners, persists a compact normalized
event ledger in git, and publishes one source-linked weekly bulletin organized
by lifecycle transitions and cross-source threads.

Daily collection and weekly publication are separate workflows. The collector
preserves lead time and amendments; the bulletin synthesizes exactly the prior
seven days of substantive events. The new repository contains only public OSINT
code and data. It imports no local-device probes or personal data from
`control-plane`.

## Value Statement

The operator gets one auditable Monday account of what changed across all 22 HVA
governance surfaces, procurement publication, and procurement disputes, while
the committed event ledger turns ephemeral GitHub runners into a durable
monitor rather than a weekly full-snapshot scraper.

## Problem

`control-plane` already has broad source access:

- HVA governance through KTweb, Dynasty, and CaseM;
- procurement notices through Hilma and TED;
- procurement disputes through the MAO path in the bulletin pipeline.

But the current system is a local research toolkit, not a publication product:

1. `output/` is gitignored and current artifacts are point-in-time snapshots.
2. Most probes deduplicate only within one invocation; the next runner cannot
   tell new, updated, and unchanged items apart.
3. A weekly-only scrape sacrifices lead time and can miss amendments.
4. The existing bulletin groups documents more readily than it proves lifecycle
   transitions across sources.
5. `control-plane` deliberately mixes public OSINT probes with macOS device/PII
   probes. Adding an unattended public workflow there would weaken that privacy
   boundary.
6. A GitHub-hosted runner is ephemeral. Without committed normalized state,
   every run starts with amnesia and can render the whole corpus as "new."

The desired output is not a source inventory. Per
`control-plane/docs/information-landscape.md`, the product is a thread: a
citable chain such as agenda -> decision -> Hilma notice -> award -> MAO appeal.

## Ideal Result

Every Monday, the public `hva-weekly-bulletin` repository gains at most one
`bulletins/<YYYY-Www>.md` containing the prior week's new early signals, thread
transitions, awards, disputes, cross-HVA patterns, upcoming deadlines, and
source-health census. Every assertion links to a source event in the committed
ledger. Quiet weeks create no bulletin and no commit. Daily collection commits
only compact state/events when something changed. A fresh baseline does not
mislabel the existing corpus as a week of news. No private device source,
personal profile, raw browser corpus, or unbounded response body enters the
repository.

## Proposed Solution

### 1. Repository boundary

Create `https://github.com/sheikkinen/hva-weekly-bulletin` as a separate public
repository outside the YAMLGraph and `control-plane` working trees.

```text
hva-weekly-bulletin/
├── .github/workflows/
│   ├── collect.yml              # daily + workflow_dispatch
│   └── bulletin.yml             # Monday + workflow_dispatch
├── graph.yaml                   # weekly thread synthesis
├── prompts/                     # one bounded synthesis judgement
├── src/hva_bulletin/
│   ├── models.py                # Pydantic source/event/thread contracts
│   ├── collect.py               # source runner + normalization
│   ├── delta.py                 # stable ID/hash comparison
│   ├── threads.py               # deterministic evidence-first linking
│   └── render.py                # validated Markdown rendering
├── probes/                      # public-only extracted/adapted probes
├── config/hvas.*                # canonical 22-HVA/platform mapping
├── state/source-items.jsonl     # compact latest-seen state
├── events/<YYYY-Www>.jsonl      # append-only weekly event ledger
├── bulletins/<YYYY-Www>.md      # published human artifact
├── tests/                       # fixtures; no live network in unit tests
├── pyproject.toml
└── README.md
```

The new repo may extract and adapt only the public-source probe subset from
`control-plane`, retaining source/provenance notes. It must not be a nested git
repository, submodule, vendored directory, generated subtree, or runtime
checkout inside YAMLGraph. It must not copy or invoke root-level device probes.

No YAMLGraph package code, capability registry, or requirement ID is changed by
this FR. YAMLGraph is consumed from PyPI like an adopter would consume it.

### 2. Source scope

The first release has exactly three source families:

| Family | Scope | Collection |
|---|---|---|
| HVA governance | Canonical 22-HVA configuration across KTweb, Dynasty, and CaseM index/detail paths | Daily index; targeted detail for new or updated items |
| Procurement | Hilma notices plus TED publication cross-reference/detail fallback | Daily; deduplicate Hilma/TED by explicit publication ID before weaker matching |
| Disputes | MAO procurement cases concerning an HVA or a procurement already in the ledger | Daily index; normalized filing/status reference |

Public notices, Hankeikkuna, Lausuntopalvelu, Eduskunta, Finlex, statistics,
company enrichment, municipal invoices, and other sector probes are deferred.
They require separate evidence that the first consumer needs them.

### 3. Normalized contracts

All source output crosses a Pydantic boundary before persistence. The minimum
item contract is:

```python
class SourceItem(BaseModel):
    source: Literal["ktweb", "dynasty", "casem", "hilma", "ted", "mao"]
    source_id: str
    title: str
      source_urls: dict[str, HttpUrl]
    organization: str
    effective_date: date | None
    fetched_at: datetime
    docket: str | None = None
    publication_id: str | None = None
    deadline: date | None = None
    value_eur: Decimal | None = None
    body_excerpt: str | None = None
```

Normalization computes a canonical content hash from substantive fields only.
Fetch timestamps, ordering, whitespace, and other observation noise do not make
an item "updated."

Each delta becomes a typed event:

```python
class SourceEvent(BaseModel):
    event_id: str
    event_type: Literal["new", "updated", "transition"]
    source: str
    source_id: str
    observed_at: datetime
    effective_date: date | None
    content_hash: str
    changed_fields: list[str]
```

`event_id` is deterministic from source, source ID, event type, and substantive
content hash — not `observed_at` — so a retry cannot create a second event.

**No `removed` event in this FR.** Absence from a bounded/top-N index is not
proof of withdrawal. A future source-specific complete-list contract may add
removal semantics under a separate FR.

### 4. Baseline, delta, and state behavior

The first successful collection is an explicit baseline:

- validate and persist current `SourceItem` state;
- emit no `new` events and no bulletin candidate;
- record source census and `baseline_at` metadata;
- require a second run with a changed fixture/live item to prove delta behavior.

Subsequent collection compares stable IDs and substantive hashes:

- unseen stable ID -> `new`;
- same ID, changed substantive hash -> `updated` with exact changed fields;
- same ID, same hash -> observation timestamp may advance in compact state, but
  no event and no commit solely for that timestamp;
- duplicate Hilma/TED publication -> one procurement item with both source URLs,
  not two events;
- collection retry -> deterministic no-op.

State is committed because Actions cache/artifacts are not durable truth.
Unbounded raw HTML, PDFs, and API responses remain short-retention workflow
artifacts and are never committed by default.

### 5. Thread linking

Link events in this evidence order:

1. exact docket number;
2. explicit prior-handling/cross-reference;
3. Hilma/TED publication ID;
4. normalized named entity plus organization;
5. topical similarity as a candidate only.

Deterministic evidence creates confirmed edges. An LLM may rank or summarize
candidate links, but topic similarity alone cannot merge threads. Every rendered
thread carries `link_basis` and its member event IDs.

The weekly graph receives only the seven-day typed event window plus confirmed
thread edges. Its prompt has one judgement: select and summarize the most
material changes into the frozen output schema. It does not fetch, deduplicate,
link, serialize, or self-correct source data.

Creating or adapting `graph.yaml` or `prompts/*.yaml` is graph authoring and must
use YAMLGraph's governed `scripts/author.sh` route. The authoring report, lint,
and smoke evidence are recorded in this FR's implementation notes; an agent
launched by that adapter follows the re-entry guard and authors directly.

### 6. Weekly bulletin contract

The deterministic renderer writes:

```markdown
# HVA Weekly Bulletin <YYYY-Www>

## New early signals
## Threads that advanced
## Awards and disputes
## Cross-HVA patterns
## Deadlines next week
## Expected next transitions
## Source health and coverage gaps
## Event ledger
```

Every substantive entry includes event IDs, direct source links, organization,
effective date, lifecycle stage/transition when known, link basis, and the next
expected observable event. The `Event ledger` appendix lists every event in the
window even when the narrative is capped.

A seven-day window with zero substantive events exits 0, writes no bulletin,
and makes no commit. A recap/bulletin commit from the prior week is never itself
an input event.

### 7. GitHub workflows

`collect.yml`:

- `schedule` daily at 05:30 UTC plus `workflow_dispatch`;
- Ubuntu runner, Python 3.12, Playwright browser installed only for CaseM;
- hard allowlist of the six public source adapters — no filesystem glob over
  inherited probes;
- `permissions: contents: write` only;
- one shared `concurrency` group, `hva-bulletin-state`, with
  `cancel-in-progress: false`;
- after collection, stage only `state/` and `events/`; no diff -> explicit green
  no-op; otherwise pull/rebase and push one bot commit.

`bulletin.yml`:

- Monday 06:00 UTC plus `workflow_dispatch`;
- same shared `hva-bulletin-state` concurrency group so collector and publisher
  cannot race;
- reads the previous seven complete UTC days from committed event files;
- provides `ANTHROPIC_API_KEY` only to the YAMLGraph synthesis step;
- stages only `bulletins/`; no substantive events -> no branch/commit;
- pull/rebase before push, then one `bulletin <ISO-week>` bot commit.

The new repo starts with the FR-819 unprotected-publication model: scoped default
`GITHUB_TOKEN`, no admin PAT, no protection-bypassing credential, and direct bot
commits. If branch protection is later enabled, migration to FR-821's
fine-grained-PAT automation-PR route requires human review and separate scope.

### 8. Source health

Every collection produces a typed census with configured/attempted/succeeded
counts, item count, duration, and errors per source/HVA. No arbitrary aggregate
success threshold is introduced.

- schema-invalid output or a total family execution failure makes collection
  fail visibly;
- individual HVA endpoint failures remain explicit degraded observations and do
  not erase successful families;
- the weekly bulletin cannot claim complete/healthy coverage when any configured
  endpoint failed in its window;
- anomalous empty results are reported as empty, never silently replaced by a
  previous/full dataset.

## Acceptance Criteria

- [ ] AC-01: Public `sheikkinen/hva-weekly-bulletin` exists outside both
      YAMLGraph and `control-plane`; neither source repo contains it as nested
      repo, submodule, vendor tree, generated artifact, or runtime checkout.
- [ ] AC-02: The new repo contains no device probe, local `~/Library` path,
      Safari/Messages/WhatsApp/Biome/Apple Intelligence extraction, personal
      profile output, or personal-data secret.
- [ ] AC-03: Fixture-backed unit tests validate all six normalized source values
      (`ktweb`, `dynasty`, `casem`, `hilma`, `ted`, `mao`) through Pydantic and
      reject missing stable IDs, titles, organizations, or source URL maps.
- [ ] AC-04: First collection seeds state and emits zero events; second changed
      fixture emits exactly one deterministic event; third identical run emits
      zero events and changes no tracked file.
- [ ] AC-05: Hash tests prove fetch timestamp, ordering, and whitespace noise do
      not emit `updated`; a substantive deadline/status/value/title change does
      emit `updated` with exact `changed_fields`.
- [ ] AC-06: Hilma/TED fixtures sharing a publication ID normalize to one
      procurement item retaining both source URLs; no fuzzy match is needed.
- [ ] AC-07: The canonical configuration enumerates exactly 22 HVAs and maps
      every one to a supported governance adapter; workflow census attempts all
      configured entries and exposes every failure.
- [ ] AC-08: No source adapter or delta code emits `removed`; a fixture absent
      from a bounded follow-up index remains state, not a fabricated withdrawal.
- [ ] AC-09: Confirmed thread tests cover exact docket, explicit prior handling,
      and Hilma/TED publication-ID edges; topical similarity alone remains a
      candidate and cannot merge threads.
- [ ] AC-10: A fixture seven-day event window renders all frozen bulletin
      sections, source links, event IDs, link bases, and complete event-ledger
      appendix; no section claims healthy coverage when census errors exist.
- [ ] AC-11: An empty seven-day event window exits 0, writes no bulletin, and the
      workflow logs a distinct no-op without committing.
- [ ] AC-12: `collect.yml` has daily cron, dispatch, contents-write permission,
      hard adapter allowlist, shared non-cancelling concurrency, scoped staging,
      safe pull/rebase, and explicit no-op behavior.
- [ ] AC-13: `bulletin.yml` has Monday 06:00 UTC cron, dispatch, the same
      concurrency group, exact seven-day UTC window, scoped secret exposure,
      scoped staging, safe pull/rebase, and no-op behavior.
- [ ] AC-14: A dispatched baseline collector run completes green; a later
      dispatched run proves durable cross-run delta/no-op behavior, with run URLs
      and commit SHAs recorded in Implementation Notes.
- [ ] AC-15: A dispatched bulletin run publishes one non-empty real-source
      bulletin; a repeated unchanged dispatch produces no duplicate bulletin or
      event, with evidence recorded.
- [ ] AC-16: The first real scheduled collector and Monday bulletin runs are
      observed and recorded; until both occur, status explicitly carries "cron
      observation pending" — dispatch evidence is not cron evidence.
- [ ] AC-17: `graph.yaml` and prompts are authored/adapted through
      `scripts/author.sh`; retained report records lint and smoke results. The
      graph consumes typed events and does not perform source fetching, delta,
      deterministic linking, or Markdown serialization.
- [ ] AC-18: README documents consumer, source coverage, cadence, state/event
      contracts, privacy boundary, source-health semantics, local fixture test,
      manual dispatch, and the direct-commit security model.
- [ ] AC-19: YAMLGraph repository changes for enforcement are limited to this
      FR's status/implementation notes and required diary evidence; no
      package, CAP/REQ, graph, prompt, example, or `control-plane` source change
      is smuggled into this FR.

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-819 GitHub-native daily digest | Reuse: separate public repo, PyPI YAMLGraph consumption, committed state, direct `GITHUB_TOKEN` commits, cron/dispatch/no-op evidence. Distinguish: FR-824 monitors civic lifecycle events and needs cross-run typed deltas/threads rather than URL dedup. |
| FR-821 weekly recap automation PR | Reuse: exact weekly window, substantive no-op, cron evidence separate from dispatch. Distinguish: FR-821 summarizes one git repo and publishes through protected-main PRs; FR-824 owns a new unprotected publication repo and collects external sources daily. |
| FR-700/702/703/704 recap graph | Distinguish: git-history workstream recap, not public governance/procurement event synthesis. No graph or prompt is copied without governed authoring. |
| `control-plane/scripts/hva-probe-orchestrator.sh` | Source precedent: normalized index envelopes and selective detail. It remains a local research orchestrator; FR-824 extracts only the public subset into the publication repo. |
| `control-plane/scripts/hva-procurement-bulletin.sh` | Source and lifecycle precedent, but rejected as deployment artifact: monolithic collection/analysis/rendering and snapshot outputs do not provide durable delta semantics. |
| `control-plane/docs/github-runner-weekly-recap-research.md` | Governing research: collect event feeds daily, synthesize weekly, persist compact state, exclude device probes, and organize output by threads rather than sources. |

## Alternatives Considered

1. **Add workflows to `control-plane`.** Rejected: it mixes public OSINT and
   local-device/PII tooling, has gitignored snapshot output, and is optimized for
   source research rather than a narrow public product.
2. **Add the bulletin to YAMLGraph examples.** Rejected: a live publication with
   daily committed state is a consumer deployment, not framework example state.
3. **Scrape only once per week.** Rejected: loses lead time and amendments. Daily
   collection is cheap; weekly synthesis is the human attention cadence.
4. **Use Actions cache/artifacts as the state store.** Rejected: evictable,
   invisible, and not a reviewable audit trail.
5. **Commit raw source responses.** Rejected: unnecessary repository growth and
   avoidable retention of attachments/body text; compact normalized evidence is
   sufficient, raw responses remain short-lived artifacts.
6. **Let the LLM deduplicate and link everything.** Rejected: stable IDs,
   publication IDs, dockets, hashes, and explicit references are mechanizable;
   asking the model to own them creates plausible but unauditable links.
7. **Publish one entry per source.** Rejected: source activity is not the
   consumer's question; lifecycle transitions and cross-source threads are.
8. **Protect `main` and use a PAT automation PR immediately.** Deferred: the
   FR-819 direct-commit model is the smallest new-repo proof. Protection changes
   the credential/control model and requires a separate human decision.

## Non-Goals

- Device/local profile probes or any personal-data publication.
- Sources beyond HVA governance, Hilma/TED, and MAO.
- Ministry/legislative vertical threads.
- Real-time alerts, email, Slack, RSS, GitHub Pages, or a dashboard.
- User accounts, subscriptions, billing, or hosted API access.
- General-purpose probe framework or extraction back into YAMLGraph core.
- Withdrawal/removal inference from bounded source indexes.
- Branch-protection or repository-ruleset changes.
- Changes to existing `control-plane` probe behavior under this FR.

## Related

- FR-819 — GitHub-native daily digest PoC repository
- FR-821 — weekly recap publication via GitHub automation
- FR-823 — hosted declarative graph runner (not required by this deployment)
- `../control-plane/docs/github-runner-weekly-recap-research.md`
- `../control-plane/docs/information-landscape.md`
- `../control-plane/docs/hva-probe-architecture-plan.md`
- `../control-plane/scripts/hva-probe-orchestrator.sh`
- `../control-plane/scripts/hva-procurement-bulletin.sh`

## Judgement

Pending independent judge via the governed `scripts/judge.sh` route.

### Questions for the human

None at planning time. The working repository name
`sheikkinen/hva-weekly-bulletin` was verified available on 2026-08-19. Any
public-repository secret or permission beyond `ANTHROPIC_API_KEY` and the scoped
default `GITHUB_TOKEN` requires a new explicit human decision before reliance.
