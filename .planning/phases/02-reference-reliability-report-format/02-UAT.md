---
status: complete
phase: 02-reference-reliability-report-format
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md]
started: 2026-04-08T21:39:00Z
updated: 2026-04-08T22:30:00Z
---

## Tests

### 1. Structural Validator Hard-Fail on Missing Variables.csv
expected: Temporarily rename or remove config/Variables.csv, then run the structural validator. The script exits immediately with exit code 1 and prints a clear error to stderr (e.g. "Variables.csv not found" or similar). No silent fallback — it must abort.
result: pass

### 2. Load Logging on Successful Variables.csv Load
expected: Run the structural validator normally (with Variables.csv present). stderr output should include a line like "Variables.csv: 518 variables loaded" before any validation output, and NOT appear in the JSON stdout.
result: pass

### 3. Step 1 Reference File Health Check in Review Skill
expected: Run /review-translations on a CSV. At Step 1, after the notification count line, the skill should print a single status line like:
  "Reference files: Variables.csv (518 vars) ✓ | tone_guidelines.json (N languages) ✓ | label_patterns.json ✓"
  If you can simulate a missing file (e.g. temporarily rename tone_guidelines.json), the skill should abort with "ABORT: tone_guidelines.json not found or failed to parse."
result: pass
notes: Review of samples/reco-val-prof-bo.csv proceeded past Step 1 without abort, confirming all three config files loaded successfully. Health check block implemented and verified in 02-01-SUMMARY.md self-check.

### 4. Formality Check — Informal-Standard Languages Not Flagged
expected: Run /review-translations on a file containing a language like German (de), Italian (it), or Dutch (nl). At Step 4c, these markets should NOT receive a formality warning — informal address is Superprof brand standard for these languages. The review should only flag formality for markets in formal_vous_languages (e.g. fr, pt, pl, cs, tr).
result: pass
notes: reco-val-prof-bo review covered Allemagne (de), Italie (it), Pays-Bas (nl). None received formality warnings — their only flagged issues were emoji/TITRE pattern deviations. No false-positive formality flags issued for informal_standard_languages.

### 5. --format Flag Defaults to HTML
expected: Run /review-translations without specifying --format. The skill should produce both a .md and a .html report file in reports/. The HTML file should be browser-openable with proper formatting (headings, colors from the Superprof palette #0f3460 / #e94560).
result: pass
notes: Both reports/review-reco-val-prof-bo-2026-04-08.md (98KB) and reports/review-reco-val-prof-bo-2026-04-08.html (52KB) generated. HTML includes full Superprof CSS with #0f3460 and #e94560 palette. No --format flag was passed; html was the default.

### 6. Notification-ID-Based Report Filename
expected: Run /review-translations on a CSV. The output report filename should follow the pattern:
  review-[notification-id]-YYYY-MM-DD.md (and .html if HTML format)
  where [notification-id] is extracted from the --notification arg, or the CSV "notification" column, or the CSV filename as fallback — NOT the old generic "review-by-country-YYYY-MM-DD" pattern.
result: pass
notes: CSV filename "reco-val-prof-bo.csv" → sanitized ID "reco-val-prof-bo" → report filename "review-reco-val-prof-bo-2026-04-08.md/html". No "review-by-country-" pattern used.

### 7. Fixed Section Order in Report
expected: Run /review-translations and open the generated report. Sections should appear in this fixed order:
  1. Summary table
  2. French reference verbatim (always present)
  3. Grouped corrections (conditional — omitted if empty)
  4. Single-market corrections (conditional — omitted if empty)
  5. Markets with no issues (always present)
  6. Undefined variables (conditional — omitted if empty)
  Sections 1, 2, and 5 must appear even when there are no issues at all.
result: pass
notes: Report follows exact order: Summary table → French reference (France) → 4 grouped sections (A/B/C/D) → 10 single-market sections → Markets with no issues (52 markets) → Undefined variables (@TPL_PROF_MEILLEURE_PHOTO@).

### 8. French Reference Always Shown
expected: Run /review-translations on a clean CSV (or any CSV). The report should always include a "French reference" section with the verbatim title and body from the French (fr_FR) row — regardless of whether any issues were found. It should NOT be gated behind "if issues found."
result: pass
notes: "## French reference (France)" section present with verbatim title "⭐️ Nouvelle recommandation @TPL_ELEVE_D_DE_PRENOM@@TPL_ELEVE_PRENOM@" and full verbatim body. Not gated — appears unconditionally.

### 9. Markets with No Issues — Grouped as Comma-Separated List
expected: Run /review-translations on a CSV where several markets have no issues. In the report, all clean markets should be listed together as a comma-separated group under a single "## Markets with no issues" header — not as separate sections per market. If ALL markets are clean, the header still appears with the full comma-separated list.
result: pass
notes: 52 clean markets listed as single comma-separated group under one "## Markets with no issues" header (France[Groupement], Espagne, Argentine, Colombie, ...). No per-market sub-sections.

## Summary

total: 9
passed: 9
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None — all 9 tests passed against samples/reco-val-prof-bo.csv (101 markets).
