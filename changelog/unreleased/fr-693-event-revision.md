---
type: feat
scope: examples
req: REQ-YG-537
---
- **FR-693 Event Revision**: close latent plot threads in the novel_fandom example by adding events (raise + release) or documenting deliberate omissions. Three pure gates: `check_latent_closure` (every `status: latent` thread needs raise+release or a waiver), `check_waiver_integrity` (each waiver names a live thread with reason + decider), and `check_byte_identity` (pre-existing event files are byte-identical — additive only). `create_event`'s `_build_event` now emits a `sequence` total-order value; `create_event.yaml` and the tool `input_mapping` carry `sequence`. The three known texture threads (gunnar_peacetime_identity, heidrun_legacy, youth_resentment) are closed via `story/thread_waivers.yaml`. Agent graph `event_revision.yaml` wires the create_event tool plus the aggregated closure/waiver gate. (REQ-YG-537, REQ-YG-538)
