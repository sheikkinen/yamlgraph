# Deadline-Bounded Enrichment Pattern

Augment an already-committed record with an LLM judgement, out of band,
without ever blocking or degrading the record's primary delivery. The
augmentation can only upgrade a pending default action to a better one; every
failure mode — slow, down, wrong, absent — resolves to the same default the
system used before the augmentation existed.

> **Evidence base: single instance.** Extracted from VBOT-130 — a Jira ticket
> and judged feature request in the sibling `customer-service-agent-platform`
> repo for post-call Ninchat queue routing (not part of this repo). That
> judgement classified the change as "contrib/example": one proven use case,
> copy-adapt the idea, but not yet a case for shared, generic machinery. It
> explicitly declined to authorize a generic `enrichment.<part>` framework —
> only a single typed field for a single consumer. Treat this document the
> same way: a pattern to recognize and copy-adapt per instance, not a shared
> library to import. Graduate to "proven" only after a second independent
> instance.

## When to use

All of these must hold:

1. A record's delivery already happens on a hard latency budget that cannot
   absorb an LLM call — the fast/critical path is committed and untouched.
2. The judgement only **improves which known-good action is taken**; it never
   decides **whether** an action happens. If a missing judgement must block
   delivery rather than downgrade to a default, this is the wrong pattern —
   see [LLM-as-Gate](llm-as-gate.md).
3. A commit-notification fan-out already exists (or can be added) so a new
   consumer sees every write without touching the producer.
4. The record store supports optimistic concurrency (compare-and-swap) so a
   new writer can add one block without racing the record's other writers.
5. A bounded staleness window (seconds to low minutes) is acceptable — the
   augmentation is a quality improvement, not a correctness requirement.

Do not use it for first-touch structured collection (that's
[Schema-Driven Extraction](schema-driven-extraction.md)), for a decision that
must gate whether output ships at all, or for any correction that must
invalidate a result already acted on once — this pattern assumes the
consumer acts exactly once, after the wait, never twice.

## Topology

```
producer commits record ──► notification fan-out (existing topic/bucket event)
                                  │
                    ┌─────────────┼──────────────────┐
                    ▼                                ▼
         existing consumer(s)               enrichment consumer (new)
         (unchanged, fast path)              own process, own credentials
                                              own subscription + DLQ
                                                  │
                                    read record → decision table (below)
                                                  │
                                    CAS-write ONE typed, additive block
                                                  │
                    ┌─────────────────────────────┘
                    ▼
         downstream consumer (existing, now deadline-aware)
         waits up to a deadline, then resolves:
           block done + valid   → act on it            (source=llm)
           block done + invalid → act on prior default  (source=default)
           block failed         → act on prior default  (source=default)
           absent/running,
             before deadline    → wait (nack / retry)
           absent/running,
             at/after deadline  → act on prior default  (source=deadline)
```

Removing the enrichment consumer and unsetting the deadline must reproduce
the pre-augmentation behavior exactly — the pattern is strictly additive.

## The four elements

### 1. A separate stage on the existing notification, with its own credentials

The enrichment consumer is a new process (or Deployment) subscribing to the
same commit notification every other consumer already uses. It gets its own
subscription and DLQ, its own IAM identity, and — critically — the *only*
LLM/provider credential in the augmentation path. Existing consumers keep
none of it; a credential-scope test can assert this statically.

Its decision table is exhaustive and ordered — first matching row wins, and
every record state maps to exactly one of **ack** (nothing to do or already
terminal), **claim → run → commit** (do the work), or **nack** (not yet
eligible). No row is allowed to silently fall through.

### 2. A typed block, CAS-written, with claim/lease/commit

The record gains **one** additive, typed field — not a generic dict —
written under compare-and-swap so a concurrent writer to other parts of the
record cannot be clobbered:

```yaml
status: running | done | failed
at: <ISO-8601 UTC>
claimant: <process/pod id>       # running only
lease_until: <ISO-8601 UTC>      # running only — crash recovery
result_key: <symbolic value>     # done only — never the resolved secret/id
error_kind: <frozen enum>        # failed only
```

Claim/lease/reclaim rules, derived so a crashed claimant can never strand the
record past the deadline:

- Fresh lease (`now < lease_until`) → another claimant is active, ack.
- Expired lease with enough time left before the downstream deadline → CAS
  reclaim with a new claimant and lease, then run.
- Expired lease too close to the deadline to finish → ack; let the
  downstream deadline resolve to default. Never race a second worker against
  a deadline that's about to resolve anyway.
- A CAS conflict on claim means another claimant already won → ack, not an
  error.

### 3. A downstream consumer that waits, then resolves to a tagged default

The existing consumer that already sends/acts is extended, not replaced,
with one more read before it acts: wait for the block up to a deadline, then
resolve through the same table shape as the enrichment stage — first
matching row wins, every branch sends/acts **exactly once**, and every
non-`done` branch (absent, still running, invalid output, `failed`) uses the
prior, pre-augmentation default. The chosen action is tagged with its source
(`llm` / `default` / `deadline`) for observability, never for branching logic
downstream.

### 4. Deadline arithmetic that is derived, not guessed

Three durations, each with explicit slack, in a fixed order:

```
graph/work timeout  <  claim lease  <  downstream wait deadline
```

- claim lease = work timeout + commit slack (time to write the CAS result
  after the work finishes);
- downstream deadline = claim lease + notification slack (time for the
  commit's own notification to reach the downstream consumer).

Compute the worst-case redelivery/backoff timeline against the downstream
deadline and assert, as a test, that the deadline resolves **before** the
subscription's retry budget is exhausted (no record should ever reach a
dead-letter queue purely because it was waiting on enrichment).

## What this pattern is not

- **Not a generic enrichment framework.** One use case, one typed field, one
  deterministic default. A second augmentation need is a new field, a new
  decision table, and a new judged change — not a shared `enrichment.<part>`
  bag. Building the generic version ahead of a second proven instance is
  exactly the machinery VBOT-130's judgement declined to authorize.
- **Not a retry or queueing primitive.** It reuses the existing at-least-once
  delivery and CAS store; it does not reimplement either.
- **Not for corrections after the fact.** The downstream consumer acts once;
  this pattern upgrades *what* it acts on before that one action, never
  reverses an action already taken.

## Constraints worth carrying into any instance

- One provider call per downstream invocation; a rejected or failed result
  commits `failed/<kind>` and is never retried against the provider from
  inside a CAS retry loop.
- No sensitive content (transcripts, callers, resolved ids/secrets) in the
  block or in logs — the block carries a symbolic key; only the downstream
  consumer's own config maps it to a real value.
- The enrichment stage never sends or acts on its own; it writes a decision.
  The existing actor remains the only sender.

## Related patterns

- [LLM-as-Gate](llm-as-gate.md) — also a semantic decision beside a
  deterministic path, but the gate decides *whether* to proceed; this pattern
  never blocks, it only decides *which* already-safe action to take.
- [FSM-as-Conductor](fsm-as-conductor.md) — the same "lifecycle owns pace,
  LLM performs one bounded judgement" division of labor, applied here to
  independent Pub/Sub consumers instead of FSM states.
