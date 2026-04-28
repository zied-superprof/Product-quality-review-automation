# Phase 10: Strategic Overview - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-28
**Phase:** 10-strategic-overview
**Areas discussed:** Phase transition model, idea-submission skill placement, document location & shape, Phase 2/3 depth, STR-02 criteria style, doc relationship to existing planning artifacts

---

## Gray area 6 — Phase transition model + new-feature routing (raised by user)

User concern (verbatim): "I am just worried about when the next phase will start, a lot of new features can be implemented before moving to phase two, and at the same time, some test can be done for phase 2 without actually moving there, we need to clearly define this and probably to create a transition period before phases. Also, how to deal with new features, should this be done with new phases or during the feedback section, is not clear for me how to manage it with the GSD skill."

### Q1 — Phase transition model

| Option | Description | Selected |
|---|---|---|
| Soft transition + readiness milestone (two-stage gate) | Open `Phase 2 readiness` milestone when must-haves green; allow Phase 2 spikes (throwaway only) in parallel with Phase 1 close-out. Phase 2 proper starts at next milestone. | ✓ |
| Hard cut (binary gate) | Phase 2 starts only when ALL STR-02 criteria green. No Phase 2 work — not even spikes — before that. | |
| Trigger-based | Phase 2 starts when a defined event fires (e.g. "3 consecutive runs need >5 manual fixes"). Criteria become triggers, not boxes. | |
| Overlapping hybrid milestone | Declare a single milestone (v1.5 say) as explicitly mixed Phase 1 + Phase 2 production work. After it, cleanly in Phase 2. | |

**User's choice:** Two-stage gate — "Yes, we can discuss it further with specific examples once we define the scope of the 3 phases later on."
**Notes:** User expects planner to revisit specifics during plan-phase 10, after the 3-phase scope sections are drafted.

### Q2 — Idea-submission skill placement

| Option | Description | Selected |
|---|---|---|
| Global, deferred to Phase 13 | Skill lives in `~/.claude/get-shit-done/` as `/gsd:submit-idea`. Reusable across projects. Reads project's STRATEGIC-OVERVIEW.md for routing answers. Built in Phase 13, not Phase 10. | ✓ |
| Local, deferred to Phase 13 | Skill lives in this project's `.claude/commands/` only. Routing rubric hardcoded. Not reusable. | |
| Defer entirely (no skill) | Don't build the skill. Read routing table in doc, call existing `/gsd:add-backlog` / `/gsd:insert-phase` manually. | |
| Bundle into Phase 10 | Build the skill as part of Phase 10. Phase 10 ships doc + skill. Risk: scope creep. | |

**User's choice:** Global, deferred to Phase 13.
**Notes:** User asked clarifying question on local-vs-global before deciding; chose global after seeing rationale (matches existing `/gsd:*` pattern).

---

## Gray area 1 — Document location & shape

| Option | Description | Selected |
|---|---|---|
| New file: `.planning/STRATEGIC-OVERVIEW.md` | Single capstone, sibling of PROJECT.md. One link target, survives milestone archival, easy to commit/track. | ✓ |
| Embed inside PROJECT.md | Add new sections to existing PROJECT.md. No new file. Risk: drift with ephemeral milestone status. | |
| Split into `docs/strategic-overview/` tree | Multiple files (one per phase + criteria). Heavier than goal asks; likely violates STR-01 success criterion #1 ("opens ONE document"). | |

**User's choice:** New file `.planning/STRATEGIC-OVERVIEW.md`.

---

## Gray area 2 — Phase 2 & Phase 3 section depth

| Option | Description | Selected |
|---|---|---|
| Goal + deliverables + open questions | ~10-line goal, bulleted deliverables, plus "Open questions resolved when phase begins" subsection per phase. | ✓ |
| Lean: goal + deliverables only | Each phase: goal + bulleted deliverables. No open questions section. | |
| Heavy: goal + deliverables + hypothesized REQs + sketch architecture | Each phase has hypothesized REQs and architecture sketches. Risk: scope creep. | |

**User's choice:** Goal + deliverables + open questions.

---

## Gray area 3 — STR-02 completion criteria shape

| Option | Description | Selected |
|---|---|---|
| Two bands (must-have + should-have) | Must-haves trigger orange light (Phase 2 spikes allowed), should-haves trigger green light (Phase 2 proper). Mix of quantitative + qualitative + audit-derived in each band. | ✓ |
| Single mixed list (quant + qual + audit) | One flat checklist; no must/should split. Doesn't support two-stage gate. | |
| Quantitative gates only | Numeric only. Easy to check; risk of hitting numbers while system still rough. | |
| Qualitative gates only | Behavior-based only. Subjective; needs Juan's call to flip. | |

**User's choice:** Two bands (must-have + should-have).
**Notes (verbatim):** "Lets go for the option 1. but this should be definied for the transtion between phases in general, meaning from one to two and from two to 3." → CONTEXT.md generalizes the pattern to apply to all phase transitions, with Phase 1 as the worked example and Phase 2/3 as placeholders.

---

## Gray area 4 — Relationship to existing planning docs

| Option | Description | Selected |
|---|---|---|
| Inline summaries + links out | 2–3 line summary per section, then links to PROJECT.md / REQUIREMENTS.md / AUDIT.md / ROADMAP.md. Reader gets gist standalone. | ✓ |
| Pure capstone, links only | Each section is just links. Tiny doc, lowest rot risk, but reader has to follow 3 links. | |
| Self-contained, restate everything | Copy validated REQs, audit findings into the doc. Highest duplication; worst drift. | |

**User's choice:** Inline summaries + links out.

---

## Gray area 5 — Maintenance posture (not deep-dived; default applied)

User did not select this for deep discussion. Default applied: **Living doc, milestone-cadence updates.**

The two-stage gate decision implicitly requires a living doc (the STR-02 checkboxes get checked off over time), so the default is consistent with other decisions. No alternatives presented in this session.

---

## Locked defaults — confirmed not in scope

User confirmed: "All locked decisions are fine."

| Dimension | Locked default |
|---|---|
| File format | Markdown (`.md`) |
| Heading hierarchy | H1 doc title → H2 phases → H3 subsections |
| Prose style | Terse, contract-style, no marketing language |
| Commit policy | Auto-commit (`commit_docs: true`) |
| Date stamps | ISO `2026-04-28` |

---

## Claude's Discretion

- Exact section ordering inside the doc
- Table layouts and column widths
- Link formatting (inline vs. footnote-style)
- Wording of summary lines
- How visual the transition flow diagram is (ASCII vs. mermaid vs. none)

---

## Deferred Ideas

- **Phase 13 (proposed):** `/gsd:submit-idea` global skill that walks the routing rubric and dispatches to existing GSD primitives.
- **Specific Phase 2 spike topics** — defined when v1.5 readiness milestone opens.
- **Phase 2 must-have / should-have checklist** — populated when Phase 2 enters its readiness milestone.
- **Phase 3 scope detail** — sketched only in this phase; full detail when Phase 3 enters its own discuss-phase.
- **Architecture diagrams for Phase 2 / Phase 3** — out of scope per D-02a.
- **Hypothesized REQs (GEN-04, GEN-05, etc.)** — belong to future Phase 2 discuss-phase.
- **Notion publishing of STRATEGIC-OVERVIEW.md** — could be added later if team needs it; not in v1.2.
