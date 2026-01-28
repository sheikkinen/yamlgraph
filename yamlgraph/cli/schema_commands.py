"""Schema CLI commands for JSON Schema export (FR-009).

Implements:
- schema export [--output FILE]
- schema path
"""

import json
import sys
from argparse import Namespace
from pathlib import Path

from yamlgraph import get_schema_path
from yamlgraph.models.graph_schema import export_graph_json_schema


def cmd_schema_export(args: Namespace) -> None:
    """Export graph schema as JSON Schema.

    Outputs to stdout by default, or to file with --output.
    """
    try:
        schema = export_graph_json_schema()
        json_str = json.dumps(schema, indent=2)

        output_path = getattr(args, "output", None)
        if output_path:
            Path(output_path).write_text(json_str)
            print(f"✓ Schema exported to {output_path}")
        else:
            print(json_str)

    except Exception as e:
        print(f"❌ Error exporting schema: {e}")
        sys.exit(1)


def cmd_schema_path(args: Namespace) -> None:
    """Print path to bundled JSON Schema file."""
    schema_path = get_schema_path()
    print(schema_path)


def cmd_schema_dispatch(args: Namespace) -> None:
    """Dispatch to schema subcommands."""
    if args.schema_command == "export":
        cmd_schema_export(args)
    elif args.schema_command == "path":
        cmd_schema_path(args)
    else:
        print(f"Unknown schema command: {args.schema_command}")
        sys.exit(1)
