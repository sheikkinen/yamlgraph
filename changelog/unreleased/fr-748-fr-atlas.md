---
type: feat
scope: examples
req: REQ-YG-566
---
- **FR-748 FR Atlas onboarding demo** (`examples/demos/fr-atlas`): turns a
  project's `feature-requests/` corpus into a newcomer-facing narrative atlas —
  deterministic collector (filename-stem ids, verbatim statuses, git-log
  dates), chunked map fan-out for theme candidates, one merge judgement, one
  story-opener judgement, and a coverage post-pass that guarantees every FR
  appears exactly once (unclaimed → visible `misc`, unknown ids raise). Model
  id claims are reconciled at the boundary — bracket sigils stripped, dropped
  `FR-` prefixes restored, shortened/paraphrased slugs repaired by unique
  numeric head or similarity floor against the collected population; ties die
  loudly. Missing CAP registry degrades the module axis to git paths with a
  loud header declaration. Verified on both corpora: yamlgraph (729 FRs → 13
  themes) and ninchat_voice (300 FRs → 14 themes). (REQ-YG-566)
