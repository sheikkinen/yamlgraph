# Feature Request: SMTP delivery tool for digest pipelines

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-29
**First consumer / first event:** `yamlgraph-daily-digest` (FR-902), at the
`send_digest` node of its 06:00 UTC scheduled run — the first run after
FR-902 Phase 1 merges emails the bulletin it has been committing silently
since 2026-08-18.
**Research:** in-body `## Alternatives Considered` dispositioned table
(FR-889 style — an equivalent committed record per the TEMPLATE note).
**Prior art:** FR-902 is a sibling filed in the same arc, not precedent —
it is the consumer that adds the node this FR supplies; the boundary is
that FR-901 owns the delivery tool and knows nothing about digests, while
FR-902 owns the graph ordering. FR-819 (GitHub-native digest PoC)
explicitly scoped email *out* ("no Fly.io, no Docker, no email"); this FR
is the deliberate reversal of that deferral now that SMTP config exists,
not a violation of it. No prior FR proposes SMTP delivery or rejects it;
`examples/daily_digest/nodes/email.py` is undocumented Resend code with no
governing FR, and is superseded rather than amended.

## Summary

A reusable FR-768 tool manifest that sends a rendered report by SMTP.
Takes `subject`, `text`, optional `html`, optional `to`; reads server
credentials from `SMTP_*` environment variables; raises on every failure.
Deliberately dumb: it delivers a string someone else rendered.

## Value Statement

Any digest pipeline — news, diary, git report, census — gains email
delivery by referencing one manifest, instead of each repo re-writing
`smtplib` glue against a vendor SDK.

## Problem

Two digest pipelines exist and neither can email without new code:

- `examples/daily_digest/nodes/email.py` binds delivery to the **Resend**
  API: a vendor SDK dependency, a vendor API key, and a sending-domain
  verification step. Its module-level `resend.api_key = os.environ.get(...)`
  is read at import, so a late-set key silently produces an unauthenticated
  client.
- `yamlgraph-daily-digest` has **no delivery at all**. It commits a
  markdown bulletin and stops. Eleven bulletins have accumulated since
  2026-08-18 that nobody is pushed.

The operator's `.env` already carries `SMTP_SERVER`, `SMTP_PORT`,
`SMTP_USER`, `SMTP_PASSWORD`, `SMTP_TO`. SMTP needs no SDK, no vendor
account, and no domain verification, and `smtplib` is standard library —
so the dependency footprint of delivery drops to zero.

There is a second, sharper reason this belongs in a tool rather than in a
runner script: **ordering**. In `examples/daily_digest` the send is the
last graph node, but the artifact is never written to disk at all; in
`yamlgraph-daily-digest` the artifact is written by `run_digest.py`
*after* `invoke()` returns. Neither shape lets a graph declare
"persist, then deliver". As a `tool_call` node the ordering becomes an
edge in `graph.yaml`, which is the same persist-before-publish contract
`deviant-daily/tools/steps.py` enforces around its DeviantArt calls.

## Ideal Result

A graph author who has a rendered report in state adds two lines to
`tools:` and one node, and the report is delivered — with the guarantee
that a delivery failure is loud, leaves the archived artifact intact, and
never half-reports success. Nothing about the tool knows what a digest is.

## Proposed Solution

### Contract

```python
def send_digest(
    subject: str,
    text: str,
    html: str | None = None,
    to: str | None = None,
) -> dict:
    """Send one report by SMTP. Returns {"sent": True, "to": <recipient>}."""
```

| Env var | Required | Meaning |
|---|---|---|
| `SMTP_SERVER` | yes | hostname |
| `SMTP_PORT` | yes | `465` → implicit TLS (`SMTP_SSL`); anything else → `SMTP` + `starttls()` |
| `SMTP_USER` | yes | login, and the `From:` address |
| `SMTP_PASSWORD` | yes | login secret; never logged, never in an exception message |
| `SMTP_TO` | when `to` is not passed | default recipient |

### Manifest

```yaml
# tools/smtp_send.tool.yaml
name: send_digest
description: "Send a rendered report by SMTP (text, optional HTML alternative)"
runtime:
  type: python
  path: smtp_send.py
  function: send_digest
```

```yaml
# In a consuming graph
tools:
  send_digest:
    manifest: tools/smtp_send.tool.yaml

nodes:
  send_digest:
    type: tool_call
    tool: send_digest
    args:
      subject: "Daily Tech Digest — {state.today}"
      text: "{state.digest_markdown}"
    state_key: sent
    on_error: fail
```

### Behavioural contracts

1. **Config validated before the socket.** Collect all missing `SMTP_*`
   keys and raise once, naming them — the `publish_step` pattern from
   `deviant-daily/tools/steps.py`. Not one-at-a-time, not at import.
2. **Credentials read at call time**, never at module import — the
   defect in `examples/daily_digest/nodes/email.py`.
3. **No silent success.** Every failure raises; there is no
   `return {"sent": False}` fallback path. `on_error` at the node is the
   caller's decision, not the tool's (Commandment 6).
4. **Secrets never surface.** `SMTP_PASSWORD` appears in no log line and
   no exception message. Exceptions from `smtplib` are re-raised with the
   server/port/recipient context only.
5. **Multipart when `html` is given.** `EmailMessage.set_content(text)`
   then `add_alternative(html, subtype="html")` — the text part is always
   present, so a plain-text client is never served an empty body.
6. **The tool does not render.** It receives strings. Markdown→HTML,
   templating, and subject construction are the caller's business.

## Acceptance Criteria

- [ ] `send_digest` implemented with the signature above
- [ ] `tools/smtp_send.tool.yaml` FR-768 manifest, header comment naming
      the first committed consumer (the shared-manifest convention)
- [ ] Missing `SMTP_*` config raises a single error naming **every**
      missing key, before any socket is opened — condemning test first
- [ ] Port `465` selects `SMTP_SSL`; any other port selects
      `SMTP` + `starttls()` — asserted with an injected SMTP double
- [ ] `html=None` produces a single text part; `html` given produces a
      multipart/alternative whose text part is non-empty
- [ ] `SMTP_PASSWORD` appears in no log record and no exception string —
      asserted, not reviewed
- [ ] Send failure propagates as a raise; no success-shaped return exists
      on any path
- [ ] Tests use an injected SMTP double (`sender=` parameter or
      equivalent seam); **no live SMTP connection in unit tests**
- [ ] One recorded live send, evidenced in the FR, before it is called done

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Keep Resend (as `examples/daily_digest` does) | **Rejected.** Vendor SDK, vendor key, sending-domain verification, and a test-domain restriction that only permits sending to the account owner. SMTP config already exists in `.env`. |
| A2 | Add delivery to the existing `nodes/email.py` as a second provider | **Rejected.** Two delivery backends in one module, for one consumer each. If a Resend consumer ever needs to coexist, a second manifest is the cheaper shape than a provider switch. |
| A3 | Put the send in `run_digest.py` rather than in the graph | **Rejected.** It is precisely the ordering — persist, then deliver — that this must guarantee, and ordering belongs in `graph.yaml` edges. A runner-script send also cannot be reused by a second digest without copying the script. |
| A4 | Tool also renders markdown → HTML | **Rejected.** Couples delivery to presentation and makes the tool digest-specific. HTML rendering is a separate node feeding `html`. |
| A5 | Tool returns `{"sent": False}` on failure instead of raising | **Rejected.** A plausible wrong answer is harder to catch than a crash (Commandment 6); an unattended cron would report green while delivering nothing. |
| A6 | Place the manifest in `examples/shared/` for cross-repo reuse | **Rejected for now.** `pyproject.toml` excludes `examples*` from the wheel, so `examples/shared/` is unreachable from a PyPI consumer (see FR-900). The manifest lives in the consumer repo until a second consumer and a distribution mechanism both exist — the `examples/shared/README.md` fit boundary. |

## Related

- FR-902 daily-digest refactor — the consumer that adds the node and the
  persist-before-deliver edge
- FR-900 release tool slots to PyPI — sibling; not a blocker for this FR,
  since FR-768 manifests are already published in `v0.5.22`
- `examples/daily_digest/nodes/email.py` — the Resend implementation this
  replaces, and the source of the import-time-credential defect
- `deviant-daily/tools/steps.py` `publish_step` — the
  collect-missing-secrets-and-raise pattern, and persist-before-publish
- `examples/shared/README.md` — the two-plus-consumer manifest fit boundary
- `reference/graph-yaml.md` "Tool Manifests (FR-768)" — the manifest contract
