# Testing Patterns

**Analysis Date:** 2026-04-08

## Test Framework

**Current Status:** No testing framework detected

- No pytest, unittest, or test runner configuration found
- No test files (no `test_*.py`, `*_test.py`, or `tests/` directory)
- No CI/CD test pipeline configured
- No `pytest.ini`, `setup.cfg`, or `tox.ini` present

**Code structure suggests manual testing approach:**
- CLI script (`structural_validator.py`) accepts file input and outputs JSON
- PDF generator (`generate_pdf.py`) has try/except with fallback strategies
- Skill definition (`.claude/commands/review-translations.md`) documents manual testing steps

## Manual Testing Approach

**For `structural_validator.py`:**
- Script accepts CSV input via `--input` argument
- Outputs JSON to stdout or file via `--output` argument
- Manual verification: Run against sample CSVs in `samples/` directory
- Validation logic is data-driven (uses config files) and testable

**Example manual test:**
```bash
python3 scripts/structural_validator.py \
    --input samples/test.csv \
    --output reports/test_results.json \
    --pretty
```

## Testing Opportunities

**Unit testable functions in `structural_validator.py`:**

1. **CSV Parsing**
   ```python
   def parse_per_notification_csv(filepath: str) -> list[dict]
   def parse_country_block(block: str) -> dict | None
   ```
   - Test: Empty blocks return None
   - Test: Valid blocks parse all three fields (country, titre, corps)
   - Test: Quoted/stripped text handled correctly

2. **Data extraction**
   ```python
   def extract_value_variables(text: str) -> list[str]
   def extract_conditional_names(text: str) -> dict
   def extract_emojis(text: str) -> list[str]
   def extract_custom_tags(text: str) -> dict
   ```
   - Test: Regex patterns match expected templates
   - Test: Empty text returns empty results
   - Test: Complex nested templates handled correctly

3. **Structural validation checks**
   ```python
   def check_variables(ref_entry: dict, entry: dict) -> list[dict]
   def check_conditionals(ref_entry: dict, entry: dict) -> list[dict]
   def check_emojis(ref_entry: dict, entry: dict) -> list[dict]
   def check_encoding(entry: dict) -> list[dict]
   def check_empty_placeholder(ref_entry: dict, entry: dict) -> list[dict]
   def check_length_anomaly(ref_entry: dict, entry: dict) -> list[dict]
   def check_html_balance(entry: dict) -> list[dict]
   ```
   - Each check function returns `list[dict]` with issue structure
   - Test fixture: Pairs of (French reference, translation with error)
   - Assertion: Specific issue type present with correct severity

4. **Configuration loading**
   ```python
   def load_valid_variables(config_dir: str) -> dict[str, str]
   ```
   - Test: Returns empty dict if Variables.csv missing
   - Test: Parses CSV correctly with multi-column format

## Test Structure Pattern

**Observed design pattern for validation functions:**

All check functions follow the same structure:
```python
def check_X(ref_entry: dict, entry: dict) -> list[dict]:
    """Check X aspect of translation."""
    issues = []
    
    # Extract data
    ref_text = ref_entry['titre'] + ' ' + ref_entry['corps']
    trans_text = entry['titre'] + ' ' + entry['corps']
    
    # Compare/validate
    ref_data = extract_something(ref_text)
    trans_data = extract_something(trans_text)
    
    # Build issues
    if ref_data != trans_data:
        issues.append({
            'check': 'check_name',
            'severity': 'error|warning|info',
            'category': 'category_name',
            'message': 'description',
            # optional fields
        })
    
    return issues
```

**This pattern is testable with:**
```python
# Test case
ref = {'titre': 'Title', 'corps': 'Body @TPL_VAR@'}
trans = {'titre': 'Title', 'corps': 'Body'}  # missing variable
issues = check_variables(ref, trans)

# Assertion
assert len(issues) == 1
assert issues[0]['check'] == 'variable_missing'
assert issues[0]['severity'] == 'error'
```

## Issue/Finding Format

**All functions return standardized issue dicts:**
```python
{
    'check': 'check_name',           # e.g., 'variable_missing', 'emoji_order'
    'severity': 'error|warning|info', # Error: breaks template, Warning: quality issue, Info: note
    'category': 'category',           # label, emoji, format, encoding, empty
    'message': 'human-readable text', # What's wrong
    'country': 'Country Name',        # Added by validate_entry()
    # Optional fields:
    'variable': '@TPL_NAME@',        # For variable-specific issues
    'detail': {...}                  # Extra data for complex issues
}
```

**Categories in use:**
- `label` — Template variables and conditionals
- `emoji` — Emoji consistency
- `format` — Whitespace, markup, HTML balance
- `encoding` — Mojibake, control characters
- `empty` — Empty translations, untranslated text

## Error Handling in Tests

**No explicit error handling patterns in tests (no tests exist).**

**Error handling observed in code:**
- File not found: Exits with non-zero status
- Invalid CSV: Returns empty results with error message
- Missing config: Returns empty dict and continues validation
- Malformed markup: Reported as warning/info, validation continues

## Integration Testing via CSV Samples

**Sample CSVs in `samples/` directory:**
- Intended for manual end-to-end testing
- Each CSV represents a real notification review scenario
- Can be used to build integration test suite

**Pattern for integration test:**
1. Load sample CSV
2. Run `run_validation(csv_path)`
3. Verify expected issues are found
4. Verify summary counts match

## Configuration-Driven Testing

**Configs that drive validation:**

1. `config/label_patterns.json` — Regex patterns and variable syntax
   - Can be extended without touching code
   - New variable patterns added by updating JSON

2. `config/tone_guidelines.json` — Formality rules per language
   - Not used by structural validator (AI review only)
   - Available for future tone-checking unit tests

3. `corrections/corrections_log.json` — Learned rules from feedback
   - Available for regression tests
   - Could be used to verify past corrections are caught

## Coverage Assessment

**Current coverage estimate:** 0% (no test suite exists)

**High-value test areas:**
1. **CSV parsing edge cases** — 5 test cases
   - Empty cells
   - Mixed quoted/unquoted text
   - Multiline body text
   - Missing country name
   - Malformed structure

2. **Variable extraction** — 8 test cases
   - Single variable
   - Multiple same variable
   - Nested conditionals
   - Extra variables
   - Malformed variable names
   - Unicode in variable names
   - Empty text

3. **Emoji handling** — 6 test cases
   - Missing emoji
   - Extra emoji
   - Emoji order swap
   - Zero-width joiner sequences
   - Emoji with skin tone modifiers
   - Empty text

4. **Conditional blocks** — 8 test cases
   - Matched pairs
   - Missing close tag
   - Extra close tag
   - Nested conditionals
   - Mixed IF/ELSE
   - Empty blocks
   - Unicode in condition names

5. **HTML balance** — 4 test cases
   - All tags balanced
   - Missing closing tag
   - Extra closing tag
   - Mixed tag nesting

6. **Encoding** — 3 test cases
   - Valid UTF-8
   - Mojibake sequences
   - Control characters

7. **Empty/placeholder detection** — 5 test cases
   - Completely empty
   - Untranslated copy-paste
   - Placeholder keywords
   - Legitimately identical (brand names)

8. **Length anomalies** — 4 test cases
   - Normal ratio
   - Too short (< 40%)
   - Too long (> 250%)
   - With markup stripped

**Recommended testing approach:**
- Use `pytest` with `pytest-mark` for categorization
- Use fixtures for CSV and entry data
- Use parametrize for multiple test cases per function
- Aim for 80%+ coverage of check functions
- No need to test CLI argparse extensively (standard library)

## Manual Testing Evidence

**Test files observed in reports:**
- `.reports/structural_results.json` — Output of validator run on real data
- `.reports/review-by-country-2026-04-*.md` — Multi-stage test results
- `corrections/corrections_log.json` — Records of corrections accepted

**These represent real-world validation runs:**
- Full pipeline tested end-to-end
- Edge cases discovered and documented in corrections log
- Formality rules validated against actual translations

## Debugging Patterns

**Print-based debugging (observed in code):**
- Status messages to stderr for progress
- JSON output to stdout for result inspection
- Optional `--pretty` flag for readable JSON output

**Example debug run:**
```bash
python3 scripts/structural_validator.py \
    --input samples/test.csv \
    --pretty \
    --output /tmp/debug.json
cat /tmp/debug.json | jq '.issues[0]'  # Inspect first issue
```

---

*Testing analysis: 2026-04-08*
