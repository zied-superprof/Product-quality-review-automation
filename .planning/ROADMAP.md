# Roadmap: Translation Quality Review Automation

## Milestones

- ✅ **v1.1 — Notion Publishing & Batch Feedback Routing** — Phases 1–3 + 5–7 (shipped 2026-04-14)
- ✅ **v1.2 — Audit, Fix & Strategic Overview** — Phases 8–12 (shipped 2026-04-29)
- 📋 **v1.3 — TBD** — start with `/gsd:new-milestone`

## Phases

<details>
<summary>✅ v1.1 — Notion Publishing & Batch Feedback Routing (Phases 1–3, 5–7) — SHIPPED 2026-04-14</summary>

- [x] Phase 1: Token Optimization (2/2 plans) — completed 2026-04-08
- [x] Phase 2: Reference Reliability + Report Format (2/2 plans) — completed 2026-04-08
- [x] Phase 3: Feedback Loop Strengthening (2/2 plans) — completed 2026-04-09
- [ ] Phase 4: Team Handoff — **deferred to v1.2 (absorbed into Phase 9)**
- [x] Phase 5: Notion Publishing (2/2 plans) — completed 2026-04-09
- [x] Phase 6: Batch Feedback Routing (2/2 plans) — completed 2026-04-10
- [x] Phase 7: Tech Debt Cleanup (1/1 plans) — completed 2026-04-14

Full details: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)

</details>

<details>
<summary>✅ v1.2 — Audit, Fix & Strategic Overview (Phases 8–12) — SHIPPED 2026-04-29</summary>

- [x] Phase 8: Project Audit (2/2 plans) — completed 2026-04-16
- [x] Phase 9: Fixes (3/3 plans) — completed 2026-04-16
- [x] Phase 10: Strategic Overview (1/1 plan) — completed 2026-04-28
- [x] Phase 11: Loop-Variable Structural Check (1/1 plan) — completed 2026-04-24 (closes IC-01)
- [x] Phase 12: zh-HK Language Code Resolution (1/1 plan) — completed 2026-04-28 (closes IC-02)

Full details: [milestones/v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)

</details>

### 📋 v1.3 — TBD

Use `/gsd:new-milestone` to start the next milestone (questioning → research → requirements → roadmap). Backlog item 999.1 (URL-driven translation review) is the leading v1.3 candidate.

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
| 8. Project Audit | v1.2 | 2/2 | Complete | 2026-04-16 |
| 9. Fixes | v1.2 | 3/3 | Complete | 2026-04-16 |
| 10. Strategic Overview | v1.2 | 1/1 | Complete | 2026-04-28 |
| 11. Loop-Variable Structural Check | v1.2 | 1/1 | Complete | 2026-04-24 |
| 12. zh-HK Language Code Resolution | v1.2 | 1/1 | Complete | 2026-04-28 |

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

**Plans:** 0/4 plans complete

Plans:
- [ ] TBD (promote with `/gsd:review-backlog` when ready)

---

*Roadmap created: 2026-04-08*
*v1.1 shipped: 2026-04-14*
*v1.2 shipped: 2026-04-29*
*Backlog 999.1 added: 2026-04-23 — URL-driven translation review (v1.3 candidate)*
