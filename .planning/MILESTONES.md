# Milestones — Translation Quality Review Automation

## v1.2 — Audit, Fix & Strategic Overview

**Shipped:** 2026-04-29
**Phases:** 8–12 (5 phases)
**Plans:** 8 total
**Timeline:** 2026-04-14 → 2026-04-28 (15 days)
**Git range:** 65f1131 → 45df660

### Delivered

Audited the project end-to-end, fixed the highest-priority brittleness (France row detection, emoji handling, corrections backup, README), shipped a 3-phase strategic overview with a Phase 1 readiness checklist, and closed both integration gaps surfaced by the v1.2 audit (wrong-loop-variable structural check + orphaned zh-HK correction rule).

### Key Accomplishments

1. **Comprehensive audit shipped** — 34 prioritized findings across dead code, workflow brittleness, scope gaps, and config contradictions; 5 critical, 14 medium, 15 low, 3 none-priority (Phase 8)
2. **Critical fixes landed** — France row detected by country-name/code search (no longer position-0 assumption), emoji detection via `unicodedata.category()` (no hardcoded ranges), corrections backup-before-write, zh_TW/zh_HK BCP-47 normalization (Phase 9)
3. **Team handoff complete** — README rewritten with the full zero-to-running-a-review journey: prerequisites, setup, run, read reports, submit feedback (Phase 9)
4. **Strategic Overview published** — `STRATEGIC-OVERVIEW.md` (242 lines): 3-phase scope (Audit & Tune → AI Translation Generation → Backoffice Integration), reusable two-stage Orange/Green gate pattern with spike governance, Phase 1 readiness checklist (4 must-have + 5 should-have gates), parseable routing rubric for new ideas (Phase 10)
5. **IC-01 closed deterministically** — `check_variable_block_placement()` in structural_validator.py catches wrong-loop-variable errors via multiset comparison against the French reference; live runs caught 12 non-Arabic languages plus a Nigéria IF→ELSE block-move bug (Phase 11)
6. **IC-02 closed by merging zh-HK into zh-TW** — orphaned correction rule deleted from both corrections JSONs (6→5 entries each); `scripts/_build_report.py` aligned with `structural_validator.py:684` Hong-Kong → zh-TW canonical mapping; backup triple recorded under `corrections/backups/20260428T152501Z_*` (Phase 12)

### Stats

- Files changed: 54 | Insertions: 9,709 | Deletions: 504
- Commits: 46 total (8 `feat()`)
- Requirements: 13/13 complete (5 AUD, 6 FIX, 2 STR)

### Known Deferred / Tech Debt

- **IC-03** (backup-before-write is text-instruction in skill, not enforceable code) — accepted, candidate for future hardening (commit hook or Python wrapper that performs the copy)
- **Broader language-database review** (audit of all 4 configs + Variables.csv for stale/redundant entries) — surfaced during Phase 12, deferred to a future phase
- **Code-level language-code guard** (pre-commit check that fails when a code appears in any source file without a config entry) — strengthened by Phase 12's `_build_report.py` drift discovery
- **Phase 9 Human Verifications** #1 (live skill backup creation) and #2 (France row at non-zero position in real CSV) — pending real-world validation

### Audit Note

`v1.2-MILESTONE-AUDIT.md` ran 2026-04-23 with verdict `gaps_found` (STR-01/STR-02 unsatisfied, IC-01/IC-02 material). All four gaps were closed by subsequent phases before milestone close: STR-01/STR-02 via Phase 10 (2026-04-28), IC-01 via Phase 11 (2026-04-24), IC-02 via Phase 12 (2026-04-28). IC-03 accepted as documented tech debt.

### Archive

- [v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)
- [v1.2-REQUIREMENTS.md](milestones/v1.2-REQUIREMENTS.md)
- [v1.2-MILESTONE-AUDIT.md](milestones/v1.2-MILESTONE-AUDIT.md)

---

## v1.1 — Notion Publishing & Batch Feedback Routing

**Shipped:** 2026-04-14
**Phases:** 1–3 (carried from v1.0), 5–7
**Plans:** 11 total
**Timeline:** 2026-04-08 → 2026-04-14 (7 days)
**Git range:** First commit → 65f1131

### Delivered

Hardened the two-tier review pipeline, connected it to the team's Notion workspace, and replaced one-at-a-time feedback with a batch routing system that suggests where each correction belongs.

### Key Accomplishments

1. **Token optimization realized** — Step 4c silent accumulation (5k–30k token savings per run) + `--summary` flag wired into Step 2 structural validator call (80–90% reduction in Step 2 output)
2. **Reference reliability hardened** — Variables.csv hard-fail, Step 1 health check logging all 3 config files, formality deviation flagging in AI review
3. **Feedback loop structured** — corrections_log.json 8-field schema, top-3 per-language rule surfacing with `occurrence_count × recency_weight × confidence_score` relevance scoring
4. **Notion publishing live** — reports auto-published to Notion on completion via MCP; HTML output removed; .md retained as local backup
5. **Batch feedback routing** — paste N Language+Issue blocks, get routing suggestion per comment (corrections_log / label_patterns / tone_guidelines / Variables.csv), confirm and apply in one pass
6. **Integration gap closed** — `--type` argparse crash on Step 2 fixed (commit 65f1131); all integration gaps from v1.1 audit resolved

### Stats

- Files changed: 56 | Insertions: 9,806 | Deletions: 211
- Python: 1,001 lines across 3 scripts
- Skill definition: 707 lines
- Commits: 70 total (15 `feat()`)
- Requirements: 20/20 active complete, 3 deferred (HND-01/02/03 → v1.2)

### Known Deferred

- HND-01: README.md
- ~~HND-02: requirements.txt~~ (superseded — PDF support removed; requirements.txt deleted)
- ~~HND-03: generate_pdf.py CLI args~~ (superseded — PDF support removed)

### Archive

- [v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)
- [v1.1-REQUIREMENTS.md](milestones/v1.1-REQUIREMENTS.md)
- [v1.1-MILESTONE-AUDIT.md](milestones/v1.1-MILESTONE-AUDIT.md)

---

*Last updated: 2026-04-14*
