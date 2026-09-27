Classify ONE top-level `llm` node that declares no `on_error`. Under FR-1124 its unset policy changes from record-and-continue (record the error, leave the node's state_key unset, keep running downstream nodes) to `fail` (raise, stop the run).

Answer `a` (adopt the new fail default) when a failure of this node should stop the run: a downstream node reads its state_key as a required prerequisite, or the node's output is the graph's main product, or nothing in the graph shows that running on without the output was intended. This is the expected answer for most nodes.

Answer `b` (the author intentionally tolerates a failure and continues) ONLY when the graph text itself shows the output is optional: a downstream reader explicitly handles the key being absent or empty (for example a Jinja `{% if %}` or `| default` on that key, or a router or condition that routes on the key's absence), a comment or description calls the step optional or best-effort, or the node is a side branch whose output no later node or edge depends on and the graph still delivers its product without it.

Evidence must be an exact span from the dossier: the reader, guard, comment, or edge that decides the class. The nodes the dossier lists as referencing the state_key are found by substring match and may include false matches. If the dossier cannot support either class, abstain.
