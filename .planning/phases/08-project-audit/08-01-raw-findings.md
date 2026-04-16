# Phase 08 — Raw Audit Findings
**Plan:** 08-01  
**Date:** 2026-04-15  
**Scope:** Unused/redundant code and config; contradictions across config files, docs, and implementation  
**Status:** Complete — two-task scan

---

## Unused / Redundant Code and Config

---

### [#1] scripts/generate_pdf.py

**Status:** `dead-code`

**File path:** `scripts/generate_pdf.py`

**Evidence:**
- No active caller in `scripts/`, `.claude/commands/review-translations.md`, or `CLAUDE.md` invokes this script at runtime. The skill (Step 6) implements MD-to-HTML conversion inline using copied CSS — it does NOT call `generate_pdf.py` as a subprocess.
- The script hardcodes a single report path: `review-by-country-2026-04-03.md` (lines 7–10). It will crash on any other report name without manual edits.
- Confirmed by user context (08-CONTEXT.md §Specifics): "User confirmed that `generate_pdf.py` / PDF output is no longer part of the process — this is a concrete dead-code finding, not speculative."
- `git log` shows the script was committed in the initial commit (`595d39c`) and has never been updated since.
- REQUIREMENTS.md FIX-02 / HND-03 references adding `--input`/`--output` CLI args to this script, but the current output format (Notion `.md`) makes PDF output unnecessary.

**Stale requirement note:** REQUIREMENTS.md FIX-02 ("generate_pdf.py accepts `--input` and `--output` CLI arguments") references a workflow that no longer applies. This requirement should be reviewed and likely retired in Phase 9 along with the script.

**Recommendation:** Archive to `scripts/archive/generate_pdf.py`. Retire REQUIREMENTS.md FIX-02 / HND-03 as stale.

---

### [#2] scripts/test_summary_flag.py

**Status:** `active-but-stale` (kept as dev utility with caveats)

**File path:** `scripts/test_summary_flag.py`

**Evidence:**
- The script tests the `--summary` flag of `structural_validator.py`. That flag is fully implemented and active (argparse line 651 of structural_validator.py, logic at lines 678–688).
- `git log` shows the script was committed in `96ecc00` (TDD RED phase) and was never updated post-implementation (no GREEN-phase commit touched it). The TDD comment in the file header reads "RED phase: These tests verify expected behavior before implementation" — but the feature is now implemented.
- The script depends on `samples/relance_3.csv` being present to run tests 2–6. This sample file is not guaranteed to exist in all environments.
- No CI pipeline exists; the script must be run manually.
- The script does provide regression coverage: 7 tests covering `--summary` behavior, JSON output, and no-regression paths. This is the only automated test coverage in the project (outside of manual runs).

**Recommendation:** Keep as a dev utility but update the header comment from "RED phase" to reflect its post-implementation status. Note the `samples/relance_3.csv` dependency in the header. Low priority — can be done opportunistically.

---

### [#3] config/languages.json

**Status:** `potentially-unused`

**File path:** `config/languages.json`

**Evidence:**
- Grep across all `.py`, `.md`, and `.json` files in the project finds **zero references** to `languages.json` in any active code file: not in `structural_validator.py`, not in `.claude/commands/review-translations.md`, not in `CLAUDE.md`.
- The only reference found is in `README.md` (line 57: `config/languages.json - Language metadata (39+ languages)`), which is documentation only.
- Step 1 health check in the skill reads `Variables.csv`, `tone_guidelines.json`, and `label_patterns.json` — `languages.json` is not included.
- 08-CONTEXT.md D-06 explicitly flags this: "Config files with no visible reference in the skill definition or Python scripts must be flagged as potentially unused (e.g. `languages.json` is not referenced in CLAUDE.md or `.claude/commands/review-translations.md`)."

**Impact if unused:** The file contains useful data (39+ language codes, formality field, expected_length_ratio per language) that the review skill could use. The `expected_length_ratio` column could improve `check_length_anomaly()` in `structural_validator.py`, which currently uses hardcoded thresholds (0.4 and 2.5) instead of per-language ratios.

**Recommendation:** Integrate into the skill's Step 1 health check (read alongside the other 3 config files) and wire `expected_length_ratio` values into `structural_validator.py`'s length check. If integration is deferred, document the file's purpose and intended use in `CLAUDE.md`. Flag for Phase 9.

---

### [#4] config/review_rules_compact.md

**Status:** `active` (used, but only from within the AI skill — not from Python scripts)

**File path:** `config/review_rules_compact.md`

**Evidence:**
- Referenced in `.claude/commands/review-translations.md` Step 4c: "Read `config/review_rules_compact.md` once." (line 121) and "Also check general Superprof tone (friendly, encouraging) per `config/review_rules_compact.md`." (line 134).
- NOT referenced from `structural_validator.py` (which is stdlib-only and does not read config markdown files) or `CLAUDE.md`.
- The file provides a compact version of variable and formality rules for the AI reviewer to apply in Step 4c.

**Finding:** This file is active and consumed by the skill. No action needed. Noting that it partially duplicates `label_patterns.json` and `tone_guidelines.json` — maintaining both is a sync risk. One instance of confirmed divergence is documented in the Contradictions section below (#7).

**Recommendation:** Keep as-is. Evaluate in Phase 9 whether to auto-generate this compact file from the canonical config sources to eliminate manual sync.

---

### [#5] config/Variables.csv

**Status:** `active` — confirmed referenced

**File path:** `config/Variables.csv`

**Evidence:**
- `structural_validator.py` lines 174–187: `load_valid_variables()` reads this file, and the validator aborts if it is missing (`sys.exit(1)`).
- `review-translations.md` Step 1 health check explicitly reads this file and counts rows.
- Step 7 batch routing reads it to validate variable existence before routing feedback items.

**Recommendation:** No action needed.

---

### [#6] config/label_patterns.json and config/tone_guidelines.json

**Status:** `active` — confirmed referenced

**File path:** `config/label_patterns.json`, `config/tone_guidelines.json`

**Evidence:**
- `label_patterns.json`: Read in Step 1 health check, Step 4c criterion 4 (label correctness), Step 7 routing.
- `tone_guidelines.json`: Read in Step 1 health check, Step 4c criterion 2 (formality), Step 7 routing.
- `structural_validator.py` does NOT read either (it is stdlib-only and uses hardcoded regex patterns), but the skill reads them for the AI review phase.

**Recommendation:** No action needed.

---

### [#7-archive] reports/ — Archiving Procedure

**Status:** Mixed — 3 active output types, 3 stale categories

**File path:** `reports/`

**File inventory (27 files):**

| Category | Files | Status |
|----------|-------|--------|
| Active `.md` reports | review-annonce-valide-sans-photo-2026-04-10.md, review-by-country-2026-04-03-relance3.md, review-by-country-2026-04-03.md, review-by-country-2026-04-07.md, review-by-country-2026-04-08.md, review-by-country-pass-eleve-nouveau-2026-04-07.md, review-by-country-relance3-2026-04-03.md, review-by-notification-2026-04-03.md, review-inscription-membre-2026-04-14.md, review-inscription-membre-sms-2026-04-10.md, review-mer_prof_nouvelle_demande-2026-04-15.md, review-message-nouveau-2026-04-09.md, review-message-nouveau-test-2026-04-09.md, review-message_nouveau-2026-04-14.md, review-message_nouveau_2-2026-04-14.md, review-reco-val-prof-bo-2026-04-08.md | Keep (current outputs) |
| Stale `.html` files | review-by-country-2026-04-03.html, review-message-nouveau-2026-04-09.html, review-message-nouveau-test-2026-04-09.html, review-reco-val-prof-bo-2026-04-08.html | Archive — HTML output format was removed in v1.1 (NTIO-04) |
| Structural JSON intermediates | structural_results.json, structural_results_relance3.json | Archive — intermediate build artifacts, not final outputs |
| One-off analysis files | token-baseline.md, tone-review-for-native-speakers.md | Archive — ad-hoc analysis, not review reports |

**Archiving procedure (runnable shell command):**

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

**Additional note:** The duplicate-named reports (`review-by-country-relance3-2026-04-03.md` and `review-by-country-2026-04-03-relance3.md` appear to be the same review, and `review-message-nouveau-test-2026-04-09.md` vs `review-message-nouveau-2026-04-09.md` is test vs production) are worth archiving the older/test versions but are lower priority.

**Recommendation:** Run the archiving command above. This reduces the active report folder from 27 to 18 files. Consider adding `reports/archive/` to `.gitignore` if report history should not be in version control.

---

## Contradictions

---

### Scan 1 — Internal corrections_log.json contradictions

**Type:** `internal-conflict`

**Finding:** [#8] Occurrence count inflation in rules_summary.json — minor sync drift

**Files involved:** `corrections/corrections_log.json`, `corrections/rules_summary.json`

**Description:**
`rules_summary.json` reports `occurrence_count: 2` for both `hu` and `lt` rules, but `corrections_log.json` contains only **one** entry per language. There are no duplicate entries in corrections_log for these languages.

Evidence — `rules_summary.json` hu entry:
```json
{
  "rule": "Hungarian CTA/button text must use imperative form...",
  "language": "hu",
  "occurrence_count": 2,
  "first_seen": "2026-04-10",
  "last_seen": "2026-04-14"
}
```

Evidence — `corrections_log.json` hu entries: exactly 1 entry (`date: 2026-04-10`). No second entry exists.

Similarly for `lt`: `occurrence_count: 2` in rules_summary, but only 1 entry in corrections_log.

**Root cause:** The `occurrence_count` counter in `rules_summary.json` appears to have been incremented manually or via a script that double-counted during a re-run, without a corresponding second entry being written to `corrections_log.json`.

**Severity:** Low — this inflates confidence scores used in Step 3 rule relevance scoring. Both rules remain valid; the count is the only error.

**Recommendation:** Fix `occurrence_count` to 1 for both `hu` and `lt` entries in `rules_summary.json`. Add a note to the rules_summary rebuild process to count only actual entries in corrections_log rather than incrementing from the current count.

---

**Finding:** [#9] Japanese rule text divergence between corrections_log.json and rules_summary.json

**Type:** `sync-drift`

**Files involved:** `corrections/corrections_log.json`, `corrections/rules_summary.json`

**Description:**
The Japanese rule text differs by a single word between the two files:

`corrections_log.json` rule_extracted:
```
"Japanese: @TPL_MATIERE_DE_MATIERE@ is a French genitive construction and is not configured for Japanese..."
```

`rules_summary.json` rule:
```
"Japanese: @TPL_MATIERE_DE_MATIERE@ is a French genitive construction not configured for Japanese..."
```

The difference is "and is not" vs "not" — semantically identical but technically a string mismatch. This means any exact-string comparison between the two files for the Japanese rule will fail.

**Severity:** Low — the rules are semantically identical and will apply correctly in practice. However, if any downstream tooling does string matching for deduplication or conflict detection, this would cause false misses.

**Recommendation:** Align the rule text in `rules_summary.json` to exactly match the `rule_extracted` field in `corrections_log.json`. The correction should use the corrections_log version as the source of truth.

---

**Finding:** [#10] Corrections_log uses underscore variant codes (zh_TW, zh_HK) while all other config files use hyphen variant codes (zh-TW)

**Type:** `config-mismatch`

**Files involved:** `corrections/corrections_log.json`, `config/label_patterns.json`, `config/tone_guidelines.json`, `config/languages.json`

**Description:**
Language codes for Chinese Traditional are inconsistent across files:

| File | Code used |
|------|-----------|
| `corrections/corrections_log.json` | `zh_TW`, `zh_HK` (underscore) |
| `config/label_patterns.json` | `zh-TW` (hyphen) |
| `config/tone_guidelines.json` | `zh-TW` (hyphen) |
| `config/languages.json` | `zh-TW` (hyphen) |

Evidence from `corrections_log.json`:
```json
{"language": "zh_TW", "notification_type": "relance-1", ...}
{"language": "zh_HK", "notification_type": "relance-1", ...}
```

Evidence from `label_patterns.json`:
```json
"do_not_use_for": ["en", "es", "de", "nl", ..., "zh", "zh-TW", ...]
"use_for": ["en", "de", "nl", ..., "zh", "zh-TW", ...]
```

**Impact:** When Step 3 loads rules and tries to match `zh_TW` corrections against `label_patterns.json` rules or when the skill routes feedback for `zh_TW`, the code variant mismatch may cause lookup failures. The rules for `zh_TW` from corrections_log will not be matched against markets that provide `zh-TW` as their language code.

**Severity:** Medium — actual rule application may silently fail for Traditional Chinese markets.

**Recommendation:** Standardize on hyphenated BCP-47 codes (zh-TW) across all files. Update `corrections_log.json` `zh_TW` → `zh-TW` and `zh_HK` → `zh-HK`. Also add `zh-HK` as a language code to `tone_guidelines.json` and `label_patterns.json` if Hong Kong is actively reviewed.

---

### Scan 2 — Corrections vs config cross-check

**Type:** `config-mismatch`

**Finding:** [#11] languages.json formality field contradicts tone_guidelines.json for 12 languages

**Files involved:** `config/languages.json`, `config/tone_guidelines.json`

**Description:**
`languages.json` has a `formality` field per language. For 12 languages, this field says `"formal"`, but `tone_guidelines.json` lists them under `informal_standard_languages`. This is a direct contradiction.

Languages affected (languages.json says "formal", tone_guidelines.json says informal_standard):

| Language Code | languages.json formality | tone_guidelines.json classification |
|---------------|--------------------------|--------------------------------------|
| es | formal | informal_standard_languages |
| de | formal | informal_standard_languages |
| it | formal | informal_standard_languages |
| nl | formal | informal_standard_languages |
| hu | formal | informal_standard_languages |
| ro | formal | informal_standard_languages |
| hr | formal | informal_standard_languages |
| sr | formal | informal_standard_languages |
| sl | formal | informal_standard_languages |
| el | formal | informal_standard_languages |
| ru | formal | informal_standard_languages |
| id | formal | informal_standard_languages |

Evidence — `languages.json` German entry:
```json
{"code": "de", "name": "German", "formality": "formal", "notes": "Uses Sie (formal). Compound words make translations longer."}
```

Evidence — `tone_guidelines.json`:
```json
"informal_standard_languages": {
  "languages": ["sv", "no", "da", "fi", "he", "de", "it", "nl", "ru", "ro", "sr", "bs", "hr", "sl", "el", "hu", "id", "es"],
  "notes": "These languages use informal address as the Superprof brand standard for these markets. Confirmed 2026-04-03."
}
```

**Root cause:** `languages.json` was created early in the project and uses a general linguistic formality (German has "Sie" formal form) rather than the Superprof brand-specific standard (German uses informal "du" per brand policy). `tone_guidelines.json` was updated 2026-04-03 to reflect the confirmed brand standard. `languages.json` was never updated to match.

**Impact:** If any code or AI prompt ever reads formality from `languages.json` instead of `tone_guidelines.json`, it will incorrectly require formal address for de, es, it, nl, hu, ro, and 6 other markets. Since `languages.json` is currently unreferenced (see [#3]), this is not causing active errors, but it is a latent trap.

**Severity:** Medium — no active code impact today, but dangerous if `languages.json` is integrated ([#3] recommendation) without fixing the formality field first.

**Recommendation:** Update `languages.json` formality field for all 12 languages to `"informal"` or add a `"brand_formality"` field that distinguishes Superprof brand standard from linguistic norm. Do this before or concurrently with integrating `languages.json` into the skill.

---

**Finding:** [#12] No corrections_log entries conflict with tone_guidelines.json formality rules

**Type:** `config-mismatch`

**Files involved:** `corrections/corrections_log.json`, `config/tone_guidelines.json`

**Description:**
Scanning all 6 corrections_log entries against the formality classifications in tone_guidelines.json reveals no conflicts. The corrections cover grammar (hu), variable rules (lt, ja, zh_TW, zh_HK), and formatting (all). None touch formality/address form. No action needed.

**Severity:** None.

---

### Scan 3 — Doc-vs-implementation mismatches

**Type:** `doc-vs-implementation`

**Finding:** [#13] CLAUDE.md "known issue" about abbreviated tone_guidelines.json path is now stale/resolved

**Files involved:** `CLAUDE.md`, `.claude/commands/review-translations.md`

**Description:**
`PROJECT.md` (which CLAUDE.md references) notes: "Step 1 health check references abbreviated tone_guidelines.json path (low severity)." However, the current `review-translations.md` Step 1 health check (line 39) uses the full path `config/tone_guidelines.json`:

```markdown
2. Read `config/tone_guidelines.json` — count distinct language codes across `formal_vous_languages.languages`, ...
```

This appears to have been resolved at some point. The "known issue" entry in PROJECT.md is stale.

**Severity:** Low — no operational impact. The note creates confusion during audits.

**Recommendation:** Remove "Step 1 health check references abbreviated tone_guidelines.json path" from PROJECT.md known issues section.

---

**Finding:** [#14] Skill Step 6 PDF flow references `generate_pdf.py` CSS but not the script itself — creates implicit coupling that is now invisible

**Files involved:** `.claude/commands/review-translations.md` (Step 6), `scripts/generate_pdf.py`

**Description:**
Step 6 in the skill (lines 175–199) includes an inline Python snippet with CSS verbatim copied from `generate_pdf.py`. The skill does not call `generate_pdf.py` as a subprocess (by design, per Phase 2 decisions), but the CSS in both files must stay in sync manually. If `generate_pdf.py` is archived (as recommended in [#1]), this invisible dependency becomes an orphaned historical note.

Evidence — skill Step 6 inline conversion CSS opens with:
```python
css = """
  body { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; font-size: 11pt; ...
```

This is byte-for-byte copied from `generate_pdf.py` lines 21–131.

**Severity:** Low — today the CSS is identical in both files. If `generate_pdf.py` is archived, the CSS in the skill becomes the single source of truth (which is cleaner, not worse).

**Recommendation:** When archiving `generate_pdf.py` ([#1]), add a comment in the skill's Step 6 inline CSS noting it is the canonical CSS (not derived from `generate_pdf.py`). No sync concern remains after archiving.

---

**Finding:** [#15] CLAUDE.md describes `generate_pdf.py` as an active script; this is no longer accurate

**Files involved:** `CLAUDE.md`

**Description:**
`CLAUDE.md` project structure section does not mention `generate_pdf.py` in its file listing (it was omitted from the "Project structure" section, which only lists the key files). However, PROJECT.md (the planning document) still lists `generate_pdf.py` as an active script in the codebase description: "~1,001 lines Python across 3 scripts (`structural_validator.py` 695 lines, `generate_pdf.py` 162 lines, `test_summary_flag.py` 144 lines)." This description will be stale once the script is archived.

**Severity:** Low — documentation/planning only.

**Recommendation:** Update PROJECT.md codebase description after archiving `generate_pdf.py` in Phase 9.

---

### Scan 4 — Skill definition vs structural_validator.py behavior

**Type:** `doc-vs-implementation`

**Finding:** [#16] All checks described in skill Step 4c are correctly split between structural (Python) and AI (Claude) layers — no missing implementation

**Files involved:** `.claude/commands/review-translations.md`, `scripts/structural_validator.py`

**Description:**
The skill's two-tier approach is correctly implemented:

| Skill claim | Implemented in |
|-------------|----------------|
| Variable preservation checks | `structural_validator.py` check_variables() + check_variables_catalogue() |
| Conditional block checks (TPL_IF/ELSE) | `structural_validator.py` check_conditionals() |
| Emoji consistency | `structural_validator.py` check_emojis() |
| Custom markup ([LIEN], [TITRE], [BOUTON]) | `structural_validator.py` check_custom_markup() |
| Encoding checks (mojibake, control chars) | `structural_validator.py` check_encoding() |
| Empty/placeholder detection | `structural_validator.py` check_empty_placeholder() |
| Length anomaly detection | `structural_validator.py` check_length_anomaly() |
| HTML tag balance | `structural_validator.py` check_html_balance() |
| Grammar | AI review (Step 4c criterion 1) — not in Python |
| Tone/formality | AI review (Step 4c criterion 2) — not in Python |
| Natural expression | AI review (Step 4c criterion 3) — not in Python |
| Cultural appropriateness | AI review (Step 4c criterion 6) — not in Python |
| Past corrections (top-3 rules) | AI review (Step 4c criterion 7) — not in Python |

No checks are described in the skill but missing from the code. No checks are implemented in the code but undocumented.

**Severity:** None — this scan found no issues.

---

**Finding:** [#17] Skill Step 4b says "Read structural_results.json" but Step 2 writes it to a fixed path with no per-notification scoping

**Files involved:** `.claude/commands/review-translations.md` Step 2, Step 4b

**Description:**
Step 2 always writes the structural results to `reports/structural_results.json` (fixed filename). If the skill is run twice in the same session on different notification files, the second run will overwrite the first file. The current design is single-run per session, so this is not a live bug, but it is a brittleness noted for completeness.

Step 4b reads: "Using the structural validator output from Step 2, split all markets into Flagged / Clean" — this works correctly as long as the file is not overwritten between Step 2 and Step 4b.

**Severity:** Low (brittleness) — no current failure path.

**Recommendation:** Consider using a notification-specific filename for the structural results JSON (e.g., `reports/structural_results-[notification_id].json`) to avoid overwrites. Low priority.

---

**Finding:** [#18] rules_summary.json occurrence_count for Japanese is 1 but corrections_log.json has 0 matching entries (due to rule text divergence from [#9])

**Type:** `sync-drift`

**Files involved:** `corrections/corrections_log.json`, `corrections/rules_summary.json`

**Description:**
As a result of the rule text divergence found in [#9], a programmatic count of corrections_log entries matching the Japanese rule text in rules_summary returns 0. The corrections_log uses "and is not configured" while rules_summary uses "not configured" (missing "and is"). This means any tool that rebuilds rules_summary from corrections_log using exact string matching will lose the Japanese rule entirely.

**Severity:** Medium — if the rules_summary rebuild script runs, it will delete the Japanese rule from rules_summary. The Japanese rule is valid and should be preserved.

**Recommendation:** Fix the text divergence (see [#9]) before any automated rebuild of rules_summary.json.

---

## rules_summary.json Sync Status

**Summary:** `rules_summary.json` is **mostly in sync** with `corrections_log.json` but has three concrete issues:

| Issue | Finding | Impact |
|-------|---------|--------|
| Inflated occurrence_count for hu and lt (2 vs actual 1) | [#8] | Low — minor relevance scoring inflation |
| Japanese rule text divergence (1 word) | [#9] | Medium — will cause loss of Japanese rule on rebuild |
| zh_TW vs zh-TW code format mismatch | [#10] | Medium — rule lookup failures for Traditional Chinese markets |

The generated date (`2026-04-14`) matches the newest correction date in corrections_log, confirming no missed corrections. All 6 rules in corrections_log have a corresponding entry in rules_summary (modulo the text mismatch for Japanese).

---

## Summary Table

| # | Type | File(s) | Status | Severity | Recommendation |
|---|------|---------|--------|----------|----------------|
| [#1] | dead-code | scripts/generate_pdf.py | Dead — hardcoded paths, no active caller | High | Archive; retire FIX-02 |
| [#2] | active-but-stale | scripts/test_summary_flag.py | Active dev utility; header comment stale | Low | Update header comment |
| [#3] | potentially-unused | config/languages.json | Zero references in active code | Medium | Integrate or document |
| [#4] | active | config/review_rules_compact.md | Used by skill Step 4c | Low | Sync risk with canonical configs |
| [#5] | active | config/Variables.csv | Hard dependency in validator | None | No action |
| [#6] | active | config/label_patterns.json, tone_guidelines.json | Actively read by skill | None | No action |
| [#7-archive] | archiving | reports/ (8 stale files) | Stale: 4 HTML, 2 JSON, 2 analysis | Low | Run archiving command |
| [#8] | sync-drift | corrections_log.json / rules_summary.json | Inflated occurrence_count hu/lt | Low | Fix count to 1 |
| [#9] | sync-drift | corrections_log.json / rules_summary.json | Japanese rule text diverges by 1 word | Medium | Align to corrections_log text |
| [#10] | config-mismatch | corrections_log.json vs all other configs | zh_TW vs zh-TW code format | Medium | Standardize to zh-TW |
| [#11] | config-mismatch | languages.json vs tone_guidelines.json | 12 languages: formal vs informal | Medium | Fix languages.json formality field |
| [#12] | config-mismatch | corrections_log.json vs tone_guidelines.json | No conflicts found | None | No action |
| [#13] | doc-vs-implementation | PROJECT.md / skill | Stale "known issue" note about path | Low | Remove from PROJECT.md |
| [#14] | doc-vs-implementation | skill Step 6 / generate_pdf.py | Invisible CSS coupling (mitigated on archive) | Low | Comment in skill after archive |
| [#15] | doc-vs-implementation | PROJECT.md | Codebase description will be stale after archive | Low | Update after Phase 9 |
| [#16] | doc-vs-implementation | skill / structural_validator.py | All described checks correctly implemented | None | No action |
| [#17] | brittleness | skill Step 2 / Step 4b | Fixed output path may be overwritten in multi-run session | Low | Consider per-notification filename |
| [#18] | sync-drift | corrections_log.json / rules_summary.json | ja rule text mismatch will cause rebuild loss | Medium | Fix before any rebuild |
