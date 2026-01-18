#!/usr/bin/env python3
"""
Configuration for data reorganization.

This module contains all configuration constants for the 5etools data
reorganization script.
"""

from pathlib import Path

# =============================================================================
# Directory and File Patterns
# =============================================================================

# Directories to skip during processing
SKIP_DIRS = {
    "generated",
    "__pycache__",
    ".git",
    "node_modules",
}

# Files to skip (not processed)
SKIP_FILES = {
    "books.json",
    "changelog.json",
    "converter.json",
}

# File patterns to skip (fnmatch patterns)
SKIP_PATTERNS = {
    "foundry-*.json",
}

# =============================================================================
# Image Categories
# =============================================================================

# Image categories to process from /img/ directory
IMAGE_CATEGORIES = {
    "bestiary",
    "book",
    "items",
    "backgrounds",
    "classes",
    "races",
    "spells",
    "deities",
    "adventure",
    "decks",
    "dmscreen",
    "vehicles",
    "hazards",
    "objects",
    "conditionsdiseases",
    "languages",
    "charcreationoptions",
    "feats",
    "optionalfeatures",
    "cultsboons",
    "rewards",
    "recipes",
    "trapshazards",
    "variantrules",
    "psionics",
    "skills",
    "senses",
    "encounters",
    "encounterbuilder",
    "life",
    "loot",
    "makecards",
    "magicvariants",
    "msbcr",
    "names",
    "bastions",
}

# =============================================================================
# JSON Entity Types
# =============================================================================

# JSON entity types (root keys) to process
ENTITY_TYPES = {
    "background",
    "item",
    "monster",
    "class",
    "subclass",
    "race",
    "feat",
    "spell",
    "deity",
    "condition",
    "disease",
    "language",
    "object",
    "vehicle",
    "hazard",
    "trap",
    "reward",
    "recipe",
    "cult",
    "boon",
    "optionalfeature",
    "skill",
    "sense",
    "psionic",
    "action",
    "skill",
    "sense",
    "language",
    "vehicle",
}

# =============================================================================
# Fluff Files
# =============================================================================

# Fluff file pattern
FLUFF_PATTERNS = "fluff-*.json"

# Fluff entity types
FLUFF_ENTITY_PREFIX = "fluff"

# =============================================================================
# Special Directories
# =============================================================================

# Subdirectories in /data/ that contain special JSON files
SPECIAL_DATA_SUBDIRS = {
    "bestiary",   # Monster data files
    "class",      # Class data files
    "adventure",  # Adventure data files
}

# =============================================================================
# Cross-Source Handling
# =============================================================================

# Whether to copy cross-source images
# If False: cross-source image references are NOT copied (links stay as-is)
# If True: all referenced images are copied regardless of source
COPY_CROSS_SOURCE_IMAGES = False

# =============================================================================
# JSON Output Settings
# =============================================================================

# JSON indentation (use "\t" for tab like original files)
JSON_INDENT = "\t"

# Ensure ASCII (False to preserve Unicode characters)
JSON_ENSURE_ASCII = False

# Sort keys in JSON output (False to preserve original order)
JSON_SORT_KEYS = False

# =============================================================================
# Validation Settings
# =============================================================================

# Whether to run validation after reorganization
RUN_VALIDATION_BY_DEFAULT = True

# Validation scripts to run
VALIDATION_SCRIPTS = {
    "check_data_integrity": "scripts/validation/check_data_integrity.py",
    "check_images": "scripts/validation/check_images.py",
    "check_cross_source": "scripts/validation/check_cross_source.py",
}

# =============================================================================
# Logging Settings
# =============================================================================

# Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
DEFAULT_LOG_LEVEL = "INFO"

# Log format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Date format for logs
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# =============================================================================
# Performance Settings
# =============================================================================

# Number of workers for parallel processing
MAX_WORKERS = 4

# Whether to show progress bars
SHOW_PROGRESS = True

# Chunk size for batch processing
BATCH_SIZE = 100

# =============================================================================
# Report Settings
# =============================================================================

# Report filename
REORGANIZATION_REPORT = "reorganization-report.json"
VALIDATION_REPORT = "validation-report.json"

# Report format (pretty-printed JSON)
REPORT_INDENT = 2

# =============================================================================
# Paths (can be overridden by command-line arguments)
# =============================================================================

# Default paths (relative to project root)
DEFAULT_DATA_DIR = Path("data")
DEFAULT_IMG_DIR = Path("img")
DEFAULT_OUTPUT_DIR = Path("data_rework")

# =============================================================================
# Source Groups
# =============================================================================

# Source groups from data-rework-structure.md
SOURCE_GROUPS = {
    "core": ["PHB", "XPHB", "DMG", "XDMG", "MM", "XMM"],
    "supplement": [
        "VGM", "XGE", "MTF", "AI", "TCE", "FTD", "MPMM",
        "BGG", "BMT", "DMTCRG"
    ],
    "supplement-alt": [
        "OGA", "AWM", "RMR", "MGELFT", "DoD", "MaBJoV", "TD",
        "MCV4EC", "HAT-TG", "ABH", "EFA"
    ],
    "setting": [
        "SCAG", "GGR", "ERLW", "EGW", "MOT", "VRGR", "SCC",
        "AAG", "BAM", "MPP", "SatO", "FRAiF", "FRHoF", "CoS"
    ],
    "setting-alt": [
        "PS-Z", "PS-I", "PS-K", "PS-A", "PS-X", "PS-D", "NF", "LFL"
    ],
    "screen": ["Screen", "ScreenDungeonKit", "ScreenWildernessKit", "ScreenSpelljammer", "XScreen"],
    "recipe": ["HF", "HFFotM", "PaF"],
    "other": ["SAC", "XSAC"],
    "organized-play": ["AL"],
}

# =============================================================================
# Metadata Settings
# =============================================================================

# Script version
VERSION = "1.0.0"

# Script author
AUTHOR = "5etools data reorganization team"

# Script description
DESCRIPTION = """
Reorganize 5etools data from content-based structure to source-based structure.

Creates /data_rework/ with subdirectories for each source (PHB, XPHB, DMG, etc.)
while preserving the original /data/ and /img/ directories.
""".strip()
