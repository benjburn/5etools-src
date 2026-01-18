#!/usr/bin/env python3
"""
JSON processor for data reorganization.

This module handles the processing and splitting of JSON files by source.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from scripts.reorganize import config
from scripts.reorganize.utils import (
    Statistics,
    create_progress_iterator,
    extract_entities_from_json,
    get_entity_source,
    group_entities_by_source,
    load_json,
    save_json,
    should_skip_file,
)


# =============================================================================
# JSON File Processing
# =============================================================================

def process_json_file(
    json_path: Path,
    sources: Dict[str, Dict[str, Any]],
    output_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
) -> Dict[str, int]:
    """
    Process a JSON file and split entities by source.

    Args:
        json_path: Path to input JSON file (e.g., data/backgrounds.json)
        sources: Dict of sources from books.json
        output_dir: Path to /data_rework/ directory
        stats: Statistics object to track results
        logger_instance: Optional logger instance

    Returns:
        Dict with counts per source

    Example:
        Input:  data/backgrounds.json (100 backgrounds from 10 sources)
        Output: data_rework/PHB/data/backgrounds.json (13 PHB backgrounds)
                data_rework/TCE/data/backgrounds.json (5 TCE backgrounds)
    """
    log = logger_instance or logger
    log.info(f"Processing {json_path.name}...")

    # Load JSON file
    data = load_json(json_path, log)
    if not data:
        stats.add_error(f"Failed to load {json_path}")
        return {}

    # Extract entities from JSON
    entity_arrays = extract_entities_from_json(
        data,
        entity_types=config.ENTITY_TYPES,
        logger=log,
    )

    if not entity_arrays:
        log.debug(f"No entity arrays found in {json_path.name}")
        return {}

    # Track output filename
    output_filename = json_path.name

    # Process each entity type
    counts_per_source = {}

    for entity_type, entities in entity_arrays:
        log.debug(f"Processing {len(entities)} {entity_type} entities...")

        # Group by source
        grouped = group_entities_by_source(entities, entity_type, log)

        # Save each source's entities
        for source_id, source_entities in grouped.items():
            if source_id not in sources:
                log.warning(f"Unknown source '{source_id}' in {json_path.name}, skipping")
                stats.add_warning(f"Unknown source '{source_id}' in {json_path.name}")
                continue

            # Create output directory
            source_output_dir = output_dir / source_id / "data"
            source_output_dir.mkdir(parents=True, exist_ok=True)

            # Build output data (preserve _meta and structure)
            output_data = {}

            # Copy _meta if present
            if "_meta" in data:
                output_data["_meta"] = data["_meta"]

            # Add entities for this source
            output_data[entity_type] = source_entities

            # Save to file
            output_file = source_output_dir / output_filename
            if save_json(output_data, output_file, log):
                # Update counts
                if source_id not in counts_per_source:
                    counts_per_source[source_id] = 0
                counts_per_source[source_id] += len(source_entities)

                log.debug(
                    f"  Saved {len(source_entities)} {entity_type} entities "
                    f"to {output_file.relative_to(output_dir)}"
                )
            else:
                stats.add_error(f"Failed to save {output_file}")

    log.info(f"  Processed {json_path.name}: {sum(counts_per_source.values())} entities from {len(counts_per_source)} sources")

    return counts_per_source


def process_bestiary_files(
    bestiary_dir: Path,
    sources: Dict[str, Dict[str, Any]],
    output_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
) -> Dict[str, int]:
    """
    Process bestiary JSON files and split by source.

    Args:
        bestiary_dir: Path to /data/bestiary/ directory
        sources: Dict of sources from books.json
        output_dir: Path to /data_rework/ directory
        stats: Statistics object to track results
        logger_instance: Optional logger instance

    Returns:
        Dict with counts per source
    """
    log = logger_instance or logger
    log.info("Processing bestiary files...")

    if not bestiary_dir.exists():
        log.error(f"Bestiary directory not found: {bestiary_dir}")
        stats.add_error(f"Bestiary directory not found: {bestiary_dir}")
        return {}

    # Find all bestiary JSON files
    json_files = list(bestiary_dir.glob("bestiary-*.json"))

    if not json_files:
        log.warning(f"No bestiary files found in {bestiary_dir}")
        return {}

    log.info(f"Found {len(json_files)} bestiary files")

    # Collect all monsters from all files
    all_monsters = []

    for json_file in create_progress_iterator(
        json_files,
        desc="Loading bestiary files",
    ):
        data = load_json(json_file, log)
        if not data:
            stats.add_error(f"Failed to load {json_file}")
            continue

        if "monster" in data and isinstance(data["monster"], list):
            all_monsters.extend(data["monster"])

    log.info(f"Loaded {len(all_monsters)} monsters total")

    # Group by source
    grouped = group_entities_by_source(all_monsters, "monster", log)

    # Save each source's monsters
    counts_per_source = {}

    for source_id, monsters in grouped.items():
        if source_id not in sources:
            log.warning(f"Unknown source '{source_id}' in bestiary, skipping")
            continue

        # Create output directory
        source_output_dir = output_dir / source_id / "data"
        source_output_dir.mkdir(parents=True, exist_ok=True)

        # Build output data
        output_data = {"monster": monsters}

        # Save to file
        output_file = source_output_dir / "bestiary.json"
        if save_json(output_data, output_file, log):
            counts_per_source[source_id] = len(monsters)
            log.debug(
                f"  Saved {len(monsters)} monsters to "
                f"{output_file.relative_to(output_dir)}"
            )

    log.info(
        f"Processed bestiary: {sum(counts_per_source.values())} monsters "
        f"from {len(counts_per_source)} sources"
    )

    return counts_per_source


def process_class_files(
    class_dir: Path,
    sources: Dict[str, Dict[str, Any]],
    output_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
) -> Dict[str, int]:
    """
    Process class JSON files and split by source.

    Args:
        class_dir: Path to /data/class/ directory
        sources: Dict of sources from books.json
        output_dir: Path to /data_rework/ directory
        stats: Statistics object to track results
        logger_instance: Optional logger instance

    Returns:
        Dict with counts per source
    """
    log = logger_instance or logger
    log.info("Processing class files...")

    if not class_dir.exists():
        log.error(f"Class directory not found: {class_dir}")
        stats.add_error(f"Class directory not found: {class_dir}")
        return {}

    # Find all class JSON files
    json_files = list(class_dir.glob("class-*.json"))

    if not json_files:
        log.warning(f"No class files found in {class_dir}")
        return {}

    log.info(f"Found {len(json_files)} class files")

    # Collect all class data from all files
    all_class_data = {}

    for json_file in create_progress_iterator(
        json_files,
        desc="Loading class files",
    ):
        data = load_json(json_file, log)
        if not data:
            stats.add_error(f"Failed to load {json_file}")
            continue

        # Merge all keys from this file
        for key, value in data.items():
            if key == "_meta":
                continue

            if key not in all_class_data:
                all_class_data[key] = []

            if isinstance(value, list):
                all_class_data[key].extend(value)

    # Group each entity type by source
    counts_per_source = {}

    for entity_type, entities in all_class_data.items():
        if not isinstance(entities, list) or not entities:
            continue

        log.debug(f"Processing {len(entities)} {entity_type} entries...")

        grouped = group_entities_by_source(entities, entity_type, log)

        for source_id, source_entities in grouped.items():
            if source_id not in sources:
                log.warning(f"Unknown source '{source_id}' in class files, skipping")
                continue

            # Create output directory
            source_output_dir = output_dir / source_id / "data"
            source_output_dir.mkdir(parents=True, exist_ok=True)

            # Load existing classes.json or create new
            output_file = source_output_dir / "classes.json"
            if output_file.exists():
                output_data = load_json(output_file, log)
                if not output_data:
                    output_data = {}
            else:
                output_data = {}

            # Add entities
            if entity_type not in output_data:
                output_data[entity_type] = []

            output_data[entity_type].extend(source_entities)

            # Save
            if save_json(output_data, output_file, log):
                if source_id not in counts_per_source:
                    counts_per_source[source_id] = 0
                counts_per_source[source_id] += len(source_entities)

    log.info(
        f"Processed classes: {sum(counts_per_source.values())} entries "
        f"from {len(counts_per_source)} sources"
    )

    return counts_per_source


def process_fluff_files(
    data_dir: Path,
    sources: Dict[str, Dict[str, Any]],
    output_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
) -> Dict[str, int]:
    """
    Process fluff JSON files and split by source.

    Args:
        data_dir: Path to /data/ directory
        sources: Dict of sources from books.json
        output_dir: Path to /data_rework/ directory
        stats: Statistics object to track results
        logger_instance: Optional logger instance

    Returns:
        Dict with counts per source
    """
    log = logger_instance or logger
    log.info("Processing fluff files...")

    # Find all fluff files
    fluff_files = list(data_dir.glob("fluff-*.json"))

    if not fluff_files:
        log.warning("No fluff files found")
        return {}

    log.info(f"Found {len(fluff_files)} fluff files")

    counts_per_source = {}

    for fluff_file in create_progress_iterator(
        fluff_files,
        desc="Processing fluff files",
    ):
        log.debug(f"Processing {fluff_file.name}...")

        data = load_json(fluff_file, log)
        if not data:
            stats.add_error(f"Failed to load {fluff_file}")
            continue

        # Extract fluff arrays
        entity_arrays = extract_entities_from_json(
            data,
            entity_types=None,  # All types in fluff files
            logger=log,
        )

        if not entity_arrays:
            log.debug(f"No fluff entries found in {fluff_file.name}")
            continue

        # Track output filename
        output_filename = fluff_file.name

        # Process each entity type
        for entity_type, entities in entity_arrays:
            # Group by source
            grouped = group_entities_by_source(entities, entity_type, log)

            for source_id, source_entities in grouped.items():
                if source_id not in sources:
                    log.warning(f"Unknown source '{source_id}' in {fluff_file.name}, skipping")
                    continue

                # Create output directory
                source_output_dir = output_dir / source_id / "data"
                source_output_dir.mkdir(parents=True, exist_ok=True)

                # Build output data
                output_data = {}

                # Copy _meta if present
                if "_meta" in data:
                    output_data["_meta"] = data["_meta"]

                # Add fluff entries for this source
                output_data[entity_type] = source_entities

                # Save to file
                output_file = source_output_dir / output_filename
                if save_json(output_data, output_file, log):
                    if source_id not in counts_per_source:
                        counts_per_source[source_id] = 0
                    counts_per_source[source_id] += len(source_entities)

    log.info(
        f"Processed fluff: {sum(counts_per_source.values())} entries "
        f"from {len(counts_per_source)} sources"
    )

    return counts_per_source


# =============================================================================
# Batch Processing
# =============================================================================

def process_all_json_files(
    data_dir: Path,
    sources: Dict[str, Dict[str, Any]],
    output_dir: Path,
    stats: Statistics,
    logger_instance: Optional[logging.Logger] = None,
    skip_special_dirs: bool = True,
) -> None:
    """
    Process all JSON files in the data directory.

    Args:
        data_dir: Path to /data/ directory
        sources: Dict of sources from books.json
        output_dir: Path to /data_rework/ directory
        stats: Statistics object to track results
        logger_instance: Optional logger instance
        skip_special_dirs: Skip bestiary/, class/, etc. (handle separately)
    """
    log = logger_instance or logger
    log.info("Processing JSON files...")

    # Process main JSON files (in root of data/)
    json_files = [
        f for f in data_dir.glob("*.json")
        if not should_skip_file(f.name, config.SKIP_FILES, config.SKIP_PATTERNS)
    ]

    if json_files:
        log.info(f"Found {len(json_files)} main JSON files to process")

        for json_file in create_progress_iterator(
            json_files,
            desc="Processing main JSON files",
        ):
            counts = process_json_file(json_file, sources, output_dir, stats, log)
            if counts:
                stats.add_json_stats(json_file.name, counts)

    # Process special subdirectories
    if not skip_special_dirs:
        # Bestiary files
        bestiary_dir = data_dir / "bestiary"
        if bestiary_dir.exists():
            counts = process_bestiary_files(bestiary_dir, sources, output_dir, stats, log)
            if counts:
                stats.add_json_stats("bestiary", counts)

        # Class files
        class_dir = data_dir / "class"
        if class_dir.exists():
            counts = process_class_files(class_dir, sources, output_dir, stats, log)
            if counts:
                stats.add_json_stats("class", counts)

    # Fluff files (always process separately)
    fluff_counts = process_fluff_files(data_dir, sources, output_dir, stats, log)
    if fluff_counts:
        stats.add_json_stats("fluff", fluff_counts)

    log.info("JSON processing complete")
