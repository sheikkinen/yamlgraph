"""FR-685 — Genesis self-correcting pipeline.

SUPERSEDED by FR-686 (agent-first rewrite). The gate-route-fix loop
architecture was replaced by an agent node with graph-tool creation
pipelines. All structural assertions from FR-685 are now invalid —
genesis.yaml no longer has validate, fix_stubs, or persist nodes.

Coverage of genesis structure is provided by test_fr686_agent_first_rewrite.py.
"""
