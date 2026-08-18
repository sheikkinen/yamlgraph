# Feature Request: FR-815 YAMLGraph Serve — Hosted Declarative Graph Runner

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 8–12 days
**Requested:** 2026-08-18
**First consumer / first event:** a YAMLGraph author who has a graph and
prompts but no deployment, at the moment they submit that bundle with input
variables and a maximum credit spend to receive a streamed result from an
isolated hosted run.

**Prior art:** FR-070 (`yamlgraph serve` web playground) was rejected because
it added a human-facing visual editor; this FR has no GUI and serves an
agent/API consumer. FR-208/FR-246 (`yamlgraph a2a serve`) expose trusted,
operator-installed graphs and explicitly delegate authentication to a reverse
proxy; they do not accept tenant-authored bundles, isolate runs, or meter
spend. FR-766 adds RunPod as an LLM provider; it does not host YAMLGraph graph
execution. These are adjacent mechanisms, not substitutes.

## Summary

Build a deployable reference service, branded **YAMLGraph Serve**, that accepts
an immutable declarative graph bundle, validates it against a restrictive
hosted profile, and executes each run in a fresh quota-bound Kubernetes pod.
Before scheduling, the service atomically reserves the caller's declared
maximum spend from a manually funded prepaid-credit ledger. It streams run
events, terminates at the budget/deadline boundary, and settles actual usage
against the reservation.

"Your own graph" means a tenant-supplied `graph.yaml` plus prompt YAML and
declared input data that pass the hosted profile. It does **not** mean arbitrary
Python, shell commands, uploaded packages, Copilot nodes, executable tools, or
arbitrary network access.

## Value Statement

Graph authors can execute and share their own YAMLGraph pipelines through an
agent-friendly API without operating YAMLGraph, Kubernetes, or provider
credentials, while prepaid reservation gives both the author and operator a
hard spend boundary.

## Problem

YAMLGraph can run a local graph and can expose preinstalled graphs over A2A,
but it has no trust boundary for a graph supplied by a remote tenant. Running
uploaded YAML in the existing long-lived server process would allow graph
features to reach local files, imported Python, tools, provider credentials,
and network services. The current A2A server also has no built-in
authentication or tenant accounting (`reference/a2a-server.md`).

Prepaid credits alone do not make arbitrary execution safe. A public runner
must answer four coupled questions before it can schedule a job:

1. Is the submitted bundle data-only and confined to an explicit hosted
   profile?
2. Can one tenant's run observe or affect another tenant, the control plane,
   provider credentials, or the cluster?
3. Can concurrent retries spend more than the caller authorized?
4. Can charged usage be reconciled to provider-reported usage and an
   append-only ledger?

## Ideal Result

An authenticated client uploads a portable declarative bundle once, receives
its content-addressed graph ID, and starts any run with inputs, model choice,
and `max_credits`. The API either rejects the request before spend or reserves
that ceiling exactly once, starts a fresh isolated pod, streams typed events,
and returns a terminal receipt containing reserved, consumed, and released
credits plus provider usage. No tenant content or provider secret survives the
pod, no duplicate request can double-charge, and no run can exceed its
reserved balance.

## Proposed Solution

Implement this as a reference deployment under `projects/hosted_runner/`, not
as a new core node type and not by adding upload handling to the existing A2A
server.

### 1. Typed control-plane API

Add a FastAPI service with Pydantic request/response models:

- `POST /v1/graphs` accepts JSON containing `graph_yaml`, a
  `prompts: {relative_path: yaml_text}` mapping, and optional bounded data
  files. It rejects duplicate paths, absolute paths, `..`, symlinks, binary
  data, and requests over configured file/count/byte limits. The immutable ID
  is a SHA-256 digest of canonical bundle content.
- `POST /v1/runs` accepts `graph_id`, typed `inputs`, a service-catalog
  `model`, and positive integer `max_credits`. An `Idempotency-Key` is
  mandatory.
- `GET /v1/runs/{run_id}` returns status and the terminal receipt.
- `GET /v1/runs/{run_id}/events` streams typed SSE events without exposing
  prompts, secrets, provider response headers, or another tenant's run.

API tokens map to one tenant. Every graph/run lookup is tenant-scoped.

### 2. Hosted graph profile

After normal YAMLGraph schema/lint validation, a second fail-closed validator
walks the parsed `GraphConfig` and permits only an enumerated data-only node
and configuration subset. The initial allowlist is `llm`, `router`, `map`,
`passthrough`, and declarative verification nodes whose execution path neither
imports tenant code nor invokes tools. The validator rejects at minimum:

- `python`, `shell`, `copilot`, `agent`, `tool_call`, MCP, A2A-call, and any
  node or tool configuration outside the allowlist;
- custom import/module/function paths, subprocess configuration, local
  checkpointers, host paths, path-bearing prompt/data references outside the
  materialized bundle, and environment-variable interpolation;
- tenant-supplied provider base URLs, provider keys, model identifiers outside
  the service catalog, and graph-level settings not explicitly supported;
- cycles, maps, retries, or timeouts whose statically declared ceilings exceed
  the service limits.

Unknown present or future graph fields fail validation; they are never ignored
or silently stripped. Validation emits stable machine-readable reason codes.

### 3. Pod-per-run execution boundary

The scheduler materializes only the validated immutable bundle into a fresh
Kubernetes Job. The pod specification is fixed by the service, not merged from
tenant input: unprivileged UID, read-only root filesystem, dropped Linux
capabilities, `RuntimeDefault` seccomp, no host namespaces or volumes, no
service-account token, bounded CPU/memory/ephemeral storage, and
`activeDeadlineSeconds`. A default-deny NetworkPolicy allows egress only to a
service-owned model gateway and the minimum result/event channel.

Provider credentials remain in the model gateway and are never mounted into
the run pod. The pod receives a short-lived, run-scoped gateway token capped
by model, run ID, deadline, and reserved credits. The gateway rejects calls
after cancellation or exhaustion and records provider-reported token usage.
The Job and writable volume are deleted after terminal receipt persistence.

### 4. Prepaid reservation ledger

Use integer microcredits and an append-only transactional ledger. This FR
supports admin-issued test credits only; purchasing credits, Stripe/payment
integration, refunds to payment instruments, tax/VAT, invoices, and cash
withdrawal are explicitly deferred.

`POST /v1/runs` performs one serializable transaction keyed by tenant and
idempotency key: reject insufficient available balance, otherwise create the
run and reserve `max_credits`. Terminal settlement debits measured usage and
releases the remainder. Duplicate starts and duplicate terminal events return
the original result without creating another reservation or debit. A run with
missing or irreconcilable provider usage fails settlement into an operator
review state; it does not invent zero usage or debit an estimate silently.

### 5. Bounded proof deployment

Provide a local `kind` deployment and an automated end-to-end witness. The
MVP is single-region, invitation-only, and non-production. It supports one
OpenAI-compatible service-owned gateway and a fixed model catalog. It proves
the execution, isolation, and accounting boundaries; it does not claim a
general serverless platform or commercial payment readiness.

## Acceptance Criteria

- [ ] AC-01: `POST /v1/graphs` stores a valid data-only bundle under a stable
      SHA-256 graph ID; byte-identical canonical content returns the same ID.
- [ ] AC-02: Table-driven tests reject every forbidden node/configuration
      class named in the hosted profile with a stable reason code before a Job
      or credit reservation is created.
- [ ] AC-03: Bundle tests reject absolute paths, traversal, duplicate
      canonical paths, symlinks, binary payloads, and configured size/count
      limit violations without writing outside tenant-scoped storage.
- [ ] AC-04: Every graph, run, event, and receipt lookup is tenant-scoped; an
      integration test proves tenant B receives `404` for tenant A's IDs.
- [ ] AC-05: A valid run atomically reserves integer `max_credits` before Job
      creation; insufficient balance creates neither reservation nor Job.
- [ ] AC-06: Twenty concurrent requests with one idempotency key produce one
      run, one Job, one reservation, and one terminal debit.
- [ ] AC-07: The gateway rejects an LLM call whose run token is expired,
      canceled, uses a different model/run ID, or would exceed reserved
      credits; provider credentials are absent from the run pod environment,
      files, and Kubernetes Job manifest.
- [ ] AC-08: The generated Job manifest mechanically satisfies all pod
      restrictions in Section 3 and contains no tenant-controlled pod-spec
      field.
- [ ] AC-09: In the `kind` witness, a malicious hosted-profile fixture cannot
      reach cluster DNS/API, cloud metadata addresses, the public internet,
      another run's writable volume, or a control-plane endpoint; the allowed
      gateway path still succeeds.
- [ ] AC-10: CPU, memory, storage, wall-clock, map, retry, and credit limits
      each have a test proving a terminal bounded failure and Job cleanup.
- [ ] AC-11: Successful settlement records provider request ID, input/output
      token counts, reserved credits, consumed credits, and released credits;
      ledger entries sum to the tenant balance exactly using integer math.
- [ ] AC-12: Missing or contradictory provider usage enters a named
      `settlement_review` state, preserves the reservation, alerts the
      operator, and never records fabricated usage.
- [ ] AC-13: SSE and terminal receipts expose typed status/usage/output only;
      tests prove API tokens, gateway tokens, provider keys, headers, and
      another tenant's content are redacted.
- [ ] AC-14: The end-to-end witness uploads a graph, grants test credits,
      starts it through the API, observes streamed events, verifies its
      output/receipt, and confirms the Job and writable volume are deleted.
- [ ] AC-15: A new capability/requirement pair covers the hosted runner tests;
      `python scripts/req_coverage.py --strict` and the project test suite pass.
- [ ] AC-16: Documentation states the exact hosted profile, pricing unit,
      isolation assumptions, data retention, invitation-only status, and the
      deferred commercial/payment concerns without claiming arbitrary-code
      safety.

## Alternatives Considered

- **Run every YAMLGraph feature in a pod:** rejected. A Kubernetes pod alone
  is not a sufficient hostile-code sandbox, and unrestricted Python/shell/
  tools turn this into a general serverless-compute and abuse-prevention
  product.
- **Add upload endpoints to `yamlgraph a2a serve`:** rejected. That server
  assumes trusted discovered files and delegates auth; mixing tenant bundle
  ingestion and billing into it would weaken both responsibilities.
- **One long-lived worker per tenant:** rejected for the MVP. It leaves
  cross-run state and makes resource/accounting cleanup harder to prove.
- **Bring your own provider key:** deferred. It complicates secret custody,
  pricing, support, and usage reconciliation while weakening the prepaid
  credit proposition.
- **Charge after completion:** rejected. Dynamic maps, retries, cancellation,
  and concurrent requests can overspend; reserve-then-settle is the minimum
  honest boundary.
- **Integrate Stripe in the MVP:** rejected. Payment acquisition, VAT,
  refunds, chargebacks, and stored-value policy are a separate product/legal
  decision. Admin-issued credits are sufficient to prove metering semantics.
- **Documentation-only deployment recipe:** insufficient. The unresolved
  value is the composition of hostile-input validation, pod isolation,
  idempotent reservation, gateway metering, and cleanup; those boundaries need
  executable witnesses.

## Scope And Strategic Classification

This is a **contrib/reference deployment**, not a YAMLGraph framework
primitive. The first consumer is one hosted product and existing core graph
loading is sufficient once guarded by the hosted profile. Any reusable core
primitive discovered during enforcement requires a separate FR with three
consumers.

Not authorized: GUI/editor work; changes to A2A or MCP protocols; arbitrary
code or package execution; public signup; payment processing; cash-valued or
transferable credits; multiple regions/providers; durable multi-turn sessions;
custom domains; SLA claims; production launch.

## Related

- `feature-requests/070-gui-web-playground.md`
- `feature-requests/FR-246-a2a-server-reference-docs.md`
- `feature-requests/FR-766-runpod-provider.md`
- `reference/a2a-server.md`
- `yamlgraph/a2a/server.py`
- `yamlgraph/compile/graph_loader.py`
