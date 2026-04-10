---
phase: 06-batch-feedback-routing
plan: 02
subsystem: review-skill
tags: [batch-feedback, step7, confirmation-flow, conflict-resolution, skill-modification]
dependency_graph:
  requires: [06-01]
  provides: [batch-confirm-write, batch-conflict-resolution, change-summary]
  affects: [.claude/commands/review-translations.md]
tech_stack:
  added: []
  patterns: [one-pass-write-D10, single-7d-rebuild, collaborative-conflict-resolution]
key_files:
  created: []
  modified:
    - .claude/commands/review-translations.md
decisions:
  - "7b-batch uses notification_type=batch-feedback for all batch-sourced corrections_log entries (distinguishes from session-specific rules)"
  - "rules_summary.json rebuilt once after ALL confirmed items written — not per item (D-10, avoids Pitfall 2)"
  - "Conflict items excluded from confirmation until resolved via 7c-batch discussion — clean items proceed independently (D-05)"
  - "No pending queue: items not listed in confirmation are silently discarded (D-09)"
metrics:
  duration: "2 minutes"
  completed_date: "2026-04-10"
  tasks_completed: 2
  files_modified: 1
---

# Phase 06 Plan 02: Batch Feedback Confirmation and Conflict Resolution Summary

## One-liner

7b-batch and 7c-batch sections added: number-based confirmation parsing, one-pass write via existing 7b/7c schema, single rules_summary rebuild, collaborative conflict resolution, and change summary output.

## What Was Built

Added two new sections to Step 7 of `.claude/commands/review-translations.md`, completing the full batch feedback flow begun in plan 06-01.

### New sections added

1. **7b-batch — Confirm and apply**
   - Parses user's number selection (accepts `1, 3, 4` / `1 3 4` / `1,3,4`)
   - Validates: rejects conflict items ("unresolved conflict"), rejects Variables.csv flags ("cannot be applied automatically"), silently ignores out-of-range numbers
   - Writes each confirmed item using exact same 7b schema (8 fields), with `notification_type: "batch-feedback"`
   - Routes to corrections_log.json, label_patterns.json, or tone_guidelines.json based on the routing decision from 7a-batch
   - Multi-market split: one corrections_log entry per market (D-07 compliance)
   - Rebuilds rules_summary.json exactly once after all writes (D-10 one-pass, not per item)
   - Outputs change summary: N corrections written, M config updates, rules_summary stats, K discarded, J Variables.csv flags

2. **7c-batch — Conflict resolution**
   - Triggered after 7b-batch if any items had ⚠️ conflicts in the block list
   - Shows full conflict context: "New rule" vs "Conflicts with [file] [section]"
   - Collaborative resolution per D-06: no fixed menu, discussion-driven outcomes (write anyway / discard / update existing)
   - Single 7d rebuild for all resolved items (not per resolution)
   - Updates change summary with each resolution outcome
   - Ends with "All conflicts addressed. Batch feedback session complete."
   - Skipped entirely if no conflicts existed

### Full batch flow (complete after plans 01 + 02)

```
7a-batch → detect format → parse items → route → conflict-check → display block list → confirmation prompt
7b-batch → parse numbers → validate → write each confirmed item (one pass) → rebuild 7d once → change summary
7c-batch → (if conflicts) show conflict details → discuss → resolve → rebuild 7d once → summary update
```

### Existing flow preserved

The single-item flow (`7a-single → 7b → 7c → 7d → 7e`) is entirely unchanged.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Tasks 1+2 | fb798ec | feat(06-02): add 7b-batch confirmation/write and 7c-batch conflict resolution |

## Deviations from Plan

None — plan executed exactly as written. Both tasks were implemented in a single edit since they both insert new sections into the same file; committed together as one atomic unit.

## Known Stubs

None. The batch feedback flow is now complete end-to-end:
- 7a-batch detects, routes, and displays the block list with confirmation prompt (plan 01)
- 7b-batch parses confirmation and writes confirmed items (this plan)
- 7c-batch resolves conflicts if any (this plan)

## Self-Check: PASSED

- FOUND: `.claude/commands/review-translations.md`
- FOUND: `### 7b-batch — Confirm and apply` section
- FOUND: `### 7c-batch — Conflict resolution` section
- FOUND: commit `fb798ec`
- FOUND: existing 7a-single, 7b, 7c, 7d, 7e sections unchanged
