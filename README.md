# Translation Quality Review Automation

Automated quality review tool for Superprof notification translations. Reviews translations from French to 39+ languages for grammar, tone, label integrity, and more.

## Quick Start

1. Open this folder in Claude Code
2. Either drop your CSV into `samples/` **or attach it directly in the chat**
3. Run: `/review-translations samples/your_file.csv` (or just `/review-translations` if you attached the file)

That's it. Reports will be generated in `reports/`.

## Requirements

- Claude Code
- Python 3 (pre-installed on macOS)
- No additional packages needed (stdlib only)

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

## Command Options

```
/review-translations samples/file.csv                    # Full review
/review-translations samples/file.csv --languages es,de  # Only Spanish and German
/review-translations samples/file.csv --notification X   # Only notification X
/review-translations samples/file.csv --structural-only  # Skip AI review
```

## Output

One report is generated in `reports/`:
- **By country** (`review-by-country-YYYY-MM-DD.md`): Issues grouped by market, with full **Current text** and **Proposed text** sections for direct copy-paste into the back office

## Learning System

The tool learns from your corrections. When you accept or modify suggested corrections, they're saved to `corrections/corrections_log.json`. Future reviews will check against these learned patterns.

## Project Structure

```
.claude/commands/review-translations.md  - The /review-translations skill
scripts/structural_validator.py          - Python structural validation
config/languages.json                    - Language metadata (39+ languages)
config/tone_guidelines.json              - Tone and formality rules
config/label_patterns.json               - Template variable patterns
corrections/corrections_log.json         - Learned corrections and rules
reports/                                 - Generated review reports
samples/                                 - Drop CSV files here
```
