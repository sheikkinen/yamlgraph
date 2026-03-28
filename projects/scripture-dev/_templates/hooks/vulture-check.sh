#!/usr/bin/env bash
# Dead code detection — skip if vulture not installed
command -v vulture >/dev/null 2>&1 || exit 0
vulture --min-confidence 60 "$@" && exit 1
exit 0
