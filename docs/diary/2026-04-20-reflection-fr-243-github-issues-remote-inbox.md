# Reflection: FR-243 GitHub Issues as Remote Chaplain Inbox

**Date:** 2026-04-20
**FR:** FR-243
**Branch:** feat/fr-243-github-issues-remote-inbox

## What Was Done

Extended `watch.sh` to poll GitHub Issues labeled `chaplain` as a remote inbox. When an issue is found, its body is written to `.chaplain/inbox/` as a markdown file, then the issue is closed and labeled `chaplain-processed` to prevent reprocessing. This enables the Plan→Judge→Enforce pipeline to be triggered from any device with GitHub access.

## Cognitive Trap: Local Filesystem Parochialism

The Chaplain daemon was designed exclusively around the local filesystem, implicitly assuming all contributors have shell access to the repo. This is a form of **infrastructure self-exemption** — the meta-tooling imposed no constraint on its own accessibility, while the workflows it governed could be triggered from anywhere.

The fix was mechanical (two shell script additions), but the insight is broader: any pipeline with a single, local entry point becomes a bottleneck. The boundary where proposals enter should be as wide as possible.

## Heuristic

**Remote by default**: Every internal pipeline's entry point should accept input from the narrowest channel available (local file) _and_ the widest practical channel (authenticated remote API). Adding remote access later is always harder than designing for it initially.

## Seed

If GitHub Issues can feed the Chaplain inbox, can PR comments? Could a `/chaplain topic description` comment in a PR automatically trigger a Plan cycle for that topic, inline with the review? That would close the loop between code review and feature planning entirely.
