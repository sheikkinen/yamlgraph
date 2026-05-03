# Reflection: FR-313 Root README Accuracy Review + Timestamp

**Date:** 2026-05-03
**FR:** FR-313

## Trap

**downstream_fix**

## What Happened

README drift was visible in user-facing text (`PROVIDER` row and reference-doc count wording), but no dedicated root README contract existed to fail when capabilities changed. The document stayed stale even though provider support expanded.

## Root Cause

Documentation correctness checks existed for other READMEs, but root `README.md` lacked boundary-level enforcement. Without a direct contract test, updates depended on manual review cadence.

## What Worked

Applying **normalize at the boundary** resolved the issue: update root README claims to current provider truth and add a focused unit contract that fails on provider-list drift, brittle hardcoded count phrasing, and missing review timestamp.

## Seed

Should README contract tests derive provider identifiers directly from capability registry metadata so front-door docs and architecture requirements cannot diverge?
