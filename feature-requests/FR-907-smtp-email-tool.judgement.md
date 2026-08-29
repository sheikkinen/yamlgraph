# Judgement: FR-907 SMTP email tool

**Prior art:** inherits the disposition in `FR-907-smtp-email-tool.md` —
FR-906/FR-908 are same-arc siblings, not precedent; FR-769 (shared vision
tool) is the structural precedent for a shared `examples/shared/` tool
with an FR-768 manifest and is followed, not contradicted.

**Verdict:** APPROVED WITH REVISIONS - the SMTP tool is a sound, small transport primitive for the first digest consumer, but authority activates only after the FR clarifies the target repository/surface, replaces an unreachable cited precedent, and makes the research/test seams mechanically exact.

**Reviewed against:** `feature-requests/FR-907-smtp-email-tool.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `examples/daily_digest/nodes/email.py`; `reference/graph-yaml.md` ("Tool Manifests (FR-768)"); `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md`; `feature-requests/FR-819-github-native-digest-poc-repo.md`; `feature-requests/FR-906-release-tool-slots-to-pypi.md`; `feature-requests/FR-908-daily-digest-slot-bound-refactor.md`; `examples/shared/README.md`; `pyproject.toml`; cited-but-absent `deviant-daily/tools/steps.py`; existing `examples/**/*.tool.yaml` manifest convention survey via `rg`.

## What is sound

The problem is real and narrowly framed. FR-907 names a concrete first consumer and event: the `yamlgraph-daily-digest` `send_email` node on the first 06:00 UTC scheduled run after FR-908 Phase 1 (`feature-requests/FR-907-smtp-email-tool.md:8-11`). The existing local email code is not a suitable reusable base: it imports `resend`, stores `resend.api_key` from the environment at import time, hardcodes a digest-shaped subject/body, and returns success-shaped `{"email_sent": False}` for dry-run and missing-recipient paths (`examples/daily_digest/nodes/email.py:1-11`, `examples/daily_digest/nodes/email.py:19-44`). FR-907 correctly identifies those as defects to avoid (`feature-requests/FR-907-smtp-email-tool.md:42-53`, `feature-requests/FR-907-smtp-email-tool.md:146-150`).

The architecture is aligned with existing YAMLGraph tool-manifest machinery rather than a new runtime. FR-768 manifests are explicitly a declaration-reuse layer that translate to existing shell/python/graph runtimes with no separate manifest runtime (`reference/graph-yaml.md:1463-1468`), and the documented Python manifest shape uses `runtime.type: python`, `path`, and `function` (`reference/graph-yaml.md:1477-1485`, `reference/graph-yaml.md:1495-1503`). FR-907's manifest sketch follows that shape (`feature-requests/FR-907-smtp-email-tool.md:112-122`).

The single responsibility boundary is strong. The proposed function receives email vocabulary (`subject`, `text`, optional `html`, `to`, `cc`, `attachments`) and explicitly excludes rendering, templating, retries, non-SMTP transports, recipient lists, and address books (`feature-requests/FR-907-smtp-email-tool.md:74-81`, `feature-requests/FR-907-smtp-email-tool.md:157-163`, `feature-requests/FR-907-smtp-email-tool.md:203-208`). This keeps FR-907 separate from FR-908, which owns digest ordering, graph wiring, workflow secrets, and body construction (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:116-123`).

The acceptance criteria are mostly mechanically testable: config validation before socket creation, TLS mode selection with an SMTP double, multipart behavior, recipient parsing, attachment failure before connect, CR/LF rejection, secret non-disclosure, raise-on-failure, no live SMTP in unit tests, and a recorded live send are all direct assertions (`feature-requests/FR-907-smtp-email-tool.md:167-188`). That satisfies the judge rubric's measurability and testability standard (`.github/skills/judge-fr/doctrine.md:43-61`).

Strategic classification: **Contrib/example tool**, not a framework primitive. The first committed use is FR-908; the other senders are plausible near-term consumers but not committed use cases (`feature-requests/FR-907-smtp-email-tool.md:60-72`). Existing FR-768 manifests already supply the abstraction (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:16-19`, `reference/graph-yaml.md:1463-1468`), so this FR should authorize a reusable SMTP tool at the consumer/tool layer, not a yamlgraph core feature.

## Required revisions

### R-1: State the target repository and exact authorized paths

Fold an explicit "Target surface" section into the FR before enforcement. It must say whether `tools/smtp_email.py` and `tools/smtp_email.tool.yaml` are created in `yamlgraph`, `yamlgraph-daily-digest`, or both. If the target is `yamlgraph-daily-digest`, say so directly and make clear that the YAMLGraph repo change authorized by this FR is only the FR/judgement record. If the target is this repository, replace the bare root `tools/` path with the exact package or example path and justify its distribution behavior, because the current repo has no root `tools/` directory and `pyproject.toml` excludes `examples*` from the wheel (`pyproject.toml:173-175`). This removes the current ambiguity between the manifest sketch (`feature-requests/FR-907-smtp-email-tool.md:112-122`) and the A7 statement that the manifest lives in the consumer repo (`feature-requests/FR-907-smtp-email-tool.md:200`).

### R-2: Replace the unreachable `deviant-daily/tools/steps.py` evidence

Remove or replace the `deviant-daily/tools/steps.py` citation unless a committed, in-closure copy is added or an exact accessible path is named. FR-907 currently relies on that path for the collect-missing-config pattern (`feature-requests/FR-907-smtp-email-tool.md:143-145`, `feature-requests/FR-907-smtp-email-tool.md:218-219`), but the cited file is absent from this repository. The replacement can be a small inline contract in FR-907 itself: "collect all missing keys into one `ValueError` before opening any socket." Do not reach outside the committed input closure to infer the pattern.

### R-3: Add the explicit `is_this_a_graph` research answer

Append one row or sentence to `## Alternatives Considered`: `is_this_a_graph: no - this is a deterministic side-effect tool invoked by a graph; no LLM orchestration, map/reduce, routing, or prompt artifact is being authored here.` Local judge doctrine requires research evidence to include genuine alternatives and the `is_this_a_graph` answer (`.github/skills/judge-fr/doctrine.md:118-128`), and the current alternatives table has the former but not the latter (`feature-requests/FR-907-smtp-email-tool.md:190-201`).

### R-4: Specify the test seam and sanitized exception boundary exactly

Revise the contract to name the SMTP injection seam used by unit tests without changing the graph-facing manifest API. Either authorize an internal keyword-only factory such as `smtp_factory`/`smtp_ssl_factory` with default `smtplib.SMTP`/`smtplib.SMTP_SSL`, or state that tests monkeypatch the `smtplib` classes directly. Also require wrapped SMTP exceptions to expose only sanitized context and not chain raw provider exceptions when that chain could surface credentials. FR-907 already requires no live SMTP unit tests and no password in log or exception strings (`feature-requests/FR-907-smtp-email-tool.md:181-186`), but the implementation seam is currently "sender= parameter or equivalent" and the public signature is otherwise exact (`feature-requests/FR-907-smtp-email-tool.md:87-97`, `feature-requests/FR-907-smtp-email-tool.md:185-186`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tools/smtp_email.py` or the revised exact target path from R-1 |
| D-2 | `tools/smtp_email.tool.yaml` or the revised exact target path from R-1 |
| D-3 | Unit tests for SMTP config, recipient parsing, TLS mode, MIME shape, attachments, CR/LF rejection, secret non-disclosure, and send-failure propagation |
| D-4 | One FR update recording the live-send evidence before completion |
| D-5 | Minimal documentation or manifest comments needed to expose the env contract and first committed consumer, at the revised target surface |

Not authorized: digest graph changes, `run_digest.py` changes, workflow changes, markdown-to-HTML rendering, templating, retry/backoff policy, queues, rate limiting, bounce handling, subscriber/address-book state, non-SMTP transports, Resend provider work, YAMLGraph core changes, graph-authoring changes, prompt changes, CI/hook/judge/review doctrine changes, or packaging/distribution changes beyond the exact target-surface clarification in R-1.

## Revised acceptance criteria

- [ ] AC-01: The FR states the exact target repository and file paths for the SMTP tool and manifest; enforcement changes no other repository or path.
- [ ] AC-02: `send_email(subject: str, text: str, html: str | None = None, to: str | None = None, cc: str | None = None, attachments: list[str] | None = None) -> dict` is implemented at the authorized path, with no digest-specific parameter or state-shaped input.
- [ ] AC-03: `send_email` returns only a success result shaped at least as `{"sent": True, "to": [...]}` after the SMTP send succeeds; no path returns `{"sent": False}` or any other success-shaped failure.
- [ ] AC-04: `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, and `SMTP_PASSWORD` are read at call time, never at module import.
- [ ] AC-05: Missing required SMTP config raises one exception naming every missing key before any socket is opened.
- [ ] AC-06: `to` and `cc` accept either a single address or a comma-separated list; if `to` is omitted, `SMTP_TO` is used; if neither yields a recipient, the call raises before any socket is opened.
- [ ] AC-07: CR or LF in `subject`, `to`, `cc`, `SMTP_FROM`, or `SMTP_TO` raises before message construction or SMTP connection.
- [ ] AC-08: Port `465` uses `smtplib.SMTP_SSL`; any other port uses `smtplib.SMTP` followed by `starttls()` before login, asserted with the R-4 SMTP double/seam.
- [ ] AC-09: `html=None` produces a single plain-text message body; non-empty `html` produces a `multipart/alternative` message with a non-empty plain-text part and an HTML alternative.
- [ ] AC-10: Each attachment path must exist before any SMTP connection is opened; present attachments are attached with a guessed MIME type and filename.
- [ ] AC-11: SMTP send/login failures raise; wrapped errors include server, port, and recipient context but do not include `SMTP_PASSWORD` in `str(exc)`, chained exception display, or captured log records.
- [ ] AC-12: Unit tests use the R-4 SMTP seam or direct `smtplib` monkeypatching; no unit test opens a live SMTP connection.
- [ ] AC-13: The FR-768 manifest names `send_email`, points at the authorized implementation path, and contains the explicit first committed consumer comment required by the FR after R-1 clarifies the convention.
- [ ] AC-14: The implementation module, manifest, and tests contain no digest-specific API, subject text, body formatting, or dependency on FR-908 internals.
- [ ] AC-15: A live SMTP send is performed once after unit tests pass, and FR-907 is updated with non-secret evidence sufficient to identify the run without exposing credentials.
- [ ] AC-16: The `deviant-daily/tools/steps.py` citation is replaced or removed, and the alternatives/research section includes the explicit `is_this_a_graph` answer.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-4 are folded into `feature-requests/FR-907-smtp-email-tool.md`. | GATE |
| C-2 | The implementation must stay at the clarified target surface; do not add YAMLGraph core APIs, packaging policy, or distribution mechanics under this FR. | GATE |
| C-3 | Unit tests must not connect to a live SMTP server; all network behavior must pass through the declared double/monkeypatch seam. | GATE |
| C-4 | Missing config, missing recipient, header injection, and missing attachments must all fail before socket creation. | GATE |
| C-5 | `SMTP_PASSWORD` must not appear in exception strings, chained exception output, or log records. | GATE |
| C-6 | No graph, prompt, workflow, digest runner, or review/judge enforcement artifact may be edited under this FR. | GATE |

Authority granted: after R-1 through R-4 are folded into the FR, the enforcer may build only the clarified consumer-scoped SMTP `send_email` tool, its FR-768 manifest, and its tests/live-send evidence.
