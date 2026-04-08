# Coding Conventions

**Analysis Date:** 2026-04-08

## Naming Patterns

**Files:**
- PascalCase + underscore prefix for test files: Not used (no test files in repo)
- snake_case for Python scripts: `structural_validator.py`, `generate_pdf.py`
- kebab-case for skill/command files: `.claude/commands/review-translations.md`

**Functions:**
- snake_case for all functions: `parse_per_notification_csv()`, `extract_value_variables()`, `check_variables()`, `load_valid_variables()`
- Descriptive verb-based names: `parse_*`, `extract_*`, `check_*`, `load_*`, `validate_*`, `run_*`
- Full words, no abbreviations: `parse_country_block()` not `parse_ctry_blk()`

**Variables:**
- snake_case throughout: `ref_entry`, `trans_text`, `all_issues`, `error_count`, `by_country`
- Dictionary keys use snake_case: `'country'`, `'titre'`, `'corps'`, `'severity'`, `'check'`
- Constants in UPPER_SNAKE_CASE: Regex patterns like `RE_VALUE_VAR`, `RE_IF_OPEN`, `RE_CUSTOM_TAGS`
- Type hints follow Python standards: `dict`, `list`, `str | None`, `tuple`

**Types/Classes:**
- Not commonly used (minimal OOP in this codebase)
- Dataclasses not adopted (uses plain dicts for data structures)
- Protocol typing not applied (duck typing patterns observed)

## Code Style

**Formatting:**
- No `.black` or `.prettierrc` config present — freestyle Python formatting
- 4-space indentation (PEP 8 standard observed in `structural_validator.py`)
- Line length: Mixed — some lines exceed 100 chars, no strict limit enforced
  - Example: Line 73 in `structural_validator.py` is ~118 chars (regex pattern)
  - Example: Line 659 in `structural_validator.py` is ~91 chars
- Single-line strings use single quotes `'...'`
- Multi-line strings use triple quotes `"""..."""` for docstrings

**Docstrings:**
- Module-level docstring at top of file: `"""Structural Validator for Superprof Translation Quality Review..."""`
- Function-level docstrings: Simple one-liner format, no multi-line descriptions
  - Example: `def parse_per_notification_csv(filepath: str) -> list[dict]:`
    ```
    """
    Parse a per-notification CSV where each cell is a country block:
      - First line of cell: country name
      - Line with "Titre: ..."
      - Line(s) with "corps..." (the email body, can be multiline)
    ...
    """
    ```
- Docstrings document input format, output structure, and usage notes

**Linting:**
- No linting configuration found (`.flake8`, `.pylintrc`, `pyproject.toml` absent)
- No `ruff`, `black`, or `flake8` config files present
- Code style appears to follow PEP 8 loosely but not strictly enforced

**Comments:**
- Section headers with hyphens: `# ---------------------------------------------------------------------------`
- Inline comments explaining complex logic: `# Extract the variable name from a conditional tag`
- Comments describe the "why", not the "what": Code is self-documenting

## Import Organization

**Order observed in `structural_validator.py`:**
1. Stdlib modules (standard library imports)
   ```python
   import argparse
   import csv
   import json
   import re
   import sys
   import unicodedata
   from collections import defaultdict
   from pathlib import Path
   ```

2. No third-party imports (stdlib only — as documented in comments)

3. No relative imports used

**Style:**
- One import per line (not bundled like `from pathlib import Path`)
- Standard imports before specialized ones (`re` before `RE_VALUE_VAR` usage)
- Unused imports removed: Code is clean, no dead imports

## Error Handling

**Patterns observed:**

**File I/O:**
- Explicit error handling: `Path.exists()` check before reading
  ```python
  path = Path(config_dir) / 'Variables.csv'
  if not path.exists():
      return {}
  ```

- Context managers for file operations:
  ```python
  with open(filepath, newline='', encoding='utf-8') as f:
      reader = csv.reader(f)
  ```

**Validation:**
- Early returns for invalid data:
  ```python
  if not lines:
      return None
  if not country:
      return None
  ```

- Graceful degradation: If Variables.csv missing, returns empty dict instead of crashing
  ```python
  if not valid_variables:
      return []
  ```

**Argument validation:**
- `argparse` for CLI validation with `required=True` flags
- File existence check with clear error message:
  ```python
  if not filepath.exists():
      print(f'Error: File not found: {filepath}', file=sys.stderr)
      sys.exit(1)
  ```

**Return values:**
- Empty collections on no errors: `[]`, `{}`
- Summary dicts always returned (never None):
  ```python
  return {
      'summary': {...},
      'issues': all_issues,
      'metadata': {...},
  }
  ```

## Logging

**Framework:** No logging module used — direct print to stderr

**Patterns:**
- Status messages to stderr for progress tracking:
  ```python
  print(
      f"Structural validation complete: {s['errors']} errors, ...",
      file=sys.stderr
  )
  ```
- Error messages explicitly to stderr: `print(..., file=sys.stderr)`
- JSON output to stdout or file: `print(json_output)`
- Status messages during validation: `print(f"HTML written: {html_path}")`

**When to log:**
- Script entry/exit events
- Error conditions (file not found, validation failure)
- Generation milestones (HTML written, PDF created)
- Summaries at end of validation run

## Function Design

**Size:**
- Average function 10–30 lines
- Longer functions (40–60 lines) are complex validators: `check_variables()`, `run_validation()`
- Most validation functions follow same 3-step pattern:
  1. Extract data from input
  2. Compare to reference
  3. Build issues list

**Parameters:**
- Explicit, strongly typed:
  ```python
  def validate_entry(ref_entry: dict, entry: dict, valid_variables: dict[str, str] | None = None) -> list[dict]:
  ```
- Optional params with defaults: `config_dir: str = 'config'`, `lang_ratios: dict = None`
- No variadic args (`*args`, `**kwargs`) used

**Return values:**
- Always return structure, not None:
  - Validation functions return `list[dict]` (may be empty)
  - Main functions return `dict` with `summary`, `issues`, `metadata` keys
  - Early returns return same type: `return {}` or `return []`

**Regex usage:**
- Patterns compiled at module level as constants (pre-compiled for performance):
  ```python
  RE_VALUE_VAR = re.compile(r'@TPL_[A-Z0-9_]+@')
  ```
- Regex flags specified when needed:
  ```python
  RE_HTML_TAGS = re.compile(r'</?(?:b|i|u|mark|li|sup|a|A)\b[^>]*>', re.IGNORECASE)
  ```

## Module Design

**Exports:**
- No `__all__` defined
- Single entry point via `if __name__ == '__main__': main()`
- All functions are public (no underscore prefix for "private")

**Organization in `structural_validator.py`:**
1. Docstring + imports (lines 1–23)
2. Regex patterns (lines 26–76)
3. CSV parser functions (lines 83–137)
4. Structural check functions (lines 143–553)
5. Main validation pipeline (lines 560–635)
6. CLI & entry point (lines 641–678)

**Barrel files:**
- Not used (no `__init__.py` files)

**Configuration loading:**
- JSON configs read at runtime:
  ```python
  valid_variables = load_valid_variables(config_dir)
  ```
- Optional: If config missing, returns empty dict and validation continues
- No hardcoded values; all patterns in config files

## Data Structure Patterns

**Collections used:**
- `list[dict]` for validation results
  ```python
  entries = parse_per_notification_csv(filepath)  # list of {country, titre, corps}
  ```

- `dict` for summary data:
  ```python
  {
      'summary': {'total': 0, 'errors': 0, ...},
      'issues': all_issues,
      'metadata': {...}
  }
  ```

- `defaultdict(lambda: {...})` for grouping:
  ```python
  by_country = defaultdict(lambda: {'errors': 0, 'warnings': 0, 'infos': 0})
  ```

- `Counter` from collections for frequency:
  ```python
  from collections import Counter
  ref_open_counts = Counter(ref_tags['opens'])
  ```

**Type hints:**
- Function parameters and return types always annotated:
  ```python
  def extract_value_variables(text: str) -> list[str]:
  def check_variables(ref_entry: dict, entry: dict) -> list[dict]:
  ```
- Union types using `|` syntax (Python 3.10+):
  ```python
  dict | None
  str | None
  ```

## String Handling

**Encoding:**
- All file operations specify `encoding='utf-8'`
  ```python
  with open(filepath, newline='', encoding='utf-8') as f:
  ```

- Ensure ASCII disabled for JSON output:
  ```python
  json.dumps(results, ensure_ascii=False, indent=2)
  ```

**F-strings:**
- Used consistently for error messages and status output
  ```python
  print(f'Error: File not found: {filepath}', file=sys.stderr)
  print(f"HTML written: {html_path}")
  ```

**Multiline strings:**
- Template HTML in `generate_pdf.py` uses triple quotes with `.format()` placeholders:
  ```python
  html = f"""<!DOCTYPE html>
  ...
  {body}
  ...
  """
  ```

---

*Convention analysis: 2026-04-08*
