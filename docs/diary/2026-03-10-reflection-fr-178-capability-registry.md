# Diary Reflection: FR-178 Capability Registry

**Date**: 2026-03-10
**FR**: FR-178, FR-177, FR-180

## Insight

The capability registry work collided with FR-182 (hello world demo) on CAP-65/REQ-YG-161 IDs. This revealed a coordination gap: multiple FRs can claim the same ID if they run in parallel or the ID registry is not checked.

## Trap: ID collision from parallel enforcement

Two independent enforcement pipelines assigned the same IDs (CAP-65, REQ-YG-161) to unrelated features:
- FR-182 used them for "Hello Demo Documentation"
- FR-178 used them for "Append-Only Capability Registry"

Neither checked if the IDs were already in use by another concurrent pipeline.

## Cure: FR-180 plan-phase ID reservation

The `.chaplain/id-registry.yaml` file, introduced in FR-180, provides a central registry where FRs reserve their ID ranges at plan time. Enforcement pipelines check this registry before assigning new IDs.

## Heuristic

> **When multiple pipelines touch shared namespace (IDs, state keys, file paths), reserve at plan time — not at implementation time.**

## Seed

Should the ID registry be merged with the capability registry? A single source of truth for all CAP/REQ IDs would eliminate the dual-registry synchronization burden.
