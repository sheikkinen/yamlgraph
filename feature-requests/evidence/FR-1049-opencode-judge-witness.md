# FR-1049 opencode judge — live witness

**Prior art:** `FR-960-claude-judge-witness.md` — the structural template (the
Claude-judge witness: authoring proof, dual-run claim inventory, human
signatures); this file is the opencode-judge analogue. `FR-1048-opencode-backend-witness.md`
and `FR-1048-opencode-cli-probe.md` — the backend's own witness and probe (this
file consumes them, does not duplicate them). `FR-1049-opencode-judge-write-probe.md`
— the load-bearing write-mechanism probe this witness completes with a real
judge run. None is a duplicate: no prior record proves the opencode judge route
writes a draft verdict end-to-end.

## 1. Authoring proof (C-3 / AC-03)

- Command: `scripts/author.sh feature-requests/authoring-briefs/fr-1049-opencode-judge-variant-brief.md`
  (sole route; pre-flight green).
- Brief: `feature-requests/authoring-briefs/fr-1049-opencode-judge-variant-brief.md`
  (deliverable D-1).
- Local authoring report (not committed, per graph-authoring SKILL):
  `tmp/draft-authoring-report.md`, sha256
  `d9e5739a1d5a8da9d12de0c5c4b4c0d017ad276d6b745823cf6b80a41c706e99`.
- Report headings present: `Artifacts`, `Precedent`, `Validation`, `Repairs`,
  `Blocked validation` — quoted essentials:
  - Artifacts: "`.github/skills/judge-fr/adapters/graph.yaml` — modified the
    existing adapter graph only."
  - Validation: lint passed (0 issues); validate passed (4 nodes, 7 edges);
    FR-1049 `TestGraphRouting` passed (4 passed); FR-931 passed (3 passed);
    FR-960 failed at authoring time on the stale "exactly two copilot nodes"
    assertion, which the enforcer then updated to three (closed-set count,
    FR-1048 AC-15 pattern) — FR-960 now green.
- Graph commit SHA: `241445e28bf4f88dd63cb366554f016edb73a58b`.
- The report is **not** committed; only its digest and quoted sections are
  recorded here.

## 2. Live runs (AC-11 / AC-12)

Target FR: `feature-requests/FR-1049-opencode-judge-variant.md`, commit
`241445e28bf4f88dd63cb366554f016edb73a58b`, on one comparison host holding
both the `deepseek` provider key and a working Copilot entitlement.

### 2.1 opencode run (AC-11)

| Field | Value |
|---|---|
| Command | `JUDGE_BACKEND=opencode scripts/judge.sh feature-requests/FR-1049-opencode-judge-variant.md` |
| Backend | `opencode` |
| CLI version (FR-1048 preflight) | `1.18.31` |
| Model argv | `--model deepseek/deepseek-v4-pro` |
| Start / end (UTC) | 2026-09-16 03:24:17Z / 03:27:13Z |
| Artifact | `tmp/draft-judgement-opencode-FR-1049-opencode-judge-variant.md`, sha256 `a9e198a096b0426f40271f6240b2d90d4a475a60d75b91bec6cdb1973aba94e4` |
| Verdict | `**Verdict:** APPROVED — …` |
| Permission/config | workspace-local `write` succeeded under the default configuration (no `--auto`, no permission flag); no denying config exercised |
| session_id | `ses_f57c18db6ffeQTIQwQjWTjx07E` |

### 2.2 Copilot run (AC-12)

| Field | Value |
|---|---|
| Command | `scripts/judge.sh feature-requests/FR-1049-opencode-judge-variant.md` (default backend) |
| Backend | `copilot` (`backend: cli`) |
| Model | `gpt-5.6-sol` |
| Start / end (UTC) | 2026-09-16 ~03:28Z |
| Artifact | `tmp/draft-judgement-copilot-FR-1049-opencode-judge-variant.md`, sha256 `7ffc58e3b363770c4ce01bbb58529c20e3b593644be793f8ca07072ecc976d77` |
| Verdict | `**Verdict:** APPROVED — …` |
| session_id | `178e9f19-810f-4da0-b751-bcca51218843` |

Both artifacts coexist with distinct hashes. Two live judge runs total (AC-12).

## 3. Dual-run claim inventory (AC-13)

Stable IDs: `CP-n` (Copilot draft), `OC-n` (opencode draft).

| ID | Claim | Disposition |
|---|---|---|
| OC-1 / CP-1 | Verdict APPROVED (no required revisions) | matched |
| OC-2 / CP-2 | Strategic classification contrib/example (one named consumer, existing abstractions) | matched |
| OC-3 / CP-3 | H-1 folded: `deepseek/deepseek-v4-pro`, Sami Heikkinen, 2026-09-16, used consistently | matched |
| OC-4 / CP-4 | Routing correction required: first-match router + former `!= "claude"` catch-all = third-value misroute | matched |
| OC-5 / CP-5 | Permission boundary precise: `--auto` exists but unmapped; workspace-local `write` under probed default; deny → artifact contract | matched |
| OC-6 / CP-6 | Frozen scope D-1..D-8 and the not-authorized list (no runtime/flag/permission/`--auto`/server-route/4th-backend changes) | matched |
| OC-7 / CP-7 | Revised AC-01..AC-16 and conditions C-1..C-10 (model frozen, kill criterion literal, two human approvals) | matched |
| OC-8 | "Reviewed against" cites `tests/unit/test_fr1049_opencode_judge_variant.py`, `tests/unit/test_fr960_claude_judge_variant.py`, `tests/unit/test_fr758_judge_review_wrappers.py`, `capabilities/CAP-211-…`, `ramp/manifest.yaml`, `ramp/…/SKILL.md`, `yamlgraph/models/node_schema.py`, `yamlgraph/node_factory/copilot_node.py`, `yamlgraph/node_factory/copilot_runtime_opencode.py` | backend-only (input-closure set is wider on the code surface) |
| CP-8 | "Reviewed against" cites `FR-1049-opencode-judge-variant.judgement.md` "round-history evidence only, not inherited authority" | backend-only (the Copilot judge read the prior judgement and flagged it; the opencode judge did not cite it) |

No substantive claim is `contradicted`. The two `backend-only` rows are input-
closure/citation-granularity variance, not disagreements on the verdict,
scope, or gates.

## 4. Human approvals (AC-14)

Two separate dated approvals by humans other than the enforcer, required
before the opencode route is operational or this FR is marked Implemented:

1. **Enforcement-infrastructure diff and route invariants** accepted by
   `<name>`, `<date>`: *PENDING.*
2. **Residual opencode provider-key payer boundary (FR-1048 §5)** accepted for
   judge execution by `<name>` (spend owner), `<date>`: *PENDING.*

## 5. Limitations

- One opencode judge run, one host, pinned `1.18.31`, one model
  (`deepseek/deepseek-v4-pro`). Widening the supported-version set needs a new
  capture (FR-1048 discipline).
- The workspace-local `write` auto-approval was exercised under the default
  configuration; a configuration that denies `write` was not exercised (the
  write-probe and this run both succeeded on the default). That denial path is
  the kill criterion's surface, covered by AC-16, not by this witness.
- The dual-run inventory is over the two draft judgements; the raw drafts are
  `tmp/draft-judgement-{opencode,copilot}-FR-1049-opencode-judge-variant.md`
  (local, advisory), not committed.
- The `deepseek` provider bills two live turns (the opencode judge run).
