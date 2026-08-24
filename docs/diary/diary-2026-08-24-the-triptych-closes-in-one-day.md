# Diary — 2026-08-24 — The triptych closes in one day

**Arc:** FR-881 (image_pipeline v3, local model as generator): plan →
inline-answered decisions → graph judge → fold → cross-repo enforce →
witnessed demo with rendered images. Third governed loop of the day on
the same model artifact (FR-876 trained it, FR-879 made it a judge,
FR-881 made it the author).

## Trap witnessed: my own decisions section lied to the enforcer

The judge's R-2 caught the FR carrying BOTH a frozen decision ("first k
passers") and a Proposed Solution paragraph still offering two ranking
alternatives "to decide at enforce time." I wrote the decision fold and
did not sweep the body it invalidated — a document-internal
`intent_drift`: plan says X in one section, still says maybe-Y in
another. An FR is one contract, not a chat log; folding a decision
means DELETING the alternatives it killed, not appending the verdict.
Same class as the FR-876 lesson (narrative forecasts are ungated), one
level up: even *resolved* narrative left standing becomes an ambiguous
instruction to a stateless enforcer.

## Trap witnessed twice: dependency status as stale snapshot

I wrote "FR-879 in flight, wait for merge" while the parallel session
was landing it; by judgement time it was Enforced, and the judge had to
burn R-1 correcting my dependency line and a citation to a judgement
file that never existed. In a multi-session repo, any statement about
ANOTHER session's work is a snapshot with second-scale staleness —
verify at write time (`git log`, file existence), or phrase it as a
predicate to check at enforce time, never as a fact.

## What worked

- Chassis reuse priced correctly: v3 cost one `--json` mode (98 lines),
  two nodes, and one authored graph — the judge's R-4 (v2's hardcoded
  output path) was the only real composition hazard, and the AC-10
  regression test now pins it.
- The sole authoring route produced a lint-clean no-llm graph on the
  first pass, with the honest "full run blocked, deferred to AC-12"
  record in the authoring report — the route's honesty contract doing
  its job.
- The demo's provenance stamps (`ckpt_sha/corpus_sha/git_sha` on every
  candidate) — planted as a Scripture seed months ago
  (`artifact_carries_code_identity`) — were verified in the wild for
  the first time: the rendered images trace to the exact model binary
  and corpus revision that produced their prompts.

**Seed:** three FRs now form a one-day pipeline lineage (train → judge
→ generate) across two repos, each stage consuming the previous
stage's witnessed artifact. The lineage is only visible by reading
three FRs end-to-end. Should the FR template grow a machine-readable
`consumes:` field (FR → artifact SHA), so provenance chains like
876→879→881 can be rendered mechanically — an atlas edge type instead
of archaeology?
