"""A2A protocol integration (FR-717): server and message translation.

Seam contract (.importlinter): a2a may import the runtime it serves,
but nothing outside this package reaches a2a internals except through
these names.
"""

from yamlgraph.a2a.message import parse_a2a_message
from yamlgraph.a2a.server import create_a2a_app

__all__ = ["create_a2a_app", "parse_a2a_message"]
