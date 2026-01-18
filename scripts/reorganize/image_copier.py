#!/usr/bin/env python3
"""
Image copier for data reorganization.

This module handles copying images from /img/ to /data_rework/{SOURCE}/img/
"""

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from scripts.reorganize import config
from scripts.reorganize.utils import (
    Statistics,
    create_progress_iterator,
    find_image_references,
    load_json,
)


# =============================================================================
# Image Copying
# =============================================================================

def copy_images_for_source(
    source_id: str,
    source_data: Dict[str, Any],
    img_dir: Path,
    output_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
) -> Dict[str, int]:
    """
    Copy images for a specific source.

    Args:
        source_id: Source ID (e.g., "PHB")
        source_data: Source metadata from books.json
        img_dir: Path to /img/ directory
        output_dir: Path to /data_rework/ directory
        stats: Statistics object to track results
        logger_instance: Optional logger instance

    Returns:
        Dict with counts per image category

    Strategy:
        1. Copy cover image: img/covers/{SOURCE}.webp -> data_rework/{SOURCE}/img/covers/{SOURCE}.webp
        2. Copy category images: img/{category}/{SOURCE}/**/* -> data_rework/{SOURCE}/img/{category}/{SOURCE}/**/*
        3. Categories to process: bestiary, book, items, backgrounds, classes, races, spells, deities, adventure, etc.
        4. Skip cross-source images (image path != entity source)
    """
    log = logger_instance or logger
    log.debug(f"Copying images for {source_id}...")

    category_counts = {}

    # 1. Copy cover image
    cover_count = _copy_cover_image(source_id, img_dir, output_dir, stats, log)
    if cover_count > 0:
        category_counts["covers"] = cover_count

    # 2. Copy category images
    for category in config.IMAGE_CATEGORIES:
        count = _copy_category_images(
            source_id, category, img_dir, output_dir, stats, log
        )
        if count > 0:
            category_counts[category] = count

    total = sum(category_counts.values())
    log.info(f"  Copied {total} images for {source_id} from {len(category_counts)} categories")

    return category_counts


def _copy_cover_image(
    source_id: str,
    img_dir: Path,
    output_dir: Path,
    stats: Statistics,
    log: logging.Logger,
) -> int:
    """
    Copy cover image for a source.

    Args:
        source_id: Source ID
        img_dir: Path to /img/ directory
        output_dir: Path to /data_rework/ directory
        stats: Statistics object
        log: Logger instance

    Returns:
        Number of images copied (0 or 1)
    """
    cover_file = img_dir / "covers" / f"{source_id}.webp"

    if not cover_file.exists():
        log.debug(f"    Cover image not found: {cover_file.name}")
        return 0

    # Output path
    output_cover_dir = output_dir / source_id / "img" / "covers"
    output_cover_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_cover_dir / cover_file.name

    # Copy file
    try:
        shutil.copy2(cover_file, output_file)
        log.debug(f"    Copied cover: {cover_file.name}")
        return 1
    except Exception as e:
        error_msg = f"Failed to copy cover {cover_file}: {e}"
        log.error(error_msg)
        stats.add_error(error_msg)
        return 0


def _copy_category_images(
    source_id: str,
    category: str,
    img_dir: Path,
    output_dir: Path,
    stats: Statistics,
    log: logging.Logger,
) -> int:
    """
    Copy images for a specific category and source.

    Args:
        source_id: Source ID
        category: Image category (e.g., "bestiary", "book")
        img_dir: Path to /img/ directory
        output_dir: Path to /data_rework/ directory
        stats: Statistics object
        log: Logger instance

    Returns:
        Number of images copied
    """
    source_img_dir = img_dir / category / source_id

    if not source_img_dir.exists():
        return 0

    # Output path
    output_category_dir = output_dir / source_id / "img" / category
    output_category_dir.mkdir(parents=True, exist_ok=True)

    output_source_dir = output_category_dir / source_id
    output_source_dir.mkdir(parents=True, exist_ok=True)

    # Copy all files recursively
    count = 0

    try:
        for item in source_img_dir.rglob("*"):
            if item.is_file():
                # Calculate relative path from source_img_dir
                rel_path = item.relative_to(source_img_dir)

                # Output file path
                output_file = output_source_dir / rel_path

                # Create parent directories if needed
                output_file.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(item, output_file)
                count += 1

        if count > 0:
            log.debug(f"    Copied {count} {category} images")

    except Exception as e:
        error_msg = f"Failed to copy {category} images for {source_id}: {e}"
        log.error(error_msg)
        stats.add_error(error_msg)

    return count


# =============================================================================
# Image Reference Checking
# =============================================================================

def check_image_references_in_reorganized_data(
    data_rework_dir: Path,
    img_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
) -> None:
    """
    Check all image references in reorganized JSON data.

    Args:
        data_rework_dir: Path to /data_rework/ directory
        img_dir: Path to /img/ directory
        stats: Statistics object to track results
        logger_instance: Optional logger instance
    """
    log = logger_instance or logger
    log.info("Checking image references in reorganized data...")

    # Find all JSON files in reorganized data
    json_files = list(data_rework_dir.rglob("data/*.json"))

    if not json_files:
        log.warning("No JSON files found in reorganized data")
        return

    log.info(f"Found {len(json_files)} JSON files to check")

    # Check each file
    for json_file in create_progress_iterator(
        json_files,
        desc="Checking image references",
    ):
        data = load_json(json_file, log)
        if not data:
            continue

        # Extract source ID from path (e.g., data_rework/PHB/data/...)
        path_parts = json_file.relative_to(data_rework_dir).parts
        if len(path_parts) < 2:
            continue

        source_id = path_parts[0]

        # Find image references
        references = find_image_references(data, source_id)

        for ref in references:
            image_path = img_dir / ref["path"]

            # Check if image exists
            if not image_path.exists():
                error_msg = f"Image not found: {ref['path']} (referenced in {json_file.relative_to(data_rework_dir)})"
                stats.add_error(error_msg)

            # Track cross-source references
            if ref["is_cross_source"]:
                stats.add_cross_source_reference({
                    "entity_source": source_id,
                    "image_path": ref["path"],
                    "image_source": ref.get("image_source"),
                    "referenced_in": str(json_file.relative_to(data_rework_dir)),
                })

    log.info("Image reference check complete")


# =============================================================================
# Orphan Detection
# =============================================================================

def find_orphaned_images(
    img_dir: Path,
    data_rework_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
) -> None:
    """
    Find images that are not referenced in any JSON data.

    Args:
        img_dir: Path to /img/ directory
        data_rework_dir: Path to /data_rework/ directory
        stats: Statistics object to track results
        logger_instance: Optional logger instance
    """
    log = logger_instance or logger
    log.info("Finding orphaned images...")

    # Collect all referenced images
    referenced_images = set()

    json_files = list(data_rework_dir.rglob("data/*.json"))

    for json_file in json_files:
        data = load_json(json_file, log)
        if not data:
            continue

        # Find image references
        references = find_image_references(data, "")

        for ref in references:
            referenced_images.add(ref["path"])

    log.info(f"Found {len(referenced_images)} referenced images")

    # Find all images in /img/
    all_images = set()

    for category in config.IMAGE_CATEGORIES:
        category_dir = img_dir / category
        if not category_dir.exists():
            continue

        for image_file in category_dir.rglob("*"):
            if image_file.is_file() and image_file.suffix in [".webp", ".png", ".jpg", ".jpeg"]:
                # Calculate path relative to img_dir
                rel_path = image_file.relative_to(img_dir)
                all_images.add(str(rel_path))

    # Find orphans
    orphans = all_images - referenced_images

    if orphans:
        log.warning(f"Found {len(orphans)} orphaned images")
        for orphan in sorted(orphans)[:20]:  # Show first 20
            stats.add_warning(f"Orphaned image: {orphan}")

        if len(orphans) > 20:
            log.warning(f"  ... and {len(orphans) - 20} more orphaned images")


# =============================================================================
# Batch Image Copying
# =============================================================================

def copy_all_images(
    sources: Dict[str, Dict[str, Any]],
    img_dir: Path,
    output_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
) -> None:
    """
    Copy images for all sources.

    Args:
        sources: Dict of sources from books.json
        img_dir: Path to /img/ directory
        output_dir: Path to /data_rework/ directory
        stats: Statistics object to track results
        logger_instance: Optional logger instance
    """
    log = logger_instance or logger
    log.info("Copying images for all sources...")

    for source_id, source_data in create_progress_iterator(
        sources.items(),
        desc="Copying images",
    ):
        category_counts = copy_images_for_source(
            source_id, source_data, img_dir, output_dir, stats, log
        )
        stats.add_image_stats(source_id, category_counts)

    total_images = sum(
        sum(counts.values())
        for counts in stats.images.values()
        if isinstance(counts, dict)
    )
    log.info(f"Image copying complete: {total_images} images copied")
