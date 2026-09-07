---
type: feat
scope: census
req: REQ-YG-670
---
- **FR-1027 Org AI dossier — GitHub + Jira census with onepager**: new
contrib/example `examples/demos/org_ai_dossier/` on the corpus-census pattern:
GitHub active repos and Jira active projects → one Azure judgement per unit →
typed LLM-free reducers (identity reconciliation, evidence-backed AI claims,
two hidden canary families, coverage denominators, AI-tool inventory, two
source-qualified person rankings with no cross-system join) → optional
explicitly-authorized person summaries → two bounded synthesis judgements →
`dossier.md`, `onepager.md` (≤800 words), `repos.md`, `jira.md`, ledgers and
`run.json` written atomically under an enforced gitignored output root.
Adapters `gh_ai_adapters.py` (active discover, AI-signal extract, org code
search) and `jira_adapters.py` (REST v3 + smoke fixtures) with numeric
ceilings that abort at N+1 before LLM spend. (REQ-YG-670)
