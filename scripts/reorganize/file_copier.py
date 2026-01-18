#!/usr/bin/env python3
"""
Universal file copier for data reorganization.

This module provides a unified interface for copying files of different types
(PDF, images) by using a common base class with specialized implementations.
"""

import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

from scripts.reorganize import config
from scripts.reorganize.utils import Statistics, create_progress_iterator


# =============================================================================
# Base Copier Class
# =============================================================================

class BaseCopier(ABC):
    """Base class for copying files of any type."""

    def __init__(
        self,
        file_type: str,
        source_dir_name: str,
        output_subdir: str,
    ):
        """
        Initialize the copier.

        Args:
            file_type: Type of files ("pdf", "image")
            source_dir_name: Name of source directory ("pdf", "img")
            output_subdir: Name of output subdirectory ("pdf", "img")
        """
        self.file_type = file_type
        self.source_dir_name = source_dir_name
        self.output_subdir = output_subdir

    @abstractmethod
    def get_source_dir(self, base_dir: Path, source_id: str) -> Path:
        """Get the path to the source directory for a given source."""
        pass

    @abstractmethod
    def get_file_pattern(self) -> str:
        """Get the file pattern for searching (e.g., "*.pdf")."""
        pass

    @abstractmethod
    def should_copy_file(self, source_file: Path, source_id: str) -> bool:
        """Determine if a file should be copied."""
        pass

    @abstractmethod
    def get_output_path(
        self,
        source_file: Path,
        output_base_dir: Path,
        source_id: str,
    ) -> Path:
        """Get the output path for copying a file."""
        pass

    @abstractmethod
    def update_stats(self, stats: Statistics, source_id: str, count: int) -> None:
        """Update statistics with copy results."""
        pass

    def copy_file(
        self,
        source_file: Path,
        output_file: Path,
        source_id: str,
        stats: Statistics,
        log: logging.Logger,
    ) -> bool:
        """
        Copy a single file with error handling.

        Args:
            source_file: Source file path
            output_file: Destination file path
            source_id: Source ID
            stats: Statistics object
            log: Logger instance

        Returns:
            True if copy was successful, False otherwise
        """
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, output_file)
            log.debug(f"    Copied {self.file_type}: {source_file.name}")
            return True
        except Exception as e:
            error_msg = f"Failed to copy {self.file_type} {source_file}: {e}"
            log.error(error_msg)
            stats.add_error(error_msg)
            return False

    def copy_for_source(
        self,
        source_id: str,
        base_dir: Path,
        output_dir: Path,
        stats: Statistics,
        log: logging.Logger,
    ) -> int:
        """
        Copy files for a single source.

        Args:
            source_id: Source ID (e.g., "PHB")
            base_dir: Base directory (e.g., /img/)
            output_dir: Output directory (e.g., /data_rework/)
            stats: Statistics object
            log: Logger instance

        Returns:
            Number of files copied
        """
        source_dir = self.get_source_dir(base_dir, source_id)

        if not source_dir.exists():
            return 0

        count = 0
        file_pattern = self.get_file_pattern()

        try:
            files = list(source_dir.rglob(file_pattern))

            if not files:
                return 0

            log.debug(f"  Copying {len(files)} {self.file_type} files for {source_id}...")

            for source_file in files:
                if not self.should_copy_file(source_file, source_id):
                    continue

                output_file = self.get_output_path(source_file, output_dir, source_id)

                if self.copy_file(source_file, output_file, source_id, stats, log):
                    count += 1

            if count > 0:
                log.debug(f"    Copied {count} {self.file_type} files for {source_id}")

        except Exception as e:
            error_msg = f"Failed to copy {self.file_type}s for {source_id}: {e}"
            log.error(error_msg)
            stats.add_error(error_msg)

        return count

    def copy_all(
        self,
        sources: Dict[str, Any],
        base_dir: Path,
        output_dir: Path,
        stats: Statistics,
        log: logging.Logger,
    ) -> None:
        """
        Copy files for all sources.

        Args:
            sources: Dict of sources from books.json
            base_dir: Base directory (e.g., /img/)
            output_dir: Output directory (e.g., /data_rework/)
            stats: Statistics object
            log: Logger instance
        """
        log.info(f"Copying {self.file_type} files for all sources...")

        total_count = 0

        for source_id, source_data in create_progress_iterator(
            sources.items(),
            desc=f"Copying {self.file_type}s",
        ):
            count = self.copy_for_source(source_id, base_dir, output_dir, stats, log)
            self.update_stats(stats, source_id, count)

            # Handle both int and dict return types
            if isinstance(count, dict):
                total_count += sum(count.values())
            else:
                total_count += count

        log.info(f"{self.file_type.capitalize()} copying complete: {total_count} files copied")


# =============================================================================
# PDF Copier
# =============================================================================

class PdfCopier(BaseCopier):
    """Copier for PDF files."""

    def __init__(self):
        super().__init__(file_type="pdf", source_dir_name="pdf", output_subdir="pdf")

    def get_source_dir(self, base_dir: Path, source_id: str) -> Path:
        """Get PDF source directory for a source."""
        return base_dir / "pdf" / source_id

    def get_file_pattern(self) -> str:
        """Get PDF file pattern."""
        return "*.pdf"

    def should_copy_file(self, source_file: Path, source_id: str) -> bool:
        """Check if file is a PDF."""
        return source_file.suffix == ".pdf"

    def get_output_path(self, source_file: Path, output_dir: Path, source_id: str) -> Path:
        """Get output path for PDF file."""
        return output_dir / source_id / "pdf" / source_file.name

    def update_stats(self, stats: Statistics, source_id: str, count: int) -> None:
        """Update statistics with PDF count."""
        stats.add_pdf_count(source_id, count)


# =============================================================================
# Image Copier
# =============================================================================

class ImageCopier(BaseCopier):
    """Copier for image files."""

    def __init__(self):
        super().__init__(file_type="image", source_dir_name="img", output_subdir="img")

    def get_source_dir(self, base_dir: Path, source_id: str) -> Path:
        """
        Get image source directory for a source.

        Uses IMAGE_PATH_SPECIAL_MAPPINGS for sources like PS-A -> PSA.
        """
        path_component = config.IMAGE_PATH_SPECIAL_MAPPINGS.get(source_id, source_id)
        return base_dir / path_component

    def get_file_pattern(self) -> str:
        """Get image file pattern."""
        return "*"

    def should_copy_file(self, source_file: Path, source_id: str) -> bool:
        """Check if file is an image."""
        return source_file.suffix in [".webp", ".png", ".jpg", ".jpeg"]

    def get_output_path(self, source_file: Path, output_dir: Path, source_id: str) -> Path:
        """Get output path for image file, preserving subdirectory structure."""
        # Get the relative path from the source directory
        source_dir = self.get_source_dir(Path("/img"), source_id)
        rel_path = source_file.relative_to(source_dir)
        return output_dir / source_id / "img" / rel_path

    def copy_for_source(
        self,
        source_id: str,
        base_dir: Path,
        output_dir: Path,
        stats: Statistics,
        log: logging.Logger,
    ) -> Dict[str, int]:
        """
        Copy images for a single source with categorization.

        Args:
            source_id: Source ID
            base_dir: Base image directory
            output_dir: Output directory
            stats: Statistics object
            log: Logger instance

        Returns:
            Dict with counts per image category
        """
        category_counts = {}

        # 1. Copy cover images
        cover_count = self._copy_cover_images(source_id, base_dir, output_dir, stats, log)
        if cover_count > 0:
            category_counts["covers"] = cover_count

        # 2. Copy category images
        for category in config.IMAGE_CATEGORIES:
            count = self._copy_category_images(
                source_id, category, base_dir, output_dir, stats, log
            )
            if count > 0:
                category_counts[category] = count

        # 3. Copy token images
        token_count = self._copy_token_images(source_id, base_dir, output_dir, stats, log)
        if token_count > 0:
            category_counts["tokens"] = token_count

        total = sum(category_counts.values())
        if total > 0:
            log.info(f"  Copied {total} images for {source_id} from {len(category_counts)} categories")

        return category_counts

    def update_stats(self, stats: Statistics, source_id: str, count: int) -> None:
        """Update statistics with image counts."""
        if isinstance(count, dict):
            stats.add_image_stats(source_id, count)
        else:
            stats.add_image_stats(source_id, {"total": count})

    def _copy_cover_images(
        self,
        source_id: str,
        img_dir: Path,
        output_dir: Path,
        stats: Statistics,
        log: logging.Logger,
    ) -> int:
        """Copy cover images for a source."""
        cover_file = img_dir / "covers" / f"{source_id}.webp"

        if not cover_file.exists():
            return 0

        output_file = output_dir / source_id / "img" / "covers" / cover_file.name

        if self.copy_file(cover_file, output_file, source_id, stats, log):
            return 1
        return 0

    def _copy_category_images(
        self,
        source_id: str,
        category: str,
        img_dir: Path,
        output_dir: Path,
        stats: Statistics,
        log: logging.Logger,
    ) -> int:
        """Copy images for a specific category."""
        path_component = config.IMAGE_PATH_SPECIAL_MAPPINGS.get(source_id, source_id)
        source_cat_dir = img_dir / category / path_component

        if not source_cat_dir.exists():
            return 0

        output_cat_dir = output_dir / source_id / "img" / category / path_component
        output_cat_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        for item in source_cat_dir.rglob("*"):
            if item.is_file() and self.should_copy_file(item, source_id):
                rel_path = item.relative_to(source_cat_dir)
                output_file = output_cat_dir / rel_path

                if self.copy_file(item, output_file, source_id, stats, log):
                    count += 1

        if count > 0:
            log.debug(f"    Copied {count} {category} images")

        return count

    def _copy_token_images(
        self,
        source_id: str,
        img_dir: Path,
        output_dir: Path,
        stats: Statistics,
        log: logging.Logger,
    ) -> int:
        """Copy token images for a source."""
        path_component = config.IMAGE_PATH_SPECIAL_MAPPINGS.get(source_id, source_id)
        source_tokens_dir = img_dir / "bestiary" / "tokens" / path_component

        if not source_tokens_dir.exists():
            return 0

        output_tokens_dir = output_dir / source_id / "img" / "bestiary" / "tokens" / path_component
        output_tokens_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        for item in source_tokens_dir.rglob("*"):
            if item.is_file() and self.should_copy_file(item, source_id):
                rel_path = item.relative_to(source_tokens_dir)
                output_file = output_tokens_dir / rel_path

                if self.copy_file(item, output_file, source_id, stats, log):
                    count += 1

        if count > 0:
            log.debug(f"    Copied {count} token images")

        return count


# =============================================================================
# Copier Factory
# =============================================================================

def get_copier(file_type: str) -> BaseCopier:
    """
    Get a copier instance for the specified file type.

    Args:
        file_type: Type of files ("pdf", "image")

    Returns:
        Instance of the appropriate copier

    Raises:
        ValueError: If file_type is unknown

    Note:
        JSON files are handled separately in json_processor.py
    """
    copiers = {
        "pdf": PdfCopier,
        "image": ImageCopier,
    }

    copier_class = copiers.get(file_type)
    if not copier_class:
        raise ValueError(f"Unknown file type: {file_type}")

    return copier_class()
