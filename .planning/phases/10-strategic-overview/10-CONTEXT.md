# Phase 10: Strategic Overview - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Produce ONE document — `.planning/STRATEGIC-OVERVIEW.md` — that:
1. Names what each of the 3 phases delivers (Phase 1: Audit & Tune → Phase 2: AI Translation Generation → Phase 3: Backoffice Integration), with scope boundaries clear enough that any reader can tell which phase a new idea belongs to.
2. Defines the **two-stage transition pattern** (must-have / should-have criteria + spike track) that governs every phase boundary.
3. Fills in Phase 1's concrete must-have / should-have checklist (the STR-02 deliverable).
4. Includes a **routing rubric table** so new ideas have an unambiguous destination.

The document itself is the deliverable. No code, no config, no validator changes. A future `/gsd:submit-idea` skill (Phase 13) will consume the rubric — not built here.

</domain>

<decisions>
## Implementation Decisions

### Document location & shape
- **D-01:** Single new file at `.planning/STRATEGIC-OVERVIEW.md` (sibling of PROJECT.md, REQUIREMENTS.md, ROADMAP.md). One link target, survives milestone archival.

### Phase 2 & Phase 3 section depth
- **D-02:** Each phase section has three subsections:
  1. **Goal** — one paragraph on what the phase delivers
  2. **Deliverables** — bulleted list (concrete artifacts, e.g. "`generate-translation` skill" for Phase 2)
  3. **Open questions resolved when phase begins** — bulleted list of known unknowns (e.g. "Which Claude model tier per generation step?")
- **D-02a:** No hypothesized requirements (no GEN-04, GEN-05, etc.) and no architecture sketches in this doc — those belong in the future discuss-phase for each phase.

### Phase transition pattern (general — applies to 1→2 AND 2→3)
- **D-03:** Every phase transition uses a **two-stage gate**:
  - **Orange light** = all *must-have* criteria green → next phase's exploration spikes allowed
  - **Green light** = all *must-have* + *should-have* criteria green AND ≥1 spike has produced commit-worthy learnings → next phase proper begins
- **D-04:** The transition pattern is documented in STRATEGIC-OVERVIEW.md as a reusable template, not as Phase-1-only logic.

### Spike governance (during orange-light period)
- **D-05:** Spikes live in `scripts/spikes/` (or `experiments/`) — never in `scripts/`. No commits to production code paths during a spike.
- **D-06:** Each spike is added as a small phase in the readiness milestone via `/gsd:add-phase`, with name pattern `Phase X.Y: Spike — [topic]`. Deliverables: 1-page PLAN.md + 1-page LEARNINGS.md. No VERIFY.md.
- **D-07:** Spikes are time-boxed to ≤ 1 week of work. Outcome at close: either "promote to real phase" or "park, lessons captured."

### Phase 1 STR-02 criteria (concrete fill)
- **D-08:** Phase 1's checklist uses a mix in each band:
  - Quantitative gates (e.g. token cost vs. baseline, tier-2 routing %)
  - Qualitative gates (e.g. "new maintainer can run + interpret a review using only README + CLAUDE.md")
  - Audit-derived gates (e.g. "all v1.2 milestone-audit IC items closed")
- **D-09:** Specific bullets to seed (planner expands during Phase 10 execution):
  - **Must-have:** zero critical AUDIT findings open; all v1.2 IC items closed (IC-01 ✓, IC-02 pending in Phase 12); new maintainer can run review unaided; no new recurring-error category in 2 consecutive sessions
  - **Should-have:** token use within 20% of v1.1 baseline; tier-2 covers ≥ 60% of markets per run; Notion-published reports require zero manual cleanup; ≥ 1 Phase 2 spike commit-worthy

### Phase 2 STR-02 criteria (sketch only)
- **D-10:** Phase 2's checklist is left as a placeholder section ("To be filled when Phase 2 enters its readiness milestone — populate using the same must-have / should-have pattern documented above"). Not detailed in this phase.

### Doc relationship to existing planning artifacts
- **D-11:** Inline summaries (2–3 lines per section) + links to source-of-truth docs (PROJECT.md, REQUIREMENTS.md, AUDIT.md, ROADMAP.md, CLAUDE.md). Reader gets the gist standalone; detail is one click away. No bulk content duplication.

### New-feature routing rubric
- **D-12:** STRATEGIC-OVERVIEW.md includes a "Where does this idea belong?" table with rows like:
  - Touches structural validator / AI review / Notion publish / corrections loop → **Phase 1** (current milestone)
  - Touches translation generation / drafting workflow → **Phase 2** (backlog until readiness)
  - Touches Superprof BO integration (URL-driven, Playwright) → **Phase 3** (backlog)
  - Bug or quick fix in shipped code → in-flight feedback / current phase
  - GSD workflow / process improvement → `~/.claude/get-shit-done/` config, not a project phase
- **D-13:** The rubric is the source of truth that the future `/gsd:submit-idea` skill (Phase 13) reads.

### Maintenance posture
- **D-14:** Living doc. Three-phase scope sections are stable. The "Phase 1 Status" section + STR-02 checklist get updated at the end of each milestone (natural ritual via `/gsd:complete-milestone`).

### Style & format (locked defaults — not discussed)
- **D-15:** Markdown. Standard heading hierarchy (H1 doc title → H2 phases → H3 subsections). Terse contract-style prose, no marketing language. Auto-commit per `commit_docs: true`.

### Claude's Discretion
- Exact section ordering inside the doc
- Table layouts and column widths
- Link formatting (inline vs. footnote-style)
- Wording of summary lines
- How visual the transition flow diagram is (ASCII vs. mermaid vs. none)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 10 requirements & boundaries
- `.planning/ROADMAP.md` §"Phase 10: Strategic Overview" — phase goal + 2 success criteria
- `.planning/REQUIREMENTS.md` — STR-01 + STR-02 specifications

### Phase 1 baseline (what the doc summarizes)
- `.planning/PROJECT.md` — current truth on validated/active/out-of-scope requirements, key decisions, constraints
- `.planning/AUDIT.md` — 34 findings with severity tags; remaining open items inform must-have / should-have gates
- `.planning/v1.2-MILESTONE-AUDIT.md` — IC-01 (closed Phase 11) and IC-02 (open, Phase 12) status — feeds the audit-derived gates
- `.planning/MILESTONES.md` — milestone history; informs the "living doc" update cadence
- `CLAUDE.md` — recurring error patterns + formality/variable rules; "follow specs literally" tone constraint

### Phase 2 hooks (referenced by name in the doc, not detailed)
- `.planning/REQUIREMENTS.md` §"Future Requirements (v2+)" — GEN-01, GEN-02, GEN-03 (Phase 2 deliverables already named)

### GSD primitives that the routing rubric points to
- `~/.claude/get-shit-done/` — `/gsd:add-backlog`, `/gsd:plant-seed`, `/gsd:insert-phase`, `/gsd:add-phase`, `/gsd:complete-milestone` (named in the rubric so readers know which command to run)

### Backlog — example of cross-phase idea capture pattern
- `.planning/phases/999.1-url-driven-translation-review/` — Phase 999.1 backlog entry; demonstrates how a Phase 3 idea is parked today

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- N/A — pure documentation phase. No code is built, refactored, or wired.

### Established Patterns
- All planning docs are Markdown in `.planning/` — STRATEGIC-OVERVIEW.md follows the same convention (sibling of PROJECT.md, etc.)
- `.planning/config.json` `commit_docs: true` triggers auto-commit on doc creation — applies here unchanged
- Existing GSD primitives (`add-backlog`, `plant-seed`, `insert-phase`, `complete-milestone`) provide all the capture mechanics — the doc only adds the *routing layer* on top

### Integration Points
- The doc is referenced by name in PROJECT.md (planner should add a link from PROJECT.md → STRATEGIC-OVERVIEW.md so the capstone is discoverable)
- The doc is the input contract for the future `/gsd:submit-idea` skill (Phase 13) — its routing table must be in a stable, parseable structure (Markdown table)
- The doc is updated at end of each milestone via `/gsd:complete-milestone` ritual — no automation built in this phase

</code_context>

<specifics>
## Specific Ideas

- User explicitly framed the transition pattern as **general** (1→2 AND 2→3), not Phase-1-only. The doc must read as "here is how phase transitions work in this project" with Phase 1 as the worked example.
- User wants the doc to make the answer to "should this be a new phase, a backlog item, or in-phase feedback?" deterministic — not a judgment call each time.
- Two-stage gate analogy "orange light / green light" landed clearly — keep that metaphor in the doc for reader recall.
- "Once we define the scope of the 3 phases later on, we can discuss specific examples" — user expects the planner to revisit transition specifics during planning, after the 3-phase scope sections are drafted.

</specifics>

<deferred>
## Deferred Ideas

### Phase 13 (proposed — not yet in roadmap)
- **Build `/gsd:submit-idea` as a global skill** in `~/.claude/get-shit-done/`. Walks the user through the routing rubric, then dispatches to the right existing GSD command (`add-backlog`, `plant-seed`, `insert-phase`, etc.). Reads the current project's `STRATEGIC-OVERVIEW.md` (or equivalent) to know which routing answers exist.

### To be defined when relevant phase opens
- **Specific Phase 2 spike topics** — defined when v1.5 readiness milestone opens
- **Phase 2 must-have / should-have checklist** — populated when Phase 2 enters readiness milestone, using the pattern documented here
- **Phase 3 scope detail** — current backlog entry (Phase 999.1: URL-driven review) hints at one Phase 3 deliverable; full Phase 3 scope is sketched in STRATEGIC-OVERVIEW.md but not detailed until Phase 3 enters its own discuss-phase
- **Architecture diagrams for Phase 2 / Phase 3** — explicitly out of scope for this phase (per D-02a)

### Out of scope for the document itself
- Hypothesized REQs (GEN-04, GEN-05, etc.) — belong to future Phase 2 discuss-phase
- Notion publishing of STRATEGIC-OVERVIEW.md — reader-facing artifact stays in repo for now; could be added later if team needs it

</deferred>

---

*Phase: 10-strategic-overview*
*Context gathered: 2026-04-28*
