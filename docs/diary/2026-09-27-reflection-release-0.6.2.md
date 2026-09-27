# Release 0.6.2: distinguish the artifact from its operating environment

## Observation

The pre-release sanity check ran the same 199 focused tests on main and on
an archive of committed HEAD. Main yielded 193 passes and six census
failures; the committed archive yielded 199 passes. The census functions
called their population committed files but discovered it with filesystem
globs, admitting ignored generated examples. The release worktree isolates
the package inputs; it does not repair that discovery defect.

FR-1125 corrects the earlier ranker schema remedy: acceptance by the SDK
transform did not mean preservation of story fields. The final schema now
declares those fields. The external digest changes are merged, but the
qualifying scheduled production run remains outstanding at release preparation.
FR-1124 also records an unmet lint clause for 14 inventory graphs.

Release hooks also exposed a record-boundary defect: CONF-492 existed but
used field labels the confession parser did not recognize. Normalizing the
existing entry to the established format made strict coverage pass, without
changing the suppression or weakening the checker.

## Heuristic

Do not promote one witness into another claim. A clean committed-tree test
run witnesses the release artifact, not arbitrary local files or a deployed
bulletin. Preserve the distinctions in the release record. Freeze fragments
unchanged, keep both version fields aligned, and tag the merged commit only
after its checks pass.

**Seed:** Can census discovery enumerate tracked repository inputs explicitly
so a generated local example cannot change the meaning of a committed ledger?
