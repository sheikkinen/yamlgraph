"""Abstraction-span — standalone YAMLGraph example (FR-589).

Scores each prompt's abstraction-span (how many *distinct kinds* of cognitive
operation it asks for in one output) with an LLM, then runs a deterministic
separation gate against known monolith/clean labels.
"""
