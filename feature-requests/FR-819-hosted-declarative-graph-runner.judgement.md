# Judgement: FR-819 YAMLGraph Serve — Hosted Declarative Graph Runner

**Verdict:** APPROVED WITH REVISIONS — the hosted declarative runner is a real contrib/reference-deployment boundary; R-1 through R-6 have been folded into the FR, so authority is active within the frozen non-production scope below.

**Reviewed against:** `feature-requests/FR-819-hosted-declarative-graph-runner.md`; `feature-requests/070-gui-web-playground.md`; `feature-requests/FR-246-a2a-server-reference-docs.md`; `feature-requests/FR-766-runpod-provider.md`; `feature-requests/FR-766-runpod-provider.judgement.md`; `reference/a2a-server.md`; `yamlgraph/a2a/server.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/compile/verify_insert.py`; `yamlgraph/compile/node_compiler.py`; `yamlgraph/constants.py`; `ARCHITECTURE.md`; `feature-requests/TEMPLATE.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

**Prior art:** FR-819 is the judged target, not an earlier proposal. FR-263
(Azure OpenAI provider), FR-259 (pipeline inlining fast path),
106-otel-observability, and FR-759 (OTel observability boundary) match only the
generic word "hosted"; none accepts tenant-authored graph bundles, creates an
isolated execution boundary, or reserves and settles prepaid credits.

## What is sound

The problem is real and distinct from rejected GUI work. FR-070 rejected a
human-facing browser playground; FR-819 serves an agent/API consumer and adds
no GUI.

The A2A distinction is sound. The current A2A server exposes trusted,
operator-selected graph paths, emits unauthenticated agent cards, delegates
production authentication to a reverse proxy, and executes discovered graphs
in-process. FR-819 correctly refuses to add hostile tenant ingestion and
metering to that server.

The strategic classification is correct: this belongs under
`projects/hosted_runner/`, not in a framework node or A2A upload path. The
safety boundary necessarily composes restrictive validation, pod isolation,
gateway secret custody, reservation-before-spend, settlement review, and
cleanup. Documentation alone cannot witness that composition.

## Required revisions

### R-1: Use project-local traceability

Keep the implementation under `projects/hosted_runner/` with its own
requirement namespace and checker. Do not add framework `REQ-YG-XXX`
requirements. Continue to run `python scripts/req_coverage.py --strict` to
prove framework coverage is unchanged.

**Folded:** FR Section 7 and AC-15.

### R-2: Validate before graph-loader side effects

Canonicalize and confine the bundle, parse raw YAML in memory, schema-check
without imports or filesystem reads, and apply the hosted profile before
materialization or normal graph loading. Name exact allowed node types and
permit `verify` only when service-inserted from supported top-level rules.

**Folded:** FR Section 2, AC-02, and AC-02a.

### R-3: Separate policy and infrastructure isolation witnesses

Use hosted-profile rejection tests for forbidden tenant requests and a fixed,
service-owned diagnostic Job for network, cluster, storage, and gateway
isolation. Tenant YAML cannot provide the diagnostic executable.

**Folded:** FR Section 3, AC-09, and AC-09a.

### R-4: Define pricing and ledger mechanics

Define integer catalog prices, rounding, token ceilings, per-call reservation,
streaming cutoff, cancellation, run states, ledger entry types, and idempotent
terminal settlement so overspend claims are mechanically testable.

**Folded:** FR Section 4, AC-06, and AC-11.

### R-5: State tenant-content retention explicitly

Resolve the distinction between ephemeral pod content and persisted bundle,
input, output, event, receipt, ledger, log, and diagnostic records with a
retention matrix.

**Folded:** FR Section 5 and AC-16.

### R-6: Gate exposure and spend on human approval

Keep enforcement local/invitation-only, configure an operator spend ceiling,
and forbid public exposure, external tenants, real-money payments, SLA claims,
production launch, or spend above the ceiling without a separate
human-approved FR.

**Folded:** FR Section 6, AC-17, and Questions For The Human.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `projects/hosted_runner/` FastAPI control plane with Pydantic models for graph upload, run start/status, and SSE events. |
| D-2 | Bundle canonicalizer/materializer with path, type, count, and size confinement plus stable SHA-256 IDs. |
| D-3 | Fail-closed hosted-profile validator with stable reason codes and the R-2 parse boundary. |
| D-4 | Pod-per-run scheduler, fixed Job/NetworkPolicy, cleanup, and service-owned model gateway with scoped tokens. |
| D-5 | Integer credit ledger, idempotency, reservation, cancellation, settlement, and `settlement_review`. |
| D-6 | Tenant-scoped run/event/receipt storage and SSE redaction. |
| D-7 | Local `kind` witness, service-owned isolation probe, project traceability, tests, docs, and FR status record. |

Not authorized: GUI/editor work; A2A or MCP changes; upload handling in
`yamlgraph a2a serve`; arbitrary Python, shell, package, or tool execution;
tenant pod specs, provider URLs/keys, uncatalogued models, or network targets;
public signup; payments; cash-valued, refundable, or transferable credits;
multiple regions/providers; durable sessions; custom domains; SLA or
production-readiness claims; external tenant/production launch; core framework
primitives without a separate FR.

## Revised acceptance criteria

- [ ] AC-01: Valid canonical bundle content produces a stable tenant-scoped SHA-256 graph ID.
- [ ] AC-02: Bundle validation rejects absolute paths, traversal, duplicate canonical paths, symlinks, binary payloads, and configured count/size limits without escaping tenant storage.
- [ ] AC-03: Hosted-profile validation follows the safe raw-YAML boundary and rejects every forbidden class before normal loading, reservation, or scheduling.
- [ ] AC-04: `verify` is accepted only when service-inserted from supported top-level rules; tenant-authored `__verify__` fails closed.
- [ ] AC-05: Tenant B receives `404` for tenant A's graph, run, event, and receipt IDs.
- [ ] AC-06: Run start requires tenant auth, graph ID, typed inputs, catalog model, positive integer ceiling, and idempotency key; invalid requests create no reservation or Job.
- [ ] AC-07: A valid run reserves credits atomically before Job creation; insufficient balance creates neither.
- [ ] AC-08: Twenty concurrent identical idempotency keys converge on one run, Job, reservation, settlement, debit, and release.
- [ ] AC-09: Gateway tokens fail when expired, canceled, model/run-mismatched, or beyond the credit ceiling; provider credentials never enter run-pod artifacts.
- [ ] AC-10: Generated Job manifests satisfy every fixed pod restriction and contain no tenant-controlled pod field.
- [ ] AC-11: Policy tests reject tenant requests for network, path, code, subprocess, tool, MCP, A2A, provider, or unsupported-model capability.
- [ ] AC-12: The service diagnostic Job proves denied cluster/DNS/API, metadata, internet, cross-run storage, and control-plane access while gateway access succeeds.
- [ ] AC-13: CPU, memory, storage, deadline, map, retry, and credit ceilings each terminate boundedly and clean up Job/volume state.
- [ ] AC-14: Successful settlement records provider request ID, token counts, reservation, debit, and release using the frozen integer algorithm.
- [ ] AC-15: Missing or contradictory usage enters `settlement_review`, preserves the reservation, alerts the operator, and fabricates nothing.
- [ ] AC-16: Events and receipts expose typed output/status/usage only and redact every API/gateway/provider secret, header, and foreign-tenant value.
- [ ] AC-17: The local `kind` witness uploads, funds, runs, streams, verifies output/receipt, and confirms Job/volume deletion.
- [ ] AC-18: Project-local requirements cover hosted-runner tests, its checker passes, and framework strict requirement coverage remains green.
- [ ] AC-19: Documentation states profile, pricing/rounding, isolation, retention, invitation status, operator ceiling, and deferred commercial concerns without claiming arbitrary-code safety.
- [ ] AC-20: The FR records implementation status, validation commands, blocked witnesses, and deviations from frozen scope.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-6 remain folded into the FR. | GATE |
| C-2 | Keep implementation in `projects/hosted_runner/`; add no core node or A2A/MCP upload path. | GATE |
| C-3 | Perform no graph loading, expansion, filesystem loading, tool parsing, import, reservation, or scheduling before bundle/profile validation. | GATE |
| C-4 | Provider/gateway credentials remain control-plane-only and never enter pod, event, receipt, or log content. | GATE |
| C-5 | Do not claim isolation from hosted YAML tests alone; the service diagnostic Job is mandatory. | GATE |
| C-6 | Never debit estimated or silent zero usage; irreconcilable usage enters `settlement_review`. | GATE |
| C-7 | No production/public launch, external tenant, payment, SLA, or provider spend above the operator ceiling is authorized. | GATE |

Authority granted: build the non-production `projects/hosted_runner/`
reference deployment that accepts declarative hosted-profile bundles, runs
them in isolated quota-bound Jobs through a service-owned model gateway, and
proves tenant isolation, streaming, cleanup, and prepaid-credit settlement.

## Amendment A-1 (2026-08-18, operator decision)

Platform substitution: Kubernetes pod-per-run → Fly Machines machine-per-run.
The operator runs an existing Fly.io fleet (daily_digest, openai_proxy,
booking, ninchat_voice) and operates no Kubernetes cluster; the human selected
this substitution in session on 2026-08-18. Read the frozen scope with this
mapping:

- D-4 "fixed Job/NetworkPolicy" → fixed Machines API config (no public IP, no
  Fly API token, `autodestroy`) plus in-image nftables default-deny egress
  with a 6PN-only gateway route.
- C-5 / AC-12 "service diagnostic Job" → service-owned diagnostic machine
  booted with the identical run-machine configuration; it remains a GATE and
  is now the load-bearing isolation proof, since egress deny moves from
  platform policy into the service-owned image.
- `activeDeadlineSeconds` → machine-local timeout plus control-plane deadline
  watchdog, both mandatory.
- AC-17 local `kind` witness → local docker-compose functional harness plus
  isolation witness on a dedicated non-production Fly runner app within the
  operator ceiling (C-7 unchanged).

Amendment A-2 (same date): catalog entries carry `catalog_version`;
`run_reserve` stamps it and receipts cite it (extends D-5/AC-14 semantics) to
keep settlement reconcilable against the price authorized — prerequisite for
the deferred payments FR. Amendment A-3: the 24-hour output retention is a
documented deliberate MVP limit. All other gates, deliverables, and the
not-authorized list are unchanged; payments remain forbidden under C-7.
