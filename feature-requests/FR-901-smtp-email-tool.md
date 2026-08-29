# Feature Request: SMTP email tool

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-29
**First consumer / first event:** `yamlgraph-daily-digest` (FR-902), at the
`send_email` node of its 06:00 UTC scheduled run — the first run after
FR-902 Phase 1 merges emails the bulletin it has been committing silently
since 2026-08-18.
**Research:** in-body `## Alternatives Considered` dispositioned table
(FR-889 style — an equivalent committed record per the TEMPLATE note).
**Prior art:** FR-902 is a sibling filed in the same arc, not precedent —
it is the first consumer, and the boundary is that FR-901 owns email and
knows nothing about digests, while FR-902 owns what it sends and when.
FR-819 (GitHub-native digest PoC) explicitly scoped email *out* ("no
Fly.io, no Docker, no email"); this FR is the deliberate reversal of that
deferral now that SMTP config exists, not a violation of it. No prior FR
proposes SMTP delivery or rejects it; `examples/daily_digest/nodes/email.py`
is undocumented Resend code with no governing FR, and is superseded rather
than amended.

## Summary

An FR-768 tool manifest that sends email over SMTP. Takes `subject`,
`text`, optional `html`, optional `to`/`cc`/`attachments`; reads server
credentials from `SMTP_*` environment variables; raises on every failure.

It is an email tool. It has no opinion about what it carries.

## Value Statement

Any graph that has produced text a human should receive — a digest, an
audit finding, a run failure, a review verdict, a scheduled report — gains
delivery by referencing one manifest.

## Problem

Nothing in the repo can send mail without a vendor account.

`examples/daily_digest/nodes/email.py` is the only email code that exists,
and it is bound to **Resend**: an SDK dependency, a vendor API key, a
sending-domain verification step, and a test-domain restriction that only
permits sending to the account owner. It is also wrong in a way worth
naming, because the replacement must not repeat it — the module does

```python
resend.api_key = os.environ.get("RESEND_API_KEY", "")
```

at import time, so a key set after import yields a silently
unauthenticated client.

Meanwhile the operator's `.env` already carries `SMTP_SERVER`, `SMTP_PORT`,
`SMTP_USER`, `SMTP_PASSWORD`, `SMTP_TO`. SMTP needs no SDK, no vendor
account, and no domain verification, and `smtplib` is standard library, so
the dependency footprint of email drops to zero.

The immediate driver is FR-902 — eleven digest bulletins committed since
2026-08-18 that nobody is pushed. But framing the tool around that consumer
would be a mistake. The plausible near-term senders are not digests:

- an unattended pipeline mailing its own failure, since a red GitHub
  Actions run notifies nobody who is not watching
- the inquisitor mailing an audit finding
- `scripts/review.sh` mailing a verdict
- any scheduled graph whose output is for a human rather than for git

All of these want "send this text to this address" and none of them want a
digest-shaped API. A tool named for its first consumer would have to be
renamed or forked by the second.

## Ideal Result

A graph author with a string in state and a recipient adds two lines to
`tools:` and one node, and mail is sent — with the guarantee that failure
is loud and never half-reports success. The tool's vocabulary is
`subject`, `text`, `html`, `to`: the vocabulary of email, not of any
application. It is the mail transport under every future graph that needs
one, and it stays boring.

## Proposed Solution

### Contract

```python
def send_email(
    subject: str,
    text: str,
    html: str | None = None,
    to: str | None = None,
    cc: str | None = None,
    attachments: list[str] | None = None,
) -> dict:
    """Send one email over SMTP. Returns {"sent": True, "to": [...]}."""
```

`to` and `cc` accept a single address or a comma-separated list.
`attachments` are filesystem paths; each is attached with a guessed MIME
type, and a missing path raises.

| Env var | Required | Meaning |
|---|---|---|
| `SMTP_SERVER` | yes | hostname |
| `SMTP_PORT` | yes | `465` → implicit TLS (`SMTP_SSL`); anything else → `SMTP` + `starttls()` |
| `SMTP_USER` | yes | login, and the default `From:` |
| `SMTP_PASSWORD` | yes | login secret; never logged, never in an exception message |
| `SMTP_FROM` | no | overrides the `From:` header when it differs from the login |
| `SMTP_TO` | when `to` is not passed | default recipient |

### Manifest

```yaml
# tools/smtp_email.tool.yaml
name: send_email
description: "Send an email over SMTP (text, optional HTML alternative, optional attachments)"
runtime:
  type: python
  path: smtp_email.py
  function: send_email
```

```yaml
# In any consuming graph
tools:
  send_email:
    manifest: tools/smtp_email.tool.yaml

nodes:
  notify:
    type: tool_call
    tool: send_email
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
2. **Credentials read at call time**, never at module import — the defect
   in `examples/daily_digest/nodes/email.py`.
3. **No silent success.** Every failure raises; there is no
   `return {"sent": False}` path. `on_error` at the node is the caller's
   decision, not the tool's (Commandment 6).
4. **Secrets never surface.** `SMTP_PASSWORD` appears in no log record and
   no exception message. `smtplib` errors are re-raised with server, port,
   and recipient context only.
5. **Multipart when `html` is given.** `set_content(text)` then
   `add_alternative(html, subtype="html")` — the text part is always
   present, so a plain-text client is never served an empty body.
6. **The tool does not render, template, or format.** It receives strings.
   Markdown→HTML, subject construction, and body assembly belong to the
   caller. This is the boundary that keeps it an email tool.
7. **Header injection is refused.** Any address or subject containing a
   newline or carriage return raises. Untrusted content reaching a header
   is the one way a dumb mail tool becomes a security defect, so the check
   lives here rather than in each caller.

## Acceptance Criteria

- [ ] `send_email` implemented with the signature above
- [ ] `tools/smtp_email.tool.yaml` FR-768 manifest, header comment naming
      the first committed consumer (the shared-manifest convention)
- [ ] Missing `SMTP_*` config raises a single error naming **every**
      missing key, before any socket is opened — condemning test first
- [ ] Port `465` selects `SMTP_SSL`; any other port selects `SMTP` +
      `starttls()` — asserted with an injected SMTP double
- [ ] `html=None` produces a single text part; `html` given produces a
      multipart/alternative whose text part is non-empty
- [ ] `to`/`cc` accept a single address and a comma-separated list;
      a missing recipient (no `to`, no `SMTP_TO`) raises
- [ ] Attachments: a present file attaches with a guessed MIME type;
      a missing path raises before connecting
- [ ] CR/LF in `subject`, `to`, or `cc` raises — header-injection test
- [ ] `SMTP_PASSWORD` appears in no log record and no exception string —
      asserted, not reviewed
- [ ] Send failure propagates as a raise; no success-shaped return exists
      on any path
- [ ] Tests use an injected SMTP double (`sender=` parameter or
      equivalent seam); **no live SMTP connection in unit tests**
- [ ] One recorded live send, evidenced in the FR, before it is called done
- [ ] Nothing in the module, the manifest, or the tests references digests

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Scope the tool to digests (`send_digest`, digest-shaped args) | **Rejected — this is the rework.** The named near-term senders are pipeline failure notices, audit findings, and review verdicts, none of which are digests. A tool named for its first consumer gets renamed or forked by the second, and the digest framing bought nothing: the implementation is identical. |
| A2 | Keep Resend (as `examples/daily_digest` does) | **Rejected.** Vendor SDK, vendor key, domain verification, and a test-domain restriction permitting sends only to the account owner. SMTP config already exists in `.env`. |
| A3 | Add SMTP to the existing `nodes/email.py` as a second provider | **Rejected.** Two backends in one module for one consumer each. If a Resend consumer ever reappears, a second manifest is cheaper than a provider switch. |
| A4 | Tool also renders markdown → HTML | **Rejected.** Couples transport to presentation. HTML rendering is a separate node feeding `html`. |
| A5 | Tool returns `{"sent": False}` on failure instead of raising | **Rejected.** A plausible wrong answer is harder to catch than a crash (Commandment 6); an unattended cron would report green while delivering nothing. |
| A6 | Omit attachments and `cc` from v1 | **Rejected, narrowly.** Both are a few lines against the same `EmailMessage`, and their absence is exactly what forces the second consumer to fork. Not extended further: no templating, no queueing, no retry, no address book. |
| A7 | Place the manifest in `examples/shared/` for cross-repo reuse | **Rejected for now.** `pyproject.toml` excludes `examples*` from the wheel, so `examples/shared/` is unreachable from a PyPI consumer (FR-900). The manifest lives in the consumer repo until a second consumer and a distribution mechanism both exist — the `examples/shared/README.md` fit boundary. |
| A8 | Retry/backoff on transient SMTP failures | **Rejected.** `on_error: retry` at the node is the caller's decision and already exists; a retry loop inside the tool would be a second, invisible policy. |

## Out of Scope

- Templating, markdown rendering, and subject construction (the caller's)
- Retry, queueing, rate limiting, bounce handling
- Any non-SMTP transport
- Recipient lists, address books, or subscriber state

## Related

- FR-902 daily-digest refactor — the first consumer; owns the
  persist-before-deliver ordering that decides *when* this is called
- FR-900 release tool slots to PyPI — sibling; **not** a blocker, since
  FR-768 manifests are already published in `v0.5.22`
- `examples/daily_digest/nodes/email.py` — the Resend implementation this
  supersedes, and the source of the import-time-credential defect
- `deviant-daily/tools/steps.py` `publish_step` — the
  collect-missing-secrets-and-raise pattern
- `examples/shared/README.md` — the two-plus-consumer manifest fit boundary
- `reference/graph-yaml.md` "Tool Manifests (FR-768)" — the manifest contract
