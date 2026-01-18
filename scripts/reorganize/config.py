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
    "traps",
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
# Image Path Validation
# =============================================================================

# Special mappings for image paths (source_id -> path component)
# These are DESIGN DECISIONS, not bugs - the paths are intentionally different
IMAGE_PATH_SPECIAL_MAPPINGS = {
    # Plane Shift sources use abbreviated forms in image paths
    # Folder: PS-A, but image paths use book/PSA/
    "PS-A": "PSA",
    "PS-I": "PSI",
    "PS-D": "PSD",
    "PS-K": "PSK",
    "PS-X": "PSX",
    "PS-Z": "PSZ",

    # HAT-TG uses TG in image paths (historical naming convention)
    "HAT-TG": "TG",

    # Submodule sources use base/submodule path structure
    # AitFR series
    "AitFR-AVT": "AitFR/AVT",
    "AitFR-DN": "AitFR/DN",
    "AitFR-FCD": "AitFR/FCD",
    "AitFR-ISF": "AitFR/ISF",
    "AitFR-THP": "AitFR/THP",

    # MCV series
    "MCV1SC": "MCV/1SC",
    "MCV2DC": "MCV/2DC",
    "MCV3MC": "MCV/3MC",
    "MCV4EC": "MCV/4EC",

    # TftYP series
    "TftYP-AtG": "TftYP/AtG",
    "TftYP-DiT": "TftYP/DiT",
    "TftYP-TFoF": "TftYP/TFoF",
    "TftYP-THSoT": "TftYP/THSoT",
    "TftYP-TSC": "TftYP/TSC",
    "TftYP-ToH": "TftYP/ToH",
    "TftYP-WPM": "TftYP/WPM",

    # NRH series
    "NRH-ASS": "NRH/ASS",
    "NRH-AT": "NRH/AT",
    "NRH-AVitW": "NRH/AVitW",
    "NRH-AWoL": "NRH/AWoL",
    "NRH-CoI": "NRH/CoI",
    "NRH-TCMC": "NRH/TCMC",
    "NRH-TLT": "NRH/TLT",

    # HAT series
    "HAT-LMI": "HAT/LMI",
}

# Sources that are known to use cross-source image references
# These are intentional and should not be flagged as errors
CROSS_SOURCE_IMAGE_SOURCES = {
    "HFFotM",  # References DMG, AAG, DoD images
    # Add more as discovered during audits
}

# Image categories to validate
IMAGE_PATH_CATEGORIES = {
    "bestiary",
    "book",
    "adventure",
    "items",
    "backgrounds",
    "classes",
    "races",
    "spells",
    "deities",
    "decks",  # For TD source
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
    "book",       # Book data files (content, sections, etc.)
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

# Log file name (will be created in output directory)
LOG_FILE = "reorganization.log"

# =============================================================================
# Submodule Settings
# =============================================================================

# Sources with hyphens that are NOT submodules (they are independent sources)
# These sources should be treated as regular sources, not split into base/submodule
NOT_SUBMODULE_SOURCES = {
    # Plane Shift sources (independent sources, not submodules)
    "PS-A",
    "PS-D",
    "PS-I",
    "PS-K",
    "PS-X",
    "PS-Z",
    # HAT-TG is an independent source (not a submodule of HAT)
    "HAT-TG",
}

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
        "AAG", "BAM", "MPP", "SatO", "FRAiF", "FRHoF"
    ],
    "setting-alt": [
        "PS-Z", "PS-I", "PS-K", "PS-A", "PS-X", "PS-D", "NF", "LFL"
    ],
    "adventure": [
        # Major adventures
        "LMoP", "HotDQ", "RoT", "PotA", "OotA", "SKT",
        "CoS", "ToA", "WDH", "WDMM", "IDRotF", "WBtW",
        "GoS", "TftYP",
        # TftYP submodules
        "TftYP-AtG", "TftYP-DiT", "TftYP-TFoF", "TftYP-THSoT",
        "TftYP-TSC", "TftYP-ToH", "TftYP-WPM",
        # Other adventures
        "CoA", "CM", "CRCotN", "DIP", "DSotDQ", "DitLCoT", "DoSI",
        "DrDe", "EFR", "ESK", "BGDIA", "JttRC", "KftGV", "LLK",
        "LR", "LRDT", "LoX", "OoW", "PaBTSO", "QftIS", "RMBRE",
        "ToFW", "VEoR", "WttHC",
        # AitFR series
        "AitFR-AVT", "AitFR-DN", "AitFR-FCD", "AitFR-ISF", "AitFR-THP",
        # NRH series
        "NRH-ASS", "NRH-AT", "NRH-AVitW", "NRH-AWoL", "NRH-CoI",
        "NRH-TCMC", "NRH-TLT",
        # Misc adventures
        "AZfyT", "BQGT", "DC", "FFotR", "GHLoE", "GotSF", "HBTD",
        "HftT", "HotB", "IMR", "KKW", "LK", "MCV1SC", "MCV2DC",
        "MCV3MC", "MFF", "MisMV1", "PiP", "RtG", "SDW", "SLW",
        "ScoEE", "SjA", "TLK", "TTP", "UtHftLH", "VD", "VNotEE", "XMtS",
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
