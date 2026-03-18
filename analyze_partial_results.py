import re

# Read the log file
with open('simulated_run_v4_fixed.log', 'r') as f:
    log = f.read()

# Extract all violations
violations = re.findall(r'    ❌ (.+)', log)

# Extract all scenario names and violation counts
scenario_blocks = re.split(r'\[\d+/\d+\] Running:', log)[1:]  # Skip header

print("=" * 60)
print("PARTIAL RESULTS ANALYSIS (44/50 scenarios completed)")
print("=" * 60)
print()

print(f"Total violations found: {len(violations)}")
print()

# Count violation types
violation_counts = {}
for v in violations:
    violation_counts[v] = violation_counts.get(v, 0) + 1

# Sort by frequency
sorted_violations = sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)

print("TOP 10 VIOLATION TYPES:")
for i, (violation, count) in enumerate(sorted_violations[:10], 1):
    print(f"{i}. [{count}x] {violation}")

print()
print(f"\nTotal unique violation types: {len(violation_counts)}")
