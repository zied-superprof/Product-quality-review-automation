# Roadmap: Translation Quality Review Automation

## Milestones

- ✅ **v1.1 — Notion Publishing & Batch Feedback Routing** — Phases 1–3 + 5–7 (shipped 2026-04-14)
- 📋 **v1.2 — Audit, Fix & Strategic Overview** — Phases 8–10 (in progress)

## Phases

<details>
<summary>✅ v1.1 — Notion Publishing & Batch Feedback Routing (Phases 1–3, 5–7) — SHIPPED 2026-04-14</summary>

- [x] Phase 1: Token Optimization (2/2 plans) — completed 2026-04-08
- [x] Phase 2: Reference Reliability + Report Format (2/2 plans) — completed 2026-04-08
- [x] Phase 3: Feedback Loop Strengthening (2/2 plans) — completed 2026-04-09
- [ ] Phase 4: Team Handoff — **deferred to v1.2 (absorbed into Phase 8/9)**
- [x] Phase 5: Notion Publishing (2/2 plans) — completed 2026-04-09
- [x] Phase 6: Batch Feedback Routing (2/2 plans) — completed 2026-04-10
- [x] Phase 7: Tech Debt Cleanup (1/1 plans) — completed 2026-04-14

Full details: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)

</details>

### v1.2 — Audit, Fix & Strategic Overview (Phases 8–12)

- [x] **Phase 8: Project Audit** — Comprehensive audit of code, workflow, scope gaps, and contradictions with prioritized findings (completed 2026-04-16)
- [x] **Phase 9: Fixes** — Implement deferred handoff items and highest-priority audit findings (completed 2026-04-16)
- [ ] **Phase 10: Strategic Overview** — Capstone document mapping 3-phase vision and Phase 1 completion criteria
- [ ] **Phase 11: Loop-Variable Structural Check** — Close IC-01 / complete FIX-06 scope (gap closure from v1.2 audit)
- [ ] **Phase 12: zh-HK Language Code Resolution** — Close IC-02 orphaned correction rule (gap closure from v1.2 audit)

## Phase Details

### Phase 8: Project Audit
**Goal**: Reviewer has a complete, prioritized audit of the project — what is unused, what is broken in the workflow, and what was planned but never built
**Depends on**: Phase 7 (all v1.1 work shipped)
**Requirements**: AUD-01, AUD-02, AUD-03, AUD-04, AUD-05
**Success Criteria** (what must be TRUE):
  1. Reviewer can open a single audit document and see every unused or redundant code file, script, and config entry identified
  2. Reviewer can read a documented list of workflow gaps — steps that are missing, brittle, or will not scale
  3. Reviewer can see scope gaps against the Phase 1 vision, distinguishing never-built from partially-built capabilities
  4. Every audit finding carries a priority label (critical / medium / low) and a concrete next-step recommendation
  5. Reviewer can see all identified contradictions — config conflicts, rule inconsistencies, and doc vs. implementation mismatches
**Plans**: 2 plans
Plans:
- [x] 08-01-PLAN.md — Scan for unused/redundant code and detect contradictions
- [x] 08-02-PLAN.md — Analyze workflow/scope gaps and assemble final AUDIT.md

### Phase 9: Fixes
**Goal**: Users and new team members can set up and run the tool reliably, and the most fragile code paths from the audit are corrected
**Depends on**: Phase 8 (FIX-06 scope is confirmed by audit findings; all other fixes are independent of audit results)
**Requirements**: FIX-01, FIX-02, FIX-03, FIX-04, FIX-05, FIX-06
**Success Criteria** (what must be TRUE):
  1. A new team member can follow the README from zero to running a review without asking Juan for help
  2. generate_pdf.py is archived to scripts/archive/ as confirmed dead code, and optional PDF dependencies are documented in requirements.txt
  3. Swapping the France row to any position in the CSV does not break the review run
  4. Adding a brand-new emoji to a translation is flagged without any code changes, using the current Unicode data
  5. After any write to the corrections log, a timestamped backup file exists in the corrections directory
**Plans**: 3 plans
Plans:
- [x] 09-01-PLAN.md — Fix France row detection and emoji detection in structural validator
- [x] 09-02-PLAN.md — Fix corrections data, add backup-before-write, archive stale files
- [x] 09-03-PLAN.md — Complete README and create requirements.txt

### Phase 10: Strategic Overview
**Goal**: The full 3-phase vision is documented with clear scope per phase and observable criteria that signal when Phase 1 is done enough to move forward
**Depends on**: Phase 9 (fixes complete; overview reflects current true state of the system)
**Requirements**: STR-01, STR-02
**Success Criteria** (what must be TRUE):
  1. Reviewer can open one document and read what each of the 3 phases delivers, with scope boundaries that make it clear what belongs where
  2. Reviewer can identify a checklist of observable conditions — not implementation tasks — that must all be true before work on Phase 2 (AI Translation Generation) begins
**Plans**: TBD

### Phase 11: Loop-Variable Structural Check
**Goal**: The structural validator catches the wrong-loop-variable error (AUDIT finding [#8]) — the most commonly observed recurring error in CLAUDE.md — without depending on the AI review tier
**Depends on**: Phase 9 (validator and label_patterns.json are the target files; Phase 9 established the current baseline)
**Requirements**: FIX-06 (completes the partially-satisfied scope — AUDIT finding [#8] was skipped silently in Phase 9; see v1.2 audit IC-01)
**Gap Closure**: Closes IC-01 from v1.2-MILESTONE-AUDIT.md
**Success Criteria** (what must be TRUE):
  1. `scripts/structural_validator.py` flags template variables used outside their allowed block (e.g. `@TPL_MATIERE_DE_MATIERE@` inside `<TPL_LOOP_ANNONCES>`, `@TPL_ANNONCE_AFFICHE_QUI_CONNECTE@` inside `<TPL_IF_LISTE_AVIS>`)
  2. `config/label_patterns.json` declares which variables are valid in which structural blocks (loop, if-block, body)
  3. The recurring Arabic-market error pattern documented in CLAUDE.md is detected by the structural layer, not only by the AI reviewer
**Plans**: TBD

### Phase 12: zh-HK Language Code Resolution
**Goal**: The Hong Kong correction learning loop actually fires — either HK gets its own `zh-HK` rule set end-to-end, or HK is consolidated under `zh-TW` and the orphaned rule is removed
**Depends on**: Phase 9 (Phase 9 Plan 02 added the zh-HK entry that became orphaned; Phase 12 decides its fate)
**Requirements**: None directly — gap closure for a material integration defect shipped under FIX-06
**Gap Closure**: Closes IC-02 from v1.2-MILESTONE-AUDIT.md and the "Hong Kong correction learning loop" broken flow
**Success Criteria** (what must be TRUE):
  1. The zh-HK rule in `corrections/corrections_log.json` + `corrections/rules_summary.json` is either consistently resolved across all four configs and the validator's country→code map, OR consolidated back into `zh-TW` with the orphaned entry removed
  2. A CSV run with a Hong Kong row exercises the intended correction path — no silent mapping divergence between the validator and the corrections store
  3. The chosen direction (split or merge) is recorded in Phase 12's summary so future readers understand why
**Plans**: TBD — planning step must first decide split vs merge

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Token Optimization | v1.1 | 2/2 | Complete | 2026-04-08 |
| 2. Reference Reliability + Report Format | v1.1 | 2/2 | Complete | 2026-04-08 |
| 3. Feedback Loop Strengthening | v1.1 | 2/2 | Complete | 2026-04-09 |
| 4. Team Handoff | v1.1 | 0/1 | Deferred | - |
| 5. Notion Publishing | v1.1 | 2/2 | Complete | 2026-04-09 |
| 6. Batch Feedback Routing | v1.1 | 2/2 | Complete | 2026-04-10 |
| 7. Tech Debt Cleanup | v1.1 | 1/1 | Complete | 2026-04-14 |
| 8. Project Audit | v1.2 | 2/2 | Complete   | 2026-04-16 |
| 9. Fixes | v1.2 | 3/3 | Complete   | 2026-04-16 |
| 10. Strategic Overview | v1.2 | 0/1 | Not started | - |
| 11. Loop-Variable Structural Check | v1.2 | 0/? | Not started (gap closure) | - |
| 12. zh-HK Language Code Resolution | v1.2 | 0/? | Not started (gap closure) | - |

---

## Backlog

### Phase 999.1: URL-driven translation review (BACKLOG)

**Goal:** [Captured for future planning] End-to-end flow: send a Superprof BO notification admin URL to the agent; Playwright scrapes the page (email/SMS tabs) and extracts translation grid(s) into 1–2 CSVs in `samples/` named after the translation name shown in the page information block; the existing review pipeline runs; the report is published to the Notion Reports DB with the translation name as the page title and the existing "task follow up" column set to the same name; a Slack message is posted to a group channel when the run completes. Coexists with the current CSV-drop flow until the URL-driven path is fully operational.

**Requirements:** TBD

**Confirmed decisions (2026-04-23):**
1. Source = Superprof BO notification admin
2. Extraction tool = Playwright (not API)
3. Email/SMS = separate tabs on the page
4. Translation name source = page information block
5. Notion "task follow up" column already exists on Reports DB
6. Completion notifier = Slack message to a group
7. CSV-drop flow stays live during rollout

**Open for v1.3 planning (discuss-phase):**
- Exact Playwright selectors for the page information block + tabs
- Notion "task follow up" column type and allowed values
- Which Slack group/channel and message format
- Auth flow for BO (session cookie, SSO, login script?)
- Rate limits / retry on Playwright failures

**Suggested phase breakdown:**
- A: Playwright extraction (URL → structured data)
- B: Data → named CSV(s) in `samples/`
- C: Orchestration + Notion task-follow-up column wiring
- D: Slack completion notifier

**Plans:** 0 plans

Plans:
- [ ] TBD (promote with `/gsd:review-backlog` when ready)

---

*Roadmap created: 2026-04-08*
*v1.1 shipped: 2026-04-14*
*v1.2 roadmap updated: 2026-04-16*
*v1.2 gap closure phases added: 2026-04-23 (per v1.2-MILESTONE-AUDIT.md — IC-01, IC-02)*
*Backlog 999.1 added: 2026-04-23 — URL-driven translation review (v1.3 candidate)*
