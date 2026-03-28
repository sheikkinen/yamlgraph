#!/usr/bin/env bash
# Forbid TODO/FIXME markers in committed code
grep -rn "TODO\|FIXME" "$@" && echo "FAIL: Remove TODO/FIXME markers" && exit 1
exit 0
