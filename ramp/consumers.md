# Ramp Consumers

Generic source-repo registry (FR-865 A-2). One row per install, written
by `scripts/ramp.sh <target> --tier N --record-consumer <owner/repo>`
after a successful non-dry-run install. Row identity is
`(target, tier, manifest_hash)`; re-installs update the row idempotently.
The target is a repository slug (`owner/repo`) — never an absolute local
path or a credential-bearing URL. Consumers of this table: the
diary-graduation sweep (`cross_project_graduation`) and a future
`ramp.sh --check` staleness diff.

| target | date | tier | source_sha | manifest_hash | reviewed_sha |
|---|---|---|---|---|---|
| sheikkinen/deviant-daily | 2026-08-24 | 3 | 560a27145f3d | fcdee1b04548 | cea3e49f |
