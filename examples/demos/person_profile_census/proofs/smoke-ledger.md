# Person Profile Census Ledger
Source: `sheikkinen@sheikkinen:2026-08-25`  visibility: `["public"]`

## Mechanical rollup
- total PRs: 90
- timespan: 2026-08-25T12:53:13Z → 2026-09-02T16:42:33Z
- merge rate: 97.8%
- classification coverage: 100.0%

### Repos

| value | count |
|---|---|
| sheikkinen/yamlgraph | 87 |
| sheikkinen/yamlgraph-daily-digest | 3 |

### change_kind

| value | count |
|---|---|
| docs | 47 |
| feat | 20 |
| fix | 15 |
| refactor | 6 |
| chore | 1 |
| test | 1 |

### surfaces

| value | count |
|---|---|
| docs | 64 |
| tooling | 32 |
| tests | 30 |
| backend | 27 |
| ci | 13 |
| hooks | 9 |
| graphs | 5 |
| adapters | 4 |
| infra | 2 |

### problem_class

| value | count |
|---|---|
| enforcement | 27 |
| tooling | 19 |
| cleanup | 17 |
| research | 11 |
| governance | 7 |
| doctrine | 6 |
| tests | 2 |
| infra | 1 |

### monthly cadence

| value | count |
|---|---|
| 2026-08 | 77 |
| 2026-09 | 13 |

## Top by size

- [sheikkinen/yamlgraph#494](https://github.com/sheikkinen/yamlgraph/pull/494) ±7995 — refactor(examples): FR-915 retire the Mastra integration demo
- [sheikkinen/yamlgraph#491](https://github.com/sheikkinen/yamlgraph/pull/491) ±5368 — refactor(a2a): FR-909 retire the A2A protocol surface
- [sheikkinen/yamlgraph#515](https://github.com/sheikkinen/yamlgraph/pull/515) ±4348 — fix(examples): FR-930 code-own FR-reference reconciliation in recap finalizer
- [sheikkinen/yamlgraph#551](https://github.com/sheikkinen/yamlgraph/pull/551) ±3452 — feat(skills): FR-948 LAN Copilot delegation channel (REQ-YG-636)
- [sheikkinen/yamlgraph#525](https://github.com/sheikkinen/yamlgraph/pull/525) ±3169 — fix(research): FR-938 FR-933 prior-art retrieval reaches the route, retry carries validation feedback
- [sheikkinen/yamlgraph#484](https://github.com/sheikkinen/yamlgraph/pull/484) ±2926 — feat(census): FR-895 census synthesize tail — the stage the human reads
- [sheikkinen/yamlgraph#550](https://github.com/sheikkinen/yamlgraph/pull/550) ±2630 — feat(skills): FR-945 LAN recon skill + FR-946/947 proposals
- [sheikkinen/yamlgraph#480](https://github.com/sheikkinen/yamlgraph/pull/480) ±2436 — feat(census): FR-893 diary trap census — recurrence by measurement, not memory
- [sheikkinen/yamlgraph#553](https://github.com/sheikkinen/yamlgraph/pull/553) ±2347 — feat(skills): FR-949 issue-queue delegation runner bundle (REQ-YG-637)
- [sheikkinen/yamlgraph#562](https://github.com/sheikkinen/yamlgraph/pull/562) ±2315 — feat(census): FR-961 person-profile census — authored-PR corpus map-reduce

## Per-PR rows

| item_ref | change_kind | problem_class | surfaces | intent |
|---|---|---|---|---|
| [sheikkinen/yamlgraph#476](https://github.com/sheikkinen/yamlgraph/pull/476) | feat | enforcement | hooks, infra, tests | Adds a main‑write guard hook that forces all writes to go through a worktree, enforcing FR‑888 rules and providing an es |
| [sheikkinen/yamlgraph#477](https://github.com/sheikkinen/yamlgraph/pull/477) | feat | research | backend, tests, ci | Adds the sole research route for FR-890, enforcing closed-input alternatives before authority, with new scripts, fixture |
| [sheikkinen/yamlgraph#478](https://github.com/sheikkinen/yamlgraph/pull/478) | fix | enforcement | backend, adapters | Fix the fail‑closed behavior of the agent so that all failed runs raise AllToolCallsFailedError before synthesis and sea |
| [sheikkinen/yamlgraph#479](https://github.com/sheikkinen/yamlgraph/pull/479) | feat | tooling | tooling, graphs, tests | Adds the corpus-census discover‑extract‑map‑reduce pipeline with invocation‑time tool‑slot binding, a fail‑closed eviden |
| [sheikkinen/yamlgraph#480](https://github.com/sheikkinen/yamlgraph/pull/480) | feat | doctrine | backend, tests, docs | Adds a diary‑trap census feature that aggregates recurrences by measurement, updates the corpus_census pipeline, introdu |
| [sheikkinen/yamlgraph#481](https://github.com/sheikkinen/yamlgraph/pull/481) | docs | cleanup | docs | Rename the diary reflection file to follow the gate-required filename pattern and add a Seed marker, as a documentation- |
| [sheikkinen/yamlgraph#482](https://github.com/sheikkinen/yamlgraph/pull/482) | docs | cleanup | docs | Rename the diary reflection file to follow the gate-required filename pattern and add a Seed: marker, as part of FR-890  |
| [sheikkinen/yamlgraph#483](https://github.com/sheikkinen/yamlgraph/pull/483) | chore | tooling | tooling | Add a cross‑platform VS Code script that generates a day‑grouped monthly work report from the local chronicle, handling  |
| [sheikkinen/yamlgraph#484](https://github.com/sheikkinen/yamlgraph/pull/484) | feat | tooling | backend, tooling | Adds a census pipeline stage that synthesizes the tail for human reading, updating scripts, diary generation, PDF librar |
| [sheikkinen/yamlgraph#485](https://github.com/sheikkinen/yamlgraph/pull/485) | feat | enforcement | adapters, graphs, tooling | Adds a census feature that discovers organization repositories, generates a repo_census graph via scripts, and pins Azur |
| [sheikkinen/yamlgraph#486](https://github.com/sheikkinen/yamlgraph/pull/486) | fix | research | backend, tests, tooling | Enforce precedent traceability for research routes by adding validation at the reducer boundary, closing enums, checking |
| [sheikkinen/yamlgraph#487](https://github.com/sheikkinen/yamlgraph/pull/487) | feat | enforcement | tooling, docs, tests | Add a VS Code script that generates per‑request session accountability reports from chat session stores, supporting full |
| [sheikkinen/yamlgraph#488](https://github.com/sheikkinen/yamlgraph/pull/488) | feat | tooling | tooling, tests | Add a shared SMTP email example tool with comprehensive contracts and tests, replacing the vendor-bound Resend node and  |
| [sheikkinen/yamlgraph#489](https://github.com/sheikkinen/yamlgraph/pull/489) | fix | enforcement | docs, tests | Renumber colliding FR identifiers, update all references, and add a guard to prevent future ID namespace collisions. |
| [sheikkinen/yamlgraph#490](https://github.com/sheikkinen/yamlgraph/pull/490) | fix | enforcement | backend, tests | Replace filesystem globbing with git ls-files for the FR-number uniqueness guard and add a test to ensure untracked file |
| [sheikkinen/yamlgraph#491](https://github.com/sheikkinen/yamlgraph/pull/491) | refactor | cleanup | backend, tests, docs, ci | Retire the A2A protocol surface by removing its implementation, CLI commands, examples, documentation, optional extra, a |
| [sheikkinen/yamlgraph#492](https://github.com/sheikkinen/yamlgraph/pull/492) | refactor | cleanup | backend, docs, tests, tooling | Retire the MCP server surface by removing its code, documentation, configuration files, and related tests, and updating  |
| [sheikkinen/yamlgraph#493](https://github.com/sheikkinen/yamlgraph/pull/493) | docs | cleanup | docs | Document the retirement of the skill export surface and the graph bench command as part of FR-912 and FR-913. |
| [sheikkinen/yamlgraph#494](https://github.com/sheikkinen/yamlgraph/pull/494) | refactor | cleanup | docs, tests, tooling | Retire the Mastra integration demo by deleting its example files and adding a witness test to confirm removal, while pre |
| [sheikkinen/yamlgraph#495](https://github.com/sheikkinen/yamlgraph/pull/495) | docs | governance | docs | Document the decisions to retire the dry-run flag (FR-903) and ban the phrase (FR-916) as part of governance. |
| [sheikkinen/yamlgraph#496](https://github.com/sheikkinen/yamlgraph/pull/496) | docs | cleanup | docs | Update documentation to reflect the retirement arc of FR-909, FR-910, and FR-915, adding heuristics and resolving recurr |
| [sheikkinen/yamlgraph#497](https://github.com/sheikkinen/yamlgraph/pull/497) | refactor | cleanup | backend, docs, hooks | Retire the committed FR board by removing its documentation, drift hook, and related command-line flags, while preservin |
| [sheikkinen/yamlgraph#498](https://github.com/sheikkinen/yamlgraph/pull/498) | docs | cleanup | docs, tooling | Retire the yamlgraph diary CLI surface and update documentation accordingly. |
| [sheikkinen/yamlgraph#499](https://github.com/sheikkinen/yamlgraph/pull/499) | feat | enforcement | hooks, backend, tests, ci | Implements FR-902 session worktree lifecycle by adding idempotent session lane hooks, fenced tool checks, checkpoint com |
| [sheikkinen/yamlgraph#500](https://github.com/sheikkinen/yamlgraph/pull/500) | fix | enforcement | tests | Hardens retirement witnesses by adding import guards and path existence checks to ensure retired modules are not importa |
| [sheikkinen/yamlgraph#501](https://github.com/sheikkinen/yamlgraph/pull/501) | docs | enforcement | docs, ci | Add operator scope documentation for FR-889 and record enforcement-ring audit diaries, updating CLAUDE.md, VS Code setti |
| [sheikkinen/yamlgraph#502](https://github.com/sheikkinen/yamlgraph/pull/502) | docs | tests | docs, ci | Adds a no-op success job to break deadlocks caused by docs-only PRs in required test contexts. |
| [sheikkinen/yamlgraph#503](https://github.com/sheikkinen/yamlgraph/pull/503) | feat | enforcement | hooks, infra, tests | Add an OS‑enforced main‑write lock to the main checkout and delete the associated grammar, updating hooks and scripts to |
| [sheikkinen/yamlgraph#504](https://github.com/sheikkinen/yamlgraph/pull/504) | docs | governance | docs, hooks | Document the plan and judgement for retiring the FR-902 lane‑guard hook machinery, with no code changes. |
| [sheikkinen/yamlgraph#505](https://github.com/sheikkinen/yamlgraph/pull/505) | fix | enforcement | hooks, docs | Remove the docs exception from the main-write lock to ensure the agent cannot write to docs, updating the lock configura |
| [sheikkinen/yamlgraph#506](https://github.com/sheikkinen/yamlgraph/pull/506) | docs | cleanup | docs | Audit and update wording for FR-889 and FR-902 to correctly reflect the invariant and policy coverage. |
| [sheikkinen/yamlgraph#507](https://github.com/sheikkinen/yamlgraph/pull/507) | docs | research | docs | Adds a research record documenting the session isolation ladder across worktree, container, VM, and cloud environments. |
| [sheikkinen/yamlgraph#508](https://github.com/sheikkinen/yamlgraph/pull/508) | refactor | cleanup | hooks, tests, tooling | Retire and remove the FR-902 lane‑guard hook machinery, deleting related scripts, tests, and configurations while preser |
| [sheikkinen/yamlgraph#509](https://github.com/sheikkinen/yamlgraph/pull/509) | docs | doctrine | docs | Update documentation to reflect the actual exercised process for gate handling, aligning the documented doctrine with ob |
| [sheikkinen/yamlgraph#510](https://github.com/sheikkinen/yamlgraph/pull/510) | fix | tooling | tooling | Clear the orphaned race timer in network-sniff.js to prevent delayed process exit and reduce sniffing time. |
| [sheikkinen/yamlgraph#511](https://github.com/sheikkinen/yamlgraph/pull/511) | docs | research | docs, ci | Provide documentation for the FR-928 cloud judge plan and judgement, outlining the research route and evaluation outcome |
| [sheikkinen/yamlgraph#512](https://github.com/sheikkinen/yamlgraph/pull/512) | docs | doctrine | docs | Add a documentation record for FR-922 latency investigation, noting that the premise was not reproduced and no code chan |
| [sheikkinen/yamlgraph#513](https://github.com/sheikkinen/yamlgraph/pull/513) | docs | enforcement | hooks, ci, docs | Add a pre‑push pre‑commit hook to check for the existence of a diary file across the push range, de‑duplicate existing i |
| [sheikkinen/yamlgraph#514](https://github.com/sheikkinen/yamlgraph/pull/514) | refactor | cleanup | tooling, tests, docs | Retire the skill/agent export CLI group and related export code, removing associated documentation and tests. |
| [sheikkinen/yamlgraph#515](https://github.com/sheikkinen/yamlgraph/pull/515) | fix | enforcement | backend, tests | Fixes the recap finalizer to reconcile FR references, enforce REQ-YG-531, strip unverified tokens, and record them in re |
| [sheikkinen/yamlgraph#516](https://github.com/sheikkinen/yamlgraph/pull/516) | feat | tooling | backend, adapters | Pin the judge and review routes to use the gpt-5.6-sol model, replacing gpt-5.5, to get a larger prompt window and lower |
| [sheikkinen/yamlgraph#517](https://github.com/sheikkinen/yamlgraph/pull/517) | docs | doctrine | docs | Adds documentation for the Excel export feature (autofilter and per-region banding) as described in FR-932. |
| [sheikkinen/yamlgraph#518](https://github.com/sheikkinen/yamlgraph/pull/518) | docs | doctrine | docs | Update documentation to clarify that alternatives are probes rather than paragraphs, adding a metacognitive entry and ex |
| [sheikkinen/yamlgraph#519](https://github.com/sheikkinen/yamlgraph/pull/519) | docs | research | docs | Add a diary entry documenting the 3‑day worktree pipeline arc, the concurrency bottleneck, and the worktree.sh --prefix  |
| [sheikkinen/yamlgraph#520](https://github.com/sheikkinen/yamlgraph/pull/520) | docs | research | docs, ci | Adds documentation describing how the merge queue eliminates the need for rebasing by enabling squash and dropping stric |
| [sheikkinen/yamlgraph#521](https://github.com/sheikkinen/yamlgraph/pull/521) | docs | enforcement | docs | Adds documentation for FR-934 and FR-935, describing the merge queue enablement and admin‑merge guard, and records the r |
| [sheikkinen/yamlgraph#522](https://github.com/sheikkinen/yamlgraph/pull/522) | feat | infra | ci, docs | Add merge_group trigger to CI workflows and update documentation to support the main merge queue. |
| [sheikkinen/yamlgraph#523](https://github.com/sheikkinen/yamlgraph/pull/523) | fix | enforcement | ci, docs, tests | Record the platform blocker for FR-934, restore strict‑regime documentation, and update test pins to reflect the blocker |
| [sheikkinen/yamlgraph#524](https://github.com/sheikkinen/yamlgraph/pull/524) | docs | tooling | docs, tooling | Provide a high‑level plan overview for the web toolkit, describing three composable capabilities and prior art. |
| [sheikkinen/yamlgraph#525](https://github.com/sheikkinen/yamlgraph/pull/525) | fix | research | backend, graphs, tooling | Fix two defects by making retry carry validation feedback and ensuring prior‑art retrieval runs correctly through proper |
| [sheikkinen/yamlgraph#526](https://github.com/sheikkinen/yamlgraph/pull/526) | docs | tooling | docs, tooling | Add a reflection pass to the web toolkit plan, updating consumer ranking, adding dispositions, cost model, and evaluatio |
| [sheikkinen/yamlgraph#527](https://github.com/sheikkinen/yamlgraph/pull/527) | docs | tooling | docs, tooling | Update the plan documentation for web toolkit revision 3, designating component C as primary and promoting the storage-b |
| [sheikkinen/yamlgraph#528](https://github.com/sheikkinen/yamlgraph/pull/528) | docs | tooling | docs, tooling | Adds documentation for the web toolkit rev 4, comparing mitmproxy2swagger and har-to-openapi converters and describing a |
| [sheikkinen/yamlgraph#529](https://github.com/sheikkinen/yamlgraph/pull/529) | docs | tooling | docs, tooling | Update the plan documentation to describe the SPA rendering product boundary and the web toolkit revision 5, outlining o |
| [sheikkinen/yamlgraph#530](https://github.com/sheikkinen/yamlgraph/pull/530) | docs | tooling | docs, tooling | Updates the documentation to incorporate the per‑component value audit into the web toolkit plan revision 6. |
| [sheikkinen/yamlgraph#531](https://github.com/sheikkinen/yamlgraph/pull/531) | docs | tooling | docs, tooling | Update the plan documentation for web toolkit revision 7, adding details about unparked sibling repository B and related |
| [sheikkinen/yamlgraph#532](https://github.com/sheikkinen/yamlgraph/pull/532) | docs | enforcement | docs, tooling | Add French documentation for FR-936 map node hardening and update the web toolkit plan revision 8, incorporating map har |
| [sheikkinen/yamlgraph#533](https://github.com/sheikkinen/yamlgraph/pull/533) | docs | governance | docs | Add a metacognitive diary entry summarizing the web-toolkit plan arc and extracting FR-936 details. |
| [sheikkinen/yamlgraph#534](https://github.com/sheikkinen/yamlgraph/pull/534) | docs | governance | docs, tooling | Add documentation for the web toolkit revision 9, describing C cost-control constraints, mercury-2 classifier pinning, a |
| [sheikkinen/yamlgraph#535](https://github.com/sheikkinen/yamlgraph/pull/535) | docs | research | docs | Add documentation for C source research and update the plan with rev 10 details, including a new C-seed row and narrowed |
| [sheikkinen/yamlgraph#536](https://github.com/sheikkinen/yamlgraph/pull/536) | docs | research | docs | Update documentation to record the judgement that FR-936 should be split into four separate feature requests, each requi |
| [sheikkinen/yamlgraph#537](https://github.com/sheikkinen/yamlgraph/pull/537) | docs | enforcement | docs, backend | Add documentation and type definitions for the map overflow policy, including on_overflow error handling, default error  |
| [sheikkinen/yamlgraph#538](https://github.com/sheikkinen/yamlgraph/pull/538) | docs | governance | docs | Update documentation and judgement record for FR-939, approve with revisions, upgrade research record, fix dead config p |
| [sheikkinen/yamlgraph#539](https://github.com/sheikkinen/yamlgraph/pull/539) | docs | tooling | docs, tooling | Update the plan documentation to describe web toolkit rev 11, reframing component C as a semantic layer over Common Craw |
| [sheikkinen/yamlgraph#540](https://github.com/sheikkinen/yamlgraph/pull/540) | docs | doctrine | docs | Adds a diary reflection documenting plan revisions 9‑11, split judgment and full cycle notes. |
| [sheikkinen/yamlgraph#541](https://github.com/sheikkinen/yamlgraph/pull/541) | fix | research | backend, tests, ci | Fix duplicated precedent contract handling in research preflight and route reducer, unify marker predicate, bound honest |
| [sheikkinen/yamlgraph#542](https://github.com/sheikkinen/yamlgraph/pull/542) | docs | tooling | docs | Add an automated weekly recap document for week 2026-W36 generated by the weekly-recap workflow. |
| [sheikkinen/yamlgraph#543](https://github.com/sheikkinen/yamlgraph/pull/543) | docs | cleanup | docs | Clean up home configuration files and deduplicate instruction context documentation, reducing redundancy and streamlinin |
| [sheikkinen/yamlgraph#544](https://github.com/sheikkinen/yamlgraph/pull/544) | docs | enforcement | docs | Update documentation to record that the session-start autocompaction was rejected for FR-942, noting the evaluation verd |
| [sheikkinen/yamlgraph#545](https://github.com/sheikkinen/yamlgraph/pull/545) | fix | enforcement | backend, tests, tooling | Normalize census judgement labels at the ledger boundary, adding deterministic stripping, separator cuts, and a frozen l |
| [sheikkinen/yamlgraph#546](https://github.com/sheikkinen/yamlgraph/pull/546) | docs | cleanup | docs | Add documentation for the judgments of FR-941 and FR-942, indicating they are approved with revisions and pending enforc |
| [sheikkinen/yamlgraph#547](https://github.com/sheikkinen/yamlgraph/pull/547) | fix | enforcement | backend, tests | Contain census row-level failures at the ledger reduce boundary by adding error handling and taxonomy, preventing malfor |
| [sheikkinen/yamlgraph#548](https://github.com/sheikkinen/yamlgraph/pull/548) | feat | enforcement | docs, tests, tooling, ci | Add a size‑gate enforcement for instruction files, rewrite CLAUDE.md as a dev‑command, compress scripture entries, and u |
| [sheikkinen/yamlgraph#549](https://github.com/sheikkinen/yamlgraph/pull/549) | fix | enforcement | graphs, backend | Fixes the map-to-map barrier join so each branch gets its correct _map_index by inserting a synthetic join, preventing d |
| [sheikkinen/yamlgraph#550](https://github.com/sheikkinen/yamlgraph/pull/550) | feat | tooling | backend, tests, tooling, docs | Implement the LAN recon skill (FR-945) with WinRM inventory reading, error handling, and tests, while proposing docs-onl |
| [sheikkinen/yamlgraph#551](https://github.com/sheikkinen/yamlgraph/pull/551) | feat | tooling | backend, docs, tests, tooling | Implement the LAN Copilot delegation channel with a new wire layer, wrapper scripts, extensive offline and live tests, a |
| [sheikkinen/yamlgraph#552](https://github.com/sheikkinen/yamlgraph/pull/552) | docs | governance | docs, backend | Adds documentation for the third‑judgement process (R‑1, R‑2, R‑4) and records operator overrides O‑1 to O‑3, including  |
| [sheikkinen/yamlgraph#553](https://github.com/sheikkinen/yamlgraph/pull/553) | feat | enforcement | backend, tests, docs, tooling | Add a self‑hosted runner bundle for GitHub issue‑queue delegation, including scripts, worker code, configuration, tests, |
| [sheikkinen/yamlgraph#554](https://github.com/sheikkinen/yamlgraph/pull/554) | docs | enforcement | docs | Document FR-954 and FR-950 residuals, describing fork-sim fidelity issues and CAP-198 attribution while noting the assoc |
| [sheikkinen/yamlgraph#555](https://github.com/sheikkinen/yamlgraph/pull/555) | fix | cleanup | backend, tests | Fix CAP-198 attribution and make the py3.14 fork test safe by pre‑importing dependencies and updating drifted confession |
| [sheikkinen/yamlgraph#556](https://github.com/sheikkinen/yamlgraph/pull/556) | docs | cleanup | docs | Update documentation to reflect the re‑scope of FR‑954 after PR #555 landed, noting Defect B and removal of pre‑import s |
| [sheikkinen/yamlgraph#557](https://github.com/sheikkinen/yamlgraph/pull/557) | docs | governance | docs | Add documentation updates for FR-936 split record and rejudgement, and include a business use‑case brainstorming documen |
| [sheikkinen/yamlgraph#558](https://github.com/sheikkinen/yamlgraph/pull/558) | test | tests | tests, docs | Implements a faithful no‑fork import simulation for FR‑954, adding assertions that os.fork is absent and updating test i |
| [sheikkinen/yamlgraph#559](https://github.com/sheikkinen/yamlgraph/pull/559) | docs | research | docs | Add documentation for FR-955, FR-956, and FR-957 map‑branch enhancements and name the three FR‑936 child tables. |
| [sheikkinen/yamlgraph#560](https://github.com/sheikkinen/yamlgraph/pull/560) | docs | enforcement | docs, hooks | Add documentation for registering the hook enforcement layer for Claude Code, describing the intended registration proce |
| [sheikkinen/yamlgraph#561](https://github.com/sheikkinen/yamlgraph/pull/561) | docs | cleanup | docs | Docs-only PR that folds the SPLIT judgement for FR-958, files its two child FRs (FR-959 and FR-960), and adds a diary en |
| [sheikkinen/yamlgraph#562](https://github.com/sheikkinen/yamlgraph/pull/562) | feat | tooling | adapters, backend, docs, tooling | Add a corpus‑reduce based person‑profile census tool that aggregates authored PRs per person for self‑audit. |
| [sheikkinen/yamlgraph-daily-digest#1](https://github.com/sheikkinen/yamlgraph-daily-digest/pull/1) | feat | enforcement | backend, tooling, tests, ci | Implement ordered archiving then email delivery per FR-903, add multipart email support, enforce ordering, remove dry-ru |
| [sheikkinen/yamlgraph-daily-digest#2](https://github.com/sheikkinen/yamlgraph-daily-digest/pull/2) | feat | enforcement | backend | Adds validation to ensure each ranked story conforms to the expected schema, dropping malformed items and raising errors |
| [sheikkinen/yamlgraph-daily-digest#3](https://github.com/sheikkinen/yamlgraph-daily-digest/pull/3) | feat | tooling | tooling, backend, graphs, tests | Introduce a tool slot to bind digest collection sources, allowing dynamic selection of source manifests and moving sourc |
