"""CLI commands for A2A server (FR-208).

Provides `yamlgraph a2a serve` and `yamlgraph a2a card` subcommands.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def cmd_a2a_dispatch(args: argparse.Namespace) -> None:
    """Dispatch a2a subcommands."""
    subcmd = getattr(args, "a2a_command", None)

    if subcmd == "serve":
        _cmd_a2a_serve(args)
    elif subcmd == "card":
        _cmd_a2a_card(args)
    else:
        print("Usage: yamlgraph a2a {serve|card} [options]")
        sys.exit(1)


def _resolve_patterns(args: argparse.Namespace) -> list[str]:
    """Resolve graph patterns from CLI args."""
    graph_path = getattr(args, "graph_path", None)
    if graph_path:
        path = Path(graph_path).resolve()
        if path.is_file():
            return [str(path)]
        elif path.is_dir():
            return [str(path / "*.yaml"), str(path / "*/*.yaml")]
        else:
            print(f"✗ Path not found: {graph_path}")
            sys.exit(1)

    # Default: discover from known locations
    from yamlgraph.discovery import DEFAULT_GRAPH_PATTERNS

    project_root = Path.cwd()
    return [str(project_root / p) for p in DEFAULT_GRAPH_PATTERNS]


def _cmd_a2a_serve(args: argparse.Namespace) -> None:
    """Start A2A HTTP server."""
    try:
        import uvicorn
    except ImportError:
        print("✗ uvicorn not installed. Install with: pip install uvicorn")
        sys.exit(1)

    from yamlgraph.a2a.server import create_a2a_app

    patterns = _resolve_patterns(args)
    host = getattr(args, "host", "0.0.0.0")  # noqa: S104  # nosec B104
    port = getattr(args, "port", 8080)

    print(f"🚀 Starting A2A server on {host}:{port}")
    print(f"📋 Agent Card: http://{host}:{port}/.well-known/agent-card.json")

    app = create_a2a_app(
        graph_patterns=patterns,
        host=host,
        port=port,
    )

    uvicorn.run(app, host=host, port=port)


def _cmd_a2a_card(args: argparse.Namespace) -> None:
    """Print Agent Card JSON for discovered graphs."""
    from yamlgraph.a2a.server import build_agent_card
    from yamlgraph.discovery import discover_graphs

    patterns = _resolve_patterns(args)
    port = getattr(args, "port", 8080)
    host = getattr(args, "host", "localhost")

    graphs = discover_graphs(patterns)

    if not graphs:
        print("✗ No graphs found matching patterns")
        sys.exit(1)

    card = build_agent_card(graphs=graphs, host=host, port=port)

    from google.protobuf.json_format import MessageToDict

    print(json.dumps(MessageToDict(card, preserving_proto_field_name=True), indent=2))
