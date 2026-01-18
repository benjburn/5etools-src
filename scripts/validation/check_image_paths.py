#!/usr/bin/env python3
"""
Image path validation script for data_rework.

This script audits all image references in JSON files across the data_rework
directory, checking for broken links, missing images, and inconsistencies.

Usage:
    python scripts/validation/check_image_paths.py
    python scripts/validation/check_image_paths.py --sources PHB PS-A
    python scripts/validation/check_image_paths.py --format json --output report.json
    python scripts/validation/check_image_paths.py --severity critical
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.validation.image_path_utils import (
    ImageRef,
    ValidationResult,
    validate_source_images,
)


# =============================================================================
# Image Path Auditor
# =============================================================================

class ImagePathAuditor:
    """
    Auditor for image paths in data_rework directory.

    Scans all JSON files, extracts image references, validates them
    against the img/ directory, and generates reports.
    """

    def __init__(
        self,
        data_dir: Path,
        img_dir: Path,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the auditor.

        Args:
            data_dir: Path to data_rework directory
            img_dir: Path to img directory
            logger: Optional logger instance
        """
        self.data_dir = data_dir
        self.img_dir = img_dir
        self.log = logger or logging.getLogger(__name__)

        # Statistics
        self.stats = {
            "sources_scanned": 0,
            "json_files_scanned": 0,
            "total_image_references": 0,
        }

        # Results by category
        self.results = {
            "valid": [],
            "special_case": [],
            "cross_source": [],
            "unexpected_location": [],
            "missing": [],
        }

    def run_full_audit(
        self,
        sources: Optional[List[str]] = None,
        output_file: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Run full audit on specified sources.

        Args:
            sources: List of source IDs to audit (None = all sources)
            output_file: Optional path to save JSON report

        Returns:
            Audit report dictionary
        """
        self.log.info("Starting image path audit...")
        self.log.info(f"Data directory: {self.data_dir}")
        self.log.info(f"Image directory: {self.img_dir}")

        # Get list of sources to audit
        if sources:
            source_dirs = [self.data_dir / s for s in sources]
        else:
            source_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]

        self.log.info(f"Auditing {len(source_dirs)} sources...")

        # Audit each source
        all_validations = []

        for source_dir in source_dirs:
            source_id = source_dir.name

            if not source_dir.is_dir():
                continue

            self.log.info(f"Auditing {source_id}...")

            validations = validate_source_images(
                source_id,
                self.data_dir,
                self.img_dir,
                self.log,
            )

            all_validations.extend(validations)
            self.stats["sources_scanned"] += 1

        self.stats["total_image_references"] = len(all_validations)

        # Categorize results
        for validation in all_validations:
            if validation.status in self.results:
                self.results[validation.status].append(validation.to_dict())

        self.stats["json_files_scanned"] = len(set(v.image_ref.file for v in all_validations))

        # Generate report
        report = self._generate_report()

        # Save report if requested
        if output_file:
            self._save_report(report, output_file)

        return report

    def _generate_report(self) -> Dict[str, Any]:
        """Generate audit report dictionary."""
        # Count issues by severity
        critical_count = len(self.results["missing"])
        warning_count = len(self.results["unexpected_location"])
        info_count = (
            len(self.results["valid"]) +
            len(self.results["special_case"]) +
            len(self.results["cross_source"])
        )

        # Build issues list
        issues = {
            "missing_images": self.results["missing"],
            "unexpected_locations": self.results["unexpected_location"],
            "cross_source_references": self.results["cross_source"],
            "special_cases": self.results["special_case"],
        }

        # Generate summary
        summary = {
            "critical_issues": critical_count,
            "warning_issues": warning_count,
            "info_issues": info_count,
            "special_design_decisions": len(self.results["special_case"]),
        }

        report = {
            "timestamp": datetime.now().isoformat(),
            "scan_summary": self.stats,
            "issues": issues,
            "summary": summary,
            "recommendations": self._generate_recommendations(),
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on audit results."""
        recommendations = []

        if self.results["missing"]:
            recommendations.append(
                f"Found {len(self.results['missing'])} missing images. "
                "These should be investigated and fixed."
            )

        if self.results["unexpected_location"]:
            recommendations.append(
                f"Found {len(self.results['unexpected_location'])} images in unexpected locations. "
                "Consider moving them to expected paths or updating references."
            )

        if not self.results["missing"] and not self.results["unexpected_location"]:
            recommendations.append(
                "All image paths are valid or follow known design decisions. "
                "No action required."
            )

        return recommendations

    def _save_report(self, report: Dict[str, Any], output_file: Path) -> None:
        """Save report to JSON file."""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.log.info(f"Report saved to: {output_file}")


# =============================================================================
# CLI Interface
# =============================================================================

def setup_logging(verbose: bool = False, quiet: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    return logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Audit image paths in data_rework directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data_rework"),
        help="Path to data_rework directory (default: %(default)s)",
    )

    parser.add_argument(
        "--img-dir",
        type=Path,
        default=Path("img"),
        help="Path to img directory (default: %(default)s)",
    )

    parser.add_argument(
        "--sources",
        nargs="+",
        help="Specific sources to audit (default: all sources)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("image-path-report.json"),
        help="Output report file (default: %(default)s)",
    )

    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: %(default)s)",
    )

    parser.add_argument(
        "--severity",
        choices=["critical", "warning", "info", "all"],
        default="all",
        help="Minimum severity level to display (default: %(default)s)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress info messages",
    )

    args = parser.parse_args()

    # Setup logging
    log = setup_logging(verbose=args.verbose, quiet=args.quiet)

    # Validate directories
    if not args.data_dir.exists():
        log.error(f"Data directory not found: {args.data_dir}")
        return 1

    if not args.img_dir.exists():
        log.error(f"Image directory not found: {args.img_dir}")
        return 1

    # Run audit
    auditor = ImagePathAuditor(args.data_dir, args.img_dir, log)

    try:
        report = auditor.run_full_audit(
            sources=args.sources,
            output_file=args.output if args.format == "json" else None,
        )

        # Display results
        if args.format == "text":
            _display_text_report(report, args.severity, log)
        elif args.format == "json":
            if args.output:
                log.info(f"Report saved to: {args.output}")
            else:
                print(json.dumps(report, indent=2, ensure_ascii=False))

        # Exit with error code if critical issues found
        if report["summary"]["critical_issues"] > 0:
            return 1

        return 0

    except Exception as e:
        log.error(f"Audit failed: {e}", exc_info=True)
        return 1


def _display_text_report(report: Dict[str, Any], severity: str, log: logging.Logger) -> None:
    """Display report in human-readable text format."""
    print()
    print("=" * 60)
    print("IMAGE PATH AUDIT REPORT")
    print("=" * 60)
    print(f"Timestamp: {report['timestamp']}")
    print()
    print("SCAN SUMMARY:")
    print(f"  Sources scanned: {report['scan_summary']['sources_scanned']}")
    print(f"  Total image references: {report['scan_summary']['total_image_references']}")
    print()
    print("ISSUES:")
    print(f"  Critical: {report['summary']['critical_issues']}")
    print(f"  Warning: {report['summary']['warning_issues']}")
    print(f"  Info: {report['summary']['info_issues']}")
    print(f"  Special design decisions: {report['summary']['special_design_decisions']}")
    print()

    # Display issues based on severity filter
    if severity in ["critical", "warning", "all"]:
        if report["issues"]["missing_images"]:
            print("MISSING IMAGES:")
            for issue in report["issues"]["missing_images"]:
                print(f"  ❌ {issue['source']}/{issue['file']}: {issue['path']}")
                print(f"     {issue['message']}")
            print()

    if severity in ["warning", "all"]:
        if report["issues"]["unexpected_locations"]:
            print("UNEXPECTED LOCATIONS:")
            for issue in report["issues"]["unexpected_locations"]:
                print(f"  ⚠️  {issue['source']}/{issue['file']}: {issue['path']}")
                print(f"     {issue['message']}")
            print()

    if severity in ["all"]:
        if report["issues"]["special_cases"]:
            print("SPECIAL CASES (Design Decisions):")
            for issue in report["issues"]["special_cases"][:5]:  # Show first 5
                print(f"  ℹ️  {issue['source']}: {issue['message']}")
            if len(report["issues"]["special_cases"]) > 5:
                print(f"  ... and {len(report['issues']['special_cases']) - 5} more")
            print()

        if report["issues"]["cross_source_references"]:
            print("CROSS-SOURCE REFERENCES:")
            for issue in report["issues"]["cross_source_references"][:5]:  # Show first 5
                print(f"  🔗 {issue['source']}/{issue['file']}: {issue['path']}")
                print(f"     {issue['message']}")
            if len(report["issues"]["cross_source_references"]) > 5:
                print(f"  ... and {len(report['issues']['cross_source_references']) - 5} more")
            print()

    print("RECOMMENDATIONS:")
    for rec in report["recommendations"]:
        print(f"  • {rec}")
    print()

    print("=" * 60)


if __name__ == "__main__":
    sys.exit(main())
