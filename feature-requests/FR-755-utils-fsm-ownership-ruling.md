# Feature Request: FR-755 Decide `yamlgraph.utils.fsm` Ownership — Framework Capability or Chaplain Infrastructure

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced (2026-07-21)
**Effort:** 1 day (documentation + enforcement; relocation explicitly out of scope)
**Requested:** 2026-07-21
**Prior art:** FR-757 (follow-up relocation filed by this FR — downstream, not overlap); FR-756 (sibling in the same boundary arc — consumes this ruling for test classification, no scope overlap); FR-723 (execution-path visualization — noun collision on `utils`/`ruling` only, unrelated domain); 107-router-route-field and FR-473 (noun collision on `ruling` only, unrelated domains).
**First consumer / first event:** the next agent or contributor who must modify `utils/fsm` and cannot determine from the package layout whether it is public framework API or internal process plumbing; first event is the next FR that touches the FSM bridge.

## Summary

`yamlgraph/utils/fsm/` (915 lines: `action.py`, `event_sender.py`, `graph_runner.py`, `helpers.py`, `snapshot.py`, `ui_log.py`) ships in the wheel as a general FSM bridge, but its consumer inventory is entirely process-side:

- `.chaplain/` runtime (primary consumer: `YamlgraphAsyncAction`, `send_event`, `run_legacy_yamlgraph_async`)
- `examples/fsm-router/`, `examples/demos/hook_classifier/`
- `scripts/hedging_check.py`

No module inside `yamlgraph/` (outside `utils/fsm` itself) imports it. It is registered as a capability (CAP-141 shared-fsm-bridge-module, CAP-146 snapshot hooks), yet a "YAML **graph** framework" shipping an FSM runtime with zero in-package consumers is an unresolved identity question — the `framework_costume` trap in reverse: chaplain infrastructure wearing a framework costume.

## Value Statement

Every future change to the FSM bridge is judged against an explicit ownership contract instead of an implicit one, eliminating the recurring "is this public API?" ambiguity for the densest incident-per-line module in the codebase (915 lines, ~116 diary entries — highest knowledge-to-code ratio on record, per Scripture `incident_density_ranking`).

## Problem

1. **Ambiguous contract:** CAP-141 registers the module as a shared bridge, but "shared between whom" is undefined. Consumers are the chaplain and two examples; external users installing the wheel receive an FSM runtime that no documentation positions as public API.
2. **Split-risk concentration:** in any future repo or package reorganization, `utils/fsm` is simultaneously the strongest candidate for extraction (no in-package consumers) and the riskiest module to move (highest incident density). This tension must be resolved by decision, not by accident during an unrelated refactor.
3. **Judgement precedent gap:** without an ownership ruling, each FSM-touching FR re-litigates scope. The 2026-05-31 asset inventory already misclassified `utils/fsm` as Tier 4 by line-count proxy (`inventory_by_visibility` trap).

## Ideal Result

A one-paragraph ownership ruling exists in `ARCHITECTURE.md`, CAP-141 states it, and the package layout matches it. A newcomer can answer "may my application import `yamlgraph.utils.fsm`?" from the docs in under a minute, and the answer is enforced (import-linter contract or explicit public-API listing), not advisory.

## Ruling (2026-07-21, operator)

**Position C — contrib tier.** Operator rationale, verbatim: *"repeating pattern, but not yamlgraph core."*

Interpretation: the FSM bridge is a genuinely recurring pattern (chaplain, `examples/fsm-router`, hook classifier, sibling projects) and therefore worth shipping and supporting — but it is not part of the YAML-graph framework identity. It belongs under `yamlgraph/contrib/` semantics: stable-but-peripheral, supported for reuse, excluded from the core API surface and core test claim.

**Forced opposite (strongest case against C):** the module's incident density (915 lines, ~116 diary entries) is the profile of *core* knowledge, not periphery — demoting it to contrib risks under-investing in the codebase's most expensively-learned boundary, and position A would have forced the documentation its reuse across three consumers arguably deserves. Rejected because incident density measures learning cost, not framework identity: every incident in the record is a process-runtime incident (chaplain, watcher, hooks), none is a graph-pipeline incident. The pattern repeats across process tooling, not across YAML-graph applications.

## Proposed Solution

Ruling is granted; remaining work is documentation + enforcement. Relocation to `yamlgraph/contrib/fsm/` becomes a follow-up FR (high-risk move per incident density; must not ride along with this FR).

1. **Inventory (mechanical):** enumerate every import of `yamlgraph.utils.fsm` across yamlgraph, `.chaplain/`, `examples/`, `scripts/`, sibling projects (`ninchat_voice`, `statemachine-engine`). Include diary-entry density per consumer. This is the migration map for the follow-up relocation FR.
2. **Document:** amend `ARCHITECTURE.md` and CAP-141 to state: contrib tier — supported repeating pattern, not core framework API.
3. **Enforce:** import-linter contract forbidding `yamlgraph` core modules (outside contrib) from importing `yamlgraph.utils.fsm` — freezing the current zero-in-package-consumer state so core can never silently grow a dependency on it.
4. **File follow-up FR:** relocation `yamlgraph/utils/fsm/` → `yamlgraph/contrib/fsm/` with effort estimate and consumer migration list. No shim, no re-export (Commandment 8) — the follow-up FR judges timing against `one_session_one_repo` risk.

## Acceptance Criteria

- [x] Consumer inventory table in this FR with import counts and diary density per consumer (raw grep output cited — `read_raw_output_first`)
- [x] Explicit ruling (C) recorded with rationale and the forced-opposite counter-case (operator, 2026-07-21)
- [x] `ARCHITECTURE.md` and `capabilities/CAP-141-shared-fsm-bridge-module.yaml` updated to state contrib-tier ownership
- [x] Import-linter contract added: core (non-contrib) modules must not import `yamlgraph.utils.fsm`; `lint-imports` passes (`detection_without_enforcement`)
- [x] Follow-up relocation FR (`utils/fsm` → `contrib/fsm`) filed with effort estimate and consumer migration list; no relocation in this FR
- [x] Diary entry

## Consumer Inventory (2026-07-21)

Raw command output (mechanical):

```bash
yamlgraph:0
.chaplain:3
examples:17
scripts:0
tests:40
../ninchat_voice:missing
../statemachine-engine:0
```

Source command:

```bash
for d in yamlgraph .chaplain examples scripts tests; do
	c=$(rg -n "yamlgraph\.utils\.fsm" "$d" --glob '*.py' 2>/dev/null | wc -l | tr -d ' ')
	echo "$d:$c"
done
for d in ../ninchat_voice ../statemachine-engine; do
	if [ -d "$d" ]; then
		c=$(rg -n "yamlgraph\.utils\.fsm" "$d" --glob '*.py' 2>/dev/null | wc -l | tr -d ' ')
		echo "$d:$c"
	else
		echo "$d:missing"
	fi
done
```

Inventory table:

| Consumer surface | Import hits | Diary density signal |
|---|---:|---|
| `yamlgraph/` core (outside `utils/fsm`) | 0 | Confirms ruling-C boundary: core has no direct dependency.
| `.chaplain/` | 3 | High: watcher/chaplain incident stream dominates FSM learning history.
| `examples/` | 17 | Medium: recurring demo/integration reuse (`fsm-router`, hook classifier).
| `tests/` | 40 | High test coupling; remains process-classified under FR-756 when crossing repo/process boundaries.
| `scripts/` | 0 | No direct imports in current tree.
| `../statemachine-engine` | 0 | No direct import in available sibling checkout.
| `../ninchat_voice` | missing | Checkout not present in this workspace; unresolved until that sibling is scanned in-place.

The module-level incident density from Scripture remains the anchor: ~116 diary entries over ~915 lines (`incident_density_ranking`).

## Alternatives Considered

- **Decide implicitly during a repo split:** rejected — the monorepo-split review (2026-07-21) concluded no split; this question survives that verdict and deserves standalone judgement.
- **Extract immediately without a decision FR:** violates `investigation_before_fix`; the module's incident density makes an unruled move the highest-risk refactor available in this codebase.

## Related

- Discovered during monorepo-split critical review (2026-07-21)
- CAP-141, CAP-146, CAP-74
- Scripture: `incident_density_ranking`, `framework_costume`, `inventory_by_visibility`, `forced_opposite`
- Diary 2026-05-31 (asset inventory misclassification)
- FR-756 (core test isolation — FSM test classification depends on this ruling)
