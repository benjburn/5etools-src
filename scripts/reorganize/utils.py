#!/usr/bin/env python3
"""
Utility functions for data reorganization.

This module contains helper functions used across the reorganization scripts.
"""

import json
import logging
import sys
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from scripts.reorganize import config


# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging(verbose: bool = False, quiet: bool = False) -> logging.Logger:
    """
    Set up logging for the reorganization script.

    Args:
        verbose: Enable DEBUG level logging
        quiet: Suppress INFO level logging (only show warnings and errors)

    Returns:
        Configured logger instance
    """
    if quiet:
        log_level = logging.WARNING
    elif verbose:
        log_level = logging.DEBUG
    else:
        log_level = getattr(logging, config.DEFAULT_LOG_LEVEL, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT,
        stream=sys.stdout,
    )

    logger_instance = logging.getLogger("reorganize")
    return logger_instance


# =============================================================================
# JSON Utilities
# =============================================================================

def load_json(file_path: Path, logger: Optional[logging.Logger] = None) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file.

    Args:
        file_path: Path to JSON file
        logger: Optional logger instance

    Returns:
        Parsed JSON data, or None if error occurred
    """
    if logger:
        logger.debug(f"Loading JSON file: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        if logger:
            logger.error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        if logger:
            logger.error(f"Error loading {file_path}: {e}")
        return None


def save_json(
    data: Dict[str, Any],
    file_path: Path,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """
    Save data to a JSON file.

    Args:
        data: Data to save
        file_path: Output file path
        logger: Optional logger instance

    Returns:
        True if successful, False otherwise
    """
    if logger:
        logger.debug(f"Saving JSON file: {file_path}")

    try:
        # Create parent directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=config.JSON_INDENT,
                ensure_ascii=config.JSON_ENSURE_ASCII,
                sort_keys=config.JSON_SORT_KEYS,
            )

        return True
    except Exception as e:
        if logger:
            logger.error(f"Error saving {file_path}: {e}")
        return False


# =============================================================================
# File System Utilities
# =============================================================================

def should_skip_file(filename: str, skip_files: Set[str], skip_patterns: Set[str]) -> bool:
    """
    Check if a file should be skipped.

    Args:
        filename: Name of the file
        skip_files: Set of filenames to skip
        skip_patterns: Set of fnmatch patterns to skip

    Returns:
        True if file should be skipped
    """
    # Check exact match
    if filename in skip_files:
        return True

    # Check patterns
    for pattern in skip_patterns:
        if fnmatch(filename, pattern):
            return True

    return False


def should_skip_dir(dirname: str, skip_dirs: Set[str]) -> bool:
    """
    Check if a directory should be skipped.

    Args:
        dirname: Name of the directory
        skip_dirs: Set of directory names to skip

    Returns:
        True if directory should be skipped
    """
    return dirname in skip_dirs


def find_image_references(data: Any, source_id: str) -> List[Dict[str, Any]]:
    """
    Recursively find all image references in JSON data.

    Args:
        data: JSON data to search
        source_id: Source ID for cross-source detection

    Returns:
        List of image reference dicts with metadata:
        {
            "path": "bestiary/MM/Goblin.webp",
            "type": "internal",
            "is_cross_source": False,
            "exists": True
        }
    """
    references = []

    def _search(obj: Any, depth: int = 0) -> None:
        # Prevent infinite recursion
        if depth > 100:
            return

        if isinstance(obj, dict):
            # Check if this is an image entry
            if obj.get("type") == "image" and "href" in obj:
                href = obj["href"]
                if isinstance(href, dict):
                    if href.get("type") == "internal" and "path" in href:
                        path = href["path"]
                        # Extract source from path (first directory component)
                        path_parts = path.split("/")
                        image_source = path_parts[0] if path_parts else None

                        references.append({
                            "path": path,
                            "type": href.get("type", "internal"),
                            "is_cross_source": image_source and image_source != source_id,
                            "image_source": image_source,
                        })

            # Recursively search all values
            for value in obj.values():
                _search(value, depth + 1)

        elif isinstance(obj, list):
            for item in obj:
                _search(item, depth + 1)

    _search(data)
    return references


# =============================================================================
# Source Utilities
# =============================================================================

def load_sources(data_dir: Path, logger: Optional[logging.Logger] = None) -> Dict[str, Dict[str, Any]]:
    """
    Load all sources from books.json.

    Args:
        data_dir: Path to data directory
        logger: Optional logger instance

    Returns:
        Dict mapping source ID to metadata:
        {
            "PHB": {
                "id": "PHB",
                "name": "Player's Handbook (2014)",
                "source": "PHB",
                "group": "core",
                ...
            },
            ...
        }
    """
    books_file = data_dir / "books.json"

    if not books_file.exists():
        if logger:
            logger.error(f"books.json not found at {books_file}")
        return {}

    data = load_json(books_file, logger)
    if not data:
        return {}

    # Extract book array
    if "book" not in data:
        if logger:
            logger.error(f"Invalid books.json format: missing 'book' key")
        return {}

    sources = {}
    for book in data["book"]:
        source_id = book.get("id") or book.get("source")
        if source_id:
            sources[source_id] = book

    if logger:
        logger.info(f"Loaded {len(sources)} sources from books.json")

    return sources


def get_source_group(source_id: str, logger: Optional[logging.Logger] = None) -> Optional[str]:
    """
    Get the group for a source ID.

    Args:
        source_id: Source ID (e.g., "PHB")
        logger: Optional logger instance

    Returns:
        Group name (e.g., "core") or None if not found
    """
    for group, sources in config.SOURCE_GROUPS.items():
        if source_id in sources:
            return group

    if logger:
        logger.warning(f"Source {source_id} not found in any group")
    return None


# =============================================================================
# Entity Utilities
# =============================================================================

def get_entity_source(entity: Dict[str, Any], entity_name: str = "Unknown") -> Optional[str]:
    """
    Extract the source field from an entity.

    Args:
        entity: Entity dict
        entity_name: Name of the entity (for logging)

    Returns:
        Source ID or None if not found
    """
    if "source" not in entity:
        return None

    return entity["source"]


def group_entities_by_source(
    entities: List[Dict[str, Any]],
    entity_type: str,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group entities by their source field.

    Args:
        entities: List of entity dicts
        entity_type: Type of entities (for logging)
        logger: Optional logger instance

    Returns:
        Dict mapping source ID to list of entities
    """
    grouped = {}
    missing_source = []

    for entity in entities:
        source = get_entity_source(entity)
        if not source:
            name = entity.get("name", "Unknown")
            missing_source.append(f"{entity_type}: {name}")
            continue

        if source not in grouped:
            grouped[source] = []
        grouped[source].append(entity)

    if logger and missing_source:
        logger.warning(
            f"Found {len(missing_source)} {entity_type} entities without source field"
        )
        if logger.isEnabledFor(logging.DEBUG):
            for entity_ref in missing_source[:10]:  # Show first 10
                logger.debug(f"  Missing source: {entity_ref}")
            if len(missing_source) > 10:
                logger.debug(f"  ... and {len(missing_source) - 10} more")

    return grouped


def deduplicate_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	"""
	Remove duplicate entities based on {name, source}.

	If duplicates exist, prefer the one with a page number.
	If both have page numbers, prefer the larger page number (likely reprint).

	Args:
		entities: List of entity dicts

	Returns:
		Deduplicated list
	"""
	seen = {}
	for entity in entities:
		name = entity.get("name")
		source = entity.get("source")
		if not name or not source:
			continue

		key = (name, source)
		page = entity.get("page")

		# Keep the version with a page number
		if key not in seen:
			seen[key] = entity
		else:
			existing_page = seen[key].get("page")
			# Prefer version with page number
			if page is not None and (existing_page is None or page > 0):
				seen[key] = entity
			elif existing_page is None and page is None:
				# Both null, keep the first one
				pass

	return list(seen.values())


def extract_entities_from_json(
    data: Dict[str, Any],
    entity_types: Optional[Set[str]] = None,
    logger: Optional[logging.Logger] = None,
) -> List[Tuple[str, List[Dict[str, Any]]]]:
    """
    Extract all entity arrays from JSON data.

    Args:
        data: JSON data dict
        entity_types: Set of entity type keys to extract (None = all)
        logger: Optional logger instance

    Returns:
        List of (entity_type, entities) tuples
    """
    results = []

    for key, value in data.items():
        # Skip _meta and other non-entity keys
        if key.startswith("_"):
            continue

        # Check if value is a list of entities
        if isinstance(value, list):
            # If entity_types specified, check if key matches
            if entity_types and key not in entity_types:
                continue

            # Check if first item is a dict (likely entity)
            if value and isinstance(value[0], dict):
                results.append((key, value))

    return results


# =============================================================================
# Report Utilities
# =============================================================================

def create_report(
    sources_processed: int,
    statistics: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
) -> Dict[str, Any]:
    """
    Create a reorganization report.

    Args:
        sources_processed: Number of sources processed
        statistics: Statistics dict
        errors: List of errors
        warnings: List of warnings

    Returns:
        Report dict
    """
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": config.VERSION,
        "sources_processed": sources_processed,
        "statistics": statistics,
        "errors": errors,
        "warnings": warnings,
        "success": len(errors) == 0,
    }

    return report


def save_report(
    report: Dict[str, Any],
    report_path: Path,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """
    Save a report to a JSON file.

    Args:
        report: Report dict
        report_path: Path to save report
        logger: Optional logger instance

    Returns:
        True if successful
    """
    return save_json(report, report_path, logger)


# =============================================================================
# Statistics Utilities
# =============================================================================

class Statistics:
    """
    Track statistics during reorganization.
    """

    def __init__(self):
        self.json_files = {}
        self.images = {}
        self.pdfs = {}
        self.errors = []
        self.warnings = []
        self.cross_source_references = []

    def add_json_stats(self, filename: str, counts_per_source: Dict[str, int]) -> None:
        """Add JSON file statistics."""
        self.json_files[filename] = counts_per_source

    def add_image_stats(self, source_id: str, category_counts: Dict[str, int]) -> None:
        """Add image statistics for a source."""
        if source_id not in self.images:
            self.images[source_id] = {}
        self.images[source_id].update(category_counts)

    def add_pdf_count(self, source_id: str, count: int) -> None:
        """Add PDF count for a source."""
        self.pdfs[source_id] = count

    def add_error(self, error: str) -> None:
        """Add an error."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning."""
        self.warnings.append(warning)

    def add_cross_source_reference(self, ref: Dict[str, Any]) -> None:
        """Add a cross-source reference."""
        self.cross_source_references.append(ref)

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dict."""
        return {
            "json_files": self.json_files,
            "images": self.images,
            "pdfs": self.pdfs,
            "cross_source_references": {
                "total": len(self.cross_source_references),
                "examples": self.cross_source_references[:100],  # Limit examples
            },
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
        }


# =============================================================================
# Progress Utilities
# =============================================================================

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


def create_progress_iterator(iterable, desc: str = "", **kwargs):
    """
    Create a progress iterator (tqdm if available, otherwise plain iterator).

    Args:
        iterable: Iterable to wrap
        desc: Description for progress bar
        **kwargs: Additional arguments for tqdm

    Returns:
        Iterable with progress tracking
    """
    if config.SHOW_PROGRESS and TQDM_AVAILABLE:
        return tqdm(iterable, desc=desc, **kwargs)
    else:
        return iterable
