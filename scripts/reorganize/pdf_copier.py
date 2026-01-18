#!/usr/bin/env python3
"""
PDF copier for data reorganization.

This module handles copying PDF files from /img/pdf/ to /data_rework/{SOURCE}/pdf/
"""

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from scripts.reorganize import config
from scripts.reorganize.utils import (
    Statistics,
    create_progress_iterator,
)


# =============================================================================
# PDF Copying
# =============================================================================

def copy_pdfs_for_source(
    source_id: str,
    img_dir: Path,
    output_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
) -> int:
    """
    Copy PDF files for a specific source.

    Args:
        source_id: Source ID (e.g., "ScoEE")
        img_dir: Path to /img/ directory
        output_dir: Path to /data_rework/ directory
        stats: Statistics object to track results
        logger_instance: Optional logger instance

    Returns:
        Number of PDF files copied

    Note:
        Most sources don't have PDFs. PDFs are in img/pdf/{SOURCE}/
    """
    log = logger_instance or logger

    source_pdf_dir = img_dir / "pdf" / source_id

    if not source_pdf_dir.exists():
        return 0

    # Output path
    output_pdf_dir = output_dir / source_id / "pdf"
    output_pdf_dir.mkdir(parents=True, exist_ok=True)

    # Copy all PDF files
    count = 0

    try:
        pdf_files = list(source_pdf_dir.glob("*.pdf"))

        if not pdf_files:
            return 0

        log.debug(f"  Copying {len(pdf_files)} PDF files for {source_id}...")

        for pdf_file in pdf_files:
            output_file = output_pdf_dir / pdf_file.name

            # Copy file
            shutil.copy2(pdf_file, output_file)
            count += 1

        if count > 0:
            log.debug(f"    Copied {count} PDF files for {source_id}")

    except Exception as e:
        error_msg = f"Failed to copy PDFs for {source_id}: {e}"
        log.error(error_msg)
        stats.add_error(error_msg)

    return count


# =============================================================================
# Batch PDF Copying
# =============================================================================

def copy_all_pdfs(
    sources: Dict[str, Dict[str, Any]],
    img_dir: Path,
    output_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
) -> None:
    """
    Copy PDF files for all sources.

    Args:
        sources: Dict of sources from books.json
        img_dir: Path to /img/ directory
        output_dir: Path to /data_rework/ directory
        stats: Statistics object to track results
        logger_instance: Optional logger instance
    """
    log = logger_instance or logger
    log.info("Copying PDF files for all sources...")

    pdf_dir = img_dir / "pdf"

    if not pdf_dir.exists():
        log.warning(f"PDF directory not found: {pdf_dir}")
        return

    total_count = 0

    for source_id, source_data in create_progress_iterator(
        sources.items(),
        desc="Copying PDFs",
    ):
        count = copy_pdfs_for_source(source_id, img_dir, output_dir, stats, log)
        stats.add_pdf_count(source_id, count)
        total_count += count

    log.info(f"PDF copying complete: {total_count} PDF files copied")


# =============================================================================
# PDF Validation
# =============================================================================

def validate_pdfs(
    img_dir: Path,
    output_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
) -> None:
    """
    Validate that all PDFs were copied successfully.

    Args:
        img_dir: Path to /img/ directory
        output_dir: Path to /data_rework/ directory
        stats: Statistics object to track results
        logger_instance: Optional logger instance
    """
    log = logger_instance or logger
    log.info("Validating PDF copies...")

    source_pdf_dir = img_dir / "pdf"

    if not source_pdf_dir.exists():
        log.info("No PDF directory to validate")
        return

    # Find all source directories
    source_dirs = [d for d in source_pdf_dir.iterdir() if d.is_dir()]

    for source_dir in source_dirs:
        source_id = source_dir.name

        # Count PDFs in source
        source_pdfs = list(source_dir.glob("*.pdf"))
        source_count = len(source_pdfs)

        if source_count == 0:
            continue

        # Count PDFs in output
        output_pdf_dir = output_dir / source_id / "pdf"

        if not output_pdf_dir.exists():
            error_msg = f"PDF directory missing for {source_id}"
            log.error(error_msg)
            stats.add_error(error_msg)
            continue

        output_pdfs = list(output_pdf_dir.glob("*.pdf"))
        output_count = len(output_pdfs)

        # Compare counts
        if source_count != output_count:
            error_msg = (
                f"PDF count mismatch for {source_id}: "
                f"expected {source_count}, found {output_count}"
            )
            log.error(error_msg)
            stats.add_error(error_msg)

    log.info("PDF validation complete")
