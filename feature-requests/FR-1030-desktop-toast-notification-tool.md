# Feature Request: FR-1030 — Shared desktop-toast notification tool, consumed by the hello demo

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced 2026-09-08. Authority granted by the operator, who ruled
that the opening prompt conferred full autonomy for this arc and that the
review's P1 was therefore incorrect — the authority the author could not
self-certify was held by the operator all along, and is now on the record.
**Effort:** 0.5 day
**Requested:** 2026-09-08
**First consumer / first event:** `examples/demos/hello/graph.yaml`, at the
moment the `greet` node returns — the smallest committed graph in the
repository submits a desktop notification carrying the greeting it just
generated. The tool ships with that consumer in the same change; it is
not an unconsumed affordance.
**Research:** [FR-1030.research.md](FR-1030.research.md)
**Judgement:** [FR-1030-desktop-toast-notification-tool.judgement.md](FR-1030-desktop-toast-notification-tool.judgement.md)
**Prior art:**
- [FR-907-smtp-email-tool.md](FR-907-smtp-email-tool.md) — the same
  absence, narrowed rather than closed: SMTP is remote, credentialed, and
  store-and-forward. This FR is local, zero-config, and sub-second. Both
  are shared `examples/shared/` transports that raise on every failure
  path; this one reuses that contract deliberately.
- [FR-478-dm-v2-button-press-feedback.md](FR-478-dm-v2-button-press-feedback.md)
  — feedback *inside a web UI the human is already looking at*. This FR
  addresses the case where the human is looking at something else.
- `call-me-maybe` (`~/.copilot/skills/call-me-maybe/SKILL.md`) — outbound
  phone escalation, explicitly last-resort and "not a convenience". Its
  own "When NOT to Use" list names the band this FR serves.
- [FR-768-tool-manifest-declaration-reuse.md](FR-768-tool-manifest-declaration-reuse.md)
  / FR-769 / FR-773 — the shared-tool manifest convention this FR
  conforms to; no new mechanism is invented.
- [FR-778-tool-call-on-error-fail.md](FR-778-tool-call-on-error-fail.md) —
  the `on_error` envelope contract the hello consumer relies on.
- FR-837 / FR-838 (gitclaw source-health) were retrieved on the noun
  "notify" only; they concern assembly recovery, not user-facing
  notification. Not applicable.
- `054-copilot-cli-reflection.md` was retrieved on "notify, problem,
  brief"; it is a reflection document, not a proposal. Not applicable.

## Summary

Add one shared tool, `examples/shared/notify_toast.py`, exposing
`send_toast(title, message)`. It submits a native desktop notification on
macOS, Windows, and Linux through the facility each OS already provides,
and raises `ToastError` on every failure path. Declare it with an FR-768
manifest and consume it from `examples/demos/hello/graph.yaml` so the
quickstart graph announces its own greeting to the human at the keyboard.

## Value Statement

An operator running graphs on a busy machine learns that a run finished —
and what it produced — without switching windows or re-reading scrollback.

## Problem

See [the problem brief](research-briefs/notify-toast-problem-brief.md) for
the closed incident record. In short: every output channel YAMLGraph has
requires the human to already be looking at it (stdout, `--full`,
LangSmith) or costs real setup and real latency (SMTP, phone). A
repository-wide grep for `toast|osascript|notify-send|terminal-notifier`
returns zero hits in any Python or YAML file: the local, immediate,
low-config band is empty. All six existing `examples/shared/` tools are
silent transport for machine consumers; none addresses the person in the
room.

## Ideal Result

Any graph in the repository can tell the human "I am done, and here is
the one line that matters" with a single YAML node, on whichever machine
the operator happens to be using. The channel never claims more than it
achieved, never becomes an injection surface for model- or user-authored
text, and never requires a desktop to exist for the test suite to pass.
The smallest demo in the repository demonstrates it, so the capability is
discovered by anyone following the quickstart rather than by reading a
tool inventory.

## Proposed Solution

### The tool

`examples/shared/notify_toast.py`:

```python
send_toast(title: str, message: str) -> dict
# -> {"submitted": True, "backend": "osascript" | "powershell" | "notify-send"}
```

**`submitted`, not `delivered`.** A zero exit status proves the operating
system's notification facility *accepted* the request. It does not prove a
human saw anything: Apple documents presentation as depending on the
user's Notifications settings, Windows honours Focus Assist and per-app
policy, and a freedesktop notification daemon may drop or queue.
Citations in [FR-1030.research.md](FR-1030.research.md). The return value
says exactly what was proven and nothing more.

Backend selected from `sys.platform`, once, at call time:

| `sys.platform` | Backend | Mechanism | Caller text travels as |
|---|---|---|---|
| `darwin` | `osascript` | frozen AppleScript read from **stdin**, `on run argv` | `argv` |
| `win32` | `powershell` | frozen script driving WinRT `ToastNotificationManager` | child **environment** |
| `linux` | `notify-send` | fixed argv with `--` terminator | `argv` |

Any other `sys.platform` raises `ToastError` naming `darwin`, `win32`,
`linux` **before** any subprocess is spawned — the same shape as
`validate_vision_provider()` (FR-776).

**The injection boundary is closed by construction, not by escaping.**
No caller-supplied text is ever interpolated into a command string,
script source, or markup:

- macOS — the AppleScript source is a frozen literal delivered on stdin
  (`osascript - <title> <message>`); the text arrives as `item 1 of argv`
  / `item 2 of argv`. There is no AppleScript string to escape.
- Windows — the PowerShell script is a frozen literal; the text arrives
  as `$env:YG_TOAST_TITLE` / `$env:YG_TOAST_MESSAGE` and is inserted into
  the toast XML through `XmlDocument.CreateTextNode`, the same text-node
  path Microsoft's own example uses, so XML metacharacters are data by
  construction rather than by string escaping.
- Linux — fixed argv with a `--` terminator, so text starting with `-`
  cannot become a flag.

Every invocation is `shell=False`, fixed argv, checked exit status,
finite timeout. `yamlgraph/tools/shell.py`'s `shlex.quote()` discipline is
deliberately **not** reused: no shell is involved anywhere, and quoting a
value no shell will parse would be theatre that obscures where the real
boundary is. Both research personas that recommended `shlex.quote()` here
are dispositioned in the table below.

**Failure is always loud.** Missing binary, non-zero exit, timeout, and
unsupported platform all raise `ToastError`. No code path returns a
`submitted`-shaped mapping on failure — an unattended caller cannot
report green while notifying nobody (Commandment 6).

Manifest sibling `examples/shared/send_toast.tool.yaml` per FR-768.

### Frozen platform contracts and prerequisites

Not "nothing installed, nothing configured". The honest preconditions,
each traceable to first-party documentation cited in the research record:

| Platform | Executable | Requires | Ships with the OS? |
|---|---|---|---|
| macOS | `osascript` | an interactive, logged-in user session | yes |
| Windows | `powershell.exe` (Windows PowerShell 5.1, in-box) | Windows 10 build 10.0.10240 or later; an interactive desktop session; a notifier identity (AUMID) belonging to a Start-menu shortcut | yes |
| Linux | `notify-send` (libnotify) | an active graphical session **and** a running notification daemon owning `org.freedesktop.Notifications` | **no — `notify-send` is not guaranteed to be installed** |

**Windows contract, frozen (judgement C-5).** Microsoft Learn states:
"For a desktop app to display a toast, the app must have a shortcut on
the Start screen. The shortcut must have an `AppUserModelID`." A desktop
process therefore cannot raise a toast anonymously. The implementation
uses `CreateToastNotifier(String)` with the in-box Windows PowerShell
AUMID
`{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe`,
whose Start-menu shortcut Windows itself installs, and follows the
content path from Microsoft's own example on the same page:
`GetTemplateContent(ToastTemplateType.ToastText02)` →
`GetElementsByTagName("text")` → `CreateTextNode(...)` →
`ToastNotification(xml)` → `.Show(toast)`. The toast is therefore
attributed to Windows PowerShell in Action Center. That attribution is a
stated consequence, not a defect: giving YAMLGraph its own AUMID would
require installing a Start-menu shortcut, which is outside this FR's
authority.

The `win32api.MessageBox`/`ctypes` route suggested by one persona is
**rejected**: freedesktop's Desktop Notifications Specification v1.3
explicitly excludes "modal message boxes" from what a notification is,
and a modal dialog steals focus and blocks — the inverse of the
requirement.

### The consumer

Operator decision on judgement R-5 / C-2, recorded verbatim: the operator
opened this work with *"new shared tool under examples/shared - user
notification via system toast functionality. **extend hello graph to
display the hello world greeting using the tool**"*, then narrowed scope
with *"note: both mac and pc support"*. The canonical quickstart
acquiring a desktop-notification side effect is therefore requested, not
inferred. The graph's own description is updated to disclose it.

```yaml
description: >
  Simple greeting generator demonstrating basic LLM usage, then submitting
  the greeting as a desktop notification (FR-1030). Running this graph
  raises a system toast on macOS, Windows, and Linux.

tools:
  send_toast:
    manifest: ../../shared/send_toast.tool.yaml

nodes:
  greet:
    # unchanged
  notify:
    type: tool_call
    tool: send_toast
    args:
      title: "Hello, {state.name}"
      message: "{state.greeting.greeting}"
    state_key: notified
    on_error: skip

edges:
  - from: START
    to: greet
  - from: greet
    to: notify
  - from: notify
    to: END
```

`on_error: skip` is deliberate and belongs in the YAML, not in the tool.
The tool always raises; the *graph* declares that a headless box, or a
Linux box without `notify-send`, should still finish the quickstart.
FR-778's skip path writes a visible failure envelope (`success: false`
plus the error string) into `state.notified`, so a suppressed toast is
recorded in the result, not swallowed. The quickstart in
`.github/copilot-instructions.md` keeps working over SSH; the failure is
legible when it happens.

## Judgement fold (R-1 … R-5)

| Revision | Disposition |
|---|---|
| **R-1** research evidence | **Folded, one refusal.** A second run of the sole route was executed and both runs are now published in the research record with the failed persona preserved. First-party citations for AppleScript, WinRT, and freedesktop were added as a labelled FR-author section, and the unconfirmed `awesome-dsh-plugin.com` URL is retained at explicitly zero evidentiary weight. The FR-768 link is corrected. **Refused:** the "four to six genuine classes" quota. Two independent runs over the same closed brief converged on three classes; `scripts/research_preflight.py` states the distinct-class count is advisory and never blocking (FR-896 R-2), and hand-adding a fourth class would put words in a persona's mouth. The convergence is published rather than papered over. |
| **R-2** submission truth | **Folded.** `delivered` → `submitted` in the signature, README, tests, demo-log expectation, and Ideal Result. Manual macOS witness recorded under *Implementation Status* with date, OS version, command, and visible text; `demo-output.log` is no longer offered as proof of pixels. |
| **R-3** honest prerequisites and frozen Windows contract | **Folded.** Prerequisite table above; "nothing installed and nothing configured" removed; Linux `notify-send` explicitly flagged as not guaranteed present; Windows AUMID/PowerShell/WinRT contract frozen against Microsoft Learn. |
| **R-4** remove `subtitle` | **Folded.** Removed from signature, consumer args, manifest, README, and tests. (For the record: Apple documents a native `subtitle` parameter, but Linux has no equivalent, so the judge's cross-platform-consistency reasoning holds.) |
| **R-5** quickstart side-effect decision | **Folded.** Operator's affirmative recorded verbatim above; graph description discloses the side effect; integration test covers both the success envelope and the `on_error: skip` failure envelope. |

## Acceptance Criteria

The judgement's revised list, restated here as the working contract.

- [ ] AC-01 Revised FR, research record, problem brief, and promoted
      judgement are committed before implementation begins; every cited
      local link resolves.
- [ ] AC-02 `examples/shared/notify_toast.py` exposes exactly
      `send_toast(title: str, message: str) -> dict` and `ToastError`;
      success is exactly `{"submitted": True, "backend": <backend>}`.
- [ ] AC-03 Unit tests patch `sys.platform` and prove `darwin` →
      `osascript`, `win32` → the frozen PowerShell/WinRT command,
      `linux` → `notify-send`.
- [ ] AC-04 Unsupported platforms raise `ToastError` naming `darwin`,
      `win32`, `linux` before any subprocess call.
- [ ] AC-05 For every backend, tests pin complete argv, stdin/child
      environment, `shell=False`, checked exit status, and a finite
      timeout. Title/message containing quotes, `$(...)`, backticks,
      XML-like text, leading hyphens, and newlines remain data and never
      enter script source or command strings.
- [ ] AC-06 Windows tests prove title and message enter only through
      child environment variables, reach the XML through
      `CreateTextNode`, and leave the frozen PowerShell script unchanged.
- [ ] AC-07 `FileNotFoundError`, non-zero exit, and timeout each become
      `ToastError`; no failure returns a `submitted`-shaped mapping.
- [ ] AC-08 All notification tests use doubles and spawn no real
      notification process; the full unit suite passes headless.
- [ ] AC-09 `examples/shared/README.md` states exact platform
      prerequisites, submission-not-delivery semantics, all failure
      modes, and the visual witness boundary; Linux explicitly requires
      `notify-send`, a graphical session, and a notification daemon.
- [ ] AC-10 `examples/demos/hello/graph.yaml` declares the manifest,
      calls `send_toast` after `greet`, records `state.notified`, uses
      `on_error: skip`, and discloses the side effect in its description.
- [ ] AC-11 A graph integration test proves successful submission yields
      `notified.success == true` and `notified.result.submitted == true`;
      a raised `ToastError` yields `notified.success == false`, preserves
      the error text, and still reaches `END`.
- [ ] AC-12 `yamlgraph graph lint examples/demos/hello/graph.yaml`
      passes and the graph-authoring validation report records the smoke
      command and outcome.
- [ ] AC-13 The committed hello `demo-output.log` comes from a real
      macOS run and contains `notified` with `success: True` and nested
      `submitted: True`.
- [ ] AC-14 This FR records a human-observed macOS notification with
      date, OS version, exact command, and visible title/body. Windows
      and Linux remain explicitly marked not visually witnessed.
- [ ] AC-15 `capabilities/CAP-268-desktop-toast-notification.yaml`
      defines `REQ-YG-672`; every new test carries
      `@pytest.mark.req("REQ-YG-672")`; `scripts/req_coverage.py
      --strict` passes.
- [ ] AC-16 Changelog fragment, FR implementation status, and Distill
      diary entry are present.

## Witness boundary (AC-14)

**macOS — visually witnessed.** Recorded at implementation time; see
*Implementation Status*.

**Windows and Linux — not visually witnessed.** Their argv/environment
construction, `shell=False`, timeout, and error conversion are witnessed
by unit tests; the pixels are not.

This is a stated limit with a reason, not a deferral. The repository's
only Windows host (`Huutokauppakone`, FR-945/FR-946) is reachable solely
over WinRM, which executes in a **non-interactive session**. Microsoft's
own toast contract requires an interactive desktop session, so a green
WinRM run would prove nothing about what a person sitting at that PC
sees — it would be `proof_by_placement` in a different costume. No
automated Windows witness exists in this repository at any price; only a
human at that keyboard can produce one. The README says so in the same
words.

## Alternatives Considered

Dispositioned from [FR-1030.research.md](FR-1030.research.md) (both runs):

| Candidate | Persona | Disposition |
|---|---|---|
| Native OS notification APIs via subprocess (`osascript` / WinRT / `notify-send`) | os-infra-primitivist (both runs) | **Adopted.** Its run-1 warning about WinRT COM is honoured by driving WinRT from PowerShell rather than binding COM from Python. Its `shlex.quote()` recommendation is **not** adopted: no shell is invoked, so quoting would misplace the boundary. |
| Shared leaf tool + FR-768 manifest, consumed by the hello demo | yamlgraph-native-planner, data-process-planner | **Adopted as the shape**, with two corrections. (a) `win32api.MessageBox` via `ctypes` is a **modal dialog**, which freedesktop's spec explicitly excludes from the notification category and which steals focus — replaced by the WinRT toast path. (b) "no desktop → no-op return, not failure" is **rejected** as the success-shaped return Commandment 6 forbids; tolerance is declared in the graph's `on_error`, where it is visible. |
| Mandatory stdout completion summary on every graph run | Subtractionist (run 1, `pursue`) | **Rejected.** It restates the problem it is asked to dissolve: the brief's premise is that stdout requires the terminal to be in front. A louder message in an unwatched window is still unwatched. |
| Declare local notification out of scope for YAMLGraph core; leave it to graph authors' own Python | Subtractionist (run 2, `dissent`) | **Partially adopted — this is what the FR does.** The tool lands in `examples/shared/`, not in `yamlgraph/`; no core module is touched; the judgement classifies it contrib/example. The dissent's own remedy and this FR's shape coincide. |
| `dsh-dingo` / `dsh-notifier` plugin precedent | librarian (both runs) | **Cited, zero weight.** The pattern matches what was adopted, but neither returned URL could be confirmed, so first-party Apple/Microsoft/freedesktop documentation carries the argument instead. Recorded rather than quietly dropped. |

Also considered and rejected without a persona: adding `plyer`,
`desktop-notifier`, or `win10toast` as a dependency — each is a governed
direct import (FR-761) for behaviour the OS already ships, and none is
maintained across all three targets.

## Related

- `examples/shared/smtp_email.py`, `examples/shared/smtp_email.tool.yaml`
- `yamlgraph/node_factory/tool_nodes.py` (FR-772 inline args, FR-778
  `on_error`)
- `scripts/check_demo_proof.sh` (`demo-proof-check` pre-commit hook)
- `.github/copilot-instructions.md` quickstart (runs the `hello` graph)

## Implementation Status

**Enforced 2026-09-08**, under authority granted by the operator after the
review.

The sequence is worth recording because the intermediate state was real. An
earlier revision of this section read "Enforced. All sixteen acceptance
criteria met" while required revision R-1 stood refused — the author ruling
on his own refusal. `scripts/review.sh` found that independently (P1), the
section was corrected to *authority contested*, and only then did the
operator supply the missing grant. The grant was always his to give; the
author's error was assuming it rather than asking. The mechanism is
recorded in
[`diary-2026-09-08-reflection-fr-1030-every-gate-that-could-stop-me.md`](../docs/diary/diary-2026-09-08-reflection-fr-1030-every-gate-that-could-stop-me.md).

### Review findings and their disposition

From `tmp/draft-review.md` (advisory; the merge decision is the operator's,
and these are his rulings):

| # | Finding | Disposition |
|---|---|---|
| P1 | Authority not granted | **Incorrect.** The opening prompt authorised full autonomy for this arc. The reviewer could not see that input; the operator ruled it. Closed. |
| P2 | `ARCHITECTURE.md` conflicts with `main` (#638 CAP-267/REQ-YG-671) | **Fixed.** Merged `origin/main` and regenerated; CAP-267/REQ-YG-671 and CAP-268/REQ-YG-672 both present. |
| P3 | The Windows AUMID is asserted by a test repeating this module's own constant — no first-party evidence about Windows | **Known, accepted, postponed.** The limitation is real and stated in the READMEs; the Windows path stays marked not visually witnessed. No follow-up FR is promised. |
| P4 | AC-05's complete-argv assertion is met on macOS and Linux, partial on Windows | **Known, accepted, postponed.** Same standing as P3: recorded as a real gap, not scheduled. |
| P5 | Two changelog fragments and 24 FR-1027 confessions exceed the frozen D-9 scope | **Insignificant.** Ruled acceptable. The confessions pay an inherited debt the noqa gate surfaced; the second fragment describes a genuinely separate user-visible change. |
| P6 | The FR does not cite its authoring brief | **Fixed.** The D-5 row below cites [`authoring-briefs/fr-1030-hello-toast-brief.md`](authoring-briefs/fr-1030-hello-toast-brief.md). |

P3 and P4 are accepted limitations, not deferrals: no target FR, no date,
and none implied. If Windows delivery is ever needed in earnest, the
evidence gap named in P3 is where that work starts.

### What was built (accurate as of this commit)

| Deliverable | Landed as |
|---|---|
| D-1 plan artifacts | `FR-1030-*.md`, `.research.md`, `.judgement.md`, `research-briefs/notify-toast-problem-brief.md` (commit `c63b3424`, before implementation) |
| D-2 tool | `examples/shared/notify_toast.py` |
| D-3 manifest | `examples/shared/send_toast.tool.yaml` |
| D-4 unit tests | `tests/unit/test_shared_notify_toast.py` — 39 tests (AC-05 incomplete on Windows, see P4) |
| D-5 consumer | `examples/demos/hello/graph.yaml` + `demo-output.log`, authored via [`authoring-briefs/fr-1030-hello-toast-brief.md`](authoring-briefs/fr-1030-hello-toast-brief.md) |
| D-6 composition test | `tests/unit/test_fr1030_hello_toast_consumer.py` — 4 tests |
| D-7 docs | `examples/shared/README.md`, `examples/demos/hello/README.md` |
| D-8 traceability | `capabilities/CAP-268-desktop-toast-notification.yaml`, `REQ-YG-672`, `ARCHITECTURE.md` |
| D-9 changelog | two fragments — one beyond the frozen scope, ruled insignificant (P5) |
| D-10 status + diary | this section; `docs/diary/diary-2026-09-08-reflection-fr-1030-every-gate-that-could-stop-me.md` |

### AC-14 witness record

**macOS — visually witnessed.**

- Date: 2026-09-08T03:03:04Z
- OS: macOS 26.3.1 (`sw_vers -productVersion`)
- Command:
  `python -c "from examples.shared.notify_toast import send_toast; send_toast('FR-1030 witness', 'Watch now: this is the macOS visual witness for the shared toast tool.')"`
- Returned: `{'submitted': True, 'backend': 'osascript'}`
- Observer: the operator, asked directly whether the notification appeared
  on screen, answered **"Yes — banner appeared"**. The first send was not
  observed (operator was not looking), so it was re-sent and confirmed;
  both attempts are recorded rather than only the successful one.

**Windows and Linux — not visually witnessed.** Unchanged from the
*Witness boundary* section above. The operator was offered the option of
running one command by hand on the Windows host and chose to ship with the
limit stated, so no Windows visual witness exists and none is claimed.

### Deviations from the frozen plan

0. **Authority was claimed before it was granted.** The claim was wrong when
   made; the operator has since granted it (see above). Recorded because
   the grant does not retroactively make the assumption sound.
1. **One judgement revision was refused, not folded** — R-1's "four to six
   genuine solution classes". Reason and evidence in the *Judgement fold*
   table above. The refusal stands on the merits; what was missing was
   someone other than its author saying so.
2. **`verification` block added to the `notify` node**, beyond the YAML
   quoted in *The consumer*. Lint rule W022 fires on `on_error: skip`
   without a verification question. The authoring route's first pass
   repaired it with `"Will return non-empty"`, which is **vacuous here** —
   the FR-778 envelope is a non-empty dict on the failure path too, so that
   predicate passes when no toast went out. The brief was amended to fix
   the question as `"Will contain submitted"` (the literal appears only in
   a real success envelope) and the route was re-run from a clean graph.
   Both authoring runs are in the record.
3. **W017 remains** (`on_error: skip` silently drops failures). Accepted,
   not repaired: the skip is the graph-level tolerance the FR argues for,
   and the composition test asserts the failure is recorded rather than
   dropped, which is the substance the warning is a proxy for.
4. **Out-of-scope commit included**: `chore(confessions)` documenting 24
   `noqa` suppressions from FR-1027 that the repo-wide gate reported the
   moment any `.py` file was staged. Owned rather than bypassed; kept in a
   separate commit so it can be read and reverted independently.
