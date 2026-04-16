# Project Audit — Translation Quality Review Automation

**Date:** 2026-04-16
**Milestone:** v1.2 — Audit, Fix & Strategic Overview
**Scope:** Code (unused/redundant), workflow gaps, scope gaps vs Phase 1 vision, and contradictions
**Total findings:** 34 (renumbered 1–34 from raw and gap analysis files)
**Phase 9 input:** Critical findings define FIX-06 scope

---

## Executive Summary

This audit covers the full translation quality review automation codebase as of v1.1 (shipped 2026-04-14). A total of **34 findings** were identified across five categories: unused/redundant code and config (7 findings), workflow gaps (15 findings), scope gaps vs the Phase 1 vision (6 findings), contradictions (5 findings), and an archiving procedure for the reports folder. Of these, **5 are critical**, **10 are medium**, and **19 are low or informational**. The most significant themes are: (1) the structural validator silently uses the wrong reference if France is not at CSV position 0 — a single column reorder would corrupt every validation result; (2) wrong-loop-variable errors, the most commonly observed recurring error in CLAUDE.md, are not detectable by the structural validator; and (3) the corrections learning system silently fails for Traditional Chinese markets due to language code format inconsistency. Phase 9 (Fixes) should prioritize [#3], [#5], [#17], and [#24] as the critical FIX-06 scope.

---

## Findings by Category

---

### 1. Unused / Redundant Code and Config

| # | File | Status | Priority |
|---|------|--------|----------|
| [#1] | scripts/generate_pdf.py | dead-code | critical |
| [#2] | config/languages.json | potentially-unused | medium |
| [#3] | config/review_rules_compact.md | active — sync risk | low |
| [#4] | scripts/test_summary_flag.py | active-but-stale header | low |
| [#5] | config/Variables.csv | active — no action | none |
| [#6] | config/label_patterns.json, config/tone_guidelines.json | active — no action | none |
| [#7] | reports/ (8 stale files) | archiving needed | low |

---

#### [#1] scripts/generate_pdf.py — dead code

**Priority:** critical
**Type:** dead-code

`generate_pdf.py` is not invoked by any active code path. The skill (Step 6) uses an inline Python snippet with CSS copied from this file — `generate_pdf.py` is never called as a subprocess. The script hardcodes the path `review-by-country-2026-04-03.md` (lines 7–10) and will crash on any other filename without manual edits. User confirmed PDF output is no longer part of the workflow. `git log` shows it has never been updated since initial commit (`595d39c`). REQUIREMENTS.md FIX-02 / HND-03 references adding CLI args to this script — those requirements should be retired along with the script.

**Next step:** `mkdir -p scripts/archive && mv scripts/generate_pdf.py scripts/archive/generate_pdf.py`. Retire REQUIREMENTS.md FIX-02 / HND-03 as stale in Phase 9.

---

#### [#2] config/languages.json — potentially unused

**Priority:** medium
**Type:** potentially-unused

Zero references in any active code file — not in `structural_validator.py`, not in the skill definition, not in `CLAUDE.md`. The file contains valuable data (`expected_length_ratio`, `formality` per language) that the validator could use. However, the `formality` field directly contradicts `tone_guidelines.json` for 12 languages (see [#31]). Using this file without fixing formality data first would introduce wrong formality checks.

**Next step:** Fix the `formality` field for 12 languages ([#31]) before integrating into the skill. Then wire `expected_length_ratio` values into `structural_validator.py` `check_length_anomaly()` via the existing but unused `lang_ratios` parameter. Phase 9 task.

---

#### [#3] config/review_rules_compact.md — active, sync risk

**Priority:** low
**Type:** active (sync risk)

File is actively consumed by the skill (Step 4c, lines 121 and 134). It partially duplicates `label_patterns.json` and `tone_guidelines.json`. One confirmed divergence is documented in [#30]. If the canonical configs are updated without updating this file, the AI reviewer will use stale rules.

**Next step:** Evaluate in Phase 9 whether to auto-generate this compact file from the canonical config sources. Until then, update it manually whenever `label_patterns.json` or `tone_guidelines.json` change.

---

#### [#4] scripts/test_summary_flag.py — active dev utility, stale header

**Priority:** low
**Type:** active-but-stale

The `--summary` flag it tests is fully implemented and active. The file header still reads "RED phase: These tests verify expected behavior before implementation" — the feature has been implemented. Tests 2–6 depend on `samples/relance_3.csv` being present, which is not guaranteed in all environments. No CI pipeline exists; the script is manually run.

**Next step:** Update the file header from "RED phase" to reflect post-implementation status. Add a note about the `samples/relance_3.csv` dependency. Low priority — do opportunistically in Phase 9.

---

#### [#5] config/Variables.csv — active, no action needed

**Priority:** none
**Type:** active

Hard dependency: `structural_validator.py` aborts with `sys.exit(1)` if this file is missing. Referenced in Step 1 health check and Step 7 batch routing. No action needed.

---

#### [#6] config/label_patterns.json and config/tone_guidelines.json — active, no action needed

**Priority:** none
**Type:** active

Both files are actively read by the skill (Step 1 health check, Step 4c, Step 7 routing). No action needed.

---

#### [#7] reports/ — archiving procedure (8 stale files)

**Priority:** low
**Type:** archiving

Of 27 files in `reports/`, 8 are stale and should be archived:
- 4 stale `.html` files (HTML output format was removed in v1.1 / NTIO-04)
- 2 structural JSON intermediates (`structural_results.json`, `structural_results_relance3.json`) — build artifacts, not final outputs
- 2 ad-hoc analysis files (`token-baseline.md`, `tone-review-for-native-speakers.md`)

See **Section 5 (Reports Folder — Archiving Procedure)** for the runnable command.

---

### 2. Workflow Gaps

Covers all five stages: structural validation, AI review, report generation, Notion publishing, batch feedback routing. Brittle findings are tagged `[brittle]` alongside the priority label.

| # | Stage | Type | Priority |
|---|-------|------|----------|
| [#8] | Structural validation | missing-check (loop variable placement) | critical |
| [#9] | Structural validation | brittleness — France row position | critical [brittle] |
| [#10] | Structural validation | missing-check (double pipe in buttons) | medium |
| [#11] | Structural validation | missing-check (malformed CSS style=) | medium |
| [#12] | Structural validation | missing-check (extra closing text) | low |
| [#13] | Structural validation | missing-feature (per-language length ratios) | low |
| [#14] | Structural validation | brittleness — emoji hardcoded ranges | medium [brittle] |
| [#15] | AI review — Haiku routing | missing-step (clean market coverage gap) | medium |
| [#16] | AI review — Step 3 | active-bug (zh_TW/zh_HK rule lookup) | medium |
| [#17] | Report generation | brittleness — fixed structural_results.json path | low [brittle] |
| [#18] | Notion publishing | missing-step (no report review tracking) | low |
| [#19] | Notion publishing | missing-step (failed publish not retried) | low |
| [#20] | Batch feedback | missing-step (no backup before write) | medium |
| [#21] | Batch feedback | workflow-note (manual confirmation — intentional) | n/a |
| [#22] | Batch feedback | unscalable-step (rules_summary rebuild at scale) | low |

---

#### [#8] Structural validator does not detect wrong-loop-variable errors

**Priority:** critical
**Type:** missing-check

CLAUDE.md lists "wrong loop variable" as a recurring error: Arabic markets put `@TPL_MATIERE_DE_MATIERE@` inside `<TPL_LOOP_ANNONCES>` when it should be `@TPL_ANNONCE_AFFICHE_QUI_CONNECTE@`, and `@TPL_ANNONCE_AFFICHE_QUI_CONNECTE@` inside `<TPL_IF_LISTE_AVIS>` when it should be `@TPL_LISTE_AVIS@`. `structural_validator.py` confirms variables exist in the overall text (cross-referencing against the French reference) but does not validate variable placement within nested blocks. A market can pass structural validation with zero findings while having this error.

**Next step:** Add a `check_loop_variable_placement()` function to `structural_validator.py`. Define allowed/disallowed variables per block in `label_patterns.json`. This is the most impactful single addition to the structural layer.

---

#### [#9] France reference row hard-assumed at position 0 in structural_validator.py

**Priority:** critical [brittle]
**Type:** brittleness

`structural_validator.py` line 597: `ref_entry = entries[0]` with comment "First entry should be France (the reference)" — no validation. A column reorder in any CSV export silently uses the wrong reference, producing false positives and false negatives for every market with zero error message. This is QUA-01 (active requirement FIX-03).

**Next step:** In `run_validation()`, search all parsed entries for one where `entry['country']` contains "France" or "fr" (case-insensitive). If found but not first, reorder. If not found, fail with a clear error. Implement as FIX-03 in Phase 9.

---

#### [#10] Structural validator does not detect double-pipe in buttons

**Priority:** medium
**Type:** missing-check

CLAUDE.md recurring error: `[BOUTON]...||text[/BOUTON]` — double pipe instead of single. `check_custom_markup()` counts tag opens/closes but does not inspect button content. Double-pipe errors pass structural validation silently.

**Next step:** Extend `check_custom_markup()` or add `check_button_content()` to extract text between `[BOUTON]` and `[/BOUTON]` and flag `||` occurrences.

---

#### [#11] Structural validator does not detect malformed CSS style attributes

**Priority:** medium
**Type:** missing-check

CLAUDE.md recurring error: `style=";text-align:right;direction:rtl"` — leading semicolon, seen in Arabic and Hebrew markets. `check_html_balance()` only checks tag balance, not style attribute values.

**Next step:** Add a regex check for `style\s*=\s*";\s*` pattern in `structural_validator.py`. Belongs in the structural layer as a straightforward pattern match.

---

#### [#12] Structural validator does not detect extra closing text outside template

**Priority:** low
**Type:** missing-check

CLAUDE.md recurring error: markets append text outside the template (e.g., "Atentamente, Equipo Superprof."). Not structurally detectable with current approach. Partially mitigated by AI review Step 4c criterion 6 (cultural appropriateness) and by `check_length_anomaly()` if the appended text is long enough to exceed the 2.5x ratio.

**Next step:** AI review currently catches this. Low priority structural enhancement — add a check for text after the last recognized closing marker with no French reference equivalent. Defer to Phase 9 or later.

---

#### [#13] Per-language length ratio thresholds not wired (dead parameter)

**Priority:** low
**Type:** missing-feature

`check_length_anomaly()` has a `lang_ratios: dict = None` parameter (line 481) that was never used — it is a dead parameter. `config/languages.json` has `expected_length_ratio` per language. Hardcoded thresholds (0.4 / 2.5) may produce false positives for Finnish, German (longer) or Japanese, Chinese (shorter per character count).

**Next step:** Wire `languages.json` `expected_length_ratio` into `check_length_anomaly()` via the existing `lang_ratios` parameter. Prerequisite: fix `languages.json` formality data first ([#31]).

---

#### [#14] Emoji detection uses hardcoded Unicode ranges — new emoji undetected

**Priority:** medium [brittle]
**Type:** brittleness

`RE_EMOJI` in `structural_validator.py` (lines 55–70) uses hardcoded Unicode ranges. Any emoji from Unicode 16.0+ falls outside the ranges and is silently ignored by `check_emojis()`. This is QUA-02 (active requirement FIX-04).

**Next step:** Replace hardcoded ranges with `unicodedata.category()` or the `emoji` library for maintained Unicode emoji detection. Implement as FIX-04 in Phase 9.

---

#### [#15] CLAUDE.md says Haiku spot-checks clean markets; skill says auto-pass — contradiction

**Priority:** medium
**Type:** missing-step / doc-vs-implementation

CLAUDE.md: "Tier 2 (clean markets, Haiku 4.5): markets with zero structural findings get a fast spot-check (emoji, encoding, past corrections only)." Skill Step 4b: "Clean: markets with zero structural findings → auto-pass, no AI review needed." The skill auto-passes clean markets entirely — no Haiku review occurs. If the team expects Haiku to catch emoji/encoding issues in clean markets, the current behavior is silent data loss.

**Next step:** Reconcile the discrepancy. Either: (a) add a Haiku spot-check sub-step for clean markets covering emoji, encoding, and past corrections, or (b) update CLAUDE.md to accurately reflect that clean markets are auto-passed. This is both a documentation fix and a potential quality gap.

---

#### [#16] Traditional Chinese rule lookups silently fail due to zh_TW/zh-TW code mismatch

**Priority:** medium
**Type:** active-bug

`corrections_log.json` uses underscore codes (`zh_TW`, `zh_HK`). The skill's Step 3 filters rules by exact language code match. When a CSV uses `zh-TW` (BCP-47 hyphen standard), `rule.language == "zh-TW"` returns zero results — Traditional Chinese markets get zero applicable past corrections despite having 2 valid rules in the log. This is directly caused by contradiction [#32].

**Next step:** Fix `corrections_log.json` `zh_TW` → `zh-TW` and `zh_HK` → `zh-HK` per [#32] recommendation. Add a normalization step in the skill's Step 3 as a defensive measure.

---

#### [#17] Fixed `structural_results.json` path overwrites on multi-run sessions

**Priority:** low [brittle]
**Type:** brittleness

Step 2 always writes to `reports/structural_results.json` (fixed filename). Running the review twice in the same session overwrites the first run's structural results. No current failure path since the workflow is single-run per session, but it is a brittleness.

**Next step:** Use a notification-specific filename for structural results (e.g., `reports/structural_results-[notification_id].json`) to avoid overwrites. Low priority.

---

#### [#18] No mechanism to track which Notion-published reports have been reviewed

**Priority:** low
**Type:** missing-step

After publication, there is no status tracking — no "reviewed" flag, no aggregated open-action list, no way to identify unpublished vs published reports. When notification count grows to 50+, manual tracking becomes infeasible.

**Next step:** Add a local `reports/index.md` or Notion index page tracking publication date, report path, Notion URL, and review status per report. Phase 9 or later.

---

#### [#19] Failed Notion publishes have no retry or detection mechanism

**Priority:** low
**Type:** missing-step

Step 6d correctly announces Notion failure but makes no persistent record. If the user misses the warning, the report exists locally but is never published. No future session can detect "saved but unpublished" reports.

**Next step:** Log failed publish attempts to `reports/unpublished.json`. Phase 9.

---

#### [#20] Corrections log not backed up before write operations

**Priority:** medium
**Type:** missing-step

Step 7b writes directly to `corrections/corrections_log.json` without backup. A partial write or incorrect feedback application could corrupt all 6 accumulated learning rules with no recovery path. This is QUA-03 (active requirement FIX-05).

**Next step:** Add a date-stamped backup in `corrections/backups/` before any Step 7b/7c write. Implement as FIX-05 in Phase 9.

---

#### [#21] Manual confirmation in batch feedback is intentional — not a gap

**Priority:** n/a (workflow note)
**Type:** workflow-note

Per D-15, the manual confirmation step (user must enter item numbers to confirm writes) is intentional. The AI process is not yet trusted enough to run unattended. This is correct design for the current stage.

**Note for Phase 9:** As confidence grows, consider an `--auto-apply` flag or reducing confirmation to conflict-only items.

---

#### [#22] rules_summary.json rebuild at 150+ entries will strain in-session context

**Priority:** low
**Type:** unscalable-step

Step 7d rebuilds `rules_summary.json` in-session by reading all corrections_log entries. Currently 6 entries. At 150+ entries (the threshold already flagged in Step 3), the in-session rebuild approaches practical context window limits.

**Next step:** When `corrections_log.json` exceeds ~100 entries, move the rebuild to a standalone Python script. The existing Step 3 warning at 150 rules is the right trigger signal.

---

### 3. Scope Gaps vs Phase 1 Vision

| # | Requirement | Type | Priority |
|---|-------------|------|----------|
| [#23] | HND-01 / FIX-01 — README | never-built | medium |
| [#24] | QUA-01 / FIX-03 — France reference row search | never-built | critical |
| [#25] | QUA-02 / FIX-04 — Unicode emoji detection | never-built | medium |
| [#26] | QUA-03 / FIX-05 — Corrections log backup | never-built | medium |
| [#27] | HND-02 / FIX-02 — requirements.txt | never-built | low (stale) |
| [#28] | HND-03 / FIX-02 — generate_pdf.py CLI args | built-but-stale | low (stale) |

---

#### [#23] README.md — never built

**Priority:** medium
**Type:** never-built
**Requirement:** HND-01 / FIX-01

No complete README covering prerequisites, setup steps, how to run a review, how to read reports, and how to submit feedback. A partial README.md may exist (referenced in config/languages.json documentation) but it does not satisfy HND-01. The project is not onboardable by a new team member without Juan's guidance.

**Next step:** Create README.md with all five required sections (prerequisites, setup, how to run, how to read reports, how to submit feedback). Implement as FIX-01 in Phase 9.

---

#### [#24] France reference row search — never built

**Priority:** critical
**Type:** never-built
**Requirement:** QUA-01 / FIX-03

`structural_validator.py` hard-assumes France is at CSV position 0 (see [#9]). QUA-01 was planned but never implemented. This is the same critical finding as [#9] — listed here because it also represents an unbuilt planned capability.

**Next step:** Implement as FIX-03 in Phase 9 (highest priority fix alongside FIX-06).

---

#### [#25] Unicode emoji detection — never built

**Priority:** medium
**Type:** never-built
**Requirement:** QUA-02 / FIX-04

Hardcoded emoji ranges (see [#14]). QUA-02 was planned but never implemented.

**Next step:** Implement as FIX-04 in Phase 9.

---

#### [#26] Corrections log backup — never built

**Priority:** medium
**Type:** never-built
**Requirement:** QUA-03 / FIX-05

No backup-before-write (see [#20]). QUA-03 was planned but never implemented. Risk grows with each new correction.

**Next step:** Implement as FIX-05 in Phase 9.

---

#### [#27] requirements.txt — never built (stale)

**Priority:** low (stale)
**Type:** never-built
**Requirement:** HND-02 / FIX-02

No `requirements.txt` exists. Since `generate_pdf.py` is confirmed dead ([#1]), the PDF dependencies (`markdown`, `weasyprint`) are no longer relevant to the active workflow.

**Next step:** Per D-08, FIX-02 bundles requirements.txt with `generate_pdf.py` CLI args — both are now stale. Phase 9 should retire FIX-02 or narrow it to a minimal requirements.txt noting deprecated PDF dependencies only.

---

#### [#28] generate_pdf.py CLI args — built-but-stale

**Priority:** low (stale)
**Type:** built-but-stale
**Requirement:** HND-03 / FIX-02

The script exists but CLI args (`--input`, `--output`) were never added. The script is confirmed dead code ([#1]). Adding CLI args to a dead script would be wasted effort.

**Next step:** Retire HND-03 / FIX-02. Archive `generate_pdf.py`. Phase 9 closes this requirement as "superseded" — not completed.

---

### 4. Contradictions

| # | Type | Files | Priority |
|---|------|-------|----------|
| [#29] | sync-drift | corrections_log.json / rules_summary.json (hu/lt count) | low |
| [#30] | doc-vs-implementation | CLAUDE.md / skill definition (Haiku vs auto-pass) | medium |
| [#31] | config-mismatch | languages.json vs tone_guidelines.json (12 languages formality) | medium |
| [#32] | config-mismatch | corrections_log.json vs all other configs (zh_TW vs zh-TW) | medium |
| [#33] | sync-drift | corrections_log.json / rules_summary.json (Japanese rule text) | medium |
| [#34] | doc-vs-implementation | PROJECT.md / skill (stale known-issue note) | low |

---

#### [#29] Inflated occurrence_count for hu and lt in rules_summary.json

**Priority:** low
**Type:** sync-drift

`rules_summary.json` reports `occurrence_count: 2` for both `hu` and `lt` rules. `corrections_log.json` has exactly 1 entry per language — no duplicates. The counter was incremented without a corresponding second log entry, inflating confidence scores for these two rules.

**Next step:** Fix `occurrence_count` to 1 for both `hu` and `lt` in `rules_summary.json`. Add a note to the rebuild process to count only actual entries rather than incrementing from the current count.

---

#### [#30] CLAUDE.md says Haiku spot-checks clean markets; skill says auto-pass

**Priority:** medium
**Type:** doc-vs-implementation

Already documented as a workflow gap in [#15]. Listed here as a contradiction: CLAUDE.md and the skill definition give different descriptions of how clean markets are handled after triage. If the team makes decisions based on CLAUDE.md (e.g., expecting Haiku to catch encoding issues in clean markets), they will be wrong.

**Next step:** Reconcile as described in [#15]. Either update the skill to add Haiku spot-check, or update CLAUDE.md to match current auto-pass behavior.

---

#### [#31] languages.json formality field contradicts tone_guidelines.json for 12 languages

**Priority:** medium
**Type:** config-mismatch

`languages.json` classifies de, es, it, nl, hu, ro, hr, sr, sl, el, ru, id as `"formal"`. `tone_guidelines.json` classifies all 12 as `informal_standard_languages` (confirmed 2026-04-03). Root cause: `languages.json` uses linguistic formality (e.g., German has "Sie" formal form) while `tone_guidelines.json` reflects the Superprof brand standard (German uses informal "du"). If `languages.json` is integrated into the skill without fixing this field first, the AI reviewer will incorrectly flag informal usage in these markets as errors.

**Next step:** Update `languages.json` formality field for all 12 languages to `"informal"` (or add a `"brand_formality"` field). Do this before or concurrently with integrating `languages.json` into the skill per [#2].

---

#### [#32] Language codes: corrections_log.json uses underscores (zh_TW) vs BCP-47 hyphens (zh-TW) everywhere else

**Priority:** medium
**Type:** config-mismatch

`corrections_log.json` uses `zh_TW`, `zh_HK` (underscore). All other config files use `zh-TW` (hyphen): `label_patterns.json`, `tone_guidelines.json`, `languages.json`. This mismatch causes the rule lookup failure in [#16] and risks silent failures in any future tooling that matches language codes across files.

**Next step:** Standardize on BCP-47 hyphen codes. Update `corrections_log.json`: `zh_TW` → `zh-TW`, `zh_HK` → `zh-HK`. Also confirm `zh-HK` is present in `tone_guidelines.json` and `label_patterns.json` if Hong Kong is actively reviewed.

---

#### [#33] Japanese rule text diverges by one word between corrections_log.json and rules_summary.json

**Priority:** medium
**Type:** sync-drift

`corrections_log.json` rule_extracted: "Japanese: @TPL_MATIERE_DE_MATIERE@ is a French genitive construction **and is not** configured for Japanese..."
`rules_summary.json` rule: "Japanese: @TPL_MATIERE_DE_MATIERE@ is a French genitive construction **not** configured for Japanese..."

The two-word difference ("and is not" vs "not") is semantically identical but a string mismatch. If `rules_summary.json` is ever rebuilt from `corrections_log.json` using exact string matching, the Japanese rule will be dropped (occurrence_count = 0 matches) — losing the only Japanese rule in the learning system.

**Next step:** Align `rules_summary.json` Japanese rule text to exactly match the `rule_extracted` in `corrections_log.json`. Fix before any automated rebuild of `rules_summary.json`.

---

#### [#34] PROJECT.md "known issues" contains stale entry about tone_guidelines.json path

**Priority:** low
**Type:** doc-vs-implementation

PROJECT.md notes: "Step 1 health check references abbreviated tone_guidelines.json path (low severity)." The current skill Step 1 (line 39) uses the full path `config/tone_guidelines.json` — this was resolved at some point. The stale note creates confusion during audits.

**Next step:** Remove "Step 1 health check references abbreviated tone_guidelines.json path" from PROJECT.md known issues section.

---

### 5. Reports Folder — Archiving Procedure

Of the 27 files in `reports/`, 8 are stale and should be archived. The remaining 19 are active `.md` reports from current review runs.

**Files to archive:**

| Category | Files |
|----------|-------|
| Stale HTML (format removed v1.1) | review-by-country-2026-04-03.html, review-message-nouveau-2026-04-09.html, review-message-nouveau-test-2026-04-09.html, review-reco-val-prof-bo-2026-04-08.html |
| Structural JSON intermediates | structural_results.json, structural_results_relance3.json |
| Ad-hoc analysis files | token-baseline.md, tone-review-for-native-speakers.md |

**Runnable archiving command:**

```bash
# Run from project root — creates archive/ and moves stale files
mkdir -p reports/archive && \
mv reports/review-by-country-2026-04-03.html \
   reports/review-message-nouveau-2026-04-09.html \
   reports/review-message-nouveau-test-2026-04-09.html \
   reports/review-reco-val-prof-bo-2026-04-08.html \
   reports/structural_results.json \
   reports/structural_results_relance3.json \
   reports/token-baseline.md \
   reports/tone-review-for-native-speakers.md \
   reports/archive/
```

**Additional note:** Two pairs of duplicate-named reports exist (`review-by-country-relance3-2026-04-03.md` vs `review-by-country-2026-04-03-relance3.md`, and `review-message-nouveau-test-2026-04-09.md` vs `review-message-nouveau-2026-04-09.md` — test vs production). Lower priority — archive the test/older versions when convenient.

**Recommendation:** Add `reports/archive/` to `.gitignore` if report history should not be in version control.

---

## Priority Summary

| Priority | Count | Finding Numbers |
|----------|-------|----------------|
| Critical | 5 | [#1], [#8], [#9], [#24] (= [#9]), and the active bug [#16] |
| Medium | 14 | [#2], [#10], [#11], [#14], [#15], [#16], [#20], [#23], [#25], [#26], [#30], [#31], [#32], [#33] |
| Low | 15 | [#3], [#4], [#7], [#12], [#13], [#17], [#18], [#19], [#22], [#27], [#28], [#29], [#34], and two no-action findings [#5], [#6] |
| None (no action) | 3 | [#5], [#6], [#21] |

**Critical findings detail:**
- **[#1]** — `generate_pdf.py` is dead code consuming maintenance attention and creating confusion about whether PDF output is supported
- **[#8]** — Wrong-loop-variable errors (most-recurring error in CLAUDE.md) are invisible to structural validation
- **[#9]** / **[#24]** — France row position brittleness: a single CSV column reorder would corrupt all validation silently
- **[#16]** — Traditional Chinese learning rules silently never apply (zh_TW vs zh-TW mismatch)

---

## Phase 9 Recommendations

Per D-03, this audit identifies issues only — fixes belong to Phase 9.

**FIX-06 scope (confirmed by critical findings):**

Phase 9's FIX-06 ("highest-priority critical findings from the AUD phase") should address, in order:

1. **[#9] / FIX-03** — France reference row search (critical brittle; QUA-01). Any CSV reorder currently corrupts all validation silently. This is the highest-risk finding and the most straightforward fix.
2. **[#8]** — Wrong-loop-variable check in `structural_validator.py` (critical missing-check). The most commonly observed recurring error in CLAUDE.md is undetectable by the structural layer. Needs a config-driven approach in `label_patterns.json`.
3. **[#16] / via [#32]** — Standardize zh_TW → zh-TW in `corrections_log.json` (medium active-bug). Quick fix with high impact — restores Traditional Chinese rule application immediately.
4. **[#1]** — Archive `generate_pdf.py` and retire FIX-02/HND-03 (critical dead-code cleanup). Clean up first to reduce confusion.

**Medium-priority fixes for Phase 9:**
- FIX-04: Unicode emoji detection ([#14], [#25])
- FIX-05: Corrections log backup ([#20], [#26])
- FIX-01: README.md ([#23])
- Fix [#31]: `languages.json` formality data before any integration
- Fix [#33]: Japanese rule text alignment before any automated rebuild

**FIX-02 staleness note (per D-08):**
FIX-02 as defined in REQUIREMENTS.md ("requirements.txt + `generate_pdf.py` CLI args") should be retired or split. `generate_pdf.py` is dead code — adding CLI args is wasted effort. A minimal requirements.txt noting deprecated PDF dependencies is the only residual value of FIX-02, if even that is worth the effort.

**Roadmap impact:**
- Phase 9 should begin with archiving `generate_pdf.py` and retiring FIX-02 to clean the requirements baseline before fixing active issues.
- The [#9] fix (FIX-03) should ship first among code changes — it guards against silent data corruption on every future review run.
- [#8] (loop variable check) is the highest-value structural improvement but requires design work (config schema for block-variable mapping). Scope carefully in Phase 9 planning.

---

*Audit produced by Phase 08, Plan 02*
*Raw findings (Plan 01): 18 findings (#1–#18 in working numbering, renumbered #1–#7 and #29–#34 here)*
*Gap findings (Plan 02, Task 1): 21 findings (#19–#39 in working numbering, renumbered #8–#28 here)*
*All findings renumbered sequentially 1–34 for this document*
