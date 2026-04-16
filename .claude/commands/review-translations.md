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
python3 scripts/structural_validator.py --input [CSV_PATH] --config-dir config/ --output reports/structural_results.json --summary
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

# Canonical CSS — this is the single source of truth (generate_pdf.py archived)
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

### Notion publish

After writing the .md report to disk, prepare and publish the report to Notion.

**Step 6a — Construct the page title:**

```
Translation Review — [notification_id] — [YYYY-MM-DD]
```

Where `[notification_id]` is the sanitized ID from Step 1 (e.g. `relance_3`) and `[YYYY-MM-DD]` is today's date.

**Step 6b — Adapt .md content for Notion-flavored Markdown:**

Take the .md report content that was just written to disk and apply these transformations to produce the `notion_content` string:

1. **Table conversion**: Convert ALL Markdown pipe-syntax tables to HTML `<table>` format. This includes:
   - The Summary table (Section 1)
   - The Undefined variables table (Section 6, if present)

   Conversion rule: For each pipe-syntax table, produce:
   ```html
   <table>
   <tr><th>Header1</th><th>Header2</th>...</tr>
   <tr><td>Cell1</td><td>Cell2</td>...</tr>
   ...
   </table>
   ```
   Remove the pipe-syntax separator row (`|---|---|`). Each `|`-delimited data row becomes a `<tr>` with `<td>` cells. The header row uses `<th>` cells.

2. **Template variable escaping**: Ensure every `@TPL_*@` variable in the report is wrapped in backtick code spans (`` `@TPL_VARIABLE_NAME@` ``). Most will already be in code spans or code blocks from the .md report. Scan for any bare `@TPL_` occurrences NOT already inside backticks or fenced code blocks and wrap them.

3. **HTML-like template tags**: Ensure square-bracket tags like `[TITRE]`, `[/TITRE]`, `[LIEN]`, `[/LIEN]`, `[BOUTON]`, `[/BOUTON]` in translation body text are wrapped in backtick code spans to prevent Notion from misinterpreting them.

4. **Translation body blocks**: When "Current text" or "Proposed text" sections contain full translation bodies with template tags and variables, wrap the entire body value in a fenced code block (triple backticks) rather than inline code spans, since bodies can be multi-line.

**Step 6c — Publish to Notion:**

Call `mcp__claude_ai_Notion__notion-create-pages` with **exactly** this parameter structure — do not guess or vary the format:

```json
{
  "parent": { "type": "page_id", "page_id": "33dd6418695a8097998fcf373ed18bf5" },
  "pages": [
    {
      "properties": { "title": "<page title from Step 6a>" },
      "content": "<adapted markdown content from Step 6b>"
    }
  ]
}
```

- `parent.type` must be `"page_id"` — never `"workspace"` or any other value
- `parent.page_id` is always `33dd6418695a8097998fcf373ed18bf5` (the "Reports/ planning" page in Notion)
- `pages[0].properties.title` is the string from Step 6a
- `pages[0].content` is the Notion-flavored Markdown string from Step 6b

**Step 6d — Handle result:**

- **On success**: Capture the returned page URL from the tool response. If the response contains a page `id` but no direct URL, construct the URL as `https://www.notion.so/[page_id_without_hyphens]`. Store the URL for the output announcement.
- **On failure**: Capture the error message. Do NOT abort the session. Store the error for the output announcement. The review is still complete — the .md file exists on disk.

**Output announcement:**

After the Notion publish attempt, announce results to the user:

- **Notion success + md format (default):**
  "Report generated at `reports/review-[id]-[date].md`
  Published to Notion: [page URL]"

- **Notion success + pdf format:**
  "Report generated at `reports/review-[id]-[date].pdf` (Markdown source: `.md`)
  Published to Notion: [page URL]"

- **Notion failure (any format):**
  "Report generated at `reports/review-[id]-[date].md`
  ⚠️ Notion publish failed: [error message]. Report saved locally."

After the announcement, proceed to Step 7 regardless of Notion success or failure.

## Step 7: Feedback loop

> **Batch mode available**: This step also works in a fresh session without an active report. Paste feedback items in the Language+Issue format below and the system will route them to the correct config files.

### Collection template

Share this template with the employee gathering native speaker feedback:

---
TRANSLATION FEEDBACK TEMPLATE
Fill in one block per issue. Copy-paste as many blocks as needed.

Language: [ISO code — e.g. es_AR, ar, de, fr]
Issue: [Describe what the AI reviewer got wrong. Was it a false positive? Wrong variable? Wrong tone?]

Language:
Issue:
---

### Step 7 — Batch mode detection

When the user provides input at Step 7, detect the format:

**Batch mode trigger**: User input contains one or more blocks matching the pattern `Language: [code]` followed by `Issue: [text]` (with optional blank lines between blocks). Even a single Language+Issue block triggers batch mode for consistency.

**Single-item mode trigger**: User input contains `#N` patterns (report item numbers like `#3 this variable is valid`). This is the existing flow — proceed to the numbered index display below.

**Ambiguous input**: If the input matches neither format clearly, ask: "Are you giving feedback on specific report items (#1, #2...) or submitting new feedback in Language+Issue format?"

If batch mode is detected, proceed to **Step 7a-batch** (below). If single-item mode, proceed to the existing flow (numbered index display and per-item processing).

### 7a-batch — Batch routing analysis

When batch mode is detected, process the input as follows:

#### Parse batch items

Split the user input into individual items by detecting `Language:` boundaries. For each block:
1. Extract the language code (trim whitespace, accept codes like `es_AR`, `ar`, `de`).
2. Extract the issue text (everything after `Issue:` until the next `Language:` or end of input).
3. If a language field contains multiple comma-separated codes (e.g. `Language: ar, he`), split into separate items — one per code — with the same issue text. Announce: "Item #N applies to [K] markets — creating [K] entries."
4. If a block is missing a `Language:` or `Issue:` field, skip it and warn: "Skipped malformed block: [first 50 chars]..."

#### Route each item

For each parsed item (language, issue_text), determine the routing destination using this decision tree:

1. **Variable mention check**: Does issue_text mention a `@TPL_*@` variable name?
   - YES: Read `config/Variables.csv` and check if the variable exists (search for the exact `@TPL_*@` string in the first column).
     - Variable NOT in Variables.csv → destination: `Variables.csv (flag only)`. Output: `⚠️ Variable @TPL_X@ may be missing from Variables.csv. Verify against BO before adding manually.` (per D-11/D-12). This item does NOT appear in the confirmation batch — it is informational only.
     - Variable IS in Variables.csv AND issue is about which variable to use, correct placement, or per-language variable rules → destination: `label_patterns.json`. Write target: `subject_variable_usage_rules.[VARIABLE_NAME]`.
     - Variable IS in Variables.csv AND issue is about translation quality around a variable (grammar, phrasing) → destination: `corrections_log.json`.
   - NO: continue to step 2.

2. **Formality/tone check**: Does issue_text mention formality, register, tone, or an address form (vos, du, tu, vous, Sie, usted, Lei, informal, formal)?
   - YES → destination: `tone_guidelines.json`. Write target: `formality_rules` (add/move language between `informal_standard_languages.languages`, `formal_vous_languages.languages`, or add to `market_notes`). Also write a corrections_log.json entry if a `rule_extracted` can be derived.
   - NO: continue to step 3.

3. **Default** → destination: `corrections_log.json`. Write as a standard 8-field entry via 7b.

#### Conflict check per item

For each item that has a writable destination (NOT Variables.csv flag-only items), run the same conflict check as 7a-single:
- Read `.claude/commands/review-translations.md` Steps 4c and 3
- If destination is `label_patterns.json`: check `subject_variable_usage_rules` for contradictions with the new rule
- If destination is `tone_guidelines.json`: check `formality_rules` for contradictions
- If destination is `corrections_log.json`: check existing entries for same language + same issue_category for semantic contradiction

Mark each item as `conflict: none` or `conflict: ⚠️ Conflicts with [file] [section] — "[existing rule text]"`.

#### Display block list (per D-04)

Present ALL items as a numbered block list:

```
Batch analysis complete — [N] items parsed:

#1 — [language_code]: [brief issue summary, max 10 words]
  → Routes to: [corrections_log.json | label_patterns.json | tone_guidelines.json | Variables.csv (flag only)]
  → Rationale: [one line — what will change and where]
  → Conflict: [none | ⚠️ Conflicts with [file] [section] — "[existing rule text]"]

#2 — [language_code]: ...
  ...
```

After the block list, show the confirmation prompt:

```
Enter the item numbers you want to apply, separated by commas (e.g. 1, 3).
Items marked ⚠️ must be resolved before they can be included.
Items not listed will be discarded.
Variables.csv flag-only items are informational — they cannot be applied.
```

**Important implementation notes:**
- The `notification_type` field for batch-sourced corrections is `"batch-feedback"` (not tied to a specific CSV review).
- Per D-05, items with conflicts are displayed but excluded from the confirmation set — the user cannot type their number until the conflict is resolved.
- Per D-13, Variables.csv items are flag-only and never appear in the confirmation set.

### 7b-batch — Confirm and apply

When the user responds to the batch confirmation prompt with item numbers:

#### Parse confirmation

Extract the item numbers from the user's reply. Accept formats: `1, 3, 4` or `1 3 4` or `1,3,4`. Ignore any non-numeric text.

**Validation:**
- If a number refers to an item marked with ⚠️ conflict, reject it: "Item #[N] has an unresolved conflict. Resolve it first (see below) or omit it."
- If a number refers to a Variables.csv flag-only item, reject it: "Item #[N] is a Variables.csv flag — it cannot be applied automatically."
- If a number does not correspond to any item in the block list, ignore it silently.
- Items not listed in the confirmation are silently discarded — no pending queue (per D-09).

#### Backup corrections log

Before writing any changes to `corrections/corrections_log.json`, create a timestamped backup:

```bash
cp corrections/corrections_log.json "corrections/corrections_log.backup.$(date +%Y%m%d-%H%M%S).json"
```

This backup runs once per feedback session, before the first write. Do NOT backup before each individual item write.

#### Write confirmed items (one pass, per D-10)

Process each confirmed item in order:

For each confirmed item:
1. **If destination is `corrections_log.json`**: Write a structured entry using the same 7b logic (8-field schema). Use these field values:
   - `language`: the parsed language code from the batch item
   - `notification_type`: `"batch-feedback"`
   - `issue_category`: infer from the issue text (one of: grammar, tone, label, cultural, emoji, encoding, format)
   - `original`: the issue text as submitted by the user
   - `corrected`: the resolution or rule derived from the issue (e.g., "FALSE POSITIVE — vos is Rioplatense brand standard for es_AR")
   - `rule_extracted`: a generalized rule for future reviews
   - `confidence`: assign per 7b rules (high for explicit confirmations and structural facts, medium for linguistic nuance, low for speculative)
   - `date`: today's date as YYYY-MM-DD

2. **If destination is `label_patterns.json`**: Update `subject_variable_usage_rules` using the same 7c logic. Depending on the issue:
   - Add a language code to `use_for` or `do_not_use_for` for the relevant variable
   - Add a `language_notes` entry for the language
   Also write a corrections_log.json entry (step 1 above) to record the rule.

3. **If destination is `tone_guidelines.json`**: Update `formality_rules` using the same 7c logic. Depending on the issue:
   - Add or move a language code between `informal_standard_languages.languages` and `formal_vous_languages.languages`
   - Add a `market_notes` entry if the issue is market-specific (e.g., es_AR vos pattern)
   Also write a corrections_log.json entry (step 1 above) to record the rule.

**Multi-market split**: If a batch item was split into multiple markets during parsing (7a-batch), each market gets its own corrections_log.json entry — one entry per market per item, per the established D-07 rule (language is always a single string).

#### Rebuild rules_summary.json (once)

After ALL confirmed items have been written, run the 7d rebuild logic exactly once:
- Read ALL entries in `corrections/corrections_log.json` > `corrections`
- Rebuild `corrections/rules_summary.json` from scratch (full rebuild, not append)
- Follow the same deduplication and scoring logic as the existing 7d section

Do NOT run 7d after each item — run it once at the end (avoiding Pitfall 2 from RESEARCH.md).

#### Output change summary

After all writes and the rebuild, output a summary:

```
Batch feedback applied:
- [N] corrections written to corrections_log.json
- [M] config updates: [list of files updated, e.g. "label_patterns.json (2 rules), tone_guidelines.json (1 rule)"]
- rules_summary.json rebuilt: [total_rules] rules across [languages] languages
- [K] items discarded (not confirmed)
- [J] items flagged as Variables.csv warnings (informational only)
```

If no items were confirmed (user typed nothing or only invalid numbers), output: "No items confirmed. Batch feedback session ended."

### 7c-batch — Conflict resolution

After the batch apply (7b-batch) completes, if any items were marked with ⚠️ conflicts in the block list:

#### Present conflict details

For each conflicted item, show the full conflict context:

```
Conflict — Item #[N] ([language]: [brief issue]):

New rule:       "[the rule that would be written]"
Conflicts with: [filename] [section] — "[existing rule or config value]"

Let's discuss — what should we do with this conflict?
```

#### Collaborative resolution (per D-06)

Discuss the conflict with the user. There is no fixed menu — the resolution emerges from discussion. Common outcomes include:
- **Write the new rule anyway** (override the existing config): proceed with 7b/7c write for this item, then rebuild 7d.
- **Discard this item**: skip it entirely. Acknowledge: "Item #[N] discarded."
- **Update the existing config instead**: the user may ask to modify the existing rule/config entry rather than add a new one. Make the requested change to the relevant file, then rebuild 7d.

#### After resolution

After each conflict is resolved (or discarded):
- If a write was made, run 7d rebuild once more (single rebuild for all resolved items, not per item).
- Update the change summary with the resolution: "Conflict #[N] resolved: [action taken]."
- If more conflicts remain, present the next one.

When all conflicts are resolved or discarded, output:
"All conflicts addressed. Batch feedback session complete."

If there were no conflicts at all, skip this section entirely — go straight from 7b-batch summary to session end.

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

### 7a-single — Pre-write conflict check (per D-17 through D-20)

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

#### Backup corrections log

Before writing any changes to `corrections/corrections_log.json`, create a timestamped backup:

```bash
cp corrections/corrections_log.json "corrections/corrections_log.backup.$(date +%Y%m%d-%H%M%S).json"
```

This backup runs once per feedback session, before the first write. Do NOT backup before each individual item write.

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

Before rebuilding, backup the current file:
```bash
cp corrections/rules_summary.json "corrections/rules_summary.backup.$(date +%Y%m%d-%H%M%S).json"
```

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
