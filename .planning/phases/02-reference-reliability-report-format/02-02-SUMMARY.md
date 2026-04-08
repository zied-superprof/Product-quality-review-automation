---
phase: 02-reference-reliability-report-format
plan: 02
subsystem: report-generation
tags: [report-format, html-output, notification-id, review-skill, markdown-to-html, css, pdf]

dependency_graph:
  requires:
    - phase: 02-reference-reliability-report-format
      plan: 01
      provides: step1-health-check (notification ID extraction placed after health check block)
  provides:
    - --format flag in Step 0 (html default, md, pdf)
    - notification-ID-based report filenames (review-[id]-YYYY-MM-DD)
    - inline MD-to-HTML Python conversion with CSS from generate_pdf.py
    - fixed section order enforcement in every report
    - always-present French reference verbatim block
    - always-present Markets with no issues section with No issues found. fallback
  affects: [phase-03-feedback-loop, phase-04-team-handoff, review-skill-users]

tech-stack:
  added: []
  patterns:
    - format-flag-default-html: --format flag defaults to html, explicit md/pdf opt-in
    - notification-id-extraction: ID derived from --notification arg > CSV column > filename, sanitized for filesystem
    - inline-html-conversion: markdown library + CSS embedded directly in skill instructions as Python snippet
    - fixed-section-order: report structure is invariant regardless of findings (conditional sections documented explicitly)

key-files:
  created: []
  modified:
    - .claude/commands/review-translations.md

key-decisions:
  - "--format defaults to html (both .md and .html) so non-technical teammates can open reports in any browser without extra steps"
  - "Notification ID derived from --notification arg first, then CSV column, then filename — filename is the fallback, not the primary source"
  - "Sections 3, 4, 6 (Grouped, Single-market, Undefined vars) are conditional — omitted when empty, not shown with No issues found. placeholder"
  - "Sections 1, 2, 5 (Summary, French ref, Markets with no issues) are always present — ensures predictable report structure"
  - "French reference verbatim title/body always shown; issues sub-section conditional on Step 4a findings"
  - "Markets with no issues groups all clean markets as comma-separated list under single header — matches user clarification to group them"

patterns-established:
  - "Format flag: user passes --format to control output type; skill defaults to most useful format, not raw markdown"
  - "Section order: fixed and documented in the skill itself, not left to AI discretion per run"

requirements-completed: [RPT-01, RPT-02, RPT-03]

duration: 11min
completed: 2026-04-08
---

# Phase 02 Plan 02: Report Format — HTML Default, Notification-ID Filenames, Fixed Section Order Summary

**--format flag (default html) with MD-to-HTML conversion using generate_pdf.py CSS, notification-ID-based filenames, and fixed section order enforced in review-translations.md**

## Performance

- **Duration:** 11 min
- **Started:** 2026-04-08T19:04:38Z
- **Completed:** 2026-04-08T19:15:48Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Added `--format html|md|pdf` flag to Step 0 with Unknown format abort instruction
- Added Notification ID extraction block to Step 1 (4-step resolution: --notification arg > CSV column > filename > sanitize)
- Replaced `review-by-country-YYYY-MM-DD` filename with `review-[notification-id]-YYYY-MM-DD` in Step 6
- Added output behavior per --format (html: .md + .html, md: .md only, pdf: weasyprint with fallback)
- Added inline MD-to-HTML Python snippet with full CSS block from generate_pdf.py (font-family, #0f3460, #e94560 palette)
- Enforced fixed section order (Summary, French ref, Grouped, Single-market, No issues, Undefined vars) with conditional/always-present rules
- French reference verbatim title/body now always shown (not gated behind "if issues found")
- Markets with no issues section always present with "No issues found." fallback; clean markets listed as comma-separated group

## Task Commits

1. **Task 1: Add --format flag, notification-ID filename, HTML conversion, and fixed section order** - `2f04c19` (feat)

**Plan metadata:** (docs commit — created at end of this SUMMARY write)

## Files Created/Modified

- `.claude/commands/review-translations.md` — Four changes: Step 0 --format flag, Step 1 notification ID extraction, Step 6 filename + HTML conversion + section order

## Decisions Made

- `--format html` is the default (not `md`) so non-technical teammates can open reports directly in any browser
- Notification ID resolution order: `--notification` arg first (explicit user intent), then CSV "notification" column, then CSV filename as last resort
- Sections 3, 4, 6 are conditional (omitted when empty) — showing empty grouped/single-market/undefined-vars sections adds noise without value
- Sections 1, 2, 5 are always present — summary table, French reference, and clean markets list are always useful
- User clarification: "Also group the markets with no issues" — clean markets listed as comma-separated group under single `## Markets with no issues` header (not one section per market)

## Deviations from Plan

### User Clarification Applied

**1. [User Input - Scope Refinement] Markets with no issues grouping clarified**
- **Found during:** Task 1 (applying Change 4)
- **Issue:** Plan said "markets with no issues — always present" but did not explicitly state they should be grouped (comma-separated) vs individually listed
- **Clarification:** User rejected the initial Change 4 edit with "Also group the markets with no issues"
- **Fix:** Updated section 5 description to explicitly state: "List all clean markets together as a comma-separated group under a single `## Markets with no issues` header"
- **Files modified:** .claude/commands/review-translations.md
- **Committed in:** 2f04c19 (Task 1 commit)

---

**Total deviations:** 0 auto-fixed (Rules 1-3), 1 user clarification incorporated
**Impact on plan:** Clarification improves report readability with no scope change.

## Issues Encountered

None.

## Known Stubs

None — all changes fully specify behavior. The HTML conversion snippet uses actual library calls and actual CSS. The notification ID extraction covers all cases including fallback to filename. No placeholder behaviors.

## Next Phase Readiness

- Phase 03 (Feedback Loop Strengthening) can proceed — reports now have notification-ID filenames making it easier to link corrections to specific notifications
- Phase 04 (Team Handoff) benefits from HTML default output — reports are browser-ready without Markdown knowledge
- No blockers

## Self-Check: PASSED

Verified after writing SUMMARY:
- `.claude/commands/review-translations.md` — exists
- `2f04c19` — git log confirms commit present
- All plan verification checks passed:
  - `--format html|md|pdf` present in Step 0 (line 16)
  - `Unknown format` abort instruction present (line 16)
  - `Notification ID extraction` present in Step 1 (line 51)
  - `lowercase, replace spaces and slashes with hyphens` sanitization present (line 55)
  - `review-[notification-id]-YYYY-MM-DD` filename pattern in Step 6 (line 140)
  - `markdown.markdown(md_content, extensions=["tables", "fenced_code"])` conversion call present (line 156)
  - `font-family: -apple-system` CSS present (line 159)
  - `#0f3460` and `#e94560` CSS colors present
  - `Section order is FIXED` present (line 183)
  - `No issues found.` fallback present (lines 189, 192, 287, 289)
  - `review-by-country-` old pattern count: 0 (removed from primary template)
  - French reference comment no longer says "only include if" for verbatim title/body

---
*Phase: 02-reference-reliability-report-format*
*Completed: 2026-04-08*
