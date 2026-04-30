#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime


def run_all_validations():
    """Run all validation scripts and generate comprehensive report."""
    validation_report = {
        "timestamp": datetime.now().isoformat(),
        "coverage_validation": {},
        "quality_validation": {},
        "test_execution": {},
        "overall_status": "UNKNOWN",
    }

    # Run coverage validation
    try:
        result = subprocess.run(
            ["python3", "validate_coverage.py"], capture_output=True, text=True
        )
        if result.returncode == 0:
            coverage_data = json.loads(result.stdout.split("\n")[0])
            validation_report["coverage_validation"] = coverage_data
            validation_report["coverage_validation"]["status"] = (
                "PASS" if coverage_data["coverage_percentage"] >= 80 else "FAIL"
            )
        else:
            validation_report["coverage_validation"]["status"] = "ERROR"
            validation_report["coverage_validation"]["error"] = result.stderr
    except Exception as e:
        validation_report["coverage_validation"]["status"] = "ERROR"
        validation_report["coverage_validation"]["error"] = str(e)

    # Run quality validation
    try:
        result = subprocess.run(
            ["python3", "validate_quality.py"], capture_output=True, text=True
        )
        if result.returncode == 0:
            quality_data = json.loads(result.stdout.split("\n")[0])
            validation_report["quality_validation"] = quality_data
            validation_report["quality_validation"]["status"] = (
                "PASS" if quality_data["overall_pass"] else "FAIL"
            )
        else:
            validation_report["quality_validation"]["status"] = "ERROR"
            validation_report["quality_validation"]["error"] = result.stderr
    except Exception as e:
        validation_report["quality_validation"]["status"] = "ERROR"
        validation_report["quality_validation"]["error"] = str(e)

    # Run basic tests
    try:
        result = subprocess.run(
            ["python3", "run_basic_tests.py"], capture_output=True, text=True
        )
        validation_report["test_execution"]["status"] = (
            "PASS" if result.returncode == 0 else "FAIL"
        )
        validation_report["test_execution"]["output"] = result.stdout
        if result.stderr:
            validation_report["test_execution"]["errors"] = result.stderr
    except Exception as e:
        validation_report["test_execution"]["status"] = "ERROR"
        validation_report["test_execution"]["error"] = str(e)

    # Determine overall status
    all_statuses = [
        validation_report["coverage_validation"].get("status", "ERROR"),
        validation_report["quality_validation"].get("status", "ERROR"),
        validation_report["test_execution"].get("status", "ERROR"),
    ]

    if all(status == "PASS" for status in all_statuses):
        validation_report["overall_status"] = "PASS"
    elif any(status == "ERROR" for status in all_statuses):
        validation_report["overall_status"] = "ERROR"
    else:
        validation_report["overall_status"] = "FAIL"

    return validation_report


if __name__ == "__main__":
    report = run_all_validations()

    # Save to file
    with open("validation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    print(f"\nOverall validation status: {report['overall_status']}")
