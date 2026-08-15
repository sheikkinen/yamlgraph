# Reflection: FR-783 and Its Subsequent Sequence

## Status Recap

| FR | Repository truth | Disposition |
|---|---|---|
| FR-784 | Proposed; judged `APPROVED WITH REVISIONS`, but revisions are not folded and no `network-sniff.js` or manifest exists | Authority inactive; blocks FR-789 |
| FR-785 | Merged as enforced; endpoint-probe graph, manifest, tests, capability, changelog, and diary exist | Delivered but not end-to-end runnable; FR-794 records a remaining prompt-schema defect assigned to an unfiled FR-795 |
| FR-786 | Merged as enforced; page-analysis graph, fixtures, tests, capability, changelog, and diary exist | Delivered |
| FR-787 | Proposed; judged `APPROVED WITH REVISIONS`, but revisions are not folded and no recon graph or manifest exists | Authority inactive; optional for orchestrator v1 |
| FR-788 | Merged as enforced; platform-confirm graph, manifest, tests, capability, changelog, and diary exist | Delivered |
| FR-789 | Proposed; judged `APPROVED WITH REVISIONS`, but revisions are not folded and no browser-sniff graph exists | Authority inactive; blocked by FR-784 and optional for orchestrator v1 |
| FR-790 | Proposed; judged `APPROVED WITH REVISIONS`, but revisions are not folded and no schema-extract graph or manifest exists | Authority inactive; blocks FR-791 |
| FR-791 | Proposed; judged `APPROVED WITH REVISIONS`, but revisions are not folded and no orchestrator graph exists | Authority inactive; blocked by FR-790 and FR-785's unresolved prompt-schema defect |
| FR-792 | Proposed; judged `APPROVED WITH REVISIONS`; revisions are not folded and the required complete source instance does not exist | Authority inactive; correctly blocked by FR-791 |
| FR-793 | RED and GREEN commits are on `main`; 27 hook tests and supporting docs exist | Delivered; FR status text is stale because it still says human review is pending before merge |
| FR-794 | Merged as enforced; manifest-root confinement fix, regression tests, capability, changelog, and diary exist | Delivered; exposed rather than closed FR-785's independent prompt-schema defect |

The API-discovery sequence itself is therefore 4 of 10 FRs delivered
(FR-783, FR-785, FR-786, FR-788), with FR-794 as a necessary framework
repair discovered by composition. The next dependency-respecting order is:
file and enforce FR-795, enforce FR-790, then FR-791. FR-784/FR-789 and
FR-787 remain optional branches. FR-792 must remain last because it extracts
a pattern whose complete source instance does not yet exist.

## Trap: Component Green Mistaken for System Green

FR-783 proved each leaf tool against local fixtures. FR-785 then proved its
graph artifact and narrow tests. Both could be individually green while the
real cross-directory manifest path failed at composition time. FR-794 fixed
that boundary, after which the next full-compile attempt exposed a second
defect in FR-785's prompt schema. Each component had evidence, but the policy
connecting manifest, consumer graph, prompt, and compiler had no witness.

This is `composition_bug` in its cleanest form: unit evidence established
local contracts, while status language implied an operational contract that
had not been exercised. “Enforced” became ambiguous between “its acceptance
tests pass” and “its first consumer can run it.” The first consumer named in
an FR is not merely planning prose; it should determine the final acceptance
witness.

## Trap: Number Order Hides Dependency Order

The sequence was numbered FR-783 through FR-792, but its executable order is
a DAG. FR-784 is low-priority infrastructure for optional FR-789. FR-787 is
also optional. FR-790, despite its later number, is the immediate blocker for
the high-priority FR-791. Reading the FRs as a queue makes unfinished optional
branches look equally urgent and obscures the critical path.

The right recap unit is not “next FR number.” It is “next unsatisfied gate on
the first runnable consumer.” For this family that gate is the missing FR-795
artifact, then schema extraction, then orchestration.

## Trap: A Split Verdict Without a Durable Successor

FR-794 correctly split the unrelated prompt-schema repair out of framework
scope. However, its FR now cites FR-795 while no FR-795 file exists. The split
preserved scope purity but lost execution continuity. A named successor that
is not represented by an artifact is not tracking; it is deferred memory.

**Heuristic:** a SPLIT verdict is complete only when every required successor
has a durable FR or proposal artifact, and the originating FR links to that
artifact rather than to an unallocated number.

## Insight: Status Must Join Evidence and Consumer Reachability

FR-793 demonstrates the opposite drift: implementation and merge are true,
but its status still says review is pending before merge. FR-785 demonstrates
the more dangerous direction: “Enforced” is true at its scoped test boundary,
but the graph remains unreachable as a working consumer. Recaps must join FR
text with git and executable evidence; no one source is operational truth.

For composed examples, completion should have two explicit axes:

- **Scope delivered:** the FR's frozen acceptance criteria pass.
- **First consumer reachable:** the named first consumer loads and executes
  through the new boundary, or the exact external blocker is durably filed.

This preserves honest local completion without implying that a pipeline is
runnable when only its parts are green.

## Seed

Can the FR finalization gate derive the named first consumer from the FR and
require one composition witness, while allowing an explicit `optional` or
`blocked-by: FR-XXX` disposition that is mechanically checked to reference an
existing artifact?