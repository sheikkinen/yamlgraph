#!/usr/bin/env bash
# File size gate — max 450 lines, warn above 400
fail=0
for f in "$@"; do
    lines=$(wc -l < "$f")
    if [ "$lines" -gt 450 ]; then
        echo "FAIL: $f has $lines lines (max 450)"
        fail=1
    elif [ "$lines" -gt 400 ]; then
        echo "WARN: $f has $lines lines (target < 400)"
    fi
done
exit $fail
