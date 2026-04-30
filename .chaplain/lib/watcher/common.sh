#!/usr/bin/env bash
# common.sh — Shared helpers for watcher scripts
#
# Source this at the top of each script:
#   source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

log_info()  { echo "ℹ️  $*" >&2; }
log_warn()  { echo "⚠️  $*" >&2; }
log_error() { echo "❌ $*" >&2; }
