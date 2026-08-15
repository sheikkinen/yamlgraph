#!/bin/bash
# Demo script showing progressive ruff remediation in action
# This simulates what watcher2.sh now does with the FR-281 enhancement

set -e

echo "🎬 Watcher2 Remediation Demo - FR-281 Enhancement"
echo "=================================================="
echo

# Create a sample file with SIM117 violations
echo "📝 Creating sample file with SIM117 violations..."
cat > /tmp/sim117_demo.py << 'EOF'
"""Sample file with SIM117 violations (nested with statements)."""

def process_files():
    # SIM117: Nested with statements that should be combined
    with open("input1.txt") as f1:
        with open("output1.txt", "w") as f2:
            data = f1.read()
            f2.write(data.upper())

def backup_files():
    # Another SIM117: More nested with statements
    with open("config.json") as config:
        with open("backup.json", "w") as backup:
            with open("log.txt", "a") as log:
                content = config.read()
                backup.write(content)
                log.write("Backup completed\n")

def read_multiple_files():
    # SIM117: Could be simplified
    with open("file1.txt") as f1:
        with open("file2.txt") as f2:
            result = f1.read() + f2.read()
            return result
EOF

echo "✅ Created /tmp/sim117_demo.py with SIM117 violations"
echo

# Show the original file
echo "🔍 Original file (with SIM117 violations):"
echo "-------------------------------------------"
cat /tmp/sim117_demo.py
echo

# Step 1: Try ruff check --fix (safe fixes only)
echo "🛠️  Step 1: ruff check --fix (safe fixes only)"
echo "----------------------------------------------"
cp /tmp/sim117_demo.py /tmp/sim117_step1.py
ruff check --fix /tmp/sim117_step1.py 2>/dev/null || true

echo "Result: Safe fixes applied (if any)"
if diff /tmp/sim117_demo.py /tmp/sim117_step1.py > /dev/null; then
    echo "✅ No changes (SIM117 requires unsafe fixes)"
else
    echo "🔄 Some safe fixes were applied"
fi
echo

# Step 2: Try ruff check --fix --unsafe-fixes (handles SIM117)
echo "🚀 Step 2: ruff check --fix --unsafe-fixes (handles SIM117)"
echo "-----------------------------------------------------------"
cp /tmp/sim117_demo.py /tmp/sim117_step2.py
ruff check --fix --unsafe-fixes /tmp/sim117_step2.py 2>/dev/null || true

echo "Result: SIM117 violations fixed!"
echo "🔍 Fixed file:"
echo "---------------"
cat /tmp/sim117_step2.py
echo

# Show the difference
echo "📊 Changes made by --unsafe-fixes:"
echo "-----------------------------------"
diff /tmp/sim117_demo.py /tmp/sim117_step2.py || true
echo

echo "✅ Demo Complete!"
echo "=================="
echo "The progressive ruff strategy in watcher2.sh (FR-281) ensures:"
echo "• Safe fixes are tried first"
echo "• Unsafe fixes handle SIM117 and similar violations"
echo "• Pipeline doesn't crash on auto-fixable linting issues"
echo "• Copilot fallback has better error code context"
echo

# Cleanup
rm -f /tmp/sim117_demo.py /tmp/sim117_step1.py /tmp/sim117_step2.py
