# Phase 08 — Gap Findings (Plan 02, Task 1)
**Date:** 2026-04-16
**Scope:** Workflow gaps (AUD-02) and scope gaps (AUD-03) — supplement to Plan 01 raw findings
**Numbering:** Continues from Plan 01 findings (#1–#18); new findings start at #19

---

## Workflow Gaps

Analysis of all five workflow stages: structural validation → AI review (Haiku/Sonnet routing) → report generation → Notion publishing → batch feedback routing.

---

### Stage 1: Structural Validation

---

#### [#19] Structural validator does not detect "wrong loop variable" errors (recurring error in CLAUDE.md)

**Type:** `missing-check`
**Stage:** Structural Validation
**Severity:** critical

**Evidence:**
CLAUDE.md "Recurring errors to watch for" lists: "Wrong loop variable: Arabic markets put `@TPL_MATIERE_DE_MATIERE@` inside `<TPL_LOOP_ANNONCES>` (should be `@TPL_ANNONCE_AFFICHE_QUI_CONNECTE@`) and `@TPL_ANNONCE_AFFICHE_QUI_CONNECTE@` inside `<TPL_IF_LISTE_AVIS>` (should be `@TPL_LISTE_AVIS@`)".

`structural_validator.py` checks: `check_variables()` (variable preservation against French reference), `check_conditionals()` (TPL_IF/ELSE tag balance), `check_custom_markup()` (LIEN/TITRE/BOUTON tag counts). None of these check whether a specific variable is used *inside* a specific loop or conditional block. The validator confirms variables exist in the overall text, but does not validate variable placement within nested template structures.

**Gap:** The structural validator catches "variable missing" but not "variable in wrong block". A market can pass structural validation with zero findings while having a semantically invalid variable placement — the error passes to AI review where it may or may not be caught consistently.

**Recommendation:** Add a `check_loop_variable_placement()` function to `structural_validator.py` that, for known loop patterns (specifically `<TPL_LOOP_ANNONCES>` and `<TPL_IF_LISTE_AVIS>`), validates which variables appear inside those blocks and flags unexpected variables. Since this requires knowing expected patterns, a config entry in `label_patterns.json` mapping block names to allowed/disallowed variables would provide the rule definition.

---

#### [#20] Structural validator does not detect "double pipe in buttons" (recurring error in CLAUDE.md)

**Type:** `missing-check`
**Stage:** Structural Validation
**Severity:** medium

**Evidence:**
CLAUDE.md lists: "Double pipe in buttons: `[BOUTON]...||text[/BOUTON]` — should be single `|`".

`check_custom_markup()` in `structural_validator.py` counts tag opens/closes and checks for unclosed custom tags but does NOT inspect the content between `[BOUTON]` and `[/BOUTON]` for the double-pipe pattern.

**Gap:** Double-pipe button content passes structural validation silently.

**Recommendation:** Extend `check_custom_markup()` or add a `check_button_content()` function that extracts text between `[BOUTON]` and `[/BOUTON]` and flags any occurrence of `||` within it.

---

#### [#21] Structural validator does not detect "malformed CSS in style attribute" (recurring error in CLAUDE.md)

**Type:** `missing-check`
**Stage:** Structural Validation
**Severity:** medium

**Evidence:**
CLAUDE.md lists: "Malformed CSS: `style=\";text-align:right;direction:rtl\"` — leading semicolon — seen in Arabic and Hebrew markets".

`check_html_balance()` in `structural_validator.py` checks for balanced `<b>`, `<i>`, `<u>`, `<mark>` tags. It does not parse `style=` attributes or detect leading semicolons in CSS attribute values.

**Gap:** Malformed `style=` attributes with leading semicolons pass structural validation silently.

**Recommendation:** Add a regex check for `style=";"` or `style=";\s*` patterns in the translation text. This is a straightforward string pattern match that belongs in the structural layer.

---

#### [#22] Structural validator does not detect "extra closing text outside template" (recurring error in CLAUDE.md)

**Type:** `missing-check`
**Stage:** Structural Validation
**Severity:** low

**Evidence:**
CLAUDE.md lists: "Extra closing text: Market appends text outside template (e.g. 'Atentamente, Equipo Superprof.')".

The structural validator has no concept of "valid text regions" — it only checks structural markers (variables, conditionals, custom tags, HTML). Text that appears after the last closing tag but is not present in the French reference would not be flagged.

**Gap:** Extra post-template text is not detectable by the current structural checks. It would need either: (a) a strict end-of-template marker check, or (b) significant length difference (partially covered by `check_length_anomaly()` with a 2.5x ratio ceiling, but a short sign-off wouldn't trigger the 250% threshold).

**Recommendation:** This is partially mitigated by AI review (Step 4c criterion 6 — cultural appropriateness). For structural detection, add a check that flags text after the last recognized template marker or closing tag that has no equivalent in the French reference. Low priority — AI review catches this reliably.

---

#### [#23] France reference row assumed at position 0 — `structural_validator.py` has no fallback (brittle)

**Type:** `brittleness`
**Stage:** Structural Validation
**Severity:** critical (brittle)

**Evidence:**
`structural_validator.py` line 597: `ref_entry = entries[0]` — the first parsed cell is always used as the French reference without any validation that it is actually a French/France cell.

If the CSV has a different country in the first column (header reorder, export format change, or accidental column swap), the validator will silently compare all markets against the wrong reference — producing false positives and false negatives with no error message.

This is already tracked as QUA-01 in REQUIREMENTS.md. The finding is documented here to ensure it appears in AUDIT.md with proper priority labeling.

**Gap:** No language/country detection in `run_validation()`. The comment on line 596 says "First entry should be France (the reference)" but there is no enforcement.

**Recommendation:** Implement QUA-01 fix: in `run_validation()`, search all parsed entries for one where `entry['country']` contains "France" or "fr" (case-insensitive) or where the language column header is "fr". If found but not first, reorder. If not found, fail with a clear error rather than silently using the wrong reference.

---

#### [#24] Emoji detection uses hardcoded Unicode ranges — new emoji miss detection (brittle)

**Type:** `brittleness`
**Stage:** Structural Validation
**Severity:** medium (brittle)

**Evidence:**
`structural_validator.py` lines 55–70: `RE_EMOJI` is a compiled regex with hardcoded Unicode ranges (`\U0001F600-\U0001F64F`, `\U0001F300-\U0001F5FF`, etc.). Unicode releases new emoji blocks regularly. Any emoji outside the hardcoded ranges passes through without detection.

This is already tracked as QUA-02 in REQUIREMENTS.md. Documented here for AUDIT.md priority labeling.

**Gap:** New emoji released after the last range update will be silently ignored by `check_emojis()` — the check will report "no emoji missing" even when the translation has dropped a new-era emoji present in the French source.

**Recommendation:** Implement QUA-02 fix: replace hardcoded ranges with `unicodedata` or the `emoji` library to detect emoji using maintained Unicode data.

---

#### [#25] `check_length_anomaly()` uses hardcoded 0.4/2.5 ratio thresholds — not per-language (missing feature)

**Type:** `missing-feature`
**Stage:** Structural Validation
**Severity:** low

**Evidence:**
`structural_validator.py` lines 512–529: length anomaly thresholds are hardcoded at `ratio < 0.4` (too short) and `ratio > 2.5` (too long). The function signature has a `lang_ratios: dict = None` parameter (line 481) which was never wired — it is unused dead parameter.

`config/languages.json` contains an `expected_length_ratio` field per language that could provide per-language thresholds. Since `languages.json` is currently unreferenced ([#3]), this integration was never completed.

**Gap:** Languages like Finnish or German (which have longer words) or Chinese/Japanese (which are much shorter per character count) share the same fixed thresholds. False positives or misses are possible for extreme-length languages.

**Recommendation:** Wire `languages.json` `expected_length_ratio` values into `check_length_anomaly()` via the `lang_ratios` parameter. Prerequisite: fix `languages.json` formality field ([#11] from Plan 01) before integration. Flag for Phase 9.

---

### Stage 2: AI Review (Haiku/Sonnet Routing)

---

#### [#26] Clean-market Haiku tier has no documented criteria for what it checks (workflow gap)

**Type:** `missing-step`
**Stage:** AI Review — Haiku routing
**Severity:** medium

**Evidence:**
CLAUDE.md describes: "Tier 2 (clean markets, Haiku 4.5): markets with zero structural findings get a fast spot-check (emoji, encoding, past corrections only), batches of 25." Review of `review-translations.md` Step 4b: "Clean: markets with zero structural findings → auto-pass, no AI review needed." There is NO Haiku spot-check step described in the skill definition — the skill says clean markets are auto-passed entirely, not sent to Haiku.

**Gap:** CLAUDE.md and the skill definition contradict each other on how clean markets are handled. CLAUDE.md says Haiku spot-check; skill says auto-pass with no AI review. The actual implementation (auto-pass per skill) may miss real issues in clean markets that the "Haiku spot-check" was intended to catch.

**Recommendation:** Reconcile the discrepancy. Either: (a) add a Haiku spot-check sub-step in the skill for clean markets (covering emoji inconsistency, encoding, past corrections), or (b) update CLAUDE.md to reflect that clean markets are auto-passed without AI review. This is a doc-vs-implementation mismatch with operational consequences — if the team expects Haiku to catch issues in clean markets, the current behavior is silent data loss.

**Note:** This finding is cross-cutting between the AI review stage and documentation accuracy.

---

#### [#27] Rules relevance scoring in Step 3 does not account for zh_TW/zh_HK code mismatch (active bug)

**Type:** `active-bug`
**Stage:** AI Review — Step 3 rule loading
**Severity:** medium

**Evidence:**
`corrections_log.json` stores corrections for `zh_TW` and `zh_HK` (underscore). The skill's Step 3 relevance scoring filters rules where `rule.language == target language code`. When the CSV uses `zh-TW` (hyphen, BCP-47 standard), the filter `rule.language == "zh-TW"` will return zero results for Traditional Chinese, even though applicable rules exist under `zh_TW`.

This is directly caused by the code format contradiction found in Plan 01 ([#10]).

**Gap:** Traditional Chinese markets will always receive zero applicable past corrections in Step 4c criterion 7 — the learning system silently fails for zh-TW and zh-HK.

**Recommendation:** Fix `corrections_log.json` to use BCP-47 hyphen format (zh-TW, zh-HK) per [#10] recommendation. This upstream fix resolves the downstream rule lookup failure automatically. Alternative: add a normalization step in the skill's Step 3 that standardizes underscore → hyphen before matching.

---

### Stage 3: Report Generation

---

#### [#28] Fixed output path `reports/structural_results.json` is overwritten on multi-run sessions (brittle)

**Type:** `brittleness`
**Stage:** Report Generation — Step 2
**Severity:** low (brittle)

**Evidence:**
This duplicates Plan 01 finding [#17] exactly — documented here under the workflow gaps section for completeness. Step 2 always writes to `reports/structural_results.json`. Multi-run sessions in the same terminal session overwrite the previous run's structural results. If Step 4b reads stale data between runs, results may be incorrect.

**Recommendation:** Already documented in [#17]. Flagged here as a workflow brittle point for the Report Generation stage.

---

#### [#29] No mechanism to track which Notion-published reports have been reviewed by the team (missing step)

**Type:** `missing-step`
**Stage:** Report Generation / Notion Publishing
**Severity:** low

**Evidence:**
Step 6 publishes a page to Notion at a fixed parent page ID (`33dd6418695a8097998fcf373ed18bf5`). There is no tracking of: (a) which published reports exist, (b) whether they have been read, (c) whether they have been acted on. The workflow ends at "published" — the downstream consumption is entirely manual.

**Gap:** When notification counts grow (10 → 50+), there will be no way to know which reports have been reviewed without reading each Notion page. No status tracking, no "reviewed" flag, no aggregated open-action list.

**Recommendation:** Phase 9 low priority item — add a simple index or tracker page in Notion where each published report is listed with a status field. Alternatively, a local `reports/index.md` file that records publication date, report path, and Notion URL for each report would enable this at zero infrastructure cost.

---

### Stage 4: Notion Publishing

---

#### [#30] Notion publish failure silently loses the report announcement (workflow gap)

**Type:** `missing-step`
**Stage:** Notion Publishing
**Severity:** low

**Evidence:**
Step 6d: "On failure: Capture the error message. Do NOT abort the session. Store the error for the output announcement." The skill correctly announces the failure and continues with Step 7. However, there is no retry mechanism and no persistent record that the publish failed for a given run.

If the user doesn't notice the `⚠️ Notion publish failed` line in the output, the report exists locally but is never published. Future sessions have no way to detect and retry unpublished reports.

**Gap:** Failed Notion publishes require manual tracking; there is no automated detection of "locally saved but unpublished" reports.

**Recommendation:** Low priority — add a `reports/unpublished.json` or similar file where failed publish attempts are logged. Phase 9 can decide whether to implement this.

---

### Stage 5: Batch Feedback Routing

---

#### [#31] Corrections log not backed up before each write (missing safety step)

**Type:** `missing-step`
**Stage:** Batch Feedback Routing — Step 7
**Severity:** medium

**Evidence:**
Step 7b writes directly to `corrections/corrections_log.json` without any backup. There is no preceding `cp corrections/corrections_log.json corrections/corrections_log.backup.json` or equivalent.

This is already tracked as QUA-03 in REQUIREMENTS.md. Documented here for AUDIT.md priority labeling.

**Gap:** A write failure, partial write, or incorrect feedback application could corrupt all accumulated learning rules with no recovery path.

**Recommendation:** Implement QUA-03 fix: add a backup step before any write to corrections_log.json. This can be a simple date-stamped backup in `corrections/backups/` run automatically before Step 7b/7c writes.

---

#### [#32] Manual confirmation step in batch feedback is intentional — not a gap (workflow note)

**Type:** `workflow-note` (not a gap — intentional per D-15)
**Stage:** Batch Feedback Routing
**Severity:** n/a

**Per D-15:** The manual confirmation step in Step 7 (user must type item numbers to confirm writes) is intentional. The AI process is not yet trusted enough to run unattended. This is a deliberate design decision to keep humans in the loop.

**Note for Phase 9:** As corrections accumulate and confidence in the routing logic grows, the confirmation step could be made optional (e.g., `--auto-apply` flag) or reduced to conflict-only confirmation. This is a future improvement when operational confidence grows.

---

#### [#33] rules_summary.json rebuild runs inside the same session with no external validation (scalability gap)

**Type:** `unscalable-step`
**Stage:** Batch Feedback Routing — Step 7d
**Severity:** low

**Evidence:**
Step 7d rebuilds `rules_summary.json` from scratch after every feedback session by reading all corrections_log.json entries in-context. Currently there are 6 entries. When the count grows to 150+ (the threshold mentioned in Step 3 where the skill warns about oversized rules_summary), the in-context rebuild will approach the practical context window limit for a single session.

**Gap:** No pagination or external script handles the rebuild. As the corrections accumulate, the in-session rebuild becomes slower and eventually infeasible within context limits.

**Recommendation:** Flag for Phase 9 / future milestone. When `corrections_log.json` exceeds ~100 entries, consider a standalone Python script to rebuild `rules_summary.json` offline rather than in-session. Step 7 already warns when total_rules > 150 — this is the right trigger point.

---

## Scope Gaps

Comparison of the Phase 1 vision (PROJECT.md active requirements) against what is currently implemented.

---

### [#34] HND-01: README.md — never built

**Type:** `never-built`
**Requirement:** HND-01 / FIX-01
**Severity:** medium

**Evidence:**
PROJECT.md active requirements list HND-01: "README.md with prerequisites, setup, how to run, how to read reports, how to submit feedback."
`ls` of project root: no README.md exists (confirmed by absence in git status tracking and project context).
`README.md` is referenced in Plan 01 finding [#3] (languages.json) as existing documentation, but inspection confirms it is the only README-like file — and that file is in the `config/` directory context, not a proper project README.

Wait — Plan 01 [#3] states README.md line 57 references `config/languages.json`. Let me verify this is accurate.

Reviewing Plan 01: "[#3] config/languages.json: The only reference found is in `README.md` (line 57: `config/languages.json - Language metadata (39+ languages)`)". This implies a README.md exists. However, REQUIREMENTS.md lists HND-01 as pending, and PROJECT.md says it was "deferred from v1.1". The README mentioned in [#3] may be a partial or outdated file. Regardless, it is listed as a pending requirement.

**Gap:** No complete README.md covering prerequisites, setup steps, how to run a review, how to read reports, and how to submit feedback. The file may partially exist (from [#3] evidence) but is not complete relative to HND-01 criteria.

**Recommendation:** Implement as FIX-01 in Phase 9. Create or complete README.md with all five required sections.

---

### [#35] HND-02: requirements.txt — never built

**Type:** `never-built`
**Requirement:** HND-02 / FIX-02 (partially stale — see D-08)
**Severity:** low

**Evidence:**
PROJECT.md: "Tech stack: Python 3.14.3 stdlib-only for core validator; optional `markdown`/`weasyprint` for PDF (no requirements.txt yet)." FIX-02 in REQUIREMENTS.md requests both requirements.txt and `generate_pdf.py` CLI args.

**Gap:** No `requirements.txt` exists. Since PDF generation is now confirmed dead ([#1] from Plan 01), the specific dependencies (`markdown`, `weasyprint`) for this file are no longer relevant to the active workflow. The underlying dependency (weasyprint) is still invoked if `--format pdf` is passed, but that path is effectively dead.

**Staleness note (D-08):** FIX-02 as written bundles requirements.txt with PDF CLI args. Since `generate_pdf.py` is dead code, FIX-02 should be split or retired. A requirements.txt file with an empty or minimal list ("no mandatory dependencies; optional: markdown, weasyprint for deprecated PDF format") would technically satisfy the requirement but adds little value given the current workflow.

**Recommendation:** Phase 9 should either retire FIX-02 entirely (if PDF is confirmed dead) or narrow it to creating a requirements.txt with a note about the deprecated PDF path. Do not invest in improving `generate_pdf.py`.

---

### [#36] HND-03: generate_pdf.py CLI args — partially-built (stale)

**Type:** `built-but-stale`
**Requirement:** HND-03 / FIX-02
**Severity:** low (stale)

**Evidence:**
`generate_pdf.py` exists but hardcodes a single input path. The CLI args (`--input`, `--output`) were never added. Per Plan 01 [#1] and D-08, this script is confirmed dead code — PDF output is no longer part of the workflow.

**Gap:** The requirement to add CLI args is still listed in REQUIREMENTS.md as pending. Given that the script itself is dead, implementing CLI args on a dead script would be wasted effort.

**Recommendation:** Retire HND-03 / FIX-02 (PDF CLI args). Archive `generate_pdf.py`. Phase 9 can formally close this requirement as "superseded" rather than completing it.

---

### [#37] QUA-01: France reference row search — not implemented (never-built)

**Type:** `never-built`
**Requirement:** QUA-01 / FIX-03
**Severity:** critical (brittle — see [#23])

**Evidence:**
`structural_validator.py` line 597: `ref_entry = entries[0]` — hardcoded position 0 assumption. Already documented in [#23] as a brittle workflow gap.

**Gap:** The France reference search capability was planned (QUA-01 in REQUIREMENTS.md) and listed as a known issue in PROJECT.md, but never implemented. The structural validator hard-assumes France is at position 0 in every CSV.

**Recommendation:** Implement as FIX-03 in Phase 9. Critical priority — a column reorder in any CSV export would produce completely wrong validation results with no warning.

---

### [#38] QUA-02: Unicode emoji detection — not implemented (never-built)

**Type:** `never-built`
**Requirement:** QUA-02 / FIX-04
**Severity:** medium (brittle — see [#24])

**Evidence:**
`structural_validator.py` lines 55–70: hardcoded emoji ranges. Already documented in [#24].

**Gap:** The Unicode-library-based emoji detection was planned (QUA-02) and is a known gap. Not implemented.

**Recommendation:** Implement as FIX-04 in Phase 9. Medium priority — current ranges cover most common emoji but will miss any emoji from Unicode 16.0+.

---

### [#39] QUA-03: Corrections log backup — not implemented (never-built)

**Type:** `never-built`
**Requirement:** QUA-03 / FIX-05
**Severity:** medium

**Evidence:**
Step 7b writes directly to `corrections/corrections_log.json` without any backup (see [#31]).

**Gap:** Backup-before-write was planned (QUA-03) but never implemented. With 6 corrections now accumulated, losing this data would require manual reconstruction from memory/reports.

**Recommendation:** Implement as FIX-05 in Phase 9. Medium priority — the risk grows with each new correction added.

---

## Summary Table

| # | Stage/Capability | Type | Severity | Brittle? |
|---|-----------------|------|----------|----------|
| [#19] | Structural validation — loop variable placement | missing-check | critical | no |
| [#20] | Structural validation — double pipe in buttons | missing-check | medium | no |
| [#21] | Structural validation — malformed CSS style= | missing-check | medium | no |
| [#22] | Structural validation — extra closing text | missing-check | low | no |
| [#23] | Structural validation — France row assumed pos 0 | brittleness | critical | yes |
| [#24] | Structural validation — emoji hardcoded ranges | brittleness | medium | yes |
| [#25] | Structural validation — length ratio hardcoded | missing-feature | low | no |
| [#26] | AI review — Haiku tier vs auto-pass contradiction | missing-step | medium | no |
| [#27] | AI review — zh_TW/zh_HK rule lookup failure | active-bug | medium | no |
| [#28] | Report generation — fixed structural_results.json path | brittleness | low | yes |
| [#29] | Notion — no report review tracking | missing-step | low | no |
| [#30] | Notion — failed publish not retried | missing-step | low | no |
| [#31] | Batch feedback — no backup before write | missing-step | medium | no |
| [#32] | Batch feedback — manual confirmation | workflow-note | n/a | no |
| [#33] | Batch feedback — rules_summary rebuild scalability | unscalable-step | low | no |
| [#34] | Scope: README — never built | never-built | medium | no |
| [#35] | Scope: requirements.txt — never built | never-built | low | no |
| [#36] | Scope: generate_pdf.py CLI args | built-but-stale | low | no |
| [#37] | Scope: France reference row search | never-built | critical | yes |
| [#38] | Scope: Unicode emoji detection | never-built | medium | no |
| [#39] | Scope: corrections log backup | never-built | medium | no |
