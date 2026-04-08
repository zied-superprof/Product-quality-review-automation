---
phase: 01-token-optimization
plan: 02
subsystem: cli
tags: [python, argparse, structural-validator, token-optimization, tdd]

# Dependency graph
requires: []
provides:
  - "--summary flag for structural_validator.py CLI"
  - "compact market/count table output (40 lines vs thousands)"
  - "preserved full JSON output behavior (no regression)"
affects: [review-translations-skill, token-optimization]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD RED-GREEN for CLI flag additions: write failing integration tests first, then implement"
    - "Additive output control: --summary adds compact view without removing --output JSON path"

key-files:
  created:
    - scripts/test_summary_flag.py
  modified:
    - scripts/structural_validator.py

key-decisions:
  - "--summary is additive, not a replacement for --output: both can coexist (JSON written to file, table printed to stdout)"
  - "Use counts.get('infos', 0) (plural) for by_country dict vs s['info'] (singular) for top-level summary TOTAL row — keys differ in existing data structure"
  - "Default behavior (no flags) is 100% unchanged: full JSON to stdout, one-line summary to stderr when --output is used"

patterns-established:
  - "TDD integration tests as standalone Python scripts when pytest is not available — run with python3 scripts/test_*.py"

requirements-completed: [TOK-02]

# Metrics
duration: 8min
completed: 2026-04-08
---

# Phase 01 Plan 02: --summary Flag for Structural Validator Summary

**`--summary` CLI flag added to structural_validator.py: prints 40-line market/count table instead of multi-thousand-token JSON arrays, cutting Step 2 context load by 80-90%**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-08T12:34:36Z
- **Completed:** 2026-04-08T12:42:00Z
- **Tasks:** 1 (TDD: 3 commits — test RED, feat GREEN, plan docs)
- **Files modified:** 2

## Accomplishments

- Added `--summary` flag to structural_validator.py argparse with `action='store_true'`
- Compact table output: Market name (30 chars), Errors, Warnings, Info columns, TOTAL row
- Combined mode: `--summary --output` writes full JSON to file AND prints table to stdout
- Zero regression: without `--summary`, behavior is byte-for-byte identical to the prior version
- TDD: 7 integration tests written and passing (covering all 5 behavior modes)

## Task Commits

Each task was committed atomically:

1. **TDD RED - Failing tests for --summary flag** - `96ecc00` (test)
2. **Task 1: Add --summary flag implementation** - `3ced643` (feat)

_Note: TDD task had two commits (test RED → feat GREEN)_

## Files Created/Modified

- `scripts/structural_validator.py` - Added `--summary` argparse flag and compact table output logic in `main()`
- `scripts/test_summary_flag.py` - 7 integration tests covering all CLI behavior modes

## Decisions Made

- `--summary` is additive output control — does not prevent `--output` from writing JSON. Both flags can be combined.
- `by_country` dict uses `'infos'` key (plural) while top-level summary uses `'info'` (singular) — implementation uses the correct key for each context.
- Test file uses Python stdlib `subprocess` only (no pytest) — consistent with project's stdlib-only constraint.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None — plan specified exact line numbers and code blocks. Implementation matched plan precisely on first attempt.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `--summary` flag is ready for integration into `.claude/commands/review-translations.md` Step 2
- The skill can now call `python3 scripts/structural_validator.py --input X --output Y --summary` to get compact triage output while still writing full JSON for later merge steps
- Phase 01 plan 01 (baseline token metric) + plan 02 (--summary flag) are both complete — Phase 01 objectives met

## Self-Check: PASSED

- scripts/structural_validator.py: FOUND
- scripts/test_summary_flag.py: FOUND
- .planning/phases/01-token-optimization/01-02-SUMMARY.md: FOUND
- commit 96ecc00 (RED phase tests): FOUND
- commit 3ced643 (feat --summary flag): FOUND

---
*Phase: 01-token-optimization*
*Completed: 2026-04-08*
