---
phase: 06-batch-feedback-routing
plan: 01
subsystem: review-skill
tags: [batch-feedback, step7, routing, skill-modification]
dependency_graph:
  requires: []
  provides: [batch-mode-detection, routing-classification, block-list-display]
  affects: [.claude/commands/review-translations.md]
tech_stack:
  added: []
  patterns: [Language+Issue-format-detection, 4-bucket-routing-decision-tree, conflict-check-reuse]
key_files:
  created: []
  modified:
    - .claude/commands/review-translations.md
decisions:
  - "Batch mode branches at Step 7 entry point: Language+Issue format triggers 7a-batch; #N format triggers existing 7a-single flow"
  - "notification_type for batch-sourced corrections_log entries is batch-feedback (distinguishes batch rules from session-specific ones)"
  - "Variables.csv routing always produces flag-only output — never included in confirmation set (D-13)"
  - "Conflict items are displayed in block list but excluded from confirmation set — clean items proceed independently (D-05, avoids Pitfall 1)"
metrics:
  duration: "3 minutes"
  completed_date: "2026-04-10"
  tasks_completed: 2
  files_modified: 1
---

# Phase 06 Plan 01: Batch Feedback Detection and Routing Summary

## One-liner

Step 7 extended with Language+Issue batch mode: session-independent entry, 4-bucket routing decision tree (label_patterns.json / tone_guidelines.json / corrections_log.json / Variables.csv flag-only), per-item conflict check, and D-04 block list display with confirmation prompt.

## What Was Built

Added a batch feedback branch to Step 7 of `.claude/commands/review-translations.md`. The modification is purely additive — the existing single-item flow (now `7a-single`) is unchanged except for the header rename.

### New sections added to Step 7

1. **Session-independence note** — tells users (and the AI) that Step 7 works in a fresh session without an active report
2. **Collection template** — a plain-language `Language: / Issue:` template for the employee collecting native speaker feedback
3. **Batch mode detection** — branch logic that reads user input format and routes to `7a-batch` or the existing `7a-single` flow; handles ambiguous input
4. **7a-batch section** — the main batch processing section containing:
   - Parse phase: splits user input on `Language:` boundaries, handles multi-market codes (`ar, he`), skips malformed blocks
   - Route phase: 4-bucket decision tree with Variables.csv existence check as first gate
   - Conflict check phase: per-item conflict check using same sources as `7a-single`
   - Block list display: numbered `#N — [lang]: [summary]` format with `Routes to`, `Rationale`, `Conflict` fields per D-04
   - Confirmation prompt: number-based selection with conflict and Variables.csv exclusion notes

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | ca1e4f9 | feat(06-01): add batch mode detection and session-independence note to Step 7 |
| Task 2 | e572dfa | feat(06-01): add 7a-batch routing classification and block list display |

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

The `7a-batch` section ends with the confirmation prompt display but intentionally defers apply logic to plan 06-02. The prompt instructs the user to "enter the item numbers you want to apply" but the system does not yet act on that input — this is a documented stub per the plan's scope boundary. Plan 02 will add confirmation parsing and one-pass write execution.

## Self-Check: PASSED

- FOUND: `.claude/commands/review-translations.md`
- FOUND: `.planning/phases/06-batch-feedback-routing/06-01-SUMMARY.md`
- FOUND: commit `ca1e4f9` (Task 1)
- FOUND: commit `e572dfa` (Task 2)
