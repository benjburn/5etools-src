# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

5etools is a static single-page application for D&D 5e reference tools. The site is built as a collection of HTML pages that load shared JavaScript libraries, with data stored as JSON files. No backend is required - everything runs client-side.

**Key architectural concepts:**
- **Static site**: HTML pages + shared JS libraries + JSON data files
- **Data-driven rendering**: All content is rendered from JSON data files using the Renderer system
- **Tag-based references**: Data uses `@tag` syntax (e.g., `{@spell fireball}`) for cross-references that are rendered dynamically
- **Build pipeline**: Several data files are generated from source data via scripts in `node/`

## Essential Commands

### Development
- `npm run serve:dev` - Start local dev server on http://localhost:5050
- `npm run test` - Run full test suite (JS linter, unit tests, CSS linter, data validation)
- `npm run test:unit` - Run Jest unit tests only
- `npm run lint` - Fix all linting issues (JS, CSS, data)
- `npm run lint:js` - Fix ESLint issues
- `npm run lint:js:fast` - Lint only changed JS files
- `npm run lint:data` - Prettify/format JSON data files

### Building and Generation
- `npm run build` - Full production build (clean JSON, generate data, build CSS, build service worker)
- `npm run gen` - Run all data generation scripts (search index, pages, lookups, etc.)
- `npm run gen:search-index` - Regenerate search index only
- `npm run gen:pages` - Regenerate HTML pages only
- `npm run build:css` - Compile SCSS to compressed CSS
- `npm run clean-jsons` - Clean/minify JSON files

### Version Management
- `npm run version-bump -- major|minor|patch` - Bump version and create git tag (runs tests first)
- `npm run version-bump -- 1.2.3` - Set specific version

### Data Quality
- `npm run test:data` - Validate JSON schemas and data integrity
- `npm run test:json` - JSON schema validation only
- `npm run test:tags` - Validate tag references in data
- `npm run spellcheck:check-data-quick` - Spellcheck only changed data files

## Code Architecture

### Data Structure (`data/`)
All game data is stored as JSON files. Key patterns:
- **Category files**: `spells.json`, `items.json`, `races.json`, `bestiary/` etc.
- **Fluff files**: `fluff-*.json` contain narrative/descriptive content separate from mechanics
- **Generated files**: `data/generated/` contains auto-generated files (don't edit manually)
- **Tag system**: `{@type name}` syntax creates clickable cross-references (e.g., `{@spell fireball}`, `{@item longsword}`)
- **Source attributes**: Every entity has a `source` field (book abbreviation) and optional `page` number

### JavaScript Structure (`js/`)
- **`parser.js`**: Core parsing utilities for converting data formats (abbreviations to full names, etc.)
- **`utils.js`** & **`utils-config.js`**: Global utilities and configuration constants
- **`renderer.js`**: Main rendering engine for converting tagged text to HTML
- **`render-*.js`**: Specialized renderers for specific data types (spells, items, creatures, etc.)
- **`filter-*.js`**: Filter components for each data type
- **Page-specific scripts**: e.g., `spells.js`, `bestiary.js` handle individual page logic

### Tag/Reference System
The `{@tag}` syntax is the core of cross-referencing:
- `{@spell fireball}` -> links to Fireball spell
- `{@creature goblin}` -> links to Goblin stat block
- `{@item longsword}` -> links to Longsword item
- `{@filter field}` -> renders UI filter controls
- `{@page 123}` -> renders page number reference

Tags are automatically rendered as interactive elements by the Renderer.

### Generation Pipeline (`node/`)
Scripts that generate derived data:
- **`generate-all.js`** - Orchestrates all generation scripts
- **`generate-pages.js`** - Generates HTML pages from templates
- **`generate-search-index.js`** - Creates search index
- **`generate-spell-source-lookup.js`** - Spell reference lookup tables
- **`tag-jsons.js`** - Auto-tags references in data (manual review required)

### Testing (`test/`)
- **`test-all.js`** - Orchestrates all tests
- **`test-json.js`** - JSON schema validation using AJV
- **`test-tags.js`** - Validates tag references resolve correctly
- **Unit tests**: Jest tests in `test/` directory

## Data Entry Conventions

### Code Style
- **JavaScript**: Use tabs (not spaces)
- **CSS**: BEM naming strategy
- **JSON**: Tab indentation, except `data/generated/` (minified)

### JSON Character Encoding
Required replacements for data consistency:
- `"` → `\u2014` (em dash)
- `–` → `\u2013` (en dash)
- `−` → `\u2212` (minus sign)
- `'` → `'` (smart quote to straight)
- `"` → `"` (smart quote to straight)

### Dashes
- `-` (hyphen): Word hyphenation only, e.g., `60-foot`, `18th-level`
- `\u2014` (em dash): Parenthetical statements, empty table rows
- `\u2013` (en dash): Numerical ranges, e.g., `1\u20135` (not `1-5`)
- `\u2212` (minus): Unary minus for penalties

### Measurements
- Adjectives: hyphen + full unit, e.g., `60-foot line`
- Nouns: space + abbreviated unit with period, e.g., `60 ft.`, `120 ft.`
- Time/frequency: `/` with capital unit, no spaces, e.g., `2/Turn`, `3/Day`

### Dice Notation
Format: `[X]dY[ <+|-|×> Z]` (spaces around operators)
- Examples: `d6`, `2d6`, `2d6 + 1`, `4d6 × 10`

### Item Names
- Title case
- Units in parentheses: sentence case, e.g., `Potion of Healing (vial)`

### Tag References
- Only tag intended mechanical references, not casual usage
- Never tag within `quote` blocks
- Avoid forward references (don't reference content from books published later)

## Important Constraints

### Data Sources
- Only "official" WotC-published content in main repo
- Homebrew goes to separate repository (github.com/TheGiddyLimit/homebrew)
- Prioritize RAW (rules as written) - 1:1 copy of source material
- Use latest version of content; older versions to homebrew if significantly different

### `_copy` Entities
Only use `_copy` when entities are meaningfully different:
- **Sufficient**: Different traits/actions, spellcasting changes, damage type changes, immunities, unique art
- **Insufficient alone**: Size, type, alignment, HP (combine with other differences)

### Target JavaScript
- Any feature available in both Chrome and Firefox for 6+ months is allowed

### Keyboard Events
- Avoid ALT-modified events (not available on macOS/Linux)
- Prefer CTRL/SHIFT modifiers

## Service Worker
The service worker enables offline use but is not committed. Build locally with:
- `npm run build:sw` - Development version (with logging)
- `npm run build:sw:prod` - Production version

Note: Service worker caches files - disable or work around it during local development to see changes.

## Issue Tracking
This project uses **bd** (beads) for issue tracking. See `AGENTS.md` for details.
- `bd ready` - Find available work
- `bd show <id>` - View issue details
- `bd close <id>` - Complete work

## Technical Documentation

Detailed technical documentation for core systems is available in the `docs/` directory:
- **[docs/tags.md](docs/tags.md)** - Tag processing and rendering system
- **[docs/coordination.md](docs/coordination.md)** - Main coordination architecture
- **[docs/data-validation.md](docs/data-validation.md)** - Data integrity validation
- **[docs/cross-source.md](docs/cross-source.md)** - Cross-source references
- **[docs/images.md](docs/images.md)** - Image reference system
- **[docs/fluff.md](docs/fluff.md)** - Fluff/narrative content

See [docs/README.md](docs/README.md) for the full documentation index.

## Python tooling policy

For all Python work in this repository:

- Use `uv` for virtual environments and dependency management.
- Do NOT use pip, poetry, or conda unless explicitly instructed.
- Preferred commands:
  - `uv init`
  - `uv venv`
  - `uv pip install`
  - `uv pip sync`

This is a strict requirement.
