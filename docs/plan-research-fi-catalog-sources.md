# Research: C's Data Sources — .fi Domain Seeds and Common Crawl Access

**Date:** 2026-08-31 (probes run live this date)
**For:** Component C, `docs/plan-web-toolkit.md`
**Method:** live endpoint probes (curl, CKAN API) + current vendor docs
(commoncrawl.org get-started, columnar-index blog). Every claim below was
verified by a probe or a docs fetch on the stated date; probe results inline.

## Finding 1 (correction): there is NO public bulk .fi domain list

The plan (revs 1–9) assumed "Traficom open-data domain list (~550k domains)"
as the completeness reference. **Probed false:**

- avoindata (`avoindata.suomi.fi`, CKAN API) has exactly one matching dataset:
  `verkkotunnusrekisteri` ("Verkkotunnusrekisteri", Traficom, **CC-BY 4.0**).
  Its two resources are *lookup UIs*, not bulk data:
  - fi-verkkotunnushaku (per-domain search)
  - WHOIS service (per-domain public info)
- No CSV/bulk resource exists in the dataset; no other dataset matches
  `fi-verkkotunnu*`.
- traficom.fi surface: the fi-verkkotunnukset section links no list/CSV/open
  -data artifact (probe scanned all hrefs for avoin|data|csv|lista|luettelo|
  vapautuv); the old `/tilastot-ja-julkaisut/avoin-data` path and
  `opendata.traficom.fi` both 404.
- The .fi zone file is registrar/EPP territory; Finland is a ccTLD, so ICANN
  CZDS does not apply.

**Consequence:** C's domain seed is assembled from observed-domain sources,
and "coverage vs the true register" becomes an estimate, not a subtraction.
The ~550k figure survives only as Traficom's published *count* statistic,
usable as a denominator for coverage claims.

## Finding 2: Common Crawl gives both the seed AND the text — three tiers

All Common Crawl data is free, no account needed, via
`https://data.commoncrawl.org/<path>` (HTTPS; S3 `s3://commoncrawl/` requires
an authenticated AWS account and must be read from us-east-1). Latest crawl at
probe time: **CC-MAIN-2026-34** (August 2026; crawls are ~monthly, id from
`https://index.commoncrawl.org/collinfo.json`).

### Tier 1 — host-level web graph: the cheapest .fi domain enumeration

`https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-<period>/host/`
publishes the host-level graph per quarter-ish period; the
`*-host-vertices.paths.gz` manifest (probed 200 for `cc-main-2025-may-jun-jul`)
lists vertex files of **every hostname observed** (reversed notation:
`fi.example.www`). Grep the vertex files for the `fi.` prefix → the .fi seed
list, including hosts CC never fetched a page from (vertices include
link-targets). Zero LLM cost, one afternoon of downloads.

### Tier 2 — columnar (URL) index: which .fi pages have content, and where

Parquet table at `s3://commoncrawl/cc-index/table/cc-main/warc/`, partitioned
by `crawl` and `subset`. Schema includes exactly C's pre-filter columns:
`url_host_tld` (= 'fi'), `url_host_registered_domain`, `fetch_status`,
`content_languages`, `content_charset`, `content_mime_detected`,
`warc_filename`/`warc_record_offset`/`warc_record_length` (byte-range pointer
into the archive).

Query options:
- **Athena**: ~$5/TiB scanned; one monthly-crawl index ≈ 300 GB ceiling, but a
  TLD-filtered, few-column query scans MBs (vendor's own .no example: 2.12 MB,
  <1 cent). C's whole "which .fi domains, which pages, homepage per domain"
  query is cents.
- **Local, zero-AWS**: download the `crawl=CC-MAIN-2026-34/subset=warc`
  parquet partition over HTTPS and query with DuckDB/pyarrow. Bigger download,
  no account, reproducible offline.

### Tier 3 — the page text itself: WET vs WARC byte-ranges

Two routes to text for a chosen page:
- **WET files** (`*.warc.wet.gz`): pre-extracted plaintext of every page in a
  crawl segment — but organized by segment, not by domain, so classifying
  .fi-only means either streaming whole WET files and filtering (bandwidth-
  heavy: .fi is a small fraction of each file) or —
- **WARC byte-range fetch** (recommended): the index row's
  `warc_filename` + `offset` + `length` → HTTP `Range` request against
  `data.commoncrawl.org` returns just that page's gzipped WARC record
  (`warcio.ArchiveIterator` parses it; vendor's reference script does exactly
  this). Per-page cost: one ranged GET. Text extraction from HTML is then
  ours — which C already owns via the fi_domain_crawl/daily_digest BS4
  precedent, and which sidesteps WET's known encoding roughness on ISO-8859-1
  era pages (A's encoding fixtures apply).

**Reading:** the plan's "v1 is Common Crawl, not crawling" holds, but the
practical route is index-driven ranged WARC fetches, not bulk WET streaming.
WET remains the fallback for bulk experiments where per-page precision doesn't
matter.

### Politeness/ToS notes

- CC terms of use apply (no restriction relevant to classification research);
  identifying User-Agent required by convention on index.commoncrawl.org
  (RFC 7231 style, vendor asks for contact info in UA).
- index.commoncrawl.org (CDX server) is rate-limited community infra — for
  550k domains use the parquet index, not the CDX API.

## Finding 3: complementary seed sources (gap-fill, all free)

| Source | What it adds | Access |
|--------|-------------|--------|
| **Certificate Transparency** (crt.sh, or Merkle log scan) | .fi hosts that serve TLS but were never crawled/linked — catches small orgs, new domains within hours of cert issuance | crt.sh Postgres interface `%.fi` (heavy; batch politely) or run a CT log tail |
| **Traficom count statistics** | The denominator (~550k active .fi) for coverage estimates | traficom.fi statistics pages, CC-BY 4.0 |
| **hva/control-plane tenant lists** | Ground-truth platform labels for the census columns (CaseM/Dynasty/KTweb hosts) — doubles as classifier eval set | sibling repos, already enumerated |
| **Tranco top list** | Popularity rank column; sanity-check that big .fi sites are in the seed | daily CSV, free |

CT + CC-vertices union is the honest "all observable .fi" seed; nothing
better exists publicly.

## Consequences for the plan (folded as rev 10)

1. **Completeness reference corrected**: Traficom bulk list → Traficom *count*
   (denominator only); seed = CC host-graph vertices ∪ CT hosts.
2. **Pre-filter gains a free stage**: columnar index (fetch_status, languages,
   charset) prunes before DNS/HEAD probing — many domains never need a live
   probe at all.
3. **Fetch route pinned**: index-driven WARC byte-range GETs, not WET bulk
   streaming; WET demoted to fallback.
4. **New cost line**: Athena cents OR pure-HTTPS parquet + DuckDB (no AWS
   account) — pilot should do the DuckDB route for reproducibility.
5. **Coverage is an estimate**: report catalog coverage against Traficom's
   published count, with CT-derived error bars, not as a subtraction from a
   register we don't have.
