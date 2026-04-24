# Requirements: Translation Quality Review Automation

**Defined:** 2026-04-14
**Milestone:** v1.2 — Audit, Fix & Strategic Overview
**Core Value:** Every review run must produce a reliable, actionable report — fast enough and cheap enough to run on every translation batch.

---

## v1.1 Requirements (Validated)

All shipped. See `.planning/PROJECT.md` → Requirements → Validated for full list.

---

## v1.2 Requirements

### Audit (AUD)

- [x] **AUD-01**: Reviewer can see a documented list of all unused or redundant code, scripts, and config files in the project
- [x] **AUD-02**: Reviewer can see identified gaps in the review→correction→improvement workflow cycle (steps missing, brittle, or unscalable)
- [x] **AUD-03**: Reviewer can see scope gaps versus the Phase 1 vision — capabilities that were planned but never built or partially built
- [x] **AUD-04**: Audit findings are prioritized (critical / medium / low) with actionable next steps
- [x] **AUD-05**: Reviewer can see identified contradictions in the project — conflicting rules across config files, mismatches between documented behavior and actual implementation, and inconsistencies in the correction rules

### Fixes (FIX)

- [x] **FIX-01**: User can set up the project using a README that covers prerequisites, setup steps, how to run a review, how to read reports, and how to submit feedback
- [x] **FIX-02**: Optional PDF dependencies are documented in a requirements.txt; `generate_pdf.py` is archived to `scripts/archive/` as confirmed dead code (Phase 8 audit finding — never called in any workflow)
- [x] **FIX-03**: CSV parser locates the France reference row by searching for `fr`/`FR` content rather than assuming it is always at position 0
- [x] **FIX-04**: Emoji detection uses maintained Unicode data (not hardcoded ranges) so new emoji are caught without code changes
- [x] **FIX-05**: Corrections log is automatically backed up before each write operation so no accumulated rules are lost
- [x] **FIX-06**: Highest-priority critical findings from the AUD phase are implemented (scope confirmed after audit) — *completed 2026-04-24 via Phase 11: `check_variable_block_placement()` added to structural_validator.py, detects wrong-loop-variable pattern (AUDIT finding [#8]) deterministically; live run caught 12 non-Arabic languages plus Nigéria IF→ELSE block-move bug.*

### Strategic Overview (STR)

- [ ] **STR-01**: A strategic overview document maps the full 3-phase vision (Phase 1: Audit & Tune → Phase 2: AI Translation Generation → Phase 3: Backoffice Integration) with clear scope and deliverables per phase
- [ ] **STR-02**: The document defines Phase 1 completion criteria — observable conditions that signal the system is tuned enough to move to Phase 2

---

## Future Requirements (v2+)

### Translation Generation

- **GEN-01**: Accumulated rules from `rules_summary.json` loaded as context for translation generation skill
- **GEN-02**: `generate-translation` skill accepts French source text + target language, uses rules_summary.json + config files to produce first-draft translation
- **GEN-03**: Generated translations validated against the same structural and reference document checks as human translations

### Backoffice Integration

- **INT-01**: Translation generation agent accessible from within the Superprof backoffice (one-click per market)
- **INT-02**: Generated translation applied directly to the target market without leaving the backoffice

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Test suite | 0% coverage is a concern but test infrastructure is explicitly out of scope for this project |
| Web interface | CLI + Notion is sufficient |
| Automated CSV correction | Tool proposes fixes, humans apply them |
| Notion comments → corrections import | Feedback comes back via Juan; future milestone |
| Feedback loop distribution (multi-reviewer) | No bottleneck pain yet; build when the need is real |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUD-01 | Phase 8 | Complete |
| AUD-02 | Phase 8 | Complete |
| AUD-03 | Phase 8 | Complete |
| AUD-04 | Phase 8 | Complete |
| AUD-05 | Phase 8 | Complete |
| FIX-01 | Phase 9 | Complete |
| FIX-02 | Phase 9 | Complete |
| FIX-03 | Phase 9 | Complete |
| FIX-04 | Phase 9 | Complete |
| FIX-05 | Phase 9 | Complete |
| FIX-06 | Phase 11 | Complete (2026-04-24 — IC-01 gap closed; variable_block_mismatch check live) |
| STR-01 | Phase 10 | Pending |
| STR-02 | Phase 10 | Pending |

**Gap closure (no direct REQ mapping):**

| Gap | Phase | Source |
|-----|-------|--------|
| IC-02 — zh-HK orphaned correction rule | Phase 12 | v1.2-MILESTONE-AUDIT.md |

**Coverage:**
- v1.2 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0
- Satisfied: 11 (FIX-06 closed via Phase 11 — IC-01 gap closure)

---
*Requirements defined: 2026-04-14*
*Last updated: 2026-04-24 — FIX-06 completed via Phase 11 (IC-01 gap closure); variable_block_mismatch check live in structural_validator.py*
