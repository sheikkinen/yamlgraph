#!/usr/bin/env bash
# Duplicate code detection — skip if jscpd not installed
command -v jscpd >/dev/null 2>&1 || exit 0
jscpd --min-lines 10 --min-tokens 80 --threshold 5 "$@" || exit 1
