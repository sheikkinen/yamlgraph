## 2026-05-19: Inquisitor Audit — Direct-push escalation, noqa gap, mixed-commit entropy

**Context:** Audited the 5 most recent commits on `main` (8a731d71..27795d03, 2026-05-19) against the Scripture. This is the fifth same-day audit (235–238 preceded). Prior audits flagged direct pushes and mixed commits; this audit checks whether the pattern has stabilized or worsened.

**Findings:**

1. ✗ **VIOLATION — WIP commit on main with mixed concerns (27795d03):** `chore: investigation of chaplain failures, wip` bundles FR-420 production code + tests, FR-415 feature request, two inquisitor audit diaries, inbox cleanup, and module-map update into a single commit. Commandment 8: "split modules before they bloat" extends to commits — mixed commits erode auditability. The WIP label violates the Submit rite ("Let CI judge. What survives the fire may merge."). Four of five audited commits bypassed branch protection entirely; only FR-418 (71c89093) went through a PR.

2. ✗ **VIOLATION — noqa S105 without CONF-XXX (scripts/hedging_check.py):** `OK = "\033[32mPASS\033[0m"  # noqa: S105` was added in the FR-420 diff. The inline comment explains intent ("ANSI colour label, not a credential") but the noqa Confessions rule requires a registered CONF-XXX entry in `docs/confessions.md`. The suppression is in script code → CONF-2XX range.

3. ⚠ **DRIFT — req frontmatter absent on fix changelogs:** FR-416 (both fragments), FR-419, and FR-420 changelog fragments omit `req:` in YAML front matter despite their tests referencing REQ-YG-319. The `changelog-req-gate` CI job validates `req:` when present but does not enforce presence for `fix` type fragments. Three consecutive audits (236–238) have flagged this drift. It is now a systemic gap in the gate, not an individual omission.

4. ⚠ **DRIFT — No diary reflection for FR-416:** Two FR-416 commits (8a731d71, 17da4033) modified production FSM code involving non-trivial debugging (event key mismatch, legacy config forwarding) without a corresponding reflection. The `diary-gate` would have caught this had the commits gone through PR. FR-419 does have a diary entry (2026-05-19-fr419-action-config-schema-boundary.md).

5. ✓ **COMPLIANT — FR-418 remains the standard (71c89093):** Conventional Commits with PR `(#419)`. Changelog fragment with `req: REQ-YG-408`. Tests tagged `@pytest.mark.req("REQ-YG-408")`. Diary with `Seed:` marker. Full doctrine compliance. This is the only commit in the batch that passed through all gates.

**Heuristic:** Four audits flagging the same direct-push pattern without remediation is the `audit_as_ritual` trap incarnate: "3+ audits without fix → ritual, not process." The Inquisitor can diagnose, but cannot enforce. Until a post-push detection mechanism converts bypasses into blocking debt (e.g., a `main` branch webhook that opens auto-issues for commits without PR references), the audit cycle will continue producing observations that decay into noise.

**Seed:** Should the Inquisitor emit a machine-readable `audit-debt.yaml` manifest alongside prose findings — enabling a CI pre-release gate that blocks version bumps when unresolved violations exceed a threshold?
