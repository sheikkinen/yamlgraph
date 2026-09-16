# The Third Backend Needed Zero Flags — a Probe, Not an Assumption, Said So

**Date:** 2026-09-16
**Trigger:** FR-1049 opencode judge variant — admitting opencode as a third
`JUDGE_BACKEND` in the sole-route judge adapter.

## The trap

`pattern_transfer`. The first two judge backends each carried a permission
machinery: Copilot CLI needed `allow_all_tools: true` because its denial is
silent and it exits 0 (NC-414), and Claude needed `--tools`/`--allowedTools`
(FR-960). The obvious move for the third backend was to reach for a matching
flag — and there is one: opencode's `--auto`, literally documented "auto-approve
permissions (dangerous!)". I almost wrote the FR around mapping `--auto`, and
the alternatives table still carries a dissent row that says the node "should
carry an explicit permission, not trust the ambient default."

## What a five-minute probe said

`opencode run --format json --model … "create probe.txt"` in a fresh directory
returned a `tool_use` event with `state.status: "completed"` and the file on
disk. opencode's headless default auto-approves a **workspace-local** `write`
— the exact operation the judge needs — with no flag at all. The whole
flag-surface collapsed to a single `model` pin. The FR's central claim became
not "which flag do we map" but "FR-1048 deliberately maps none, and the probe
proves none is needed under the probed default."

## The cure

`probe_the_default_before_inventing_the_flag`. When a new backend "obviously"
needs a permission/tool/approval surface, the first move is a live probe of the
vendor's default, not a search for the matching flag. A vendor default is an
external boundary; a probe is the only thing that reads it. The write-probe
cost one tiny billed turn and eliminated a whole permission-mapping design from
the FR — the cheapest bug (the invented flag) was killed in the spec.

**Seed:** Which other backends' "obvious" permission needs are actually vendor
defaults a five-minute probe would dissolve — and is there a `cli` or `claude`
flag in this repo that a fresh probe today would now prove redundant, i.e. a
flag we mapped that the vendor's default already grants?
