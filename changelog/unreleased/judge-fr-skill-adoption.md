---
type: feat
scope: skills
---
- **judge-fr skill bundle adoption (P-1 copy, csap NC-412)**: added
  `.github/skills/judge-fr/` — canonical non-invocable `doctrine.md`
  (8-criterion rubric extracted from `.chaplain` FR-084→257→305, CORE
  fence for cross-repo drift diffs), thin `SKILL.md` discovery wrapper,
  `judgement.template.md`, `MANIFEST.yaml` provenance, and thin
  adapters (`/judge-fr` + `/review-pr` prompts, non-authoritative
  yamlgraph graph prototype). Scripture Judge step now points at the
  doctrine; yamlgraph-local judge extensions preserved.
- **csap NC-414 mirror**: `allow_all_tools: true` on the judge node
  (file-write contract) plus execution-identity recursion guard (graph
  prompt + doctrine.md CORE re-entry section + Scripture exception) —
  prevents the judge cascade observed on csap.
