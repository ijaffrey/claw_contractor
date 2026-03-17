#!/bin/bash
# Run targeted photo and emergency scenarios

scenarios=(
    "plumb_visible_damage_photos"
    "gc_remodel_kitchen_photos"
    "roof_photo_request_success"
    "roof_photo_request_cant_access"
    "plumb_emergency_no_photos"
    "plumb_emergency_burst_pipe"
)

echo "Running 6 targeted scenarios to test ONE question compliance..."
echo ""

for scenario in "${scenarios[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Testing: $scenario"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python3 openclaw_test_harness/test_harness.py --scenario "$scenario" --quiet
    echo ""
done

echo ""
echo "All targeted scenarios complete. Check results/ for latest run."
