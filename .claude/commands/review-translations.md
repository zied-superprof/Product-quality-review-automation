---
description: Review translation quality for Superprof notifications. Parses CSV, runs structural validation, performs AI quality review, and generates reports grouped by country and by notification.
---

# Translation Quality Review

You are reviewing Superprof notification translations for quality. Follow these steps precisely.

## Step 0: Parse arguments

The user's message after the command may contain:
- A file path — the CSV to review (can be an absolute path, relative path, or filename only)
- `--languages XX,YY` — optional, only review these language codes
- `--notification ID` — optional, only review this notification
- `--structural-only` — optional, skip AI review and only run structural checks
- `--format md|pdf` — optional, controls report output. Default: `md` (writes .md only). `pdf` writes .md + .pdf (requires weasyprint). If an unrecognized value is passed, print: `Unknown format "[value]". Valid options: md, pdf` and abort.

**Resolving the file path** (try in order):
1. If the user passed a path and it exists — use it directly.
2. If the user passed a filename only (e.g. `relance_3.csv`), check `samples/[filename]`.
3. If the user attached a file in the chat (IDE attachment or dropped file), use that file's path. Copy it to `samples/` with `cp [attached_path] samples/[filename]` so it's available for the validator.
4. If no file is identified, list the CSV files in `samples/` and ask the user which one to review.

Never default to a previously reviewed file or hardcoded path.

## Step 1: Identify and parse the CSV

Read the first 5 rows of the CSV file to determine:
1. **CSV type**: Is this a "per-notification" CSV (one notification, all languages as columns) or a "full-database" CSV (all notifications x all languages)?
2. **Column structure**: Identify which columns contain language codes, the French source, notification IDs, etc.
3. **Variable format**: Identify the template variable syntax used (e.g., `{{var}}`, `%{var}`, `{var}`)

If the variable format hasn't been seen before, update `config/label_patterns.json` with the discovered pattern.

Report to the user: "Found [X] notifications across [Y] languages. CSV type: [type]. Variable format: [format]."

**Reference file health check** — Before proceeding to Step 2, verify all three config files load successfully:
1. Read `config/Variables.csv` — count rows starting with `@TPL_` (these are the valid variables).
2. Read `config/tone_guidelines.json` — count distinct language codes across `formal_vous_languages.languages`, `informal_standard_languages.languages`, and `neutral_languages.languages` (deduplicated).
3. Read `config/label_patterns.json` — confirm the file parses as valid JSON.

Print a single status line:
`Reference files: Variables.csv ([N] vars) ✓ | tone_guidelines.json ([M] languages) ✓ | label_patterns.json ✓`

Where [N] is the count of `@TPL_*@` rows in Variables.csv, and [M] is the total distinct language codes across all three formality lists in tone_guidelines.json.

**If any file fails to load or is missing, abort immediately** with:
`ABORT: [filename] not found or failed to parse. Cannot proceed with review.`
Do NOT continue to Step 2.

**Notification ID extraction** — Extract the notification identifier for use in the report filename:
1. If `--notification` was passed, use that value as the notification ID.
2. Otherwise, look for a column in the CSV header that contains "notification" (case-insensitive). If found, use the value from the first data row.
3. If no notification column exists, derive the ID from the CSV filename: strip the `.csv` extension, strip any path prefix.
4. Sanitize the ID for filenames: lowercase, replace spaces and slashes with hyphens, strip characters that are not alphanumeric or hyphens.

Store the sanitized notification ID for use in Step 6 filename generation.

## Step 2: Run structural validation

Execute the Python structural validator:
```bash
python3 scripts/structural_validator.py --input [CSV_PATH] --type [per-notification|full-database] --config-dir config/ --output reports/structural_results.json
```

Read the JSON output and summarize: "Structural validation complete: [X] errors, [Y] warnings, [Z] info items."

## Step 3: Load learned rules

Read `corrections/rules_summary.json`.

If the file does not exist or is empty, skip this step silently — no rules to apply.

If `total_rules` exceeds 150, log one line: "rules_summary.json has grown large ([N] rules) — consider pruning low-confidence entries."

**Relevance scoring** (per D-13):

For each rule in the `rules` array, compute:
- `confidence_score`: high = 1.0, medium = 0.75, low = 0.5
- `recency_weight`: calculate days between today and `last_seen`:
  - 0-30 days -> 1.0
  - 31-90 days -> 0.8
  - 91+ days -> 0.6
- `relevance_score` = `occurrence_count` x `recency_weight` x `confidence_score`

**Per-language rule selection** (per D-14, D-16):

For each language in the review batch:
1. Filter rules where `rule.language` == target language code. Score and sort descending by `relevance_score`. Take top-5 (per D-16 cap).
2. If fewer than 3 language-specific rules: pad with the highest-scoring rules where `rule.language` == `"all"` (scored with the same formula), until 3 total rules reached — or all available if fewer than 3 exist total.
3. The top-3 from this combined list become additional review criteria in Step 4c criterion 7 ("Past corrections").

**Output** (per D-15): Rules are loaded silently — no per-language announcement. After all languages processed, if any rules were loaded, output one line: "Applying [N] learned rules from previous reviews."

## Step 4: AI quality review

### 4a — Review French reference

Before reviewing any translation, check the French reference (France cell) for:
1. **Word-level typos** — misspelled words, missing accents, doubled letters, wrong homophones
2. **Variable name typos** — transposed or missing characters in `@TPL_*@` variable names (e.g. `@TPL_PREF_PRENOM@` instead of `@TPL_PROF_PRENOM@`), or malformed conditional tag names
3. **Minor wording/grammar issues** — grammatical errors in the French source itself

If any issues are found, output them as a JSON array using the same issue format (with `"market": "France"` and `"lang": "fr"`). These will appear in the report under the French reference section.

If the French reference is clean, proceed silently.

### 4b — Triage

Using the structural validator output from Step 2, split all markets into:

- **Flagged**: markets with any structural error or warning → full AI review below
- **Clean**: markets with zero structural findings → auto-pass, no AI review needed

Report: "Flagged (full review): [N] markets. Clean (auto-pass): [M] markets."

If `--languages` or `--notification` filters are set, treat all filtered markets as flagged.

### 4c — Full review of flagged markets (inline, sequential)

Read `config/review_rules_compact.md` once.

Work through each flagged market **inline in this conversation** — no subagents, no batching. For each market, evaluate the 7 criteria below and **append all issues to `ai_findings`** (a running flat list held in memory). Do NOT output JSON arrays to the conversation. Instead, output one progress line per market:

"Reviewed [Country] ([lang]) — [N] issues found."

**Criteria to check per market:**
1. Grammar — correct in the target language?
2. Tone and formality — matches Superprof voice? Load `config/tone_guidelines.json`. For this market's language code:
   - If language is in `formality_rules.formal_vous_languages.languages`: market MUST use formal address (vous/Sie/usted/Lei/etc.). If informal address detected, emit a Warning finding: `{"severity": "warning", "category": "tone", "issue": "Formality deviation: [market] uses informal address but tone_guidelines.json specifies formal (formal_vous_languages)"}`
   - If language is in `formality_rules.informal_standard_languages.languages`: informal address is the Superprof brand standard for this market. Do NOT flag informal usage as an error or warning.
   - If language is in `formality_rules.neutral_languages.languages` (en, ga, sw): polite register, no formal/informal distinction to check.
   - If language is not found in any list: do not flag formality — the language has no configured standard.
   Also check general Superprof tone (friendly, encouraging) per `config/review_rules_compact.md`.
3. Natural expression — sounds natural to a native speaker, not overly literal?
4. Label correctness — all @TPL_*@ variables preserved? Apply subject variable rules exactly.
5. Emoji consistency — same emoji as French source, same positions?
6. Cultural appropriateness — anything inappropriate or confusing in the target market?
7. Past corrections — apply the top-3 rules loaded in Step 3 for this language. Flag if the translation repeats a known past error.

**Issue schema** (each object appended to `ai_findings`):
```json
[{"market":"...","lang":"...","severity":"error|warning|suggestion","category":"grammar|tone|label|cultural|emoji|encoding|format","issue":"...","original_fr":"...","current_translation":"...","suggested_fix":"..."}]
```

After all markets are reviewed, output a summary line: "AI review complete: [N] markets reviewed, [M] total issues found." The `ai_findings` list is the AI findings set for Step 5.

## Step 5: Merge results

Combine structural validator findings with AI review findings. Deduplicate (don't re-flag issues caught by both). Assign priority:
- **Error**: Missing variables, broken labels, encoding issues
- **Warning**: Grammar mistakes, wrong formality level, missing emoji
- **Suggestion**: Tone improvements, more natural phrasing, style preferences

## Step 6: Generate reports

Generate one Markdown report file in `reports/`:

### Report filename and output

**Filename**: `reports/review-[notification-id]-YYYY-MM-DD.md` (and `.pdf` if `--format pdf`)

Where `[notification-id]` is the sanitized ID from Step 1, and `YYYY-MM-DD` is today's date.

**Output behavior by --format flag:**
- `md` (default): Write the Markdown report to `reports/review-[id]-[date].md`. Tell the user: "Report generated at `reports/review-[id]-[date].md`"
- `pdf`: Write .md, convert to .html internally (not announced), then convert to .pdf using weasyprint. If weasyprint is not installed, print: "PDF generation requires weasyprint. Install with: pip install weasyprint" and fall back to md behavior. Tell the user: "Report generated at `reports/review-[id]-[date].pdf` (Markdown source: `.md`)"

**MD-to-HTML conversion step** (runs only for `pdf` format — HTML is an internal intermediate, not announced as output):
After writing the .md file, run an inline Python snippet:
```python
import markdown
from pathlib import Path

md_content = Path("[md_path]").read_text(encoding="utf-8")
body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

css = """
  body { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; font-size: 11pt; line-height: 1.65; color: #1a1a2e; max-width: 800px; margin: 0 auto; padding: 32px 40px; }
  h1 { font-size: 20pt; font-weight: 700; color: #0f3460; border-bottom: 3px solid #e94560; padding-bottom: 8px; margin-top: 0; }
  h2 { font-size: 13pt; font-weight: 700; color: #ffffff; background: #0f3460; padding: 6px 12px; margin-top: 24px; border-radius: 3px; }
  h3 { font-size: 11pt; font-weight: 600; color: #0f3460; margin-top: 16px; border-left: 4px solid #e94560; padding-left: 8px; }
  h4 { font-size: 10pt; font-weight: 600; color: #333; font-style: italic; margin-top: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 9pt; margin: 12px 0; }
  th { background: #0f3460; color: white; padding: 5px 8px; text-align: left; font-weight: 600; }
  td { padding: 4px 8px; border-bottom: 1px solid #e0e0e0; vertical-align: top; }
  tr:nth-child(even) td { background: #f8f9fc; }
  blockquote { border-left: 3px solid #e94560; margin: 10px 0; padding: 5px 12px; background: #fff5f5; color: #555; font-style: italic; }
  code { background: #f0f0f0; padding: 1px 4px; border-radius: 3px; font-family: 'Courier New', monospace; font-size: 9pt; }
  pre { background: #f6f8fa; padding: 12px; border-radius: 4px; overflow-x: auto; font-size: 9pt; }
  strong { color: #0f3460; }
  hr { border: none; border-top: 1px solid #ddd; margin: 16px 0; }
  ol, ul { padding-left: 20px; }
  li { margin-bottom: 4px; }
  @media print { body { max-width: 100%; padding: 0; } h2 { -webkit-print-color-adjust: exact; print-color-adjust: exact; } th { -webkit-print-color-adjust: exact; print-color-adjust: exact; } tr:nth-child(even) td { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
"""

html = f"<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n<title>Translation Quality Review</title>\n<style>{css}</style>\n</head>\n<body>\n{body}\n</body>\n</html>"
Path("[html_path]").write_text(html, encoding="utf-8")
```
Replace `[md_path]` and `[html_path]` with the actual report paths.

**Section order is FIXED — every report must use these sections in this exact order, regardless of findings:**

1. **Summary table** — always present, shows all markets with their error/warning/suggestion counts (even if all zeros)
2. **French reference** — ALWAYS present, even when the reference is clean. Shows verbatim French title and body. If Step 4a found issues, the "French reference issues" sub-section appears below; if clean, only the verbatim text is shown.
3. **Grouped sections** — markets with identical corrections grouped together. If no groups exist, omit this section entirely (do not show an empty group header).
4. **Single-market sections** — markets with unique corrections. If none, omit.
5. **Markets with no issues** — always present. List all clean markets together as a comma-separated group under a single `## Markets with no issues` header. If every market has issues, show: `## Markets with no issues\nNo issues found.`
6. **Undefined variables** — shown ONLY when the structural validator returned `variable_undefined` findings (per D-07). If all variables are recognized, omit this section entirely.

**Empty section rule (per D-17):** Sections 1, 2, and 5 are always present. If section 5 has no clean markets, display `No issues found.` under the header. Sections 3, 4, and 6 are conditional — they appear only when relevant findings exist; they are not shown with "No issues found." when empty.

#### Grouping rule
Before writing the report, identify corrections that are **exactly identical** across multiple markets (same issue, same fix, same variables). Group those markets into a single section. If markets share an issue type but differ in details (e.g. some also have an accent typo, one has an extra spelling error), split into sub-groups — do not over-merge.

#### Item numbering
Every flagged item (Error, Warning, Suggestion) gets a sequential `**[#N]**` tag, counting globally across the entire report. These numbers are used in the feedback loop in Step 7.

```markdown
# Translation Quality Review - By Country
**Date**: [date] | **Input**: [filename] | **Notifications reviewed**: [count]

## Summary
| Country | Language | Errors | Warnings | Suggestions |
|---------|----------|--------|----------|-------------|
| ...     | ...      | ...    | ...      | ...         |

---

## French reference (France)
**Title**: [verbatim French title — all variables, emoji, markup exactly as in CSV]
**Body**: [verbatim French body — all variables, emoji, markup exactly as in CSV]

<!-- FRENCH REFERENCE ISSUES: verbatim title and body above are ALWAYS shown. The issues sub-section below is conditional — include only if Step 4a found issues, omit if clean. -->
### ⚠️ French reference issues
> These issues are in the France source text itself and will affect all markets until corrected.

**[#N]** — [Category]
- **Issue**: [what's wrong]
- **Current**: [exact text with error]
- **Suggested fix**: [corrected text]

---

<!-- GROUPED SECTION (use when 2+ markets have exactly the same correction) -->
## [Descriptive group label] — [N markets]
**Markets**: Country1, Country2, Country3, ...

### Errors / Warnings / Suggestions
**[#N]** **[Notification ID]** — [Category]
- **Issue**: [what's wrong]
- **Original (FR)**: [French source text]
- **Current**: [current translation]
- **Suggested fix**: [proposed correction]

### Current text (representative — [Country])
**Title**: [verbatim title]
**Body**: [verbatim body — all variables, emoji, markup exactly as in CSV]

### Proposed text
> **MANDATORY — Empty translations**: If the current text is completely empty (blank title AND blank body), you MUST generate a full AI translation from the French source. Do NOT write "pending" or defer to the translation team. Use the target language and market context. Mark every generated field:
> **Title**: [AI-generated title] `[AI-proposed — human review required]`
> **Body**: [AI-generated body] `[AI-proposed — human review required]`

**Title**: [corrected title]
**Body**: [corrected body — variables and markup preserved, only text corrected. Add `[verify]` for uncertain fixes.]
*(identical fix applies to all markets in this group)*

---

<!-- SINGLE-MARKET SECTION (use when a market's correction is unique) -->
## [Country Name] ([CODE]) — [Language] ([lang_code])

### Overview
[Brief description of what changes are proposed for this market]

### Errors / Warnings / Suggestions
**[#N]** **[Notification ID]** — [Category]
- **Issue**: [what's wrong]
- **Original (FR)**: [French source text]
- **Current**: [current translation]
- **Suggested fix**: [proposed correction]

### Structural Errors
[bullet list from validator, if any]

### Current text
**Title**: [verbatim title]
**Body**: [verbatim body]

### Proposed text
> **MANDATORY — Empty translations**: If the current text is completely empty (blank title AND blank body), you MUST generate a full AI translation from the French source. Do NOT write "pending" or defer to the translation team. Use the target language and market context. Mark every generated field:
> **Title**: [AI-generated title] `[AI-proposed — human review required]`
> **Body**: [AI-generated body] `[AI-proposed — human review required]`
>
> If only structural errors with no text corrections possible (translation exists but has broken variables):
> `Proposed text: pending — structural variables must be restored before a clean version can be drafted`
>
> If no issues (good quality): include Current text only — no Proposed text.

**Title**: [corrected title]
**Body**: [corrected body — variables and markup preserved, only text corrected. Add `[verify]` for uncertain fixes.]

---

<!-- CLEAN MARKETS: always present. If no clean markets exist, show "No issues found." -->
## Markets with no issues
[Comma-separated list of clean markets, or "No issues found." if all markets had findings]

<!-- UNDEFINED VARIABLES SUMMARY (only include if structural validator returned variable_undefined findings) -->
## Undefined variables
> These variables appear in translations but are not documented in `config/Variables.csv`. They may be new, undocumented, or deprecated. No action needed in translations — add them to Variables.csv if confirmed valid.

| Variable | Markets |
|----------|---------|
| `@TPL_VARIABLE_NAME@` | Country1, Country2, ... (N markets) |
```

Tell the user about the generated files per the output behavior described above (md default: .md only; pdf: .md + .pdf or fallback message).

## Step 7: Feedback loop

After presenting the report, ask:

"Would you like to give feedback on this review?
1. Give feedback — tell me what I missed, over-flagged, or got wrong, so I can update the rules for future reviews
2. Skip — no feedback needed"

If the user picks **option 1**, show the full numbered index of all flagged items (mirroring the report grouping):

```
Here are all the corrections I proposed. Enter the item numbers you want to give feedback on and what to improve — e.g. `#3 this variable is valid in Arabic`, `#7 tone was correct for this market`:

**ERRORS**
#1. [Country or group] ([lang]) — [brief description]
#2. ...

**WARNINGS**
#N. [Country or group] ([lang]) — [brief description]
...

**SUGGESTIONS**
#N. ...
```

When the user replies with numbers + notes, process each feedback item:

### 7a — Pre-write conflict check (per D-17 through D-20)

Before writing any correction or rule, read these files and check for contradictions:
- `.claude/commands/review-translations.md` — Steps 4c and 3 sections
- `config/label_patterns.json` — if the rule touches variable usage (check `subject_variable_usage_rules`)
- `config/tone_guidelines.json` — if the rule touches formality (check `formality_rules`)

**What counts as a conflict:**
- New rule says "do NOT flag X for language Y" but skill Step 4c says "always flag X" (or vice versa)
- New rule says "use variable A for language Z" but label_patterns.json `subject_variable_usage_rules` says use variable B
- New rule contradicts a formality classification in tone_guidelines.json

**What is NOT a conflict:**
- New rule adds guidance for a case not covered by existing rules (additive rule)
- New rule refines an existing rule without contradicting it

**If conflict detected** — do NOT write. Show:
```
Conflict detected before writing:

New rule:       "[extracted rule text]"
Conflicts with: [filename] [section] — "[existing rule or behavior text]"

Which takes precedence?
1. Write the new rule anyway
2. Discard the new rule
3. Update the existing process instead
```
Wait for user choice before proceeding.

**If no conflict** — proceed silently to write (no confirmation prompt per D-20).

### 7b — Write structured correction entry (per D-07, D-08)

For each feedback item, write ONE entry per market to `corrections/corrections_log.json` > `corrections` array. If a feedback item applies to 5 markets, that is 5 separate entries — each with a single `language` string value (per D-07).

Each entry has exactly these 8 fields:
```json
{
  "language": "[market ISO code — string, not array, e.g. 'ar', 'lt', 'es_AR']",
  "notification_type": "[BO notification ID from this review session, e.g. 'relance_3']",
  "issue_category": "[one of: grammar | tone | label | cultural | emoji | encoding | format]",
  "original": "[the flagged finding text from the report]",
  "corrected": "[the corrected text, OR dismissal reason if false-positive per D-06]",
  "rule_extracted": "[generalized rule for future reviews — what should Claude remember]",
  "confidence": "[high | medium | low — set automatically per D-08]",
  "date": "[today's date as YYYY-MM-DD]"
}
```

**Confidence assignment (D-08):**
- `high`: user explicitly confirmed the correction, OR it is a clear structural fact (empty translation, wrong variable for language, broken HTML tag)
- `medium`: correction is valid but context-dependent, involves linguistic nuance, or applies to tone/formality
- `low`: flagged as speculative, needs native speaker verification, or inferred from ambiguous feedback

### 7c — Update config files if applicable

- If the rule touches variable usage -> also update `config/label_patterns.json` > `subject_variable_usage_rules`
- If the rule touches tone/formality -> also update `config/tone_guidelines.json`

### 7d — Rebuild rules_summary.json

Read ALL entries in `corrections/corrections_log.json` > `corrections`. Rebuild `corrections/rules_summary.json` from scratch (per D-10 — full rebuild, no append):

For each correction entry:
1. Check if a rule already exists in the rebuild with same `language` + same `issue_category` + semantically similar `rule_extracted` (per D-11)
2. If match: increment `occurrence_count`, update `last_seen` to the later date, update `confidence` to the highest level seen (high > medium > low)
3. If no match: create new rule entry:
```json
{
  "rule": "[the rule_extracted text]",
  "language": "[language code, or 'all' for universal patterns]",
  "issue_category": "[category]",
  "occurrence_count": 1,
  "confidence": "[confidence level]",
  "first_seen": "[date from correction]",
  "last_seen": "[date from correction]"
}
```

Write the full file:
```json
{
  "generated": "[today's date YYYY-MM-DD]",
  "total_rules": [N],
  "rules": [... all rule entries ...]
}
```

Announce: "Rules summary updated: [N] rules across [M] languages -> corrections/rules_summary.json" (per D-12)

### 7e — Confirm session

"Updated [N] rules. Config files updated: [list or 'none']."
