#!/usr/bin/env python3
"""
Reorganize 5etools data from content-based structure to source-based structure.

Creates /data_rework/ with subdirectories for each source (PHB, XPHB, DMG, etc.)
while preserving the original /data/ and /img/ directories.

Usage:
    python scripts/reorganize/reorganize_data.py
    python scripts/reorganize/reorganize_data.py --sources PHB XPHB
    python scripts/reorganize/reorganize_data.py --skip-validation
    python scripts/reorganize/reorganize_data.py --verbose
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.reorganize import config
from scripts.reorganize.file_copier import get_copier
from scripts.reorganize.json_processor import (
    process_all_json_files,
    process_bestiary_files,
    process_book_files,
    process_class_files,
    process_spells_files,
)
from scripts.reorganize.utils import (
    Statistics,
    create_report,
    load_sources,
    save_report,
    setup_logging,
)
from scripts.reorganize.validation import (
    create_baseline,
    quick_integrity_check,
    run_validation,
)


# =============================================================================
# Directory Creation
# =============================================================================

def create_source_directories(
    sources: dict,
    output_dir: Path,
    log: logging.Logger,
) -> None:
    """
    Create directory structure for all sources.

    Args:
        sources: Dict of sources from books.json
        output_dir: Path to /data_rework/ directory
        log: Logger instance

    Creates for each source:
        data_rework/{SOURCE}/data/
        data_rework/{SOURCE}/img/
        data_rework/{SOURCE}/pdf/
    """
    log.info("Creating directory structure...")

    for source_id in sources.keys():
        # Create subdirectories
        (output_dir / source_id / "data").mkdir(parents=True, exist_ok=True)
        (output_dir / source_id / "img").mkdir(parents=True, exist_ok=True)
        (output_dir / source_id / "pdf").mkdir(parents=True, exist_ok=True)

    log.info(f"Created directories for {len(sources)} sources")


# =============================================================================
# Main Function
# =============================================================================

def main():
    """Main function to reorganize 5etools data."""
    parser = argparse.ArgumentParser(
        description=config.DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=config.DEFAULT_DATA_DIR,
        help="Path to data directory (default: %(default)s)",
    )

    parser.add_argument(
        "--img-dir",
        type=Path,
        default=config.DEFAULT_IMG_DIR,
        help="Path to img directory (default: %(default)s)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=config.DEFAULT_OUTPUT_DIR,
        help="Path to output directory (default: %(default)s)",
    )

    parser.add_argument(
        "--sources",
        nargs="+",
        help="Specific sources to process (default: all sources)",
    )

    parser.add_argument(
        "--create-baseline",
        type=Path,
        help="Create baseline snapshot before reorganization",
    )

    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help=f"Skip validation (default: {'false' if config.RUN_VALIDATION_BY_DEFAULT else 'true'})",
    )

    parser.add_argument(
        "--quick-check-only",
        action="store_true",
        help="Only run quick integrity check (skip full validation)",
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
        help="Suppress info messages (only show warnings and errors)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {config.VERSION}",
    )

    args = parser.parse_args()

    # Setup logging
    log = setup_logging(verbose=args.verbose, quiet=args.quiet)

    log.info("=" * 60)
    log.info("5etools Data Reorganization")
    log.info(f"Version: {config.VERSION}")
    log.info("=" * 60)

    # Validate input directories
    if not args.data_dir.exists():
        log.error(f"Data directory not found: {args.data_dir}")
        return 1

    if not args.img_dir.exists():
        log.error(f"Image directory not found: {args.img_dir}")
        return 1

    # Create baseline if requested
    if args.create_baseline:
        create_baseline(args.data_dir, args.create_baseline, log)

    # Load sources
    sources = load_sources(args.data_dir, log)

    if not sources:
        log.error("No sources loaded from books.json")
        return 1

    # Filter sources if --sources specified
    if args.sources:
        filtered_sources = {}
        for source_id in args.sources:
            if source_id in sources:
                filtered_sources[source_id] = sources[source_id]
            else:
                log.warning(f"Unknown source: {source_id}")

        if not filtered_sources:
            log.error("No valid sources specified")
            return 1

        sources = filtered_sources
        log.info(f"Processing {len(sources)} specific sources: {', '.join(sources.keys())}")

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Create directory structure
    create_source_directories(sources, args.output_dir, log)

    # Initialize statistics
    stats = Statistics()

    try:
        # Step 1: Process JSON files
        log.info("=" * 60)
        log.info("Step 1: Processing JSON files...")
        log.info("=" * 60)

        process_all_json_files(
            args.data_dir,
            sources,
            args.output_dir,
            stats,
            log,
            skip_special_dirs=False,  # We'll handle them separately below
        )

        # Process special subdirectories separately
        bestiary_dir = args.data_dir / "bestiary"
        if bestiary_dir.exists():
            bestiary_counts = process_bestiary_files(
                bestiary_dir, sources, args.output_dir, stats, log
            )
            if bestiary_counts:
                stats.add_json_stats("bestiary", bestiary_counts)

        class_dir = args.data_dir / "class"
        if class_dir.exists():
            class_counts = process_class_files(
                class_dir, sources, args.output_dir, stats, log
            )
            if class_counts:
                stats.add_json_stats("class", class_counts)

        book_dir = args.data_dir / "book"
        if book_dir.exists():
            book_counts = process_book_files(
                book_dir, sources, args.output_dir, stats, log
            )
            if book_counts:
                stats.add_json_stats("book", book_counts)

        # Process spells directory
        spells_dir = args.data_dir / "spells"
        if spells_dir.exists():
            spells_counts = process_spells_files(
                spells_dir, sources, args.output_dir, stats, log
            )
            if spells_counts:
                stats.add_json_stats("spells", spells_counts)

        # Step 2: Copy images
        log.info("=" * 60)
        log.info("Step 2: Copying images...")
        log.info("=" * 60)

        image_copier = get_copier("image")
        image_copier.copy_all(sources, args.img_dir, args.output_dir, stats, log)

        # Step 3: Copy PDFs
        log.info("=" * 60)
        log.info("Step 3: Copying PDFs...")
        log.info("=" * 60)

        pdf_copier = get_copier("pdf")
        pdf_copier.copy_all(sources, args.img_dir, args.output_dir, stats, log)

        # Step 4: Quick integrity check
        log.info("=" * 60)
        log.info("Step 4: Quick integrity check...")
        log.info("=" * 60)

        quick_integrity_check(args.data_dir, args.output_dir, stats, log)

        # Step 5: Run validation (if not skipped)
        validation_report = None

        if not args.skip_validation:
            log.info("=" * 60)
            log.info("Step 5: Running validation...")
            log.info("=" * 60)

            if args.quick_check_only:
                # Already done above
                pass
            else:
                validation_report = run_validation(
                    args.data_dir,
                    args.output_dir,
                    args.img_dir,
                    stats,
                    log,
                )

        # Generate report
        log.info("=" * 60)
        log.info("Generating report...")
        log.info("=" * 60)

        report = create_report(
            sources_processed=len(sources),
            statistics=stats.to_dict(),
            errors=stats.errors,
            warnings=stats.warnings,
        )

        # Add validation report if available
        if validation_report:
            report["validation"] = validation_report

        # Save report
        report_path = args.output_dir / config.REORGANIZATION_REPORT
        save_report(report, report_path, log)

        if validation_report:
            validation_report_path = args.output_dir / config.VALIDATION_REPORT
            save_report(validation_report, validation_report_path, log)

        # Print summary
        log.info("=" * 60)
        log.info("Reorganization Summary")
        log.info("=" * 60)
        log.info(f"Sources processed: {len(sources)}")
        log.info(f"JSON files processed: {len(stats.json_files)}")
        log.info(f"Images copied: {sum(sum(c.values()) if isinstance(c, dict) else [c] for c in stats.images.values())}")
        log.info(f"PDFs copied: {sum(stats.pdfs.values())}")
        log.info(f"Errors: {len(stats.errors)}")
        log.info(f"Warnings: {len(stats.warnings)}")

        if stats.cross_source_references:
            log.info(f"Cross-source references: {len(stats.cross_source_references)}")

        if validation_report:
            status = validation_report.get("overall_status", "unknown").upper()
            log.info(f"Validation status: {status}")

        log.info("=" * 60)
        log.info(f"✅ Reorganization complete!")
        log.info(f"📁 Output directory: {args.output_dir}")
        log.info(f"📊 Report saved to: {report_path}")
        log.info("=" * 60)

        # Exit with error code if validation failed
        if validation_report and validation_report.get("overall_status") == "failed":
            return 1

        return 0

    except KeyboardInterrupt:
        log.warning("\nReorganization interrupted by user")
        return 130
    except Exception as e:
        log.error(f"Reorganization failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
