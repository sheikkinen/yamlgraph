# The Requirement That Survived Its Capability

**Date:** 2026-08-29
**Context:** Enforcing FR-909 (retire A2A) and FR-910 (retire MCP) back to back.

## The trap: retirement as a file-level operation

Both FRs read like deletions. Delete the module, delete the tests, delete the
demo, flip two CAP files to `status: retired`, write a changelog fragment.
Six deliverables each, all mechanical. I planned them that way.

Then `req_coverage.py --strict` failed on FR-909 with a phantom requirement.
CAP-81 — "A2A Protocol Server" — hosted **REQ-YG-206, shared graph
discovery**. Nine live tests tag it. `discovery.py` survives the retirement by
the judgement's own C-3. Retiring the CAP file would have retired a
requirement that is still true.

The unit of retirement is the CAP *file*. The unit of truth is the *requirement*.
When a capability accretes a requirement that outlives its own subject, those
units diverge, and a file-level retirement silently takes a live claim with it.
`validate_capabilities.py` forbids duplicate REQ IDs, so the requirement had to
**move**, not be copied — and moving it broke the changelog↔CAP cross-check for
a fragment frozen in release 0.4.64, three years of releases ago.

One deletion, three registries, all coupled.

## The mirror image on FR-910

FR-910's judgement froze C-3: *do not delete `discovery.py`; the research says
it stays because it is CLI-consumed.* After deleting the MCP server I ran
`vulture`, which reported `discover_graphs` and `DEFAULT_GRAPH_PATTERNS` as
dead. I checked: `yamlgraph graph list` does not import them. Nothing in
production does. The MCP server was the last consumer, and the judgement's
justification for keeping the module was **false at the moment it was written**.

C-3 is a GATE. The correct move was not to be clever — it was to obey the gate,
whitelist the names with the reason in plain sight, and write the finding into
the FR and the PR body so a follow-up FR can dispose of the module with the
evidence in hand. A gate built on a wrong premise still binds; what it does not
do is silence you.

## The heuristic

**`retirement_orphans_the_tenant`** — before retiring any container
(capability, module, extra, package), enumerate what *lives inside it that is
not about it*. The container's name describes its subject; its contents may
have accreted lodgers with independent lifetimes. Grep the container's
identifiers against live consumers before flipping the status field, not after
the strict gate fails.

Sibling of `refactor_orphans_secondary` (Scripture) — that one is about a
function's second responsibility; this one is about a registry entry's second
tenant. Same failure shape at a different granularity, which is the second
witness. One more and it graduates.

Corollary — **`gate_premise_may_be_stale`**: a judgement's GATE is binding, but
its *reason* is a claim about the world at authoring time. Enforcement is the
first moment anyone actually checks. When the premise fails, obey the gate,
record the falsification loudly, and hand the disposition to a successor FR.
Do not silently expand scope to "fix" it, and do not silently pretend the
premise held.

## What went right

The RED-first discipline paid twice. Both witness tests were written and
committed failing before a single deletion — and both immediately exposed
surfaces the FRs had missed. FR-909's witness caught `.importlinter`, whose
`a2a-seam` contract named a module about to stop existing (`lint-imports`
fails hard on that, not soft). FR-910's witness caught the `is_this_a_graph`
Scripture clause and, through `vulture`, the orphaned discovery API.

Neither FR listed `.importlinter`. Neither judgement did either. The test found
them because a witness that asserts *absence over a named surface list* is a
search, not just an assertion.

## Seed

Both retirements were only discoverable as safe because someone had recorded
that nothing consumed them — the operator's memory, plus a diary entry
(`builders_never_call`) that predated the breakage. The registry itself knows
who *declares* a capability but not who *calls* it.

**What would it take for the capability registry to carry a consumer count?**
Not a hand-maintained field — a derived one: for each CAP, the set of live
non-test importers of its declared modules, computed the way
`direct_import_scan.py` already walks imports. A CAP whose modules have zero
production consumers for N days is a retirement candidate that proposes
*itself*, and `growth_as_default` loses its favourite hiding place: the claim
nobody ever checks.
