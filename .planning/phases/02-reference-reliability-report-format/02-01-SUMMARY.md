---
phase: 02-reference-reliability-report-format
plan: 01
subsystem: validation-pipeline
tags: [reference-reliability, structural-validator, review-skill, formality, config-loading]
dependency_graph:
  requires: []
  provides: [hard-fail-on-missing-variables-csv, load-logging, step1-health-check, step4c-formality-criteria]
  affects: [scripts/structural_validator.py, .claude/commands/review-translations.md]
tech_stack:
  added: []
  patterns: [hard-fail-on-missing-config, stderr-load-logging, config-driven-formality-check]
key_files:
  modified:
    - scripts/structural_validator.py
    - .claude/commands/review-translations.md
decisions:
  - "load_valid_variables returns None (not empty dict) to force explicit abort in caller — prevents silent bypass surviving future refactors"
  - "Load logging goes to stderr to avoid polluting JSON stdout output"
  - "Step 4c criterion 2 references tone_guidelines.json directly so formality rules are config-driven, not hardcoded in the prompt"
  - "Informal-standard languages are explicitly guarded against false-positive formality warnings"
metrics:
  duration: ~8 minutes
  completed: 2026-04-08T19:01:26Z
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 02 Plan 01: Reference Reliability — Structural Validator Hardening and Review Skill Update Summary

**One-liner:** Hard-fail + stderr logging on Variables.csv load in structural_validator.py; config-driven formality enforcement and Step 1 health check in review-translations.md.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Harden structural_validator.py — hard-fail on missing Variables.csv, remove silent bypass, add load logging | a602037 | scripts/structural_validator.py |
| 2 | Update review skill — Step 1 reference file log and Step 4c formality criteria | 120bab0 | .claude/commands/review-translations.md |

## What Was Built

### Task 1 — structural_validator.py hardening

Three changes to `scripts/structural_validator.py`:

1. **`load_valid_variables()` return type changed** from `dict[str, str]` to `dict[str, str] | None`. Missing Variables.csv now returns `None` instead of silent empty dict.

2. **Load logging added** — after successful load, prints to stderr: `Variables.csv: {N} variables loaded`. Does not pollute JSON stdout.

3. **`run_validation()` abort gate added** — immediately after calling `load_valid_variables()`, checks `if valid_variables is None:` and calls `sys.exit(1)` with a clear message to stderr.

4. **`check_variables_catalogue()` silent bypass removed** — the `if not valid_variables: return []` guard is gone. With the abort gate in `run_validation()`, this code path is now unreachable, but removing the guard prevents future regressions.

### Task 2 — review-translations.md updates

**Step 1 reference file health check** added after the existing "Found [X] notifications..." summary line. The skill now:
- Reads all three config files (Variables.csv, tone_guidelines.json, label_patterns.json) before proceeding
- Prints a single status line: `Reference files: Variables.csv ([N] vars) ✓ | tone_guidelines.json ([M] languages) ✓ | label_patterns.json ✓`
- Aborts immediately with `ABORT: [filename] not found or failed to parse.` if any file is missing

**Step 4c criterion 2 rewritten** from a vague "Apply formality rules from config/review_rules_compact.md exactly" to an explicit config-driven check against `tone_guidelines.json`:
- Formal languages (`formal_vous_languages.languages`): emit Warning finding with `"Formality deviation: [market] uses informal address but tone_guidelines.json specifies formal (formal_vous_languages)"`
- Informal-standard languages (`informal_standard_languages.languages`): explicitly NOT flagged — informal is brand standard
- Neutral languages (en, ga, sw): no formal/informal check
- Unknown languages: no flag

## Verification Results

All plan verification checks passed:
- `python3 scripts/structural_validator.py --help` — no import errors
- `grep -n "return None" scripts/structural_validator.py` — present in load_valid_variables
- `grep -n "sys.exit" scripts/structural_validator.py` — present in run_validation abort gate
- `grep "Reference files:" .claude/commands/review-translations.md` — health check line present
- `grep "formal_vous_languages" .claude/commands/review-translations.md` — explicit formality check present
- `grep "ABORT:" .claude/commands/review-translations.md` — abort instruction present
- Running validator against samples/reco-val-prof-bo.csv exits 0, logs "Variables.csv: 518 variables loaded"

## Deviations from Plan

None — plan executed exactly as written. Task 1 was pre-committed before this execution session began; all changes were verified as correct and meeting acceptance criteria before the Task 2 commit was made.

## Known Stubs

None — all changes are fully wired. The health check block reads real files and prints real counts. The formality criteria references real config file paths.

## Self-Check: PASSED

- `scripts/structural_validator.py` — exists and passes all AST checks
- `a602037` — git log confirms commit present
- `120bab0` — git log confirms commit present
- `.claude/commands/review-translations.md` — contains all required strings (Reference files:, ABORT:, formal_vous_languages, informal_standard_languages, Formality deviation, neutral_languages)
