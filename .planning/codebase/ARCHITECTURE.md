# Architecture

**Analysis Date:** 2026-04-08

## Pattern Overview

**Overall:** Two-tier modular pipeline with structural validation and AI-driven review

**Key Characteristics:**
- Separation of structural validation (deterministic Python) from linguistic review (AI-driven)
- Learning system via corrections history that accumulates rules across reviews
- Claude-native workflow: Python validator produces JSON, Claude skill handles AI review and report generation
- Reference-based architecture: French is always the golden standard for all comparisons

## Layers

**Structural Layer:**
- Purpose: Deterministic validation of template variables, conditionals, HTML tags, emoji consistency, encoding integrity
- Location: `scripts/structural_validator.py`
- Contains: CSV parser, regex-based pattern extraction, structural checks
- Depends on: Input CSV file, optional Variables.csv catalog
- Used by: AI review layer (flagging), report generation

**AI Review Layer:**
- Purpose: Linguistic and cultural validation of flagged markets using Claude
- Location: `.claude/commands/review-translations.md` (steps 4c, embedded in Claude workflow)
- Contains: Grammar, tone, natural expression, cultural appropriateness checks
- Depends on: Structural findings, learned rules from corrections history, review guidelines
- Used by: Report generation, corrections learning system

**Configuration Layer:**
- Purpose: Domain knowledge and rules for template syntax, formality, subject variables, brand voice
- Location: `config/` directory
- Contains: `label_patterns.json` (syntax definitions, subject variable rules), `tone_guidelines.json` (formality by language), `review_rules_compact.md` (linguistic criteria)
- Depends on: None (read-only, configuration)
- Used by: Structural validator (pattern extraction), AI review layer (rule application)

**Learning System:**
- Purpose: Accumulate corrections and extracted rules from each review for future reference
- Location: `corrections/corrections_log.json`
- Contains: Applied corrections (with before/after), extracted rules, rule summaries by category
- Depends on: User feedback in Step 7 of review workflow
- Used by: AI review layer (filters relevant rules per language) and report generation (historical context)

**Report Generation:**
- Purpose: Translate combined findings into actionable Markdown reports grouped by country and organized by issue type
- Location: `.claude/commands/review-translations.md` (Step 6)
- Contains: Grouped market sections, per-country issues, current text and proposed fixes
- Depends on: Structural findings, AI review findings (merged), learned rules context
- Used by: User for decision-making and corrections feedback

## Data Flow

**Review Execution:**

1. **Input ingestion** → User provides CSV file (attached or dropped in `samples/`)
2. **CSV parsing** → Skill determines type (per-notification or full-database) and column structure
3. **Structural validation** → Python validator extracts variables, conditionals, emoji, custom markup; compares against French reference; outputs JSON with issues and severity
4. **Structural triage** → Skill splits markets into:
   - **Flagged**: Have structural errors/warnings → require full AI review
   - **Clean**: Zero structural findings → auto-pass with light spot-checks only
5. **AI review (flagged only)** → For each flagged market, Claude checks 7 criteria:
   - Grammar correctness in target language
   - Tone match (Superprof voice, formality level)
   - Natural expression (not machine-sounding)
   - Label correctness (variables, conditional placement)
   - Emoji consistency (same as French, same positions)
   - Cultural appropriateness (market-specific sensitivities)
   - Past corrections (repeat violations from learned rules)
6. **Merge findings** → Combine structural + AI findings, deduplicate, assign priority (Error/Warning/Suggestion)
7. **Generate reports** → Create Markdown report with grouped sections, current text, proposed fixes, global item numbering
8. **User feedback** → User corrects issues and provides feedback
9. **Learn from corrections** → Skill extracts new rules, updates `corrections_log.json`

**State Management:**

- **French reference is stateless** — each review compares against the French entry in the current CSV
- **Structural validator output is ephemeral** — not persisted beyond current review (written to `reports/structural_results.json` for audit)
- **Corrections history is persistent** — accumulated in `corrections_log.json`, consulted at start of each review
- **Reports are permanent** — timestamped in filename, retained for audit trail

## Key Abstractions

**CSV Entry:**
- Purpose: Represents one market's translation (or France reference)
- Examples: France row/cell, Germany row/cell, Japan row/cell
- Pattern: Dictionary with keys `country`, `titre` (title), `corps` (body)

**Issue Record:**
- Purpose: Single validation finding
- Examples: Missing variable, incorrect formality, emoji mismatch
- Pattern: Dictionary with `check`, `severity`, `category`, `message`, optional `detail`, optional `variable`, optional `country`

**Grouped Correction:**
- Purpose: Single fix that applies to multiple markets with identical translation error
- Examples: "All Arabic markets use wrong loop variable @TPL_MATIERE_DE_MATIERE@"
- Pattern: Markdown section combining all markets that share exact same error + fix

**Learned Rule:**
- Purpose: Extracted pattern from user-accepted corrections for reuse
- Examples: "In Russian, past tense verbs must match gender of subject", "Spanish subject variable rule: use @TPL_MATIERE_DE_MATIERE@ for declension, not @TPL_MATIERE_FIRST_MAJUS@"
- Pattern: JSON record in `corrections_log.json` with rule category, languages affected, description, examples

## Entry Points

**CLI Entry (Structural Validator):**
- Location: `scripts/structural_validator.py` → `main()`
- Triggers: `python3 scripts/structural_validator.py --input [CSV] --output [JSON]`
- Responsibilities: Parse CSV, run all structural checks, output JSON results, print summary to stderr

**Skill Entry (Review Workflow):**
- Location: `.claude/commands/review-translations.md`
- Triggers: `/review-translations [samples/file.csv] [optional flags]`
- Responsibilities: Orchestrate entire pipeline (steps 1–9), execute Python validator, perform AI review, generate report, learn from feedback

**Python Library Entry (Import):**
- Location: `scripts/structural_validator.py` → `run_validation(filepath, config_dir)`
- Triggers: Import and call function directly
- Responsibilities: Provide programmatic interface for batch validation without CLI overhead

## Error Handling

**Strategy:** Fail-fast for structural issues, graceful degradation for AI review, comprehensive logging

**Patterns:**

- **CSV parsing errors:** Validator reports "No country entries found" and returns empty results with error message, allowing skill to ask for clarification
- **Missing variables:** Reported as **error** severity — critical for template integrity
- **Encoding issues:** Reported as **error** severity — breaks email rendering
- **AI review edge cases:** If a market translation is empty, AI layer must generate full translation from French reference with `[AI-proposed — human review required]` label
- **Unclosed conditionals:** Reported as **error** — indicates broken template structure
- **Structural validator crashes:** Skill catches Python subprocess errors, reports to user, allows retry with different file/config
- **Learning system conflicts:** New rule contradicts existing rule in `corrections_log.json` — flag in report, ask user for clarification

## Cross-Cutting Concerns

**Logging:** 
- Structural validator prints summary to stderr upon completion
- Python writes JSON output to file for audit trail
- Skill reports progress inline to user at each step (parsing, validation, triage, review completion)

**Validation:**
- Two-phase: structural (deterministic regex) then AI (linguistic)
- Configuration-driven: all language rules, formality levels, brand voice sourced from JSON config files
- User-configurable: `--languages` flag filters to specific markets, `--notification` flag filters to specific notification, `--structural-only` skips AI review

**Reference Implementation:**
- France entry always first in parsed CSV
- All comparisons (variables, emoji, length) done against France
- French reference itself reviewed for typos in Step 4a before other markets are checked
- Language-specific rules (formality, subject variables) from `config/` only applied to target language, not globally

---

*Architecture analysis: 2026-04-08*
