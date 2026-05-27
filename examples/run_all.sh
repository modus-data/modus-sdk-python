#!/usr/bin/env bash
# Run all SDK examples and report pass/fail for each.
#
# Usage:
#   export MODUS_API_KEY=modus_xxx
#   export MODUS_BASE_URL=http://localhost:3040
#   bash examples/run_all.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python}"

EXAMPLES=(
    list_skills.py
    org_overview.py
    manage_context.py
    sync_knowledge.py
)

passed=0
failed=0
failed_names=()

for example in "${EXAMPLES[@]}"; do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ">>> $example"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if "$PYTHON" "$SCRIPT_DIR/$example"; then
        echo ""
        echo "  ✓ $example passed"
        passed=$((passed + 1))
    else
        exit_code=$?
        echo ""
        echo "  ✗ $example FAILED (exit code $exit_code)"
        failed=$((failed + 1))
        failed_names+=("$example")
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Results: $passed passed, $failed failed"

if [ ${#failed_names[@]} -gt 0 ]; then
    echo "Failed:"
    for name in "${failed_names[@]}"; do
        echo "  - $name"
    done
    exit 1
fi
