#!/usr/bin/env python3
"""
5etools Data Reorganization Package.

This package contains scripts for reorganizing 5etools data from
content-based structure to source-based structure.

Modules:
    config: Configuration constants
    utils: Utility functions
    json_processor: JSON file processing
    image_copier: Image copying
    pdf_copier: PDF copying
    validation: Validation runner
    reorganize_data: Main script
"""

__version__ = "1.0.0"
__author__ = "5etools data reorganization team"

from scripts.reorganize import config
from scripts.reorganize.utils import Statistics, setup_logging

__all__ = [
    "config",
    "Statistics",
    "setup_logging",
]
