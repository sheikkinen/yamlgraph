# Multi-Concern Topic: New Lint Rule AND CLI Output Format

This topic bundles two orthogonal concerns that should be split into separate feature requests.

## Concern 1: Add a lint rule for unused state keys

Detect state keys defined in graph YAML that are never read by any downstream node.
This is a static analysis enhancement to `yamlgraph graph lint`.

## Concern 2: Add JSON output format to CLI commands

Allow `yamlgraph graph info` and `yamlgraph graph list` to emit JSON via a `--format json` flag.
This is a CLI presentation concern unrelated to linting.

These concerns are orthogonal: each can be implemented, tested, and merged independently.
