# Feature Request: Colorize CLI graph list output

**Priority:** LOW
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-26
**First consumer / first event:** a developer running `yamlgraph graph
list` in a terminal, at the moment the list exceeds one screen.

<!-- FR-890 D-8 fixture: intentionally lacks a **Research:** field.
     Used to witness that the judge grants no authority to a
     post-activation FR without committed research evidence (AC-13). -->

## Summary

Add ANSI color to `yamlgraph graph list` output: graph names in cyan,
descriptions dimmed, so long listings scan faster.

## Value Statement

Developers scanning many graphs find the one they need faster.

## Problem

`yamlgraph graph list` prints monochrome text; with 100+ graphs the
name/description boundary is hard to scan.

## Ideal Result

Names and descriptions are visually distinct in any ANSI terminal, with
a `--no-color` escape and automatic suppression when stdout is not a
TTY.

## Proposed Solution

Wrap the existing list formatter with ANSI codes gated on
`sys.stdout.isatty()` and a `--no-color` flag.

## Acceptance Criteria

- [ ] Names render cyan, descriptions dim, when stdout is a TTY
- [ ] `--no-color` and non-TTY output remain byte-identical to today
- [ ] Tests added

## Alternatives Considered

- rich/textual dependency — rejected, stdlib ANSI suffices.

## Related

- `yamlgraph/cli.py`
