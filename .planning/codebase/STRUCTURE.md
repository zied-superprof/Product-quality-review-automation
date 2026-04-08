# Codebase Structure

**Analysis Date:** 2026-04-08

## Directory Layout

```
product-quality-review-automation/
├── .claude/
│   ├── commands/
│   │   └── review-translations.md      # Main /review-translations skill (9-step workflow)
│   └── settings.local.json             # Local config: Bash pre-approval, Write access rules
├── .planning/
│   └── codebase/                       # Generated analysis docs (this directory)
├── config/
│   ├── label_patterns.json             # Template variable syntax, validation rules, subject variable usage per language
│   ├── tone_guidelines.json            # Formality levels, informal_standard_languages list, brand voice per language
│   ├── review_rules_compact.md         # Linguistic review criteria and language-specific rules
│   ├── languages.json                  # Language metadata (codes, names, native speakers, market info)
│   └── variables.csv                   # Catalog of valid @TPL_*@ variables and descriptions
├── corrections/
│   └── corrections_log.json            # Accumulated corrections, learned rules, rule summaries from past reviews
├── reports/
│   ├── review-by-country-YYYY-MM-DD.md       # Generated report: issues grouped by country
│   ├── review-by-notification-YYYY-MM-DD.md  # Generated report: issues grouped by notification
│   ├── structural_results.json                # Raw JSON output from structural validator
│   └── *.html                                 # Optional: PDF/HTML exports of reports
├── samples/
│   └── *.csv                           # Input files: user-dropped or CLI-provided CSVs to review
├── scripts/
│   ├── structural_validator.py         # Core Python validator: CSV parser, pattern checks, JSON output
│   └── generate_pdf.py                 # Utility: converts Markdown reports to PDF/HTML
├── CLAUDE.md                           # Project-level instructions (concepts, formality rules, errors to watch)
├── README.md                           # User-facing quick start guide
└── .gitignore                          # Ignores: .DS_Store, samples/, reports/
```

## Directory Purposes

**`.claude/`:**
- Purpose: Claude IDE integration and local configuration
- Contains: Skill definitions (`.md` files), local settings
- Key files: `commands/review-translations.md` (the skill), `settings.local.json` (pre-approvals)

**`config/`:**
- Purpose: Domain knowledge and validation rules
- Contains: Variable syntax patterns, language metadata, formality/tone rules, linguistic criteria
- Key files: 
  - `label_patterns.json` — Syntax rules for `@TPL_*@`, `<TPL_IF_*>`, custom markup; subject variable usage rules per language
  - `tone_guidelines.json` — Formality levels (formal vs. informal), language-specific voice rules
  - `review_rules_compact.md` — 7-point review criteria and language-specific linguistic rules
  - `languages.json` — Language codes, names, native speaker context

**`corrections/`:**
- Purpose: Learning system output
- Contains: Accumulated corrections from user feedback, extracted rules, rule summaries
- Key files: `corrections_log.json` — structured data: corrections (with before/after), rules by category, languages affected

**`reports/`:**
- Purpose: Generated output from reviews
- Contains: Markdown reports (by country, by notification), raw JSON structural findings, optional PDF/HTML exports
- Key files: Timestamped `review-by-country-YYYY-MM-DD.md`, `structural_results.json`

**`samples/`:**
- Purpose: Input staging area
- Contains: CSV files to review (user-dropped or copied from attachments)
- Key files: User-provided `.csv` files only

**`scripts/`:**
- Purpose: Programmatic validators and utilities
- Contains: Python modules for structural validation and report export
- Key files: `structural_validator.py` (main validator), `generate_pdf.py` (export utility)

## Key File Locations

**Entry Points:**
- `/.claude/commands/review-translations.md`: Main skill orchestrating entire 9-step workflow
- `/scripts/structural_validator.py` → `main()`: CLI entry for structural validation
- `/scripts/structural_validator.py` → `run_validation()`: Programmatic entry for batch validation

**Configuration:**
- `/config/label_patterns.json`: All template syntax definitions and validation rules
- `/config/tone_guidelines.json`: All brand voice and formality rules by language
- `/config/review_rules_compact.md`: All linguistic review criteria
- `/config/languages.json`: Language metadata
- `/config/variables.csv`: Catalog of valid template variables

**Core Logic:**
- `/scripts/structural_validator.py`: 
  - CSV parsing: `parse_per_notification_csv()`, `parse_country_block()`
  - Pattern extraction: `extract_value_variables()`, `extract_conditional_names()`, `extract_emojis()`
  - Checks: `check_variables()`, `check_conditionals()`, `check_emojis()`, `check_custom_markup()`, `check_encoding()`, `check_empty_placeholder()`, `check_length_anomaly()`, `check_html_balance()`
  - Validation pipeline: `validate_entry()`, `run_validation()`

**Testing:**
- No dedicated test files — validation is tested via real CSV files in `samples/` and inspection of `reports/structural_results.json`

**Learning System:**
- `/corrections/corrections_log.json`: Structured record of corrections and rules
- Step 7 of skill workflow: Extracts new rules from user-accepted corrections and updates this file

## Naming Conventions

**Files:**
- Reports: `review-by-country-YYYY-MM-DD.md` or `review-by-notification-YYYY-MM-DD.md` (date format: YYYY-MM-DD)
- Structural output: `structural_results.json` (overwritten per run, timestamped report uses same date as report)
- Input CSVs: User-provided names (no strict convention), copied to `samples/` for consistency
- Config: Lowercase with underscores (`label_patterns.json`, `tone_guidelines.json`)
- Scripts: Lowercase with underscores (`structural_validator.py`, `generate_pdf.py`)

**Directories:**
- `.` prefix for meta (`.claude/`, `.planning/`, `.gitignore`)
- Plural for collections (`scripts/`, `reports/`, `samples/`, `corrections/`)
- Singular for config (`config/`)

**Variables in Code:**
- Regex patterns: `RE_*` prefix (e.g., `RE_VALUE_VAR`, `RE_IF_OPEN`, `RE_EMOJI`)
- Functions: snake_case (e.g., `parse_per_notification_csv()`, `check_variables()`)
- Classes: None used — functional style preferred
- Module-level constants: UPPER_SNAKE_CASE (following Python convention)

## Where to Add New Code

**New Structural Check:**
- Primary code: `scripts/structural_validator.py` → add new function `check_*()` following existing pattern
- Pattern: Function takes `ref_entry: dict, entry: dict` and returns `list[dict]` of issues
- Integration: Add to `validate_entry()` function's `all_issues.extend()` calls
- Config: If rule is configurable, add to `config/label_patterns.json` and load in validator

**New Language or Tone Rule:**
- Primary code: `config/tone_guidelines.json` → add language code and rules
- Pattern: Top-level key is language code (e.g., `"de"`), value is object with formality level and rules
- Reference: In `.claude/commands/review-translations.md` Step 4c, criteria 2 (Tone check) applies rules from this file

**New Subject Variable Rule:**
- Primary code: `config/label_patterns.json` → `subject_variable_usage_rules` object
- Pattern: Language code (e.g., `"es"`) maps to array of valid subject variables for that language
- Reference: In `.claude/commands/review-translations.md` Step 4c, criteria 4 (Label correctness) applies these rules

**New Linguistic Criterion:**
- Primary code: `config/review_rules_compact.md` → add section describing new criterion
- Integration: Update Step 4c of skill to check criterion (currently 7 criteria listed)
- Pattern: Describe check, provide language-specific exceptions, give examples

**New AI Review Step or Modification:**
- Primary code: `.claude/commands/review-translations.md` → modify or extend relevant step
- Pattern: Steps numbered 0–6 are fixed; Step 7+ is feedback loop (user-driven, not code-controlled)
- Key constraint: Do not add subagents or batching — all AI review is inline in main conversation

**New Report Format:**
- Primary code: `.claude/commands/review-translations.md` → Step 6 (Generate reports)
- Pattern: Current format is "by-country" Markdown. For alternative format, add parallel step or modify grouping logic
- Option: Use `generate_pdf.py` to convert Markdown to PDF/HTML

**New Learned Rule Extraction:**
- Primary code: `.claude/commands/review-translations.md` → Step 7 (feedback loop)
- Pattern: User provides corrected text and optional rule. Skill parses rule, adds to `corrections_log.json`
- Config: No new files needed — all rules stored in `corrections_log.json` structure defined in first review run

## Special Directories

**`.planning/codebase/`:**
- Purpose: Generated architectural analysis docs (ARCHITECTURE.md, STRUCTURE.md, etc.)
- Generated: Yes (by GSD mapping agent)
- Committed: Yes — part of project documentation

**`reports/`:**
- Purpose: Generated review outputs
- Generated: Yes (by skill workflow)
- Committed: No — git ignores `reports/` (user-specific and reproducible)

**`samples/`:**
- Purpose: Input staging for CSV files
- Generated: Partially (user provides original, skill copies attachments)
- Committed: No — git ignores `samples/` (user-specific input)

**`.claude/`:**
- Purpose: IDE integration
- Generated: No (committed with project)
- Committed: Yes — contains skill definitions and settings

---

*Structure analysis: 2026-04-08*
