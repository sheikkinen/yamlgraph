#!/usr/bin/env bash
# Radon complexity gate — skip if radon not installed
command -v radon >/dev/null 2>&1 || exit 0
radon cc --min D --show-complexity --no-assert "$@" \
  | grep -E "^\s+[A-Z]\s" \
  && echo "FAIL: Functions with complexity >= 21 (grade D)" && exit 1
exit 0
