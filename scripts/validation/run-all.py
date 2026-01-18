#!/usr/bin/env python3
"""
Run all validation scripts.

This script orchestrates running all validation checks.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


# List of validation scripts to run
VALIDATION_SCRIPTS = [
    "check_pdf.py",
    "check_links.py",
    # "check_images.py",  # Uncomment when implemented
    # "check_cross_source.py",  # Uncomment when implemented
    # "check_fluff.py",  # Uncomment when implemented
    # "check_data_integrity.py",  # Uncomment when implemented
]


def run_script(script_name: str, script_dir: Path, args: List[str] = None) -> Dict[str, Any]:
    """
    Run a single validation script.

    Args:
        script_name: Name of the script to run
        script_dir: Directory containing scripts
        args: Additional arguments to pass to script

    Returns:
        Report dictionary
    """
    script_path = script_dir / script_name

    if not script_path.exists():
        return {
            "script": script_name,
            "status": "SKIPPED",
            "message": f"Script not found: {script_path}"
        }

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        # Try to parse JSON output
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError:
            report = {
                "script": script_name,
                "status": "OK" if result.returncode == 0 else "ERROR",
                "output": result.stdout,
                "stderr": result.stderr
            }

        return report

    except Exception as e:
        return {
            "script": script_name,
            "status": "ERROR",
            "message": f"Failed to run script: {str(e)}"
        }


def run_all(
    script_dir: Path,
    output_dir: Path = None,
    quick: bool = False,
    verbose: bool = False,
    skip: List[str] = None
) -> Dict[str, Any]:
    """
    Run all validation scripts.

    Args:
        script_dir: Directory containing validation scripts
        output_dir: Directory to save reports
        quick: Quick mode (skip some checks)
        verbose: Verbose output for all scripts
        skip: List of scripts to skip

    Returns:
        Combined report
    """
    report = {
        "script": "run-all.py",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "OK",
        "summary": {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
        },
        "reports": [],
    }

    # Prepare output directory
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare common arguments
    common_args = []
    if verbose:
        common_args.append("--verbose")

    # Run each script
    for script_name in VALIDATION_SCRIPTS:
        if skip and script_name in skip:
            report["reports"].append({
                "script": script_name,
                "status": "SKIPPED",
                "message": "Skipped by user request"
            })
            report["summary"]["skipped"] += 1
            continue

        if quick:
            # Skip some scripts in quick mode
            if script_name in ["check_cross_source.py", "check_fluff.py"]:
                report["reports"].append({
                    "script": script_name,
                    "status": "SKIPPED",
                    "message": "Skipped in quick mode"
                })
                report["summary"]["skipped"] += 1
                continue

        print(f"\n{'='*60}")
        print(f"Running: {script_name}")
        print(f"{'='*60}")

        script_report = run_script(script_name, script_dir, common_args)
        report["reports"].append(script_report)
        report["summary"]["total"] += 1

        # Save individual report if output_dir specified
        if output_dir:
            output_file = output_dir / f"{script_name}.json"
            with open(output_file, "w") as f:
                json.dump(script_report, f, indent=2)

        # Update summary
        status = script_report.get("status", "UNKNOWN")
        if status == "OK":
            report["summary"]["passed"] += 1
        elif status == "ERROR":
            report["summary"]["failed"] += 1
            report["status"] = "ERROR"
        elif status == "WARNING":
            if report["status"] != "ERROR":
                report["status"] = "WARNING"

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Run all 5etools validation scripts"
    )
    parser.add_argument(
        "--script-dir",
        type=Path,
        default=Path(__file__).parent,
        help="Directory containing validation scripts (default: same as run-all.py)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to save reports",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode (skip some checks)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output for all scripts",
    )
    parser.add_argument(
        "--skip",
        action="append",
        help="Skip specific script (can be used multiple times)",
    )

    args = parser.parse_args()

    # Run all validations
    report = run_all(
        args.script_dir,
        args.output_dir,
        args.quick,
        args.verbose,
        args.skip or []
    )

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total: {report['summary']['total']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Skipped: {report['summary']['skipped']}")
    print(f"Status: {report['status']}")

    # Save combined report if output_dir specified
    if args.output_dir:
        output_file = args.output_dir / "run-all.json"
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nCombined report saved to: {output_file}")

    # Exit with error code if any validation failed
    if report["status"] == "ERROR":
        sys.exit(1)


if __name__ == "__main__":
    main()
