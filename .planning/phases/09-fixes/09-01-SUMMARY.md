---
phase: 09-fixes
plan: "01"
subsystem: validation
tags: [python, unicodedata, csv-parsing, emoji-detection, structural-validator]

# Dependency graph
requires:
  - phase: 08-project-audit
    provides: Critical findings list — France row assumption (finding #19) and hardcoded emoji ranges
provides:
  - France reference row detection by content search (not position)
  - Unicode-category-based emoji detection via unicodedata stdlib
affects: [review-translations, structural_validator, emoji-checks]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Find France row by iterating entries and matching country name/code, not by index"
    - "Use unicodedata.category() for emoji detection instead of hardcoded Unicode ranges"

key-files:
  created: []
  modified:
    - scripts/structural_validator.py

key-decisions:
  - "Match France by country == 'france' (case-insensitive) OR country == 'fr' — covers both country-name and language-code CSV formats"
  - "Keep extract_emojis() as public API for backward compatibility, delegate to new extract_emoji()"
  - "is_emoji_char() handles ZWJ (0x200D) and variation selector (0xFE0F) explicitly since they appear in compound emoji sequences"

patterns-established:
  - "Content-based row lookup: always search by value, never assume position in list"
  - "unicodedata.category() pattern: use 'So' (Symbol, Other) as primary emoji test with supplemental codepoint checks"

requirements-completed: [FIX-03, FIX-04]

# Metrics
duration: 2min
completed: 2026-04-16
---

# Phase 09 Plan 01: Structural Validator Brittleness Fixes Summary

**France row located by country-name/code search and emoji detected via unicodedata.category(), eliminating position-0 assumption and hardcoded Unicode ranges**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-04-16T12:23:22Z
- **Completed:** 2026-04-16T12:24:29Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Replaced `ref_entry = entries[0]` with a loop searching for `country == 'france'` or `country == 'fr'`, so the France row can appear at any position in the CSV
- Added `sys.exit(1)` with a clear error message when no France row is found, preventing silent wrong-reference comparisons
- Removed `RE_EMOJI` compiled regex with 11 hardcoded Unicode ranges
- Added `is_emoji_char()` using `unicodedata.category()` — auto-updates with each Python release; no code changes needed for new Unicode versions
- Added `extract_emoji()` helper; kept `extract_emojis()` as backward-compatible delegator

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix France reference row detection in run_validation()** - `b19ba9c` (fix)
2. **Task 2: Replace hardcoded emoji ranges with unicodedata-based detection** - `90aec73` (feat)

## Files Created/Modified

- `scripts/structural_validator.py` — run_validation() France row search + unicodedata emoji detection

## Decisions Made

- Match France by `country.strip().lower() == 'france'` OR `== 'fr'` — covers country-name CSVs and language-code CSVs
- Keep public `extract_emojis()` function signature unchanged for backward compatibility; delegate to `extract_emoji()`
- ZWJ (U+200D) and variation selector (U+FE0F) handled explicitly since `unicodedata.category()` classifies them as non-emoji but they appear in compound emoji sequences

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

The plan's inline verification script (for Task 1) searched for the first `sys.exit(1)` in the file, which matched the pre-existing Variables.csv error exit rather than the new France row exit. This was a false-alarm in the verification script logic, not in the implementation. Ran a corrected check using `re.search` with a look-forward pattern and confirmed acceptance criteria were fully met.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- FIX-03 and FIX-04 requirements are satisfied
- scripts/structural_validator.py is backward-compatible — existing CSV workflows unaffected
- Ready for 09-02 (zh_TW/zh_HK underscore key normalization in corrections_log.json)

---
*Phase: 09-fixes*
*Completed: 2026-04-16*
