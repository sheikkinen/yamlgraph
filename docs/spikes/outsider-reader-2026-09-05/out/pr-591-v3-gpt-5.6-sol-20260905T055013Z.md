<!-- outsider spike | input: inputs/pr-591-v3.md | model: gpt-5.6-sol | 2026-09-05T05:50:45.548562+00:00 -->

## 1. In my own words

This change adds a local, AI-assisted research pipeline that examines a 30-capability pilot from a catalog of 242 capabilities, collects descriptions and code references, classifies intended users and retention status, validates model claims against collected evidence, and checks six predetermined cases. It delivers committed run ledgers and findings for project maintainers deciding which capabilities may warrant separate removal requests. The trial found two apparent removal candidates, many developer-facing capabilities, three unsupported consumer claims, unreliable user-type classification, and business-value statements unsuitable for ranking.

## 2. Could I decide whether to merge this from the description alone?

YES

The description identifies the changes, results, artifacts, execution method, cost, limitations, and work intentionally deferred.

## 3. Words and references I could not understand

- **“FR-990”** · What does an FR represent in this project, and what lifecycle or approval rules apply to one?
- **“yamlgraph”** · What project or tool provides this command, and what does its graph execution model mean?
- **“author_graph,run_operate,debug_observe…”** · What are the exact definitions and boundaries of these ten user-type identifiers?
- **“mercury-2”** · What provider and model version does this name identify?

## 4. What a merge decision would still need

- [ ] The exact changed-file diff and whether it contains changes unrelated to the census.
- [ ] Whether the existing repository test, lint, and static-analysis checks pass.
- [ ] The Python, `yamlgraph`, provider-client, and credential prerequisites for the run command.
- [ ] How the 30 capabilities were selected and whether that permits extrapolating the observed rate to all 242.
- [ ] The pipeline’s behavior when code search, source loading, provider calls, or artifact writing fails.
- [ ] Whether a clean checkout can reproduce the committed ledgers using the documented command and model endpoint.
- [ ] The six canary cases, their expected answers, and how those answers were established.
