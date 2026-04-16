# Translation Quality Review Automation

## What this project does
Automated quality review of Superprof notification translations. Notifications are written in French and translated to 39+ languages by human translators. This tool validates translations structurally and linguistically, then generates reports.

## How to use
**Option A — Attach the file in chat:**
Drag the CSV file into the Claude chat, then run:
```
/review-translations
```
The skill will detect the attached file automatically and copy it to `samples/`.

**Option B — Drop it in the samples folder:**
```
/review-translations samples/your_file.csv
```

## Key concepts
- **Two CSV types**: "per-notification" (one notification, all languages as columns) and "full-database" (all notifications x all languages)
- **Template variables**: Translations contain labels/variables that must be preserved exactly (format defined in `config/label_patterns.json`)
- **Language-specific variables**: Some variables are language-specific — see `config/label_patterns.json` > `subject_variable_usage_rules` for per-language subject variable guidance
- **Superprof tone**: Friendly. Formality varies by market — many languages use informal address as brand standard. See `config/tone_guidelines.json` for the full list.
- **French is always the reference**: All translations are validated against the France cell/row

## Project structure
- `scripts/structural_validator.py` — Python structural checks (stdlib only, no pip)
- `config/label_patterns.json` — Template variable syntax, validation rules, and `subject_variable_usage_rules` (which subject variable to use per language)
- `config/tone_guidelines.json` — Brand voice and formality rules per language (includes `informal_standard_languages` list)
- `config/Variables.csv` — Canonical variable catalog (788 rows)
- `config/review_rules_compact.md` — Compact review rules for AI reviewer
- `corrections/corrections_log.json` — Learning system: accumulated corrections and extracted rules
- `corrections/rules_summary.json` — Derived per-language rules index
- `requirements.txt` — Optional PDF dependencies (deprecated — PDF generation script archived)
- `reports/` — Generated review reports
- `samples/` — Drop CSV files here
- `.claude/commands/review-translations.md` — The /review-translations skill definition
- `.claude/settings.local.json` — All bash commands pre-approved (`"Bash"` rule), plus Write access to `reports/`, `corrections/`, `samples/`

## Formality rules (confirmed 2026-04-03)
- **Formal address required**: fr, pt, pl, cs, sk, bg, tr, uk, ja, ko, zh, ar, th, vi, ms and others — see `formal_vous_languages` in tone_guidelines.json
- **Informal address is brand standard**: de, it, nl, ru, ro, sr, bs, hr, sl, el, hu, id, es (and Scandinavian/Finnish/Hebrew) — do NOT flag these as errors
- **Argentina (es_AR)**: uses Rioplatense "vos" — confirmed brand standard

## Subject variable rules (confirmed 2026-04-03)
Full rules in `config/label_patterns.json` > `subject_variable_usage_rules`. Key points:
- **`@TPL_MATIERE_DE_MATIERE@`**: valid for declension/article languages (fr, es, pt, it, ar, pl, sk, cs, ro, ru, el, hu, lt, etc.) when configured in BO. NOT limited to French. Only flag as error for en, de, nl, Nordic, etc., OR if used in wrong structural position (e.g. inside `<TPL_LOOP_ANNONCES>`)
- **`@TPL_MATIERE_FIRST_MAJUS_SMART@`**: correct for English, German, Dutch, Nordic, Japanese, Korean, Chinese, Indonesian, etc.
- **`@TPL_MATIERE_MINUS_SMART@`**: correct for standalone subject name in declension markets (pl, sk, cs, ro, ru, bg, etc.) — preferred over `@TPL_MATIERE_MINUS@` or `@TPL_MATIERE_NOM@`

## Review workflow (optimized)
The skill uses a two-tier model routing strategy:
- **Tier 2 (clean markets, Haiku 4.5)**: markets with zero structural findings get a fast spot-check (emoji, encoding, past corrections only), batches of 25
- **Tier 1 (flagged markets, Sonnet 4.6)**: markets with structural findings get a full 7-point review, batches of 25
- Reports group identical corrections across markets into one section to reduce length
- Every flagged item is numbered `[#N]` globally for use in the feedback loop (Step 7)

## Recurring errors to watch for (seen across multiple notifications)
- **Wrong loop variable**: Arabic markets put `@TPL_MATIERE_DE_MATIERE@` inside `<TPL_LOOP_ANNONCES>` (should be `@TPL_ANNONCE_AFFICHE_QUI_CONNECTE@`) and `@TPL_ANNONCE_AFFICHE_QUI_CONNECTE@` inside `<TPL_IF_LISTE_AVIS>` (should be `@TPL_LISTE_AVIS@`)
- **French compound var in English/CJK title**: `@TPL_MATIERE_DE_MATIERE@` used for English, Chinese, Japanese, Korean — should be `@TPL_MATIERE_FIRST_MAJUS_SMART@`
- **"Tú" typo**: Latin American markets — "Tú" (subject pronoun with accent) used instead of "Tu" (possessive, no accent)
- **Empty translations**: Entire title+body blank — seen in Kazakhstan, Thailand, Russia, South Korea
- **Extra closing text**: Market appends text outside template (e.g. "Atentamente, Equipo Superprof.")
- **Malformed CSS**: `style=";text-align:right;direction:rtl"` — leading semicolon — seen in Arabic and Hebrew markets
- **Double pipe in buttons**: `[BOUTON]...||text[/BOUTON]` — should be single `|`
- **Unclosed `<strong>` tag**: Tag opened but never closed within the same paragraph
- **Wrong template body**: Market cell contains body from a different notification entirely
- **Missing subject variable in title**: English title has no `@TPL_MATIERE_*@` variable at all
- **Inconsistent variable across title/body**: Different subject variable used in title vs. body (e.g. `@TPL_MATIERE_FIRST_MAJUS@` in title, `@TPL_MATIERE_DE_MATIERE@` in body)
