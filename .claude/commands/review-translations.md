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

## Step 2: Run structural validation

Execute the Python structural validator:
```bash
python3 scripts/structural_validator.py --input [CSV_PATH] --type [per-notification|full-database] --config-dir config/ --output reports/structural_results.json
```

Read the JSON output and summarize: "Structural validation complete: [X] errors, [Y] warnings, [Z] info items."

## Step 3: Load corrections history

Read `corrections/corrections_log.json`. Extract the `rules_summary` section. Filter rules relevant to the languages being reviewed. These become additional review criteria.

If there are relevant learned rules, mention: "Applying [N] learned rules from previous reviews."

## Step 4: AI quality review

### 4a — Triage: split markets into two tiers

Using the structural validator output from Step 2, split all markets into:

- **Tier 1 — Flagged**: markets with any structural error or warning → full review (Sonnet)
- **Tier 2 — Clean**: markets with zero structural findings → spot-check only (Haiku)

Report: "Tier 1 (full review): [N] markets. Tier 2 (spot-check): [M] markets."

### 4b — Tier 2 spot-check (Haiku 4.5, parallel subagents)

Read `config/review_rules_compact.md` and the relevant rules from `corrections/corrections_log.json` once. You will embed them in each subagent prompt.

Split the clean markets into batches of up to 22. Launch **all batches simultaneously** — send a single message with one `Agent` tool call per batch (model: haiku). Do not wait for one batch to finish before launching the next.

Each subagent prompt must follow this template exactly:

```
You are reviewing Superprof notification translations. Check each market for:
1. Emoji consistency — same emoji as French source, same positions
2. Encoding issues — mojibake, broken characters, blank content
3. Past corrections — does this repeat a rule from the corrections history below?

## Rules
[paste full contents of config/review_rules_compact.md]

## Corrections history
[paste relevant rules from corrections_log.json rules_summary]

## Markets to review
[For each market: market name, language code, French title+body, translation title+body]

## Output format
Return ONLY a JSON array of issues found. Return an empty array [] if no issues. No prose, no explanation.
Format: [{"market":"...","lang":"...","severity":"error|warning|suggestion","category":"emoji|encoding|label|grammar|tone|format","issue":"...","suggested_fix":"..."}]
```

After all Haiku subagents return: collect every non-empty result. Markets flagged by any subagent are promoted to Tier 1. Markets with empty arrays remain clean.

### 4c — Tier 1 full review (Sonnet 4.6, parallel subagents)

The Tier 1 pool = original structural flagged markets + any markets promoted from Tier 2 spot-check.

Split the Tier 1 pool into batches of up to 20. Launch **all batches simultaneously** — send a single message with one `Agent` tool call per batch (model: sonnet). Do not run them sequentially.

Each subagent prompt must follow this template exactly:

```
You are doing a full quality review of Superprof notification translations.
French is always the reference. For each market, evaluate all criteria below.

## Rules
[paste full contents of config/review_rules_compact.md]

## Corrections history
[paste relevant rules from corrections_log.json rules_summary]

## Markets to review
[For each market: market name, language code, French title+body, translation title+body, structural validator findings (if any)]

## Criteria to check
1. Grammar — correct in the target language?
2. Tone — matches Superprof voice? Apply formality rules from Rules section exactly.
3. Natural expression — sounds natural to a native speaker, not overly literal?
4. Label correctness — all @TPL_*@ variables preserved? Apply subject variable rules from Rules section exactly.
5. Emoji consistency — same emoji as French source, same positions?
6. Cultural appropriateness — anything inappropriate or confusing in the target market?
7. Past corrections — does this repeat a rule from corrections history?

## Output format
Return ONLY a JSON array of issues found. Return an empty array [] if no issues. No prose, no explanation.
Format: [{"market":"...","lang":"...","severity":"error|warning|suggestion","category":"grammar|tone|label|cultural|emoji|encoding|format","issue":"...","original_fr":"...","current_translation":"...","suggested_fix":"..."}]
```

After all Sonnet subagents return: merge all issues arrays into a single flat list. This is the AI findings set for Step 5.

If `--languages` or `--notification` filters are set, skip triage entirely and run only Tier 1 (Sonnet) on the filtered markets.

## Step 5: Merge results

Combine structural validator findings with AI review findings. Deduplicate (don't re-flag issues caught by both). Assign priority:
- **Error**: Missing variables, broken labels, encoding issues
- **Warning**: Grammar mistakes, wrong formality level, missing emoji
- **Suggestion**: Tone improvements, more natural phrasing, style preferences

## Step 6: Generate reports

Generate one Markdown report file in `reports/`:

### `reports/review-by-country-YYYY-MM-DD.md`

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
**Title**: [corrected title]
**Body**: [corrected body — variables and markup preserved, only text corrected. Add `[verify]` for uncertain fixes.]
*(identical fix applies to all markets in this group)*

> If the current text is empty (no translation exists), generate a translation from the French source using the target language and market context. Mark each generated field with `[AI-proposed — human review required]`:
> **Title**: [AI-generated title] `[AI-proposed — human review required]`
> **Body**: [AI-generated body] `[AI-proposed — human review required]`

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
**Title**: [corrected title]
**Body**: [corrected body — variables and markup preserved, only text corrected. Add `[verify]` for uncertain fixes.]

> If the current text is empty (no translation exists), generate a translation from the French source using the target language and market context. Mark each generated field with `[AI-proposed — human review required]`:
> **Title**: [AI-generated title] `[AI-proposed — human review required]`
> **Body**: [AI-generated body] `[AI-proposed — human review required]`
>
> If only structural errors with no text corrections possible:
> `Proposed text: pending — structural variables must be restored before a clean version can be drafted`
>
> If no issues (good quality): include Current text only — no Proposed text.

---

<!-- CLEAN MARKETS -->
## Markets with no issues
[Comma-separated list]
```

Tell the user: "Report generated at `reports/review-by-country-[date].md`."

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

When the user replies with numbers + notes:
- For each item, extract a rule from the feedback (e.g. "don't flag X for language Y", "correct variable for context Z is W")
- Save the rule to `corrections/corrections_log.json` > `rules_summary`
- If the rule touches variable usage → also update `config/label_patterns.json` > `subject_variable_usage_rules`
- If the rule touches tone/formality → also update `config/tone_guidelines.json`
- Confirm: "Updated [N] rules. Config files updated: [list]."
