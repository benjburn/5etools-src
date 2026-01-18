# 5etools Technical Documentation

This directory contains detailed technical documentation for the 5etools codebase, covering core modules and systems.

## Documentation Index

### Core Systems

- **[Tags Module](tags.md)** - Complete guide to the tag processing system
  - Tag parsing and rendering
  - Tag types and syntax
  - Cross-reference system
  - ~70 tags in the system
  - 265 lines

- **[Coordination Module](coordination.md)** - Main coordination architecture
  - Page initialization and loading
  - Data management (DataUtil)
  - Navigation system (Hist)
  - Homebrew/Prerelease integration
  - 938 lines

### Data Management

- **[Data Validation](data-validation.md)** - Data integrity and validation
  - JSON schema validation (AJV)
  - Tag reference validation
  - Image validation
  - Test infrastructure
  - 902 lines

- **[Cross-Source References](cross-source.md)** - Cross-source reference system
  - Source tracking (2014 vs 2024)
  - Reference resolution
  - Redirect lookup
  - 431 lines

- **[Data Rework Structure](data-rework-structure.md)** - Planned /data_rework directory structure
  - Source-based organization (60 sources)
  - Folder structure by source
  - File format specifications
  - Migration from current /data structure
  - Examples and validation requirements

### Python Scripts

- **[Python Validation Scripts](python-scripts.md)** - Python validation scripts guide
  - Environment setup with `uv`
  - Running validation scripts
  - PDF validation (check_pdf.py)
  - Links validation (check_links.py)
  - Troubleshooting and development
  - Complete guide for all Python tools

### Content Systems

- **[Image References](images.md)** - Image reference system
  - Image loading and caching
  - URL generation
  - Token handling
  - Gallery rendering
  - 807 lines

- **[Fluff Module](fluff.md)** - Fluff/narrative content system
  - Fluff data structure
  - Inline vs referenced fluff
  - DataLoader integration
  - Rendering narrative content
  - 743 lines

## About This Documentation

These documents are technical references for understanding the internal architecture of 5etools. They provide in-depth analysis of:

- Module responsibilities and interactions
- Code flow and execution patterns
- Data structures and formats
- Validation and testing infrastructure

For contribution guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md). For development setup, see [CLAUDE.md](../CLAUDE.md).

## Quick Links

- [Project README](../README.md) - Project overview and setup
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute
- [Development Guide](../CLAUDE.md) - Development instructions and conventions
