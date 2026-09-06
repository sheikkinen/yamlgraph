---
type: removal
scope: fr
---
- **FR-1015 Supersede FR-975 / FR-980 under FR-1010**: the unimplemented CAP/REQ ID-ledger program (FR-975 remote-ref compare-and-swap reservation, FR-980 mandatory route enforcement — judged 2026-09-03, never enforced: no CAP entry, code, test, hook, workflow or pre-commit entry cites either) is retired by the operator decision recorded in FR-1010 § "ID-allocation decision (R-2)": both FRs now read `Superseded by FR-1010 (2026-09-06)` and carry a `## Superseded` block quoting FR-1010's replacement contract verbatim (mechanical enumeration at filing, `max(ids on main + all open PR heads) + headroom`; FR-701's `validate_registry()` stays the post-hoc duplicate gate; no new allocator). FR-970, the SPLIT parent, is unchanged. The legacy registry artifacts themselves are not deleted here — that is FR-1012's census-governed Phase 2. Phase 1½ of FR-1010.
