# Roadmap: Translation Quality Review Automation
## Milestone: Optimization & Hardening

## Overview

This milestone hardens an existing, working system: the two-tier translation review pipeline is deployed and producing reports, but it has a token bottleneck, fragile reference document handling, a freeform corrections log that cannot feed a generation tool, and no way for a non-Claude-Code teammate to run a review independently. Four phases address these in dependency order — token efficiency first (unblocks cheaper runs), then reference reliability and report format (unblocks trustworthy output), then feedback loop structure (unblocks the future generation milestone), then team handoff (delivers the finished system to the team).

## Phases

- [x] **Phase 1: Token Optimization** - Eliminate context-window waste in Step 4c and add a compact triage mode to the structural validator
- [x] **Phase 2: Reference Reliability + Report Format** - Harden config file usage, enforce variable catalog checks, and ship configurable HTML-default reports (completed 2026-04-08)
- [ ] **Phase 3: Feedback Loop Strengthening** - Restructure corrections_log.json with a machine-readable schema and surface relevant past rules per-language at review time
- [ ] **Phase 4: Team Handoff** - Write README, declare optional dependencies, and make generate_pdf.py runnable without source edits

## Phase Details

### Phase 1: Token Optimization
**Goal**: Review runs consume significantly fewer context-window tokens — the primary cost and speed bottleneck is eliminated
**Depends on**: Nothing (first phase)
**Requirements**: TOK-01, TOK-02, TOK-03
**Success Criteria** (what must be TRUE):
  1. Running a full review no longer outputs verbose JSON arrays to the conversation during Step 4c — findings accumulate silently to the report file
  2. `python3 scripts/structural_validator.py --summary` prints only market names and issue counts, not full JSON arrays
  3. A baseline token count exists for a reference notification (before optimization) and a post-optimization count for the same file shows measurable reduction
**Plans**: 2 plans

Plans:
- [x] 01-01: Implement silent accumulation in Step 4c of review-translations.md (TOK-01) and establish baseline token metric (TOK-03)
- [x] 01-02: Add `--summary` flag to structural_validator.py (TOK-02)

---

### Phase 2: Reference Reliability + Report Format
**Goal**: The review skill verifiably uses its config files on every run, variable catalog misses are always surfaced, and reports are readable by non-technical teammates without Markdown knowledge
**Depends on**: Phase 1
**Requirements**: REF-01, REF-02, REF-03, RPT-01, RPT-02, RPT-03
**Success Criteria** (what must be TRUE):
  1. At the start of every review run, the skill logs the name, row count, and load status of each reference file (label_patterns.json, tone_guidelines.json, Variables.csv) — visible in the conversation
  2. If Variables.csv is absent or a variable is not in the catalog, the report shows an explicit "FAIL — unknown variable" finding rather than silently passing
  3. When a market's formality deviates from its tone_guidelines.json standard, the report includes a finding for that market
  4. Running `/review-translations` produces an HTML file by default; `.md` and PDF remain selectable without editing source code
  5. Every report has the same sections in the same order regardless of which markets were flagged
**Plans**: 2 plans

Plans:
- [x] 02-01: Reference document reliability — load logging (REF-01), Variables.csv hard enforcement (REF-02), formality deviation flagging (REF-03)
- [x] 02-02: Report format — configurable output flag (RPT-01), consistent section structure (RPT-02), HTML as default output (RPT-03)

---

### Phase 3: Feedback Loop Strengthening
**Goal**: The corrections log is machine-readable with a consistent schema, and the review skill surfaces the most relevant past rules per language rather than loading undifferentiated history
**Depends on**: Phase 2
**Requirements**: FBK-01, FBK-02, FBK-03, FBK-04
**Success Criteria** (what must be TRUE):
  1. Every entry in corrections_log.json has all eight required fields: `language`, `notification_type`, `issue_category`, `original`, `corrected`, `rule_extracted`, `confidence`, `date` — freeform entries no longer exist
  2. After a Step 7 feedback session, the skill appends structured records (not freeform text) that conform to the schema
  3. A `rules_summary.json` file exists after each feedback session — a flat, language-keyed list of extracted rules that a future generation tool could load as context
  4. At the start of an AI review for a given language, the skill surfaces the top 3 most relevant past rules for that language (not the full log)
**Plans**: 2 plans

Plans:
- [ ] 03-01: Schema migration — define and enforce corrections_log.json schema (FBK-01), update Step 7 to write structured records (FBK-02)
- [ ] 03-02: Rules export and retrieval — generate rules_summary.json after feedback (FBK-03), surface top-3 rules per language at review time (FBK-04)

---

### Phase 4: Team Handoff
**Goal**: A non-Claude-Code teammate can clone the repo, read the README, and run a complete review without asking for help — and the PDF generator works without editing source code
**Depends on**: Phase 3
**Requirements**: HND-01, HND-02, HND-03
**Success Criteria** (what must be TRUE):
  1. README.md exists at the project root and covers: prerequisites, setup steps, how to run a review, how to read a report, and how to submit feedback — a first-time user can follow it without prior context
  2. `requirements.txt` exists listing `markdown` and `weasyprint` with a pinned version; README references it with an install command
  3. `python3 scripts/generate_pdf.py --input reports/foo.html --output reports/foo.pdf` runs successfully without any edits to source code
**Plans**: 1 plan

Plans:
- [ ] 04-01: Write README.md (HND-01), create requirements.txt (HND-02), add CLI args to generate_pdf.py (HND-03)

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Token Optimization | 2/2 | Complete   | 2026-04-08 |
| 2. Reference Reliability + Report Format | 2/2 | Complete   | 2026-04-08 |
| 3. Feedback Loop Strengthening | 0/2 | Not started | - |
| 4. Team Handoff | 0/1 | Not started | - |

---

## Coverage

| Requirement | Phase | Status |
|-------------|-------|--------|
| TOK-01 | Phase 1 | Complete |
| TOK-02 | Phase 1 | Complete |
| TOK-03 | Phase 1 | Complete |
| REF-01 | Phase 2 | Complete |
| REF-02 | Phase 2 | Complete |
| REF-03 | Phase 2 | Complete |
| RPT-01 | Phase 2 | Pending |
| RPT-02 | Phase 2 | Pending |
| RPT-03 | Phase 2 | Pending |
| FBK-01 | Phase 3 | Pending |
| FBK-02 | Phase 3 | Pending |
| FBK-03 | Phase 3 | Pending |
| FBK-04 | Phase 3 | Pending |
| HND-01 | Phase 4 | Pending |
| HND-02 | Phase 4 | Pending |
| HND-03 | Phase 4 | Pending |

v1 requirements mapped: 16/16

---

*Roadmap created: 2026-04-08*
*Granularity: Coarse*
*Milestone: Optimization & Hardening*
