# Feature Request: FR-815 YAMLGraph Serve — Hosted Declarative Graph Runner

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged — Approved with revisions folded (2026-08-18)
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

Validation starts before the normal graph loader can expand manifests, load
data paths, import code, or parse tools:

1. Canonicalize and path-confine every bundle member in memory.
2. Parse `graph_yaml` with `yaml.safe_load()` and require a mapping.
3. Validate the raw mapping against a hosted schema that performs no imports,
      filesystem reads, manifest expansion, or template rewrites.
4. Validate both raw and normalized mappings against the fail-closed hosted
      profile.
5. Only after acceptance, materialize the immutable bundle and call the normal
      YAMLGraph loader inside the isolated run pod.

The initial exact node allowlist is `llm`, `router`, `map`, `passthrough`, and
the inserted `verify` node only when derived by the service from supported
top-level `verify:` rules. Tenant-authored `__verify__` nodes are rejected.
The validator rejects at minimum:

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

Isolation has two separate witnesses. Hosted-profile tests prove tenant YAML
that asks for code, path, tool, provider, or network capabilities is rejected
before reservation or scheduling. A fixed service-owned diagnostic image,
which tenant YAML can never select, probes the generated namespace, Job, and
NetworkPolicy: cluster DNS/API, cloud metadata, public internet, another run's
storage, and control-plane endpoints must fail while the model-gateway route
succeeds.

### 4. Prepaid reservation ledger

Use integer microcredits and an append-only transactional ledger. This FR
supports admin-issued test credits only; purchasing credits, Stripe/payment
integration, refunds to payment instruments, tax/VAT, invoices, and cash
withdrawal are explicitly deferred.

The model catalog is typed service-owned configuration. Each entry contains
model ID, integer microcredits per one million input and output tokens,
maximum input/output tokens, and per-call overhead. Charges use integer
ceiling division per provider request; no floating-point money enters the
ledger. Before forwarding a call, the gateway reserves the catalog-priced
maximum output plus known input/overhead from the run's remaining reservation.
During streaming it counts output tokens and cancels before the next token
would exceed that call reservation. Cancellation settles reported consumed
tokens and releases unused call reservation; provider usage that contradicts
the gateway count enters `settlement_review`.

Run states are `reserved`, `scheduled`, `running`, `canceling`, `succeeded`,
`failed`, and `settlement_review`; terminal states are immutable except an
operator-reviewed transition from `settlement_review`. Ledger entry types are
`credit_grant`, `run_reserve`, `run_debit`, and `run_release`, each keyed by
tenant, run, and unique source event. A terminal transaction writes at most
one debit and one release against one reservation.

`POST /v1/runs` performs one serializable transaction keyed by tenant and
idempotency key: reject insufficient available balance, otherwise create the
run and reserve `max_credits`. Terminal settlement debits measured usage and
releases the remainder. Duplicate starts and duplicate terminal events return
the original result without creating another reservation or debit. A run with
missing or irreconcilable provider usage fails settlement into an operator
review state; it does not invent zero usage or debit an estimate silently.

### 5. Tenant content retention

| Artifact | Storage | Retention/deletion | Visibility | Content risk |
|---|---|---|---|---|
| Graph bundle and prompts | Tenant-scoped object store | Until tenant deletion; blocked by active runs | Owning tenant | Tenant graph/prompt content |
| Run inputs | Encrypted run record | 24 hours | Owning tenant until deletion | Tenant content |
| Run output and SSE events | Encrypted run/event store | 24 hours | Owning tenant until deletion | Model/tenant content |
| Provider request ID and token counts | Receipt database | 90 days | Tenant and operator | Metadata only |
| Credit receipt and ledger entries | Ledger database | 7 years unless shortened before external use | Tenant and operator | No prompt/input/output content |
| Service logs | Operator log store | 7 days | Operator | IDs/status only; content forbidden |
| Diagnostic probe artifacts | Test namespace/log store | Delete after witness | Operator | Synthetic service-owned data |
| Run pod and writable volume | Kubernetes | Delete after terminal receipt | Not exposed | Ephemeral tenant content |

"No tenant content survives the pod" means no content remains in pod files,
volumes, environment, or Kubernetes resources after cleanup. It does not
exclude the tenant-scoped bundle and 24-hour API result records above.

### 6. Bounded proof deployment

Provide a local `kind` deployment and an automated end-to-end witness. The
MVP is single-region, invitation-only, and non-production. It supports one
OpenAI-compatible service-owned gateway and a fixed model catalog. It proves
the execution, isolation, and accounting boundaries; it does not claim a
general serverless platform or commercial payment readiness.

The deployment has a configured integer operator spend ceiling. Scheduling
stops before aggregate provider reservations exceed it. This FR authorizes
only local `kind` and operator-controlled invitation-only test tenants. No
public endpoint, external tenant, real-money payment, SLA, production launch,
or provider spend above that ceiling is permitted without a separate
human-approved FR.

### 7. Project-local traceability

Because implementation remains in `projects/hosted_runner/`, it uses a
project-local requirement namespace and checker. It does not add a framework
`REQ-YG-XXX` or capability. `python scripts/req_coverage.py --strict` must
still pass to prove framework coverage was not regressed.

## Acceptance Criteria

- [ ] AC-01: `POST /v1/graphs` stores a valid data-only bundle under a stable
      SHA-256 graph ID; byte-identical canonical content returns the same ID.
- [ ] AC-02: Hosted-profile validation follows the raw-YAML parse order in
      Section 2 and table-driven tests reject every forbidden class with a
      stable reason code before normal graph loading, a Job, or reservation.
- [ ] AC-02a: `verify` is accepted only when service-inserted from supported
      top-level `verify:` rules; tenant-authored `__verify__` nodes fail closed.
- [ ] AC-03: Bundle tests reject absolute paths, traversal, duplicate
      canonical paths, symlinks, binary payloads, and configured size/count
      limit violations without writing outside tenant-scoped storage.
- [ ] AC-04: Every graph, run, event, and receipt lookup is tenant-scoped; an
      integration test proves tenant B receives `404` for tenant A's IDs.
- [ ] AC-05: A valid run atomically reserves integer `max_credits` before Job
      creation; insufficient balance creates neither reservation nor Job.
- [ ] AC-06: Twenty concurrent requests with one idempotency key converge on
      the same run/reservation/Job/settlement; duplicate terminal events write
      at most one `run_debit` and one `run_release` for that reservation.
- [ ] AC-07: The gateway rejects an LLM call whose run token is expired,
      canceled, uses a different model/run ID, or would exceed reserved
      credits; provider credentials are absent from the run pod environment,
      files, and Kubernetes Job manifest.
- [ ] AC-08: The generated Job manifest mechanically satisfies all pod
      restrictions in Section 3 and contains no tenant-controlled pod-spec
      field.
- [ ] AC-09: Hosted-profile tests reject tenant YAML requesting network, path,
      code, subprocess, tool, MCP, A2A, provider-key/URL, or unsupported-model
      capabilities before scheduling.
- [ ] AC-09a: A fixed service-owned diagnostic Job proves cluster DNS/API,
      cloud metadata, public internet, another run's storage, and control-plane
      endpoints are unreachable while the model-gateway path succeeds.
- [ ] AC-10: CPU, memory, storage, wall-clock, map, retry, and credit limits
      each have a test proving a terminal bounded failure and Job cleanup.
- [ ] AC-11: Successful settlement records provider request ID, input/output
      token counts, reserved credits, consumed credits, and released credits;
      pricing, rounding, gateway cutoff, cancellation, and ledger transitions
      use the exact integer algorithm and state machine in Section 4.
- [ ] AC-12: Missing or contradictory provider usage enters a named
      `settlement_review` state, preserves the reservation, alerts the
      operator, and never records fabricated usage.
- [ ] AC-13: SSE and terminal receipts expose typed status/usage/output only;
      tests prove API tokens, gateway tokens, provider keys, headers, and
      another tenant's content are redacted.
- [ ] AC-14: The end-to-end witness uploads a graph, grants test credits,
      starts it through the API, observes streamed events, verifies its
      output/receipt, and confirms the Job and writable volume are deleted.
- [ ] AC-15: Hosted-runner tests map to project-local requirements and its
      checker passes; `python scripts/req_coverage.py --strict` also passes
      without adding a framework `REQ-YG-XXX`.
- [ ] AC-16: Documentation states the hosted profile, pricing/rounding,
      isolation assumptions, retention matrix, operator ceiling,
      invitation-only status, and deferred commercial/payment concerns without
      claiming arbitrary-code safety.
- [ ] AC-17: Scheduling halts before aggregate reservations exceed the
      configured operator ceiling; no external/public deployment path exists.

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

## Questions For The Human

None for this enforcement. Scope is strictly local `kind` plus
operator-controlled invitation-only test tenants and a configured spend
ceiling. External exposure, real-money payment, production claims, an SLA, or
a ceiling increase requires a separate human-approved FR.

## Judgement (2026-08-18)

**Verdict:** APPROVED WITH REVISIONS — R-1 through R-6 from the canonical
judge artifact are folded above; authority is active for the frozen
non-production `projects/hosted_runner/` reference deployment only.

**Purge list:** core node types; A2A/MCP upload changes; arbitrary execution;
tenant pod/provider configuration; external launch; payments; transferable or
refundable credits; multiple regions/providers; durable sessions; SLA or
production-readiness claims.

**Scope frozen:** D-1 through D-7 and conditions C-1 through C-7 in
`feature-requests/FR-815-hosted-declarative-graph-runner.judgement.md`.

## Related

- `feature-requests/070-gui-web-playground.md`
- `feature-requests/FR-246-a2a-server-reference-docs.md`
- `feature-requests/FR-766-runpod-provider.md`
- `reference/a2a-server.md`
- `yamlgraph/a2a/server.py`
- `yamlgraph/compile/graph_loader.py`
