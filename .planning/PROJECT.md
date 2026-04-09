# Translation Quality Review Automation

## Current Milestone: v1.1 — Notion Publishing & Batch Feedback Routing

**Goal:** Connect the review output to the team's Notion workspace and replace the one-at-a-time feedback loop with a batch routing system that suggests where each correction belongs.

**Target features:**
- Automatic Notion publishing on report completion (no manual step)
- HTML output removed; .md stays as local backup
- Batch feedback submission with system-suggested routing (rule / config file update / conflict)

---

## What This Is

An automated quality review tool for Superprof notification translations. French notifications are translated to 39+ languages by human translators; this tool validates those translations structurally and linguistically, then generates correction reports. Reports are automatically published to Notion for the team to review and apply corrections. The feedback loop routes batches of reviewer comments back into the corrections log and config files.

## Core Value

Every review run must produce a reliable, actionable report — fast enough and cheap enough to run on every translation batch.

## Requirements

### Validated

- ✓ Two-tier review pipeline: deterministic structural validation (Python) + AI linguistic review (Claude) — existing
- ✓ French reference validation: all market translations compared against the France cell — existing
- ✓ Variables.csv catalog integration: unknown variables flagged and summarized in reports — existing
- ✓ Two-tier model routing: Haiku for clean markets, Sonnet for flagged markets — existing
- ✓ Learning system: corrections_log.json accumulates rules from user feedback after each review — existing
- ✓ Report generation: grouped Markdown reports with numbered findings, current text, and proposed fixes — existing
- ✓ Undefined variables summary section in reports — existing
- ✓ AI-generated translations mandated for empty entries — existing
- ✓ PDF generation capability (fragile, manual path editing required) — existing
- ✓ Token optimization: Step 4c silent accumulation + `--summary` flag for structural_validator.py — Validated in Phase 01
- ✓ Reference document reliability: structural_validator.py hard-fails on missing Variables.csv; Step 1 health check confirms all 3 config files loaded; Step 4c formality logic explicitly references tone_guidelines.json — Validated in Phase 02
- ✓ Report format: `--format html|md|pdf` flag, notification-ID filenames, HTML output with inline CSS, fixed section order — Validated in Phase 02
- ✓ Notion publishing: report automatically published to Notion on completion; HTML removed as user-facing output, .md kept as local backup — Validated in Phase 05

### Active

- [ ] Batch feedback routing: submit a batch of reviewer comments; system suggests routing action per comment (new rule / config update / conflict); user confirms

### Out of Scope

- Translation generation tool — the long-term goal, but a separate future milestone after this one proves the rule accumulation works
- Web interface — team access via CLI + Notion is sufficient
- Automated CSV correction — tool proposes fixes, humans apply them
- Notion comments → corrections import — feedback still comes back via Juan; future milestone
- Team handoff / README — Juan runs the tool throughout v1.1; deferred
- generate_pdf.py CLI args — HTML removed, PDF less relevant; deferred

## Context

- **Stack**: Python 3.14.3 stdlib-only for core validator; optional `markdown`/`weasyprint` for PDF (undeclared dependencies). No requirements.txt exists yet.
- **Codebase**: 840 lines of Python across 2 scripts (`structural_validator.py` 678 lines, `generate_pdf.py` 162 lines) + 249-line Claude skill definition.
- **Token bottleneck identified**: Step 4c in `review-translations.md` processes markets inline sequentially, accumulating verbose JSON arrays in context window — this is the primary optimization target.
- **Known bug**: CSV parser assumes France is always the first entry. If it isn't, validation compares against the wrong reference market.
- **Config files**: `label_patterns.json` defines template variable syntax and subject variable rules per language. `tone_guidelines.json` defines formality standards per market. `Variables.csv` (788 rows after deduplication) is the canonical variable catalog. All three are read at review start but their influence on AI decisions is not explicitly verifiable.
- **Test coverage**: 0%. All validation is manual.
- **Corrections system**: `corrections/corrections_log.json` accumulates corrections with before/after values and extracted rules, consulted at the start of each review to filter relevant past patterns per language.

## Constraints

- **Tech stack**: Core validator must remain stdlib-only (no pip install for main scripts) — keeps setup simple for team handoff
- **Data locality**: All inputs, outputs, and config stay local — no cloud sync, no external APIs
- **Compatibility**: Must run on macOS without any environment setup beyond Python 3.x
- **Scope**: This milestone is optimization and hardening, not feature expansion

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Silent accumulation for Step 4c | Eliminates token waste from verbose JSON in context; write findings to report file instead | — Pending |
| Evaluate report format before committing to PDF | Token cost of generating PDF vs .md is unknown; team education cost is also unknown — measure first | — Pending |
| Keep stdlib-only constraint for core validator | Simplifies team handoff; no pip install step for reviewer | — Pending |
| Corrections log as bridge to generation | Structure corrections_log.json now so it can feed a translation generation system later — build with that end in mind | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-09 after Phase 05 complete (Notion Publishing — HTML removed, auto Notion publish added)*
