# Translation Quality Review Automation

## Key Documents

- [Strategic Overview](STRATEGIC-OVERVIEW.md) — three-phase vision, two-stage gate pattern, Phase 1 readiness checklist (STR-02), routing rubric.

## What This Is

An automated quality review tool for Superprof notification translations. French notifications are translated to 39+ languages by human translators; this tool validates those translations structurally (Python, stdlib-only) and linguistically (Claude AI), then auto-publishes correction reports to the team's Notion workspace. The feedback loop accepts batches of reviewer comments, routes each to the correct config file or corrections log, and applies confirmed changes in one pass.

## Core Value

Every review run must produce a reliable, actionable report — fast enough and cheap enough to run on every translation batch.

## Current Milestone: v1.2 Audit, Fix & Strategic Overview

**Goal:** Audit the project for gaps and unused elements, implement the highest-priority fixes, and produce a strategic overview that maps the full 3-phase vision and defines when Phase 1 is "done enough" to move forward.

**Target features:**
- Comprehensive project audit (code, workflow, scope)
- Team handoff documentation (README)
- Top quality improvements (France ref row search, Unicode emoji detection)
- Strategic overview document: 3-phase vision with Phase 1 completion criteria

## Requirements

### Validated

- ✓ Two-tier review pipeline: deterministic structural validation (Python) + AI linguistic review (Claude) — v1.0
- ✓ French reference validation: all market translations compared against the France cell — v1.0
- ✓ Variables.csv catalog integration: unknown variables flagged and summarized in reports — v1.0
- ✓ Two-tier model routing: Haiku for clean markets, Sonnet for flagged markets — v1.0
- ✓ Learning system: corrections_log.json accumulates rules from user feedback after each review — v1.0
- ✓ Report generation: grouped Markdown reports with numbered findings, current text, and proposed fixes — v1.0
- ✓ Token optimization: Step 4c silent accumulation + `--summary` flag wired into Step 2 call site — v1.1 (Phase 01 + Phase 07)
- ✓ Reference document reliability: structural_validator.py hard-fails on missing Variables.csv; Step 1 health check confirms all 3 config files loaded; Step 4c formality logic explicitly references tone_guidelines.json — v1.1 (Phase 02)
- ✓ Report format: notification-ID filenames, fixed section order — v1.1 (Phase 02)
- ✓ Feedback loop structured: corrections_log.json 8-field schema, Step 7 writes structured records, rules_summary.json rebuilt after each session — v1.1 (Phase 03)
- ✓ Top-3 rule surfacing: most relevant past rules per language injected at AI review time using relevance scoring — v1.1 (Phase 03)
- ✓ Notion publishing: report automatically published to Notion on completion; HTML output removed; .md kept as local backup — v1.1 (Phase 05)
- ✓ Batch feedback routing: batch Language+Issue blocks parsed, routed to correct config file, conflicts flagged, user confirms, one-pass writes executed, change summary shown — v1.1 (Phase 06)

### Active

- [ ] **GEN-01**: Accumulated rules from `rules_summary.json` loaded as context for translation generation skill
- [ ] **GEN-02**: `generate-translation` skill accepts French source text + target language, uses rules_summary.json + config files to produce first-draft translation
- [ ] **GEN-03**: Generated translations validated against the same structural and reference document checks as human translations

### Validated in Phase 9: Fixes

- ✓ **HND-01**: README.md with prerequisites, setup, how to run, how to read reports, how to submit feedback — Phase 9 (FIX-01)
- ✓ ~~**HND-02**: requirements.txt for optional PDF dependencies (`markdown`, `weasyprint`) — Phase 9 (FIX-02)~~ — superseded: PDF support removed from project entirely
- ✓ ~~**HND-03**: `generate_pdf.py` archived as dead code (Phase 8 audit confirmed it's never called) — Phase 9 (FIX-02)~~ — superseded: PDF support removed from project entirely
- ✓ **QUA-01**: CSV parser finds France reference row by content search, not assuming position 0 — Phase 9 (FIX-03)
- ✓ **QUA-02**: Emoji detection uses `unicodedata.category()` instead of hardcoded ranges — Phase 9 (FIX-04)
- ✓ **QUA-03**: Corrections log backed up before each write — Phase 9 (FIX-05)

### Validated in Phase 10: Strategic Overview

- ✓ **STR-01**: `.planning/STRATEGIC-OVERVIEW.md` capstone document maps the 3-phase vision (Audit & Tune → AI Translation Generation → Backoffice Integration) with named scope boundaries, two-stage Orange/Green-Light gate pattern, and parseable routing rubric — Phase 10
- ✓ **STR-02**: Phase 1 readiness checklist with Must-Have / Should-Have bands and 9 observable conditions blending quantitative (≤20% structural error rate, ≥60% AI rule precision), qualitative, and audit-derived (IC-01, IC-02) gates — Phase 10

### Validated in Phase 11: Loop-Variable Check

- ✓ **FIX-06**: Structural validator flags wrong-loop-variable errors deterministically via `check_variable_block_placement()` — compares multiset of innermost block contexts per variable between French reference and translation. Closes v1.2 audit IC-01 (AUDIT finding #8 skipped in Phase 9). Universal check — fires for every market, not Arabic-specific. Live-validated on 2 real CSVs producing 12 findings across 12 distinct non-Arabic languages — Phase 11

### Validated in Phase 12: zh-HK Resolution

- ✓ **IC-02 / FIX-06 / AUD-05**: Orphaned `zh-HK` correction rule merged into `zh-TW`. Both `corrections/corrections_log.json` (6→5 entries) and `corrections/rules_summary.json` (`total_rules` 6→5) cleaned; `scripts/_build_report.py` country-to-code map and prose strings aligned with canonical `structural_validator.py:684` (Hong-Kong → zh-TW). Backup-before-write triple recorded under `corrections/backups/20260428T152501Z_*`. Phase-wide grep confirms zero `zh-HK`/`zh_HK` references in active config, corrections, scripts, or skill — Phase 12

### Out of Scope

- Web interface — CLI + Notion is sufficient
- Automated CSV correction — tool proposes fixes, humans apply them
- Notion comments → corrections import — feedback comes back via Juan; future milestone
- Test suite — 0% coverage is a concern but test infrastructure is out of scope

## Context

- **Stack**: Python 3.14.3 stdlib-only. No external dependencies.
- **Codebase**: Python scripts (`structural_validator.py`, `test_summary_flag.py`) + Claude skill definition. Line counts move with active development — see `.planning/codebase/STRUCTURE.md` for current snapshot.
- **Shipped in v1.1**: Notion publishing live; HTML output removed; batch feedback routing; token optimization fully realized; all integration gaps closed.
- **Phase 9 complete**: France row detection fixed (content-based), emoji detection future-proofed (unicodedata), corrections data cleaned (zh-TW codes, synced counts), backup-before-write added, README complete, stale files archived.
- **Phase 11 complete**: Wrong-loop-variable detection now deterministic — `variable_block_mismatch` check catches any template variable whose innermost block context differs from the French reference across all markets. Optional `block_scope_overrides` key in `config/label_patterns.json` supports per-language grammatical exemptions (empty by default). Closes v1.2 audit IC-01.
- **Phase 10 complete**: Strategic overview document published — defines the 3-phase vision, two-stage Orange/Green-Light gate pattern as a reusable template, Phase 1 readiness checklist (STR-02), and a parseable routing rubric for future scope decisions.
- **Phase 12 complete**: Orphaned zh-HK correction rule merged into zh-TW across both corrections files; `scripts/_build_report.py` aligned with canonical Hong-Kong→zh-TW mapping. Closes v1.2 audit IC-02. Hong-Kong CSV rows now hit a real correction rule via the validator's existing alias.
- **Known issues**: Step 1 health check references abbreviated tone_guidelines.json path (low severity).
- **Test coverage**: 0%. All validation is manual + live run.
- **Deferred**: Translation generation is the long-term v2 goal.

## Constraints

- **Tech stack**: Core validator must remain stdlib-only — keeps setup simple for team handoff
- **Data locality**: All inputs, outputs, and config stay local — no cloud sync, no external APIs (except Notion MCP for publishing)
- **Compatibility**: Must run on macOS without any environment setup beyond Python 3.x

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Silent accumulation for Step 4c | Eliminates token waste from verbose JSON in context; write findings to report file instead | ✓ Good — 5k–30k tokens saved per run |
| `--format` defaults to `.md` (not HTML) | HTML removed (NTIO-04); .md is lightweight and Notion-publishable | ✓ Good — clean delivery path |
| Notion publish via MCP inside skill | MCP already configured; no separate script needed; soft-fail keeps review usable if Notion is down | ✓ Good |
| Batch feedback extends Step 7 (not a separate skill) | Same session context; natural continuation of review flow | ✓ Good |
| Variables.csv routing flag-only in batch | CSV changes need careful validation; routing suggestions only, no writes | ✓ Good — prevents accidental catalog corruption |
| Corrections log as bridge to generation | Structure corrections_log.json now so it can feed a translation generation system later | — Pending (v2 goal) |
| Keep stdlib-only constraint for core validator | Simplifies team handoff; no pip install step for reviewer | ✓ Good |
| `--type` flag removed from structural_validator.py call | Flag was planned but never implemented in argparse; caused argparse crash on every run | ✓ Good — fixed 2026-04-14 |

---
*Last updated: 2026-04-28 after Phase 12 (zh-HK Resolution) completion — IC-02 closed via merge of orphaned zh-HK rule into zh-TW*
