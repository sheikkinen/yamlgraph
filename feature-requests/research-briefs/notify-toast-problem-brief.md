# Problem brief: a graph that finishes has no way to tell the human it finished

<!-- Closed input for the research route (FR-890). Incident record only;
     no solution content. -->

**Prior art:** filename-noun hits on other `*-problem-brief.md` files are
unrelated subject matter — not applicable. `FR-907` (shared SMTP tool) is
genuine adjacent precedent and is distinguished below: it is a remote,
credentialed, store-and-forward channel. `call-me-maybe` (outbound phone
escalation, `~/.copilot/skills/call-me-maybe/SKILL.md`) is genuine adjacent
precedent: last-resort, real-phone, explicitly "not a convenience".
`FR-478` (DM v2 button-press feedback) is genuine adjacent precedent: it
gives feedback inside a web UI the human is already looking at.

## Problem statement

Every output channel a YAMLGraph run has today requires the human to
already be looking at something. Stdout requires the terminal to be in
front; `--full` result blocks require the terminal to be in front;
LangSmith traces require a browser and a deliberate click;
`examples/shared/smtp_email.py` requires SMTP credentials, a mail client,
and tolerates minutes of delay; the `call-me-maybe` skill rings a real
phone and is documented as last-resort, never routine. There is nothing
in between: no channel that costs nothing to configure, arrives in under
a second, and reaches a human sitting at the same machine but with the
terminal behind another window.

The operator runs long graphs and agent pipelines on a machine he is
using for other work at the same time. A run that ends — successfully or
not — is silent. The human discovers completion by polling: switching
windows, re-reading a scrollback, or asking. Every graph in
`examples/demos/` ends this way; the `hello` demo, the smallest possible
consumer, prints a `RESULT` block into a terminal nobody is watching.

The gap is also structural, not only ergonomic. `examples/shared/` holds
six tools and every one of them is silent transport for a *machine*
consumer: search results, generated images, split PDF pages, rendered
page PNGs, image descriptions, email to a remote inbox. None of them
address the human at the keyboard. A graph author who wants to say "I am
done" to the person in the room has to write Python outside the graph.

The machines in question are not one platform. The operator works on
macOS (this repository's primary checkout) and on Windows (the
`Huutokauppakone` LAN host used by the `lan-delegate` and `lan-recon`
skills, a self-hosted Windows service runner referenced by
`issue-delegate`). A channel that only works on the mac would be absent
exactly where unattended delegated runs happen.

## Classification

enforcement/latency-critical

## Constraints

- Must work on macOS and on Windows. Both are first-class; neither is a
  fallback for the other. Linux is present in CI containers.
- No new runtime dependency may be required for the tool to work on
  either platform. The repository's dependency governance (FR-761)
  treats every new direct import as a governed addition.
- CI runs headless: there is no logged-in desktop session, no
  notification centre, and no user to see anything. The repository's
  own test suite must pass with no desktop present, and the
  `demo-proof-check` pre-commit gate requires a committed
  `demo-output.log` that was produced by a real run of the graph next to
  it.
- Any subprocess invocation carrying user-controlled text is an
  injection boundary. `yamlgraph/tools/shell.py` establishes the
  repository's existing position: user variables are `shlex.quote()`d
  before shell substitution, and tools elsewhere run `shell=False` with
  fixed argv.
- Scripture forbids success-shaped returns on failure paths
  (Commandment 6): a channel that reports delivered while delivering
  nothing is worse than one that raises.
- Shared example tools follow the FR-768 manifest convention: a
  `*.tool.yaml` sibling naming `name`, `description`, and a
  `runtime: {type, module, function}` triple, consumed by a committed
  demo graph.
- `examples/demos/hello/` is the repository's canonical minimal example
  and is referenced from `.github/copilot-instructions.md` as the
  quickstart smoke test; whatever lands must keep that quickstart
  runnable and its `demo-output.log` honest.

## Witnessed incidents

- This session (2026-09-08): a survey of `examples/shared/` found six
  tools — `websearch.py`, `replicate_tool.py`, `vision_tool.py`,
  `split_document.py`, `render_page.py`, `smtp_email.py` — and a
  `grep -rniE "toast|osascript|notify-send|terminal-notifier"` across
  the repository returned zero hits in any Python or YAML file. The only
  matches were prose in `FR-478`, one diary entry, and
  `docs-planning/plan-npc-web-ui.md`. No local user-notification
  capability exists anywhere in the codebase.
- `FR-907`/`CAP-252` shipped the SMTP tool because the
  `yamlgraph-daily-digest` graph had no way to reach a human with the
  bulletin it archived. That FR solved the *remote, asynchronous* case
  and left the local, immediate case untouched — the same absence,
  narrowed rather than closed.
- The `call-me-maybe` skill exists precisely because the escalation gap
  was felt sharply enough to justify wiring Twilio, ElevenLabs, and a
  Gemini call graph. Its own "When NOT to Use" list ("routine
  questions", "non-urgent matters") documents the unserved band: there
  is a class of message too important for silent scrollback and too
  trivial for a phone call, and nothing serves it.
- Operator request, this session: "user notification via system toast
  functionality", followed by the explicit scope correction "both mac
  and pc support" — the cross-platform requirement was raised by the
  human before any implementation was proposed, not discovered later.
