# Milestones — Translation Quality Review Automation

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
- HND-02: requirements.txt
- HND-03: generate_pdf.py CLI args

### Archive

- [v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)
- [v1.1-REQUIREMENTS.md](milestones/v1.1-REQUIREMENTS.md)
- [v1.1-MILESTONE-AUDIT.md](milestones/v1.1-MILESTONE-AUDIT.md)

---

*Last updated: 2026-04-14*
