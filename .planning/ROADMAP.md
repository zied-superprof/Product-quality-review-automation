# Roadmap: Translation Quality Review Automation

## Milestone v1.0: Optimization & Hardening

## Overview

This milestone hardened an existing, working system: the two-tier translation review pipeline was deployed and producing reports, but had a token bottleneck, fragile reference document handling, a freeform corrections log that could not feed a generation tool, and no way for a non-Claude-Code teammate to run a review independently. Four phases addressed these in dependency order — token efficiency first (unblocks cheaper runs), then reference reliability and report format (unblocks trustworthy output), then feedback loop structure (unblocks the future generation milestone), then team handoff (deferred).

## Phases (v1.0)

- [x] **Phase 1: Token Optimization** - Eliminate context-window waste in Step 4c and add a compact triage mode to the structural validator
- [x] **Phase 2: Reference Reliability + Report Format** - Harden config file usage, enforce variable catalog checks, and ship configurable HTML-default reports (completed 2026-04-08)
- [x] **Phase 3: Feedback Loop Strengthening** - Restructure corrections_log.json with a machine-readable schema and surface relevant past rules per-language at review time (completed 2026-04-09)
- [ ] **Phase 4: Team Handoff** - Write README, declare optional dependencies, and make generate_pdf.py runnable without source edits (deferred)

## Phase Details (v1.0)

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
- [x] 03-01: Schema migration — define and enforce corrections_log.json schema (FBK-01), update Step 7 to write structured records (FBK-02)
- [x] 03-02: Rules export and retrieval — generate rules_summary.json after feedback (FBK-03), surface top-3 rules per language at review time (FBK-04)

---

### Phase 4: Team Handoff
**Goal**: A non-Claude-Code teammate can clone the repo, read the README, and run a complete review without asking for help — and the PDF generator works without editing source code
**Depends on**: Phase 3
**Requirements**: HND-01, HND-02, HND-03
**Status**: Deferred to future milestone
**Success Criteria** (what must be TRUE):
  1. README.md exists at the project root and covers: prerequisites, setup steps, how to run a review, how to read a report, and how to submit feedback — a first-time user can follow it without prior context
  2. `requirements.txt` exists listing `markdown` and `weasyprint` with a pinned version; README references it with an install command
  3. `python3 scripts/generate_pdf.py --input reports/foo.html --output reports/foo.pdf` runs successfully without any edits to source code
**Plans**: 1 plan

Plans:
- [ ] 04-01: Write README.md (HND-01), create requirements.txt (HND-02), add CLI args to generate_pdf.py (HND-03)

---

## Progress (v1.0)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Token Optimization | 2/2 | Complete | 2026-04-08 |
| 2. Reference Reliability + Report Format | 2/2 | Complete | 2026-04-08 |
| 3. Feedback Loop Strengthening | 2/2 | Complete | 2026-04-09 |
| 4. Team Handoff | 0/1 | Deferred | - |

---

---

## Milestone v1.1: Notion Publishing & Batch Feedback Routing

## Overview

Two natural delivery boundaries: first, connect report output to the team's Notion workspace and remove the now-redundant HTML format; second, replace the one-at-a-time feedback loop with a batch routing system that suggests which config file each correction belongs in. Both phases build on the structured feedback loop from v1.0 Phase 3.

## Phases (v1.1)

- [x] **Phase 5: Notion Publishing** - Auto-publish completed reports to Notion via MCP and remove HTML output; .md stays as local backup (completed 2026-04-09)
- [ ] **Phase 6: Batch Feedback Routing** - Accept a batch of reviewer comments, suggest routing action per comment, apply confirmed actions immediately

## Phase Details (v1.1)

### Phase 5: Notion Publishing
**Goal**: Completed review reports are automatically available in Notion for the team — no manual step after the review run, and no HTML file to manage
**Depends on**: Phase 3 (report format established)
**Requirements**: NTIO-01, NTIO-02, NTIO-03, NTIO-04
**Success Criteria** (what must be TRUE):
  1. After a review run completes, a Notion page exists without the user running any extra command — the publish step is part of the skill's normal flow
  2. The Notion page contains all the same content as the .md report — all markets, same section order, same findings — with no information lost in the conversion
  3. The Notion page title contains both the notification ID and the review date, making the page identifiable in the workspace without opening it
  4. Running `/review-translations` no longer produces an HTML file; a .md file is still written to `reports/` as local backup
**Plans**: 2 plans

Plans:
- [x] 05-01-PLAN.md — Remove HTML output format from --format flag and Step 6 (NTIO-04)
- [x] 05-02-PLAN.md — Add Notion publish block to Step 6 with content adaptation (NTIO-01, NTIO-02, NTIO-03)

---

### Phase 6: Batch Feedback Routing
**Goal**: The user can paste multiple reviewer comments at once and get a routing suggestion per comment — each pointing to the correct config file or corrections log — then confirm to apply all at once
**Depends on**: Phase 5
**Requirements**: FBK-05, FBK-06, FBK-07
**Success Criteria** (what must be TRUE):
  1. The user can paste 2 or more correction comments in a single Step 7 input and receive a separate analysis for each one — no need to re-invoke the skill per comment
  2. For each comment the system outputs: the suggested destination (corrections_log.json, label_patterns.json, tone_guidelines.json, or Variables.csv), a one-line rationale, and a conflict flag if the suggestion contradicts an existing rule
  3. After the user confirms (or rejects per item), all confirmed actions are applied in one pass — the target files are updated and the user sees a summary of what changed
**Plans**: TBD

---

## Progress (v1.1)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 5. Notion Publishing | 2/2 | Complete   | 2026-04-09 |
| 6. Batch Feedback Routing | 0/TBD | Not started | - |

---

## Coverage

### v1.0 Requirements

| Requirement | Phase | Status |
|-------------|-------|--------|
| TOK-01 | Phase 1 | Complete |
| TOK-02 | Phase 1 | Complete |
| TOK-03 | Phase 1 | Complete |
| REF-01 | Phase 2 | Complete |
| REF-02 | Phase 2 | Complete |
| REF-03 | Phase 2 | Complete |
| RPT-01 | Phase 2 | Complete |
| RPT-02 | Phase 2 | Complete |
| RPT-03 | Phase 2 | Complete |
| FBK-01 | Phase 3 | Complete |
| FBK-02 | Phase 3 | Complete |
| FBK-03 | Phase 3 | Complete |
| FBK-04 | Phase 3 | Complete |
| HND-01 | Phase 4 | Deferred |
| HND-02 | Phase 4 | Deferred |
| HND-03 | Phase 4 | Deferred |

v1.0 requirements mapped: 16/16

### v1.1 Requirements

| Requirement | Phase | Status |
|-------------|-------|--------|
| NTIO-01 | Phase 5 | Pending |
| NTIO-02 | Phase 5 | Pending |
| NTIO-03 | Phase 5 | Pending |
| NTIO-04 | Phase 5 | Pending |
| FBK-05 | Phase 6 | Pending |
| FBK-06 | Phase 6 | Pending |
| FBK-07 | Phase 6 | Pending |

v1.1 requirements mapped: 7/7

---

*Roadmap created: 2026-04-08*
*v1.1 phases added: 2026-04-09*
*Phase 5 planned: 2026-04-09*
*Granularity: Coarse*
