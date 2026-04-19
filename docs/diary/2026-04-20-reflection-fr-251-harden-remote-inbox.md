# Reflection: FR-251 Harden GitHub Issues Remote Inbox

**Date:** 2026-04-20
**FR:** FR-251
**Branch:** feat/fr-251-harden-remote-inbox

## What Was Done

Hardened the GitHub Issues remote inbox (FR-243) against abuse: added an allowlist gate (`.chaplain/allowed-authors.txt`, one login per line), body size cap (`BODY_SIZE_CAP=10000` chars, truncated with warning), and audit header (`<!-- author: @login -->`) prepended to every imported file. Author login is fetched before title/body for early rejection. When the allowlist file is absent, all authors are accepted (opt-in security, not opt-out).

## Cognitive Trap: Expanded Trust Boundary Without Guard

FR-243 noted in its Security section: "GitHub Issues open the Chaplain pipeline to anyone with issue-writing permission." The fix (allowlist + body cap) was planned but deferred to a follow-up FR. This is **detection without enforcement** at the design level — the security concern was identified, documented, and then deferred past the initial ship. FR-251 closes that gap.

The lesson: when a security gap is identified during planning (FR-243's Security note), the follow-up FR should be created *immediately* and linked, not left as a comment. A documented gap without a tracking FR will be forgotten.

## Heuristic

**Security notes become FRs, not prose**: Any security concern identified in a Feature Request must be immediately converted to a follow-up FR with `Priority: HIGH` and linked from the original. A security note in prose is advisory; a follow-up FR is enforceable.

## Seed

The allowlist is a flat text file — simple, auditable. But it requires a repo commit to add a new trusted author. Could the allowlist itself be managed via GitHub Issues (a `chaplain-allowlist` label on an issue opened by a repo owner)? That would close the bootstrap problem: a new trusted contributor could be added without cloning the repo. The recursion is intentional — the inbox secures itself.
