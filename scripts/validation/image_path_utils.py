#!/usr/bin/env python3
"""
Utility functions and data classes for image path validation in data_rework.

This module provides shared utilities for auditing and fixing image references
in JSON files across the data_rework directory structure.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from scripts.reorganize import config


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ImageRef:
    """
    Reference to an image found in JSON data.

    Attributes:
        source: Source ID (e.g., "PHB", "PS-A", "HAT-TG")
        file: JSON filename (e.g., "book.json", "bestiary.json")
        path: Image path from JSON (e.g., "book/PSA/001.webp")
        category: Image category (book, bestiary, adventure, etc.)
        context: Additional context (parent keys, line number if available)
    """
    source: str
    file: str
    path: str
    category: str
    context: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.source}/{self.file}: {self.path}"


@dataclass
class ValidationResult:
    """
    Result of validating an image reference.

    Attributes:
        image_ref: The image reference being validated
        status: Validation status (valid, missing, broken, cross_source, special_case)
        actual_path: Actual filesystem path if it exists
        expected_path: Expected path in img/ directory
        severity: Issue severity (critical, warning, info)
        message: Human-readable message about the validation result
    """
    image_ref: ImageRef
    status: str
    actual_path: Optional[Path]
    expected_path: Optional[Path]
    severity: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": self.image_ref.source,
            "file": self.image_ref.file,
            "path": self.image_ref.path,
            "category": self.image_ref.category,
            "status": self.status,
            "actual_path": str(self.actual_path) if self.actual_path else None,
            "expected_path": str(self.expected_path) if self.expected_path else None,
            "severity": self.severity,
            "message": self.message,
        }


# =============================================================================
# Path Normalization Functions
# =============================================================================

def normalize_source_for_image_path(source_id: str) -> str:
    """
    Normalize source ID for use in image paths.

    This handles special cases where the source folder name differs from
    the image path component (design decisions, not bugs).

    Examples:
        PS-A -> PSA
        PS-I -> PSI
        HAT-TG -> TG
        PHB -> PHB

    Args:
        source_id: Source ID from data_rework folder name

    Returns:
        Normalized source ID for image path lookup
    """
    if source_id in config.IMAGE_PATH_SPECIAL_MAPPINGS:
        mapping = config.IMAGE_PATH_SPECIAL_MAPPINGS[source_id]
        if isinstance(mapping, dict):
            return mapping["path_component"]
        return mapping
    return source_id


def get_expected_image_path(
    source_id: str,
    image_path: str,
    img_dir: Path,
) -> Optional[Path]:
    """
    Get the expected filesystem path for an image reference.

    Args:
        source_id: Source ID (e.g., "PS-A")
        image_path: Path from JSON (e.g., "book/PSA/001.webp")
        img_dir: Base img directory

    Returns:
        Path object if image should exist in this source's directory,
        None if it's a cross-source reference
    """
    # Extract category and path components
    parts = image_path.split("/", 1)
    if len(parts) != 2:
        return None

    category, rest = parts

    # Extract source component from the path
    path_parts = rest.split("/")
    if not path_parts:
        return None

    path_source = path_parts[0]

    # Check if it's a cross-source reference
    normalized_source = normalize_source_for_image_path(source_id)
    if path_source != normalized_source:
        # Cross-source reference - image is in a different source's directory
        return None

    # Build expected path for this source
    # The 'rest' already includes the source component, so we don't add it again
    expected_path = img_dir / category / rest

    return expected_path


def get_actual_image_path(
    source_id: str,
    image_path: str,
    img_dir: Path,
) -> Optional[Path]:
    """
    Get the actual filesystem path where an image is located.

    This handles special cases and checks if the image exists in various locations.

    Args:
        source_id: Source ID (e.g., "PS-A")
        image_path: Path from JSON (e.g., "book/PSA/001.webp")
        img_dir: Base img directory

    Returns:
        Path object if image exists, None otherwise
    """
    # Extract category and rest of path
    parts = image_path.split("/", 1)
    if len(parts) != 2:
        return None

    category, rest = parts
    path_parts = rest.split("/")
    if not path_parts:
        return None

    path_source = path_parts[0]
    filename = path_parts[-1] if len(path_parts) > 1 else None
    subpath = "/".join(path_parts[1:]) if len(path_parts) > 1 else None

    # Try the path as specified in JSON first
    direct_path = img_dir / category / path_source
    if subpath:
        direct_path = direct_path / subpath

    if direct_path.exists():
        return direct_path

    # Try with normalized source name
    normalized = normalize_source_for_image_path(source_id)
    normalized_path = img_dir / category / normalized
    if subpath:
        normalized_path = normalized_path / subpath

    if normalized_path.exists() and normalized_path != direct_path:
        return normalized_path

    # For HAT-TG specifically, check if image is in TG/ directory
    if source_id == "HAT-TG" and path_source == "TG":
        tg_path = img_dir / category / "TG"
        if subpath:
            tg_path = tg_path / subpath
        if tg_path.exists():
            return tg_path

    # Image not found
    return None


# =============================================================================
# Image Reference Extraction
# =============================================================================

def find_image_references(data: Any, source: str, filename: str) -> List[ImageRef]:
    """
    Extract all image references from JSON data.

    Recursively searches through the data structure for image paths
    in 'href.path' fields.

    Args:
        data: Parsed JSON data (dict, list, or primitive)
        source: Source ID for context
        filename: JSON filename for context

    Returns:
        List of ImageRef objects found in the data
    """
    references = []

    def extract_from_value(value: Any, parent_key: str = "", context: Dict = None) -> None:
        """Recursively extract image references from a value."""
        if context is None:
            context = {}

        if isinstance(value, dict):
            # Check if this is an image reference
            if value.get("type") == "image":
                href = value.get("href")
                if isinstance(href, dict):
                    path = href.get("path")
                    if isinstance(path, str) and path:
                        # Determine category from path
                        category = path.split("/")[0] if "/" in path else "unknown"

                        ref = ImageRef(
                            source=source,
                            file=filename,
                            path=path,
                            category=category,
                            context={"parent_key": parent_key, **context},
                        )
                        references.append(ref)

            # Recursively search other dict values
            for key, val in value.items():
                new_context = {**context, "parent_key": key}
                extract_from_value(val, key, new_context)

        elif isinstance(value, list):
            # Recursively search list items
            for i, item in enumerate(value):
                new_context = {**context, "index": i}
                extract_from_value(item, parent_key, new_context)

    extract_from_value(data)
    return references


# =============================================================================
# Validation Functions
# =============================================================================

def validate_image_reference(
    ref: ImageRef,
    img_dir: Path,
    logger: Optional[logging.Logger] = None,
) -> ValidationResult:
    """
    Validate a single image reference.

    Args:
        ref: ImageRef to validate
        img_dir: Base img directory
        logger: Optional logger instance

    Returns:
        ValidationResult with validation details
    """
    log = logger or logging.getLogger(__name__)

    # Get expected path for this source
    expected_path = get_expected_image_path(ref.source, ref.path, img_dir)

    # Get actual path (where image really is)
    actual_path = get_actual_image_path(ref.source, ref.path, img_dir)

    # Check for special cases (design decisions, not bugs)
    normalized = normalize_source_for_image_path(ref.source)
    path_source = ref.path.split("/")[1] if "/" in ref.path else ""

    # Detect special cases
    if ref.source in config.IMAGE_PATH_SPECIAL_MAPPINGS and path_source == normalized:
        # This is a known special case (e.g., PS-A using PSA in paths)
        if actual_path and actual_path.exists():
            return ValidationResult(
                image_ref=ref,
                status="special_case",
                actual_path=actual_path,
                expected_path=expected_path,
                severity="info",
                message=f"Special case: {ref.source} uses {normalized} in image paths (design decision)",
            )

    # Check for cross-source references
    if expected_path is None:
        # This is a cross-source reference
        target_source = path_source
        return ValidationResult(
            image_ref=ref,
            status="cross_source",
            actual_path=actual_path,
            expected_path=None,
            severity="info",
            message=f"Cross-source reference to {target_source}",
        )

    # Check if image exists
    if actual_path and actual_path.exists():
        # Image found - valid
        if actual_path == expected_path:
            return ValidationResult(
                image_ref=ref,
                status="valid",
                actual_path=actual_path,
                expected_path=expected_path,
                severity="info",
                message="Image path is valid",
            )
        else:
            # Image exists but in unexpected location
            return ValidationResult(
                image_ref=ref,
                status="unexpected_location",
                actual_path=actual_path,
                expected_path=expected_path,
                severity="warning",
                message=f"Image exists at {actual_path.relative_to(img_dir)}, expected at {expected_path.relative_to(img_dir)}",
            )
    else:
        # Image not found - broken link
        return ValidationResult(
            image_ref=ref,
            status="missing",
            actual_path=None,
            expected_path=expected_path,
            severity="critical",
            message=f"Image not found at {expected_path.relative_to(img_dir) if expected_path else 'unknown path'}",
        )


def validate_source_images(
    source_id: str,
    data_dir: Path,
    img_dir: Path,
    logger: Optional[logging.Logger] = None,
) -> List[ValidationResult]:
    """
    Validate all image references for a single source.

    Args:
        source_id: Source ID to validate
        data_dir: Base data_rework directory
        img_dir: Base img directory
        logger: Optional logger instance

    Returns:
        List of ValidationResult objects
    """
    log = logger or logging.getLogger(__name__)
    results = []

    source_dir = data_dir / source_id
    if not source_dir.exists():
        log.warning(f"Source directory not found: {source_dir}")
        return results

    # Find all JSON files in data/ subdirectory
    data_files = []

    # Main data directory
    main_data = source_dir / "data"
    if main_data.exists():
        data_files.extend(main_data.glob("*.json"))
        data_files.extend(main_data.glob("bestiary/*.json"))
        data_files.extend(main_data.glob("class/*.json"))
        data_files.extend(main_data.glob("adventure/*.json"))

    log.debug(f"Found {len(data_files)} JSON files for {source_id}")

    # Process each JSON file
    for json_file in data_files:
        try:
            import json
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract image references
            filename = json_file.name
            refs = find_image_references(data, source_id, filename)

            log.debug(f"Found {len(refs)} image references in {filename}")

            # Validate each reference
            for ref in refs:
                validation = validate_image_reference(ref, img_dir, log)
                results.append(validation)

        except Exception as e:
            log.error(f"Error processing {json_file}: {e}")

    return results
