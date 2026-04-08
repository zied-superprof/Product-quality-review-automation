# Technology Stack

**Analysis Date:** 2026-04-08

## Languages

**Primary:**
- Python 3 (3.14.3 verified) - Structural validation and report generation

**Configuration & Data:**
- JSON - Configuration files, output reports, learning system state
- CSV - Input data (translation data in per-notification and full-database formats)
- Markdown - Command definitions, review reports, documentation

## Runtime

**Environment:**
- macOS (deployment target verified at 23.6.0)
- Python 3.x (3.14.3 installed, no version pinning required)

**Python Execution:**
- Direct execution via `python3` command
- Stdlib only — no pip packages required for structural validation
- Optional package `markdown` for PDF generation (handles HTML generation)

## Frameworks

**Core Validation:**
- **Custom regex-based template validator** - Pattern matching for Superprof template syntax
  - Location: `scripts/structural_validator.py`
  - Validates: Template variables (`@TPL_*@`), conditionals (`<TPL_IF_*>`), custom markup (`[LIEN]`, `[BOUTON]`)
  - CSV parsing: Built on stdlib `csv` module

**Report Generation:**
- **Python markdown library** (optional) - Markdown to HTML conversion for PDF output
  - Location: `scripts/generate_pdf.py`
  - Purpose: Convert markdown reports to HTML with styled layout

**PDF Conversion (fallback chain):**
1. `weasyprint` library (if installed)
2. `cupsfilter` system command (UNIX/macOS)
3. HTML-only fallback (no PDF auto-generation)

## Key Dependencies

**Critical (Stdlib only):**
- `argparse` - CLI argument parsing
- `csv` - CSV file parsing (Sheet113-style format)
- `json` - JSON configuration and output handling
- `re` - Regex pattern matching for template validation
- `pathlib` - File system operations
- `unicodedata` - Unicode character normalization for mojibake detection
- `collections.defaultdict` - Data structure for grouping

**Optional:**
- `markdown` (Python package) - Markdown parsing for PDF generation
- `weasyprint` (Python package) - HTML to PDF conversion
- `subprocess` - System command execution (cupsfilter fallback)

**System Commands:**
- `python3` - Entry point for all scripts
- `cupsfilter` - PDF generation fallback (macOS/UNIX only)

## Configuration

**Environment:**
- No environment variables required (stdlib-only execution)
- Configuration files stored as JSON (no .env or dotenv)
- File paths resolved relative to project root via `pathlib.Path`

**Build:**
- No build process — pure Python scripts
- No package.json, requirements.txt, or setup.py
- Scripts called directly: `python3 scripts/structural_validator.py`
- Execution pre-approved in `.claude/settings.local.json`

## Configuration Files

**Core configuration:**
- `config/label_patterns.json` - Template variable syntax patterns, validation regex, subject variable usage rules per language
- `config/tone_guidelines.json` - Brand voice principles, formality rules (formal_vous_languages vs informal_standard_languages), tone guidelines per language
- `config/languages.json` - 40+ language metadata (codes, names, formality, expected length ratios, character encoding notes)
- `config/variables.csv` - Complete list of all valid Superprof template variables and their categories

**Learning system:**
- `corrections/corrections_log.json` - Accumulated corrections from previous reviews, extracted rules, and validation patterns

**CLI command definition:**
- `.claude/commands/review-translations.md` - Skill definition for `/review-translations` command with full workflow steps

## Platform Requirements

**Development:**
- Python 3 (tested with 3.14.3)
- macOS or UNIX system (for cupsfilter PDF fallback)
- Text editor or Claude Code IDE
- No additional system libraries needed

**Production:**
- Python 3.x runtime
- CSV input files in per-notification or full-database format
- Read access to `config/` and `corrections/` directories
- Write access to `reports/` and `corrections/` directories for output

## Entry Points

**Python scripts:**
- `scripts/structural_validator.py` - Main validation engine (CLI: `python3 scripts/structural_validator.py --input <csv> --type <type> --config-dir config/`)
- `scripts/generate_pdf.py` - PDF generation utility (produces markdown-to-HTML-to-PDF conversion)

**Claude skill:**
- `.claude/commands/review-translations.md` - Orchestrates full workflow (called via `/review-translations` command)

## Data Flow Architecture

1. **Input**: CSV files (per-notification or full-database format)
2. **Parsing**: `csv` module parses per-country/per-language blocks
3. **Structural validation**: `structural_validator.py` runs 10+ checks (label integrity, emoji consistency, encoding, HTML tag balance)
4. **AI quality review**: Claude reviews flagged markets against learned rules and tone guidelines
5. **Report generation**: Merged findings grouped by country, written to `reports/review-by-country-[date].md`
6. **PDF conversion**: Optional markdown→HTML→PDF via `markdown` library + weasyprint/cupsfilter
7. **Learning loop**: User feedback → rules extracted → saved to `corrections/corrections_log.json`

## Encoding & Character Support

**UTF-8 throughout:**
- All files read/written with `encoding='utf-8'`
- Supports 40+ language scripts: Latin, Cyrillic, Arabic (RTL), CJK, Thai, Devanagari, Bengali, Hebrew
- Mojibake detection: Custom regex pattern matching common UTF-8 misinterpretation sequences
- Unicode normalization via `unicodedata` module

## Assumptions & Constraints

- **CSV format**: Expects per-notification or full-database layout (not free-form)
- **Template syntax**: Fixed to `@TPL_*@`, `<TPL_IF_*>`, `[LIEN]` etc. (hardcoded patterns)
- **French as reference**: All validation compares against French cell/row
- **No database**: File-based configuration and output (JSON, CSV, Markdown)
- **No external APIs**: Fully self-contained (except optional markdown library for PDF)
- **Single-threaded**: Sequential processing, no async or parallel execution

---

*Stack analysis: 2026-04-08*
