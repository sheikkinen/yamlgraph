# Research: Publication Channels for External Signals

**Date:** 2026-08-18
**Origin:** `docs/diary/diary-2026-08-18-missing-last-leg.md` (Proclaim/Harvest
stages). Scope: enumerate publication channels where YAMLGraph artifacts can
face external consumers — human and agent equally — with the measurable
signal each channel emits and how to harvest it. Monetization is one signal
class among several, not the goal.

## Baseline (verified 2026-08-18)

| Channel | Status | Signal today |
|---|---|---|
| PyPI (`yamlgraph` 0.5.22) | **Published** | downloads unmeasured |
| GitHub (`sheikkinen/yamlgraph`) | **Public** | 3 stars |
| Everything else | Absent | zero |

The striking fact: two channels already exist and emit signals *nobody
harvests*. The last leg is not greenfield — it is two unread instruments
plus an empty proclamation calendar. First act is reading existing gauges,
not building new ones.

## What the repo can publish (inventory of proclaimable artifact classes)

1. **The framework** — PyPI package, MCP server, A2A server
2. **The doctrine** — Scripture, chaplain pipeline, hook architecture; the
   ebook pipeline (ch00–ch08) already generates a book about it
3. **Content pipeline output** — horoscopes, novels (novel_fandom, dungeon
   master), TTS audio (chatterbox), images, kalevala lyrics, daily_digest
4. **The diaries** — 1,198 metacognitive entries on agent-driven
   development; genuinely novel essay material
5. **The corpus as data** — FR knowledge graph, judge verdicts: research
   artifacts for the agent-engineering community

Classes 3–5 are unusual: most OSS projects can publish only class 1–2.
The content pipelines mean the repo can publish *product*, not just *tooling*.

## Channel map

### Agent-facing channels (thesis-aligned: agents as first consumers)

| Channel | Artifact | Signal | Harvest method |
|---|---|---|---|
| MCP registries (GitHub MCP registry, mcp.so, Smithery, VS Code gallery) | `mcp_server.py` exposing graphs as tools | installs; external invocations | server-side invocation log with client fingerprint |
| A2A directory / agent cards | a2a_server agents | inbound A2A calls from foreign agents | server access log (already CAP-101/104/105 substrate) |
| PyPI | framework | downloads (agents pip-install too) | `pypistats` API, weekly |
| `llms.txt` + agent-readable docs on the repo/site | reference/*.md re-served | fetches by agent user-agents | hosting access log UA analysis |
| GitHub dependents graph | framework | repos importing yamlgraph | GitHub API, monthly |
| Skill/agent marketplaces (Copilot skills, Claude skills) | the doctrine packaged as installable skills | installs | marketplace stats |

The purest thesis-test signal: **an external agent invoking a yamlgraph MCP
tool or A2A endpoint unprompted**. One such event outweighs a thousand views
— it is the thesis observed in the wild.

### Human-facing channels

| Channel | Artifact | Signal | Harvest method |
|---|---|---|---|
| HN / Reddit (r/LocalLLaMA, r/MachineLearning) / lobste.rs | framework launch, doctrine essays | upvotes, comments, referral stars | GitHub traffic API + post metrics |
| Blog / dev.to / Medium | diary-derived essays (the Scripture, the chaplain, "the pipeline ate the filter") | reads, follows | platform stats |
| YouTube / TikTok shorts | content-pipeline output: TTS-voiced horoscopes, dungeon-master scenes, image-that-speaks | views, watch time | platform APIs |
| Leanpub / Gumroad / KDP | ebook (pipeline exists, ch00–ch08) | sales — the cleanest monetization signal | platform reports |
| Newsletter | daily_digest graph output | subscribers, opens | ESP stats |
| GitHub itself | README showcase, releases | stars, traffic (14-day window — harvest or lose) | GitHub API |

### Monetization (a signal class, not the goal)

| Mechanism | Reads on | Latency |
|---|---|---|
| Ebook sales | doctrine value to humans | weeks |
| GitHub Sponsors | framework goodwill | months |
| Metered A2A/MCP endpoints | agent demand | weeks once listed |
| Content channel revenue share | content pipeline quality | months |

## Structural observations

1. **Proclaim artifacts are already generated; publishing adapters are not.**
   The ebook pipeline, daily_digest, TTS, and demo logs exist as graphs. The
   missing code is thin: per-channel publish tools (a `tools/publish_*.py`
   per channel) plus a harvest ingestion script. Dogfooding: each Proclaim
   pipeline is itself a YAMLGraph graph — the framework demonstrating itself
   is the demo.
2. **Human and agent channels differ in what they validate.** Human channels
   validate the *story* (doctrine essays, content); agent channels validate
   the *thesis* (machine consumption). Both are external; only agent
   channels can falsify "build for agents first."
3. **Content channels decouple signal from framework adoption.** A TikTok
   viewer of a generated horoscope never learns YAMLGraph exists — and
   that's fine: the signal measures the *pipeline's output quality*, which
   is what a content capability's slot-defense should rest on.
4. **GitHub traffic data expires in 14 days.** Harvest must start before
   any proclamation, or early referral signals are lost unrecoverable.

## Recommended first slice (fastest bell per consumer type)

1. **Harvest what exists (zero proclamation needed):** weekly cron pulling
   pypistats + GitHub stars/traffic/dependents into
   `data/harvest/ledger.jsonl`. Cost: one script. Establishes the baseline
   curve every later proclamation is measured against.
2. **Agent bell:** register the MCP server in one registry; add invocation
   logging with client fingerprint. Signal: first external agent call.
3. **Human bell:** one doctrine essay (the diary corpus already wrote it —
   "The Pipeline Ate the Filter" is publishable nearly as-is) posted to
   HN/dev.to, with GitHub traffic harvest running to attribute referrals.
4. **Monetization bell:** finish the ebook pipeline's last mile → Leanpub.
   Slowest of the four; start last.

Order matters: harvest before proclaim (else signals land on no
instrument), agent before human (thesis priority), monetization last
(longest latency, least informative early).

## Risks

- **Proclaim-surplus** (from the last-leg diary): the pipeline that
  overproduced features can overproduce posts. One channel per artifact
  class until its signal is understood.
- **Vanity drift**: views on content are valid *for content capabilities
  only* — never let them defend framework or doctrine slots.
- **Harvest as ritual**: the ledger must feed the judge's portfolio
  question and the retirement pipeline mechanically, or it is a dashboard
  with no reader — failing the first-reader gate it was born from.
