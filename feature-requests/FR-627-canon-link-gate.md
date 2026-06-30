# Feature Request: Deterministic Canon-Link Gate (no-orphan / no-leak)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-06-30

## Summary

A non-LLM, deterministic pre-commit check that reads typed front-matter across a
canon-first generation workspace and refuses to persist any state that violates
two structural invariants:

- **no-orphan** — every relationship edge declared in a canon node must resolve
  to another authored canon node.
- **no-leak** — every entity a plot beat references must already exist as
  authored canon (canon is authored or post-action grounded, never plot-derived).

The check is `os.walk` + front-matter parse + set membership. No model call.
It exits non-zero with a `file: reason` line per violation, blocking the commit.

## Value Statement

Canon-first authors get drift caught at commit time as a free, reproducible,
blocking failure with an exact file:line cause — instead of as a fluent-but-wrong
contradiction discovered hundreds of tokens later by a human reader.

## Problem

In canon-first generation (the inversion described in
[`docs/plan-fandom-generation.md`](../docs/plan-fandom-generation.md)) the LLM
authors meaning and code authors persistence. The dominant failure mode is
**drift**: the model invents an entity, contradicts the timeline, or lets a plot
fact leak into canon that was never authored. These failures are:

- invisible at the token level — the prose is fluent and plausible;
- detected late — after downstream generation has built on the broken fact;
- compounding — the drifted fact becomes a foundation.

This is the generalized form of the FR-550 lesson
([`FR-550-dm-v2-rollback-world-codex.md`](./FR-550-dm-v2-rollback-world-codex.md)):
canon must be authored or post-action grounded, never derived from plot. That
discipline is currently a principle, not an enforced contract. An LLM judge
cannot enforce it cheaply or reproducibly (it reads fluent prose and passes it);
only a deterministic check over typed front-matter can tell *fluent* from
*consistent*.

This adopts the **Karpathy/Graphiti commit-gate pattern** documented in
[`docs/plan-fandom-generation.md`](../docs/plan-fandom-generation.md) §10–§11:
the LLM proposes, plain code disposes; verification is mechanical and blocking,
not advisory.

## Proposed Solution

A small, dependency-light check (Python leaf tool + thin pre-commit / test entry)
that operates purely on typed front-matter.

### Canon node shape (typed front-matter)

```markdown
---
type: character
id: kaelen
faction: ashguard
relationships:
  - { to: maren, kind: mentor }
possessions: [emberbrand_blade]
---
Kaelen is a disciplined Ashguard captain.
```

### Plot beat shape (references must resolve to canon)

```markdown
---
type: plot_beat
window: age_of_cinders
roster: [kaelen]
references:
  - { character: kaelen, asserts: "wields emberbrand_blade" }
---
Kaelen drew the Emberbrand, its ember guttering.
```

### The gate (sketch)

```python
# yamlgraph/tools/canon_link_gate.py  (Layer 3 leaf tool, no Layer 2 imports)
def check_canon_links(canon_dir: str, draft_dir: str) -> list[str]:
    canon_ids = _collect_ids(canon_dir)          # set[str]
    violations: list[str] = []
    # no-orphan: edge targets inside canon must resolve
    for path, fm in _front_matter(canon_dir):
        for rel in fm.get("relationships", []):
            if rel["to"] not in canon_ids:
                violations.append(f"{path}: orphan edge -> '{rel['to']}'")
    # no-leak: plot references must be authored canon
    for path, fm in _front_matter(draft_dir):
        for ref in fm.get("references", []):
            ent = ref.get("character") or ref.get("item")
            if ent not in canon_ids:
                violations.append(f"{path}: leak -> '{ent}' absent from canon")
    return violations
```

CLI / hook entry exits non-zero when `violations` is non-empty and prints each
line. Failures are typed as a structured result (Pydantic) for programmatic use,
rendered as `file: reason` for humans.

## Acceptance Criteria

- [ ] `check_canon_links(canon_dir, draft_dir)` returns a typed result listing
      every orphan edge and every plot leak with `file` + `reason`.
- [ ] A fixture workspace with one dangling relationship edge and two invented
      plot entities yields exactly three violations (matching the worked example
      in [`docs/plan-fandom-generation.md`](../docs/plan-fandom-generation.md)).
- [ ] A fully-grounded fixture workspace yields zero violations and exit 0.
- [ ] The check makes **no LLM call** and runs in O(changed nodes + neighbors),
      not O(n^2) (scoped/delta linting per §11 of the plan).
- [ ] `test_no_leak` regression test added, modeled on the existing
      [`examples/dungeon_master/tests/test_no_world_codex.py`](../examples/dungeon_master/tests/test_no_world_codex.py).
- [ ] Wired as a blocking entry (pre-commit hook or CI gate), not advisory.
- [ ] Tagged with a `@pytest.mark.req("REQ-YG-XXX")` and a matching capability
      entry (ADR-001 traceability).
- [ ] `docs/plan-fandom-generation.md` updated to reference this FR as the
      realization of the no-leak gate.

## Alternatives Considered

- **LLM-as-judge over drafts** — rejected: expensive per write, non-reproducible,
  and reads fluent prose as correct (the exact failure this gate exists to catch).
- **Advisory lint (warn, don't block)** — rejected: advisory checks get ignored;
  the value is in the refusal (`detection_without_enforcement` trap).
- **Full-repo relint on every commit** — rejected: O(n^2) as canon grows; use
  scoped delta linting over changed nodes + graph neighbors instead.

## Dependencies

- Typed canon node + plot beat front-matter schema. May land alongside or just
  after the persistence primitives in
  [`FR-625-write-data-file-tool.md`](./FR-625-write-data-file-tool.md) /
  [`FR-626-write-data-file-demo.md`](./FR-626-write-data-file-demo.md).
- Conceptual ground truth: world-bible thesis in
  [`FR-552-dm-v2-world-bible.md`](./FR-552-dm-v2-world-bible.md).

## Related

- [`docs/plan-fandom-generation.md`](../docs/plan-fandom-generation.md) — §1 the
  inversion, §4 no-leak constraint, §10 prior art, §11 tooling landscape.
- [`FR-550-dm-v2-rollback-world-codex.md`](./FR-550-dm-v2-rollback-world-codex.md)
  — the canon-derived-from-plot failure this generalizes.
- [`examples/dungeon_master/tests/test_no_world_codex.py`](../examples/dungeon_master/tests/test_no_world_codex.py)
  — model for the regression test.
- Karpathy *LLM Wiki* status-token sweep; Graphiti invalidate-don't-delete
  (external prior art, cited in the plan).
