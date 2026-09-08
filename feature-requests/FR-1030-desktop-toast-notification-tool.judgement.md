# Judgement: FR-1030 Shared desktop-toast notification tool, consumed by the hello demo

**Prior art:** `FR-1030-desktop-toast-notification-tool.md` and
`FR-1030.research.md` are the artifacts under judgement (self-hits).
`FR-478-dm-v2-button-press-feedback.md` matches on the noun "toast" only
and is dispositioned in the FR's Prior art section — it is in-web-UI
feedback, not an OS notification. `FR-769-shared-vision-tool.judgement.md`
and `FR-771-vision-demo-executes-manifest-tool.judgement.md` match on the
filename suffix `tool.judgement`, not on subject matter; they judge a
vision tool and are the structural precedent for the shared-tool +
FR-768-manifest + committed-demo-consumer shape this judgement applies.

**Verdict:** APPROVED WITH REVISIONS — the local notification transport is a coherent contrib/example, but authority activates only after R-1 through R-5 are folded into committed artifacts and the operator explicitly approves making the canonical quickstart emit a desktop notification by default.

**Reviewed against:** `feature-requests/FR-1030-desktop-toast-notification-tool.md`; `feature-requests/FR-1030.research.md`; `feature-requests/research-briefs/notify-toast-problem-brief.md`; `feature-requests/FR-907-smtp-email-tool.md`; `feature-requests/FR-478-dm-v2-button-press-feedback.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-778-tool-call-on-error-fail.md`; `~/.copilot/skills/call-me-maybe/SKILL.md`; `examples/shared/smtp_email.py`; `examples/shared/smtp_email.tool.yaml`; `examples/shared/README.md`; `examples/demos/hello/graph.yaml`; `examples/demos/hello/demo-output.log`; `yamlgraph/node_factory/tool_nodes.py`; `scripts/check_demo_proof.sh`; `scripts/demo_log_semantics.sh`; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; and repository source-control state reported by `git status --short` at judgement time.

## What is sound

The problem is real and bounded. The incident brief distinguishes local notification from terminal output, SMTP, and phone escalation (`feature-requests/research-briefs/notify-toast-problem-brief.md:17-47`), while the FR narrows the implementation to one leaf tool, one manifest, and one consumer (`feature-requests/FR-1030-desktop-toast-notification-tool.md:34-42`). Fixed subprocess inputs, `shell=False`, and caller data carried through argv or child-process environment variables place the injection defense at the process boundary rather than relying on escaping (`feature-requests/FR-1030-desktop-toast-notification-tool.md:84-113`). Loud tool failure combined with graph-owned `on_error: skip` also matches the existing envelope contract: `tool_call` records `success: false` and the error at the configured state key (`yamlgraph/node_factory/tool_nodes.py:105-119`, `145-159`).

| Rubric criterion | Finding |
|---|---|
| Scope | The transport, manifest, tests, documentation, and one consumer form one deliverable. The optional `subtitle` is unnecessary scope because its cross-platform behavior is not specified or tested (`feature-requests/FR-1030-desktop-toast-notification-tool.md:79-90`, `138-142`). |
| Consistency | The failure policy is internally coherent, but `delivered: true` contradicts the claim that delivery is never overstated: subprocess success proves submission to an OS facility, not display to a human (`feature-requests/FR-1030-desktop-toast-notification-tool.md:64-68`, `79-82`, `115-118`). The claim that all three backends use only OS-shipped facilities also omits the Linux `notify-send` prerequisite (`feature-requests/FR-1030-desktop-toast-notification-tool.md:36-39`, `86-90`). |
| Measurability | Dispatch, argument transport, and exception conversion are directly assertable. AC-1 is not: a committed log can prove process success but not visible pixels, and the repository gate accepts any listed success marker (`feature-requests/FR-1030-desktop-toast-notification-tool.md:164-180`; `scripts/demo_log_semantics.sh:5-34`). The manual witness must be recorded separately. |
| Feasibility | macOS argv transport and Linux fixed argv are workable. Windows feasibility is not yet evidenced: the FR names WinRT but does not freeze the PowerShell/AUMID contract, while the research merely asserts first-party corroboration without citing it (`feature-requests/FR-1030-desktop-toast-notification-tool.md:88-106`, `216-225`; `feature-requests/FR-1030.research.md:24-29`). |
| Architecture alignment | The FR correctly reuses FR-768 manifests and FR-778 error envelopes rather than extending framework execution. The manifest citation itself is dangling (`feature-requests/FR-1030-desktop-toast-notification-tool.md:26` names `FR-768-tool-manifest.md`, but the cited artifact is `FR-768-tool-manifest-declaration-reuse.md`). |
| Single responsibility | The tool and its demonstration are one notification concern; no split is required. Global run-completion behavior, retries, and dependency installation remain outside it. |
| Strategic classification | **Contrib/example.** There is one committed consumer and existing manifest/tool-call abstractions already fit, matching the doctrine's 1-2-use-case classification (`.github/skills/judge-fr/doctrine.md:51-55`). This is not a framework primitive. |
| Testability | Most branches can be condemned with subprocess doubles. The missing Windows execution contract, undefined `subtitle`, and conflation of command success with visible delivery prevent direct tests for the current full claim (`feature-requests/FR-1030-desktop-toast-notification-tool.md:164-201`). |

## Required revisions

### R-1: Repair and commit the research evidence

Commit the FR, research record, and problem brief before promoting this judgement or beginning enforcement. At judgement time all three are untracked, so the hard committed-input boundary is not satisfied (`.github/skills/judge-fr/doctrine.md:16-24`, `118-130`).

Replace the current three unique solution classes (`os-permissions`, `external-method`, and `subtraction`) with a substantive record containing four to six genuine classes. Preserve the failed persona and disagreement already recorded, add at least one genuinely different class such as CLI lifecycle integration/boundary enforcement, and retain an explicit `is_this_a_graph` answer for every candidate (`feature-requests/FR-1030.research.md:7-15`, `24-29`). Add direct first-party citations for the exact AppleScript, Windows WinRT/PowerShell, and Linux notification contracts relied upon; the unsupported `dsh-dingo` URL may remain only as zero-weight provenance. Fix the FR-768 link to `FR-768-tool-manifest-declaration-reuse.md`.

### R-2: State submission truth instead of delivery certainty

Change the success contract to:

```python
send_toast(title: str, message: str) -> dict
# -> {"submitted": True, "backend": "osascript" | "powershell" | "notify-send"}
```

Replace every assertion that exit status proves "delivery" with the narrower claim that the OS notification facility accepted the request. State explicitly that notification settings, focus modes, session state, and platform policy may suppress presentation after a successful submission. Keep `ToastError` for failures to submit: unsupported platform, missing executable, timeout, and non-zero process exit. Update the Ideal Result, failure prose, tests, README contract, and demo-log expectation to use `submitted`, not `delivered`.

The macOS hardware witness remains valuable but is a separate human observation. Record its date, OS version, exact command, visible title/body, and observer statement in the FR; do not present `demo-output.log` as proof of pixels.

### R-3: Freeze honest platform prerequisites and the Windows contract

Replace "using only what the operating system already ships" and "nothing installed and nothing configured" with platform-specific preconditions:

- macOS: `osascript` in an interactive logged-in user session.
- Windows: the exact executable, WinRT XML template, notifier application identity/AUMID behavior, and supported Windows/PowerShell versions established by the first-party evidence added under R-1.
- Linux: `notify-send`, an active graphical user session, and a notification daemon; document that `notify-send` is not guaranteed to be installed by the base OS.

Keep the witness boundary explicit: macOS is visually witnessed; Windows and Linux have construction/error-path unit evidence only and must be labeled "not visually witnessed", not represented as observed delivery. Add tests that pin each complete argv, macOS stdin script, Windows child environment and frozen script, `shell=False`, checked exit status, and the finite timeout.

### R-4: Remove the undefined subtitle surface

Delete `subtitle` from the function signature, consumer args, documentation, and manifest comments. The proposal transports only title and message on macOS and Windows, gives Linux no subtitle semantics, and omits subtitle from its injection criteria (`feature-requests/FR-1030-desktop-toast-notification-tool.md:79-106`, `138-142`, `172-177`). A third field is not required by the stated problem and is not authorized in this iteration.

### R-5: Obtain the quickstart side-effect decision and make its proof specific

Record the operator's answer to this product question in the FR:

> May `examples/demos/hello/graph.yaml`, the canonical minimal quickstart, emit an OS desktop notification by default on every successful run?

An affirmative answer is a GATE because the current graph explicitly describes itself as a minimal basic LLM example (`examples/demos/hello/graph.yaml:1-6`), while the proposal adds an externally visible side effect (`feature-requests/FR-1030-desktop-toast-notification-tool.md:124-160`). If the answer is not affirmative, return the plan for a separately judged consumer choice; this judgement does not authorize silently substituting another graph.

With an affirmative answer, update the hello graph's header/description to disclose the notification side effect. Add an integration witness that exercises the committed graph with a subprocess double and proves both paths: successful submission produces `notified.success == true` and `notified.result.submitted == true`; `ToastError` under `on_error: skip` still reaches `END` with `notified.success == false` and the error text. Keep the real macOS run for the committed demo log and manual witness.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised and committed `feature-requests/FR-1030-desktop-toast-notification-tool.md`, `feature-requests/FR-1030.research.md`, and `feature-requests/research-briefs/notify-toast-problem-brief.md` |
| D-2 | `examples/shared/notify_toast.py` with exactly `send_toast(title, message)` and `ToastError` |
| D-3 | `examples/shared/send_toast.tool.yaml` using the existing Python-module manifest runtime |
| D-4 | Focused unit tests for dispatch, process construction, injection boundaries, result shape, and all specified failures |
| D-5 | `examples/demos/hello/graph.yaml` and `examples/demos/hello/demo-output.log`, only after the affirmative R-5 decision |
| D-6 | Integration test for the hello success envelope and skipped-failure envelope |
| D-7 | `examples/shared/README.md` documentation, including prerequisites and witness boundary |
| D-8 | `capabilities/CAP-268-desktop-toast-notification.yaml` with `REQ-YG-672`, tagged tests, and requirement coverage |
| D-9 | One `changelog/unreleased/` fragment |
| D-10 | FR implementation-status update and the required `docs/diary/` Distill entry with a `Seed:` |

Not authorized: changes to `yamlgraph/node_factory/tool_nodes.py`, manifest loading, CLI-wide completion behavior, shell execution utilities, CI or hooks; new runtime dependencies; dependency installers; retry, queueing, scheduling, persistence, notification history, action buttons, icons, sound controls, urgency levels, or provider abstractions; automatic notification in any graph other than the operator-approved hello consumer; claims of visually witnessed Windows or Linux behavior; or additional graph consumers.

## Revised acceptance criteria

- [ ] AC-01: The revised FR, substantive four-to-six-class research record, problem brief, and promoted judgement are committed before implementation begins; every cited local link resolves.
- [ ] AC-02: `examples/shared/notify_toast.py` exposes exactly `send_toast(title: str, message: str) -> dict` and `ToastError`; success is exactly `{"submitted": True, "backend": <selected backend>}`.
- [ ] AC-03: Unit tests patch `sys.platform` and prove `darwin` selects `osascript`, `win32` selects the frozen Windows PowerShell/WinRT command, and `linux` selects `notify-send`.
- [ ] AC-04: Unsupported platforms raise `ToastError` naming `darwin`, `win32`, and `linux` before any subprocess call.
- [ ] AC-05: For every backend, tests pin complete argv, stdin/child environment, `shell=False`, checked exit status, and a finite timeout. Caller title/message values containing quotes, shell substitution, XML-like text, backticks, leading hyphens, and newlines remain data and never enter script source or command strings.
- [ ] AC-06: Windows tests prove title and message enter only through child environment variables, are escaped before XML insertion, and leave the frozen PowerShell script unchanged.
- [ ] AC-07: `FileNotFoundError`, non-zero exit, and timeout each become `ToastError`; no failure returns a `submitted`-shaped mapping.
- [ ] AC-08: All notification unit and integration tests use doubles and spawn no real notification process; the full unit suite passes headless.
- [ ] AC-09: The README states exact platform prerequisites, submission-not-delivery semantics, all failure modes, and the visual witness boundary. Linux explicitly requires `notify-send`, a graphical session, and a notification daemon.
- [ ] AC-10: After the affirmative R-5 decision, `examples/demos/hello/graph.yaml` declares the manifest, calls `send_toast` after `greet`, records `state.notified`, uses `on_error: skip`, and discloses the side effect in its description.
- [ ] AC-11: A graph integration test proves successful submission yields `notified.success == true` and `notified.result.submitted == true`; a raised `ToastError` yields `notified.success == false`, preserves the error text, and still reaches `END`.
- [ ] AC-12: `yamlgraph graph lint examples/demos/hello/graph.yaml` passes, and the graph-authoring validation report records the required smoke command and outcome.
- [ ] AC-13: The committed hello `demo-output.log` comes from the real macOS graph run and contains `notified.success: true` plus nested `submitted: true`; the generic demo-proof gate passing is not by itself sufficient evidence for this criterion.
- [ ] AC-14: The FR records a human-observed macOS notification with date, OS version, exact command, and the visible title/body. Windows and Linux remain explicitly marked not visually witnessed.
- [ ] AC-15: `capabilities/CAP-268-desktop-toast-notification.yaml` defines `REQ-YG-672`; every new test carries `@pytest.mark.req("REQ-YG-672")`; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-16: The changelog fragment, FR implementation status, and Distill diary entry are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not begin enforcement from untracked or otherwise uncommitted FR, research, or problem-brief inputs. | GATE |
| C-2 | The operator must answer R-5 affirmatively in the FR before `examples/demos/hello/graph.yaml` is modified. A negative or absent answer returns the consumer choice to planning. | GATE |
| C-3 | Treat process success only as OS submission acceptance; no implementation, test, documentation, or log may claim guaranteed display or human receipt. | GATE |
| C-4 | No caller-controlled text may be interpolated into script source, command strings, or XML, and no subprocess may use a shell. | GATE |
| C-5 | The Windows implementation may proceed only after the FR freezes its first-party-evidenced PowerShell/WinRT contract and supported environment. | GATE |
| C-6 | Because hello's `graph.yaml` is materially modified, enforcement must use the repository's graph-authoring route and preserve its validation report. | GATE |
| C-7 | Core tool-call, manifest-loader, shell utility, dependency, CI, and hook changes are outside authority. | GATE |

Authority granted: none yet; after R-1 through R-5 and C-1 through C-7 are satisfied and human-reviewed, authority is limited to the frozen contrib/example desktop-notification tool and the explicitly approved hello consumer above.
