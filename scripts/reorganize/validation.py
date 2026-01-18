#!/usr/bin/env python3
"""
Validation runner for data reorganization.

This module runs validation scripts after reorganization is complete.
"""

import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.reorganize import config
from scripts.reorganize.utils import (
    Statistics,
    create_report,
    save_json,
    setup_logging,
)


# =============================================================================
# Validation Script Runner
# =============================================================================

def run_validation_script(
    script_path: Path,
    args: List[str],
    log: logging.Logger,
) -> Dict[str, Any]:
    """
    Run a validation script.

    Args:
        script_path: Path to validation script
        args: Command line arguments for the script
        log: Logger instance

    Returns:
        Dict with validation result
    """
    if not script_path.exists():
        return {
            "script": str(script_path),
            "status": "skipped",
            "message": f"Script not found: {script_path}",
        }

    log.info(f"Running validation script: {script_path.name}...")

    cmd = [sys.executable, str(script_path)] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
        )

        # Try to parse output as JSON (if script outputs JSON)
        output_data = None
        if result.stdout:
            try:
                output_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                pass  # Not JSON output

        validation_result = {
            "script": str(script_path),
            "name": script_path.name,
            "status": "passed" if result.returncode == 0 else "failed",
            "return_code": result.returncode,
            "stdout": result.stdout if log.isEnabledFor(logging.DEBUG) else None,
            "stderr": result.stderr if log.isEnabledFor(logging.DEBUG) else None,
            "output": output_data,
        }

        if result.returncode != 0:
            log.warning(f"  Validation failed: {script_path.name}")
            if result.stderr:
                log.debug(f"  Error output: {result.stderr[:500]}")
        else:
            log.info(f"  Validation passed: {script_path.name}")

        return validation_result

    except subprocess.TimeoutExpired:
        log.error(f"  Validation timed out: {script_path.name}")
        return {
            "script": str(script_path),
            "name": script_path.name,
            "status": "timeout",
            "message": "Validation timed out after 5 minutes",
        }
    except Exception as e:
        log.error(f"  Error running validation: {e}")
        return {
            "script": str(script_path),
            "name": script_path.name,
            "status": "error",
            "message": str(e),
        }


# =============================================================================
# Main Validation Runner
# =============================================================================

def run_validation(
    data_dir: Path,
    data_rework_dir: Path,
    img_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    """
    Run all validation scripts on reorganized data.

    Args:
        data_dir: Path to original /data/ directory
        data_rework_dir: Path to /data_rework/ directory
        img_dir: Path to /img/ directory
        stats: Statistics object with reorganization results
        logger_instance: Optional logger instance

    Returns:
        Validation report dict
    """
    log = logger_instance or logger
    log.info("=" * 60)
    log.info("Running validation...")
    log.info("=" * 60)

    validation_results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data_dir": str(data_dir),
        "data_rework_dir": str(data_rework_dir),
        "validations": [],
    }

    # Prepare common arguments for validation scripts
    common_args = []

    # Run check_data_integrity
    integrity_script = Path(config.VALIDATION_SCRIPTS["check_data_integrity"])

    # Try to create baseline before comparison
    baseline_file = data_dir / "baseline-before.json"

    # Note: We don't create baseline here, assuming it was created before reorganization
    # If baseline exists, use it for comparison
    if baseline_file.exists():
        integrity_args = common_args + [
            "--compare-baseline",
            str(baseline_file),
            "--data-dir",
            str(data_rework_dir),
        ]
    else:
        log.warning(f"Baseline file not found: {baseline_file}")
        integrity_args = common_args + [
            "--data-dir",
            str(data_rework_dir),
        ]

    result = run_validation_script(integrity_script, integrity_args, log)
    validation_results["validations"].append(result)

    # Run check_images
    images_script = Path(config.VALIDATION_SCRIPTS["check_images"])

    images_args = common_args + [
        "--data-dir",  # Note: check_images might not have --data-dir, adjust as needed
    ]

    result = run_validation_script(images_script, images_args, log)
    validation_results["validations"].append(result)

    # Run check_cross_source
    cross_source_script = Path(config.VALIDATION_SCRIPTS["check_cross_source"])

    cross_source_args = common_args + [
        "--analyze-dependencies",
        "--data-dir",
        str(data_rework_dir),
    ]

    result = run_validation_script(cross_source_script, cross_source_args, log)
    validation_results["validations"].append(result)

    # Calculate overall status
    failed_count = sum(
        1 for v in validation_results["validations"]
        if v.get("status") in ["failed", "error", "timeout"]
    )

    validation_results["overall_status"] = (
        "passed" if failed_count == 0 else "failed"
    )
    validation_results["failed_count"] = failed_count
    validation_results["total_count"] = len(validation_results["validations"])

    # Summary
    log.info("=" * 60)
    log.info("Validation Summary:")
    log.info(f"  Total: {validation_results['total_count']}")
    log.info(f"  Failed: {failed_count}")
    log.info(f"  Status: {validation_results['overall_status'].upper()}")
    log.info("=" * 60)

    return validation_results


# =============================================================================
# Quick Integrity Check
# =============================================================================

def quick_integrity_check(
    data_dir: Path,
    data_rework_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
) -> bool:
    """
    Perform a quick integrity check without running external validation scripts.

    Args:
        data_dir: Path to original /data/ directory
        data_rework_dir: Path to /data_rework/ directory
        stats: Statistics object with reorganization results
        logger_instance: Optional logger instance

    Returns:
        True if check passed, False otherwise
    """
    log = logger_instance or logger
    log.info("Performing quick integrity check...")

    passed = True

    # Check 1: Verify all sources were processed
    sources_with_data = set()

    for source_dir in data_rework_dir.iterdir():
        if source_dir.is_dir() and (source_dir / "data").exists():
            sources_with_data.add(source_dir.name)

    log.info(f"  Sources processed: {len(sources_with_data)}")

    if stats.errors:
        log.warning(f"  Errors during reorganization: {len(stats.errors)}")
        passed = False

    if stats.warnings:
        log.info(f"  Warnings during reorganization: {len(stats.warnings)}")

    # Check 2: Verify JSON files were created
    json_count = sum(
        1 for _ in data_rework_dir.rglob("data/*.json")
    )

    log.info(f"  JSON files created: {json_count}")

    if json_count == 0:
        log.error("  No JSON files were created!")
        passed = False

    # Check 3: Verify images were copied
    image_count = sum(
        1 for _ in data_rework_dir.rglob("img/**/*")
        if _.is_file()
    )

    log.info(f"  Images copied: {image_count}")

    # Check 4: Verify PDFs were copied
    pdf_count = sum(
        1 for _ in data_rework_dir.rglob("pdf/*.pdf")
    )

    log.info(f"  PDFs copied: {pdf_count}")

    # Check 5: Cross-source references
    if stats.cross_source_references:
        log.info(
            f"  Cross-source references found: {len(stats.cross_source_references)}"
        )

        if config.COPY_CROSS_SOURCE_IMAGES:
            log.warning(
                "    WARNING: Cross-source images were copied despite config setting!"
            )
            passed = False

    # Summary
    if passed:
        log.info("  Quick integrity check: PASSED")
    else:
        log.error("  Quick integrity check: FAILED")

    return passed


# =============================================================================
# Baseline Creation
# =============================================================================

def create_baseline(
    data_dir: Path,
    baseline_path: Path,
    logger_instance: Optional[logging.Logger] = None,
) -> bool:
    """
    Create a baseline snapshot of the original data structure.

    Args:
        data_dir: Path to /data/ directory
        baseline_path: Path to save baseline file
        logger_instance: Optional logger instance

    Returns:
        True if successful
    """
    log = logger_instance or logger
    log.info(f"Creating baseline: {baseline_path}")

    baseline_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data_dir": str(data_dir),
        "files": {},
        "entity_counts": {},
    }

    # Count entities in each JSON file
    json_files = list(data_dir.glob("*.json"))

    for json_file in json_files:
        # Skip certain files
        if json_file.name in config.SKIP_FILES:
            continue

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Count entities
            entity_counts = {}
            for key, value in data.items():
                if isinstance(value, list) and value:
                    entity_counts[key] = len(value)

            baseline_data["entity_counts"][json_file.name] = entity_counts

        except Exception as e:
            log.warning(f"Failed to read {json_file.name}: {e}")

    # Save baseline
    try:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)

        with open(baseline_path, "w", encoding="utf-8") as f:
            json.dump(baseline_data, f, indent=config.REPORT_INDENT)

        log.info(f"Baseline saved: {baseline_path}")
        return True

    except Exception as e:
        log.error(f"Failed to save baseline: {e}")
        return False
