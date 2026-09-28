---
type: feat
scope: census
req: REQ-YG-717
---
- **FR-1130 LangGraph issues census**: new gh-issues corpus_census adapters (`gh_issues_adapters.py`) list a GitHub repository's issues and PRs with one paginated `gh api` call per run, validate every record, and atomically replace a typed snapshot that versions and extraction read without further API calls; `gh_issues_report.py` adds memo glue, a crosstab that refuses unresolved, unknown, duplicate, missing, off-taxonomy or canary-contradicting ledgers, a citation verifier and a disposition checker. The `langgraph_issues_census` graph classifies every langchain-ai/langgraph issue and PR under a frozen 17-category pain taxonomy through the map memo, and its committed results split the categories into solves / inherits / untouched dispositions. (REQ-YG-717)
