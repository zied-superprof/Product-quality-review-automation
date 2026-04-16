# Translation Quality Review Automation

Automated quality review tool for Superprof notification translations. Reviews translations from French to 39+ languages for grammar, tone, label integrity, and more.

## Prerequisites

- **Claude Code** — CLI required to run the `/review-translations` skill. Download at https://claude.ai/download
- **Python 3.10+** — macOS ships with Python 3. On Linux: `sudo apt install python3`
- **Git** — for cloning the project
- **No pip packages required** for core functionality (stdlib only)
- **Optional:** For PDF output (deprecated workflow), install from `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```

## Setup

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd "Product quality review automation"
   ```

2. Open the folder in Claude Code:
   ```bash
   claude
   ```

3. Verify the tool loads correctly — run:
   ```
   /review-translations
   ```
   Claude will prompt you for a CSV file. This confirms the skill is loaded.

4. (Optional) If you need PDF output (deprecated workflow), install the optional dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running a Review

### Option A: Attach the file in chat

Drag your CSV file into the Claude Code chat, then type:
```
/review-translations
```

### Option B: Drop it in samples/

Copy your CSV to the `samples/` folder, then:
```
/review-translations samples/your_file.csv
```

### Command options

```
/review-translations samples/file.csv                    # Full review
/review-translations samples/file.csv --languages es,de  # Only Spanish and German
/review-translations samples/file.csv --notification X   # Only notification X
/review-translations samples/file.csv --structural-only  # Skip AI review
```

### CSV format

The tool accepts two CSV formats:
- **Per-notification**: One notification, all languages as columns. First row = headers (language/country names). Must include a France/fr column as the reference.
- **Full-database**: All notifications x all languages.

The French translation is always the reference — all other languages are compared against it.

## Reading Reports

Reports are saved to `reports/` as Markdown files and optionally published to Notion.

### Report structure

Each report groups findings by country/market. For each market with issues:
- **Severity**: error (must fix), warning (should review), info (minor)
- **Category**: label (template variables), format (whitespace/HTML), grammar, tone, emoji, encoding, empty
- **Current text**: The translation as-is (copy-paste ready)
- **Proposed text**: The suggested correction (copy-paste ready for the back office)

### Numbered findings

Every finding is numbered `[#1]`, `[#2]`, etc. Use these numbers when giving feedback (see below).

### Markets with no issues

Markets that pass all structural and AI checks are listed as "clean" — no action needed.

## Submitting Feedback

After reviewing a report, you can teach the tool by providing feedback. The tool learns from corrections and applies them to future reviews.

### Quick feedback (report items)

Reference findings by number:
```
#3 this variable is actually valid for Spanish
#7 the tone is correct — informal is our brand standard for German
```

### Batch feedback (Language + Issue format)

For feedback from native speakers, use this template:
```
Language: es_AR
Issue: "vos" form is correct for Argentina — do not flag as informal error

Language: de
Issue: "du" is the Superprof brand standard for German — informal is correct
```

### What happens with feedback

- Corrections are saved to `corrections/corrections_log.json`
- Config files (`tone_guidelines.json`, `label_patterns.json`) are updated if the feedback changes a rule
- Future reviews automatically check against learned corrections
- A backup of the corrections log is created before each write

## What it checks

| Check | Type | Description |
|-------|------|-------------|
| Label integrity | Structural | All template variables preserved in translation |
| Emoji consistency | Structural | Same emoji as French source |
| Format validation | Structural | Whitespace, punctuation, HTML tags |
| Length anomalies | Structural | Translation length vs expected ratio |
| Encoding issues | Structural | Mojibake, invalid characters |
| Empty/placeholder | Structural | Untranslated or placeholder text |
| Grammar | AI | Grammatical correctness in target language |
| Tone | AI | Matches Superprof's friendly-formal voice |
| Natural expression | AI | Sounds natural, not machine-translated |
| Cultural fit | AI | Appropriate for target market |

## Learning System

The tool learns from your corrections. When you accept or modify suggested corrections, they're saved to `corrections/corrections_log.json`. Future reviews will check against these learned patterns.

## Project Structure

```
.claude/commands/review-translations.md  - The /review-translations skill
scripts/structural_validator.py          - Python structural validation (stdlib only)
config/languages.json                    - Language metadata (39+ languages)
config/tone_guidelines.json              - Tone and formality rules per market
config/label_patterns.json               - Template variable patterns and rules
config/Variables.csv                     - Canonical variable catalog (788 rows)
config/review_rules_compact.md           - Compact review rules for AI reviewer
corrections/corrections_log.json         - Learned corrections and rules
corrections/rules_summary.json           - Derived per-language rules index
requirements.txt                         - Optional PDF dependencies (deprecated)
reports/                                 - Generated review reports
samples/                                 - Drop CSV files here
```
