### Added
- FR-827: gitclaw — forkable issue-to-feature cron runner
  (https://github.com/sheikkinen/gitclaw). GitHub issue triggers a
  plan→judge→enforce→review Copilot CLI pipeline on Actions that
  commits a working YAMLGraph feature; daily cron runs all features
  and commits outputs. Witnessed end-to-end: issue #3 → committed
  feature → closed in one green run (32322004422).
