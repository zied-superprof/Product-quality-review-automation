# Codebase Concerns

**Analysis Date:** 2026-04-08

## Tech Debt

**Missing error handling in PDF generation:**
- Issue: `scripts/generate_pdf.py` has broad `except Exception as e` blocks that catch all errors without proper logging or retry logic. If weasyprint fails, the system silently falls back to cupsfilter without distinguishing between different failure modes.
- Files: `scripts/generate_pdf.py` (lines 142, 157)
- Impact: Failures are hard to diagnose; users get incomplete error messages to stderr without structured logging. If both PDF backends fail, the HTML exists but users are left with a "Could not generate PDF automatically" message.
- Fix approach: Replace broad exception handlers with specific error types; use logging module instead of stderr prints; add detailed error messages that distinguish between missing dependencies, permissions issues, and conversion failures.

**Hardcoded file paths in PDF generation:**
- Issue: `scripts/generate_pdf.py` hardcodes paths and report dates (`review-by-country-2026-04-03.md`, `.html`, `.pdf`). The script must be manually edited for each new report.
- Files: `scripts/generate_pdf.py` (lines 8-10)
- Impact: Script is not reusable. Users cannot automate PDF generation for new reports without editing source code.
- Fix approach: Convert paths to command-line arguments or accept `--input` and `--output` flags. Use `argparse` to match the validator's interface.

**PDF generation dependency not declared:**
- Issue: `scripts/generate_pdf.py` imports `markdown` and `weasyprint` without any `requirements.txt` or setup.py. The CLAUDE.md states "stdlib only" for the validator, but the PDF generator has undeclared external dependencies.
- Files: `scripts/generate_pdf.py` (lines 2-3), missing: `requirements.txt`
- Impact: Users cannot easily install dependencies; script fails silently with ImportError if packages are missing.
- Fix approach: Create `requirements.txt` with `markdown` and `weasyprint` (or `pdfkit` as fallback). Document installation in README.md.

## Known Bugs

**CSV parser assumes France is always first entry:**
- Symptom: If the CSV does not have France as the first row/cell, validation will fail or compare against the wrong reference market.
- Files: `scripts/structural_validator.py` (lines 594-596)
- Trigger: Upload a per-notification CSV where France is not the first cell, or a full-database CSV without France at all.
- Workaround: Always ensure France is first in the CSV before validation.
- Root cause: The parser extracts entries in CSV order (row-by-row, left-to-right) without searching for France; it assumes it's always entry[0].

**Emoji detection regex may fail on newer Unicode standards:**
- Symptom: Some modern emoji sequences (Zero Width Joiner combinations, emoji with variation selectors) may not match the hardcoded Unicode ranges.
- Files: `scripts/structural_validator.py` (lines 55-70)
- Trigger: Use emoji like family emoji (👨‍👩‍👧) that combine base emoji + ZWJ + combining emoji, or Apple color variants.
- Impact: Emoji consistency checks will under-report missing emoji; warnings may be false negatives.
- Fix approach: Use a maintained emoji library (e.g., `regex` crate or `emoji` package) instead of hardcoded ranges. Document the limitation in README.md.

**Variable catalog check ignores user-defined variables:**
- Symptom: `scripts/structural_validator.py` loads `config/Variables.csv` to validate variable names, but the CSV file is optional and not included in the repo. If missing, all variables pass as "undefined" with only a warning, not an error.
- Files: `scripts/structural_validator.py` (lines 174-186, 223-239)
- Trigger: Run validator without `config/Variables.csv` (optional per lines 177).
- Impact: Typos in variable names are not caught; review quality depends on a file that may not exist.
- Fix approach: Make `Variables.csv` required or embed a canonical list of valid variables in code. Document the schema.

## Security Considerations

**No input validation on CSV parsing:**
- Risk: Malicious CSV files with extremely long cells or deeply nested conditionals could cause memory exhaustion or regex DoS.
- Files: `scripts/structural_validator.py` (lines 83-103, regex patterns lines 30-76)
- Current mitigation: None. The regex patterns are broad and not anchored; deeply nested `<TPL_IF_...>` blocks will be processed naively.
- Recommendations: 
  1. Add cell size limits (e.g., reject cells > 1MB).
  2. Add nesting depth checks for conditionals (e.g., fail if more than 5 levels of `<TPL_IF_...>` nesting).
  3. Use timeout on regex matching to prevent ReDoS.

**Skill writes to `corrections/corrections_log.json` without validation:**
- Risk: The `/review-translations` skill writes user feedback directly to the corrections log without schema validation. Malformed feedback could corrupt the learning system.
- Files: `.claude/commands/review-translations.md` (Step 7, lines 245-247)
- Current mitigation: None documented.
- Recommendations:
  1. Validate all user feedback against the schema before writing to `corrections_log.json`.
  2. Back up the corrections log before writes.
  3. Log all updates with timestamp and source.

**Config files contain no integrity checks:**
- Risk: If `config/tone_guidelines.json` or `config/label_patterns.json` are manually edited and corrupted, the skill will fail silently or use wrong rules.
- Files: `config/tone_guidelines.json`, `config/label_patterns.json`
- Current mitigation: None.
- Recommendations:
  1. Add JSON schema validation at skill start.
  2. Version config files and warn if versions are incompatible.

## Performance Bottlenecks

**Structural validator processes all issues linearly without optimization:**
- Problem: Each check function (lines 189-572) iterates the entire text independently. For a 100KB email body with 30 checks, this is slow.
- Files: `scripts/structural_validator.py` (lines 560-578)
- Cause: Regexes are compiled at function scope; no caching or early exit. Variables, conditionals, emojis are all extracted separately.
- Improvement path:
  1. Compile all regexes once at module load (move to top level).
  2. Cache extraction results (e.g., store `extract_value_variables()` output in a dict).
  3. Exit early if severity='error' found (for one-pass mode).
  4. Process countries in batches (already done in skill, but single validator call is sequential).

**AI review in skill uses inline sequential processing:**
- Problem: `.claude/commands/review-translations.md` (Step 4c, lines 75-95) processes flagged markets one by one in the conversation, no parallelization.
- Files: `.claude/commands/review-translations.md`
- Cause: Design requires "inline in this conversation" for transparency, but limits throughput.
- Improvement path:
  1. For >25 flagged markets, batch into sub-agents (already mentioned in skill, but not implemented).
  2. Consider creating a parallel multi-agent approach for large reviews.

**Markdown report generation does not deduplicate similar issues:**
- Problem: If 50 markets have the same correction (e.g., missing emoji), the report shows 50 separate entries instead of grouping.
- Files: `.claude/commands/review-translations.md` (Step 6, lines 110-111 mentions grouping but Step 5 doesn't enforce it)
- Cause: Step 5 mentions grouping "exactly identical" items, but implementation is manual and error-prone.
- Improvement path:
  1. Add a deduplication step after merging results (Step 5) that groups by (category, issue, fix).
  2. Auto-group in report generation.

## Fragile Areas

**Emoji variable order assumption:**
- Files: `scripts/structural_validator.py` (lines 340-347)
- Why fragile: The check assumes emoji should appear in the same order as the French source. But different markets might display emoji in different positions for cultural reasons, or emoji rendering may be browser-specific.
- Safe modification: Document that emoji order checks are soft warnings, not errors. Add a configuration option `emoji_order_strict: true/false`.
- Test coverage: Missing tests for emoji sequences; no test for reordered emoji.

**Hardcoded language lists for formality rules:**
- Files: `config/tone_guidelines.json` (lines 13-34), `config/review_rules_compact.md` (lines 25-29)
- Why fragile: If a new market is added (e.g., `en_IN` for India), it may not appear in either `formal_vous_languages` or `informal_standard_languages`. The skill will silently treat it as neutral.
- Safe modification: Add a "catch-all" rule that defaults to the parent language code (e.g., `en_*` defaults to English rules). Document this clearly.
- Test coverage: No tests for new market codes; no validation that all markets have a formality rule.

**CSV parser assumes UTF-8 without fallback:**
- Files: `scripts/structural_validator.py` (line 93: `encoding='utf-8'`)
- Why fragile: If a CSV is uploaded in Latin-1 or Windows-1252, the parser will fail with `UnicodeDecodeError` instead of attempting recovery.
- Safe modification: Add `encoding='utf-8-sig'` to strip BOM; add a try/except to attempt Latin-1 as fallback with a warning.
- Test coverage: No tests for non-UTF-8 files.

**Variable validation depends on optional Variables.csv:**
- Files: `scripts/structural_validator.py` (lines 174-186)
- Why fragile: If `config/Variables.csv` is missing, the check silently passes all variables. Users will not know if they're using undefined variables.
- Safe modification: Make Variables.csv required and auto-generate it from the configs on first run if missing.
- Test coverage: No tests verify behavior when Variables.csv is absent.

## Scaling Limits

**Current capacity:**
- Validator: Tested on notifications with 39 languages; scales linearly with language count and text size.
- Skill: Processes 25 markets per batch in Tier 2 (Haiku), 25 in Tier 1 (Sonnet); no documented limits for >500 markets.

**Limit:**
- For a full-database CSV (all notifications × all languages), if there are >500 unique notifications × 39 languages, the skill will need to make hundreds of API calls. No current caching or session management.
- Memory: Structural results JSON is stored in memory; a report with 10,000 issues will be ~2-5MB, acceptable but not optimized.

**Scaling path:**
1. Implement result streaming instead of storing entire JSON in memory.
2. Add batching logic for >100 markets (auto-split into multiple skill invocations).
3. Persist intermediate results to avoid re-running validator if review is interrupted.
4. Consider a database backend for large-scale reviews (SQLite for simplicity).

## Dependencies at Risk

**markdown and weasyprint are undeclared:**
- Risk: Users attempting to generate PDFs will fail silently if these packages are not installed.
- Impact: PDF feature is entirely broken if dependencies are missing.
- Migration plan: Create `requirements.txt`; use `try/except ImportError` with a helpful message; consider switching to a lighter PDF backend (e.g., `reportlab` or `pdfkit` with wkhtmltopdf).

**No version pins in config:**
- Risk: Behavior may change if `config/label_patterns.json` or `config/tone_guidelines.json` are updated without version control.
- Impact: Corrections from previous reviews may stop applying if rules are silently changed.
- Migration plan: Add a `_version` field to each config file (e.g., `label_patterns: v1.2`); log version on each run; warn if versions don't match expected.

## Missing Critical Features

**No ability to re-run reviews on updated translations:**
- Problem: After user corrections are applied, there's no workflow to re-validate the same CSV to confirm fixes.
- Blocks: Users cannot close the feedback loop; corrections are logged but not verified.
- Fix approach: Add a `--compare-to` flag to validator to compare old vs. new CSV. Add a `/verify-corrections` skill.

**No support for bulk feedback updates:**
- Problem: Step 7 feedback loop in the skill requires users to manually number each correction and type feedback. For 100 corrections, this is tedious.
- Blocks: Learning system is slow to improve; users are unlikely to provide detailed feedback.
- Fix approach: Create a structured feedback format (JSON or YAML) that users can prepare offline and upload; use a separate `/update-rules` skill.

**No rollback for bad rule updates:**
- Problem: If a user provides feedback that corrupts rules (e.g., marking a valid variable as invalid), there's no undo.
- Blocks: Mistakes in the corrections log compound over time.
- Fix approach: Version the corrections log (e.g., `corrections_log.v1.json`, `corrections_log.v2.json`); add a `--rollback` flag to revert to a previous version.

## Test Coverage Gaps

**No unit tests for structural validator:**
- What's not tested: Individual check functions (check_variables, check_emojis, check_html_balance, etc.) have no test coverage.
- Files: `scripts/structural_validator.py`
- Risk: Changes to regex patterns or logic could break validation silently.
- Priority: High — this is the core logic.

**No tests for CSV parsing edge cases:**
- What's not tested: Multi-line cells, cells with quotes or commas, France-not-first, missing countries.
- Files: `scripts/structural_validator.py` (lines 83-136)
- Risk: Parser may fail unexpectedly on real CSVs from the BO.
- Priority: High — data is user-provided and variable.

**No tests for skill workflow:**
- What's not tested: The `/review-translations` skill's argument parsing, file resolution, structural validation invocation, report generation, and feedback loop.
- Files: `.claude/commands/review-translations.md`
- Risk: Regressions in skill logic are only caught by manual testing.
- Priority: Medium — the skill is the entry point.

**No tests for config file formats:**
- What's not tested: JSON schema validation, missing fields, invalid language codes in tone_guidelines.json.
- Files: `config/tone_guidelines.json`, `config/label_patterns.json`
- Risk: Corrupted config files will silently break reviews.
- Priority: Medium — config is less volatile than code.

**No tests for emoji and Unicode handling:**
- What's not tested: Different emoji formats (base + ZWJ, with variation selectors), non-UTF-8 input, mojibake detection.
- Files: `scripts/structural_validator.py` (emoji detection, encoding checks)
- Risk: Emoji checks under-report issues; encoding detection may fail on edge cases.
- Priority: Low-Medium — less critical but impacts quality.

---

*Concerns audit: 2026-04-08*
