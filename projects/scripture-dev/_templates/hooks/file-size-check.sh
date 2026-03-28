#!/usr/bin/env bash
# File size gate — max __MAX_FILE_LINES__ lines, warn above 400
fail=0
for f in "$@"; do
    lines=$(wc -l < "$f")
    if [ "$lines" -gt __MAX_FILE_LINES__ ]; then
        echo "FAIL: $f has $lines lines (max __MAX_FILE_LINES__)"
        fail=1
    elif [ "$lines" -gt 400 ]; then
        echo "WARN: $f has $lines lines (target < 400)"
    fi
done
exit $fail
