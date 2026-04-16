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

### v1.2 — Audit, Fix & Strategic Overview (Phases 8–10)

- [x] **Phase 8: Project Audit** — Comprehensive audit of code, workflow, scope gaps, and contradictions with prioritized findings (completed 2026-04-16)
- [ ] **Phase 9: Fixes** — Implement deferred handoff items and highest-priority audit findings
- [ ] **Phase 10: Strategic Overview** — Capstone document mapping 3-phase vision and Phase 1 completion criteria

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
- [ ] 09-02-PLAN.md — Fix corrections data, add backup-before-write, archive stale files
- [x] 09-03-PLAN.md — Complete README and create requirements.txt

### Phase 10: Strategic Overview
**Goal**: The full 3-phase vision is documented with clear scope per phase and observable criteria that signal when Phase 1 is done enough to move forward
**Depends on**: Phase 9 (fixes complete; overview reflects current true state of the system)
**Requirements**: STR-01, STR-02
**Success Criteria** (what must be TRUE):
  1. Reviewer can open one document and read what each of the 3 phases delivers, with scope boundaries that make it clear what belongs where
  2. Reviewer can identify a checklist of observable conditions — not implementation tasks — that must all be true before work on Phase 2 (AI Translation Generation) begins
**Plans**: TBD

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
| 9. Fixes | v1.2 | 2/3 | In Progress|  |
| 10. Strategic Overview | v1.2 | 0/1 | Not started | - |

---

*Roadmap created: 2026-04-08*
*v1.1 shipped: 2026-04-14*
*v1.2 roadmap updated: 2026-04-16*
