# Reflection: FR-206 Demo Proof Gate

**Date:** 2026-03-28
**FR:** FR-206 (demo proof gate)
**Trap:** Incomplete verification

## Context

Added a CI gate requiring `demo-output.log` for PRs that modify demo directories—proving demos were actually executed before merge.

## Insight

The diary-gate itself (FR-150) caught that this feat PR lacked a reflection. Meta-enforcement working as designed: gates guarding gates.

## Heuristic

*Enforcement at merge boundary* — Any PR that touches demo code must prove execution. Advisory documentation insufficient; blocking gate required.

## Seed

Could auto-generate demo proof by running `examples/demos/demo.sh` in CI and comparing output hashes?
