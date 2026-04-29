# Project Research Summary

**Project:** Translation Quality Review Automation — v1.3 End-to-End Review Automation
**Domain:** Claude-skill-orchestrated translation review tool — adding URL ingestion + Slack output
**Researched:** 2026-04-29
**Confidence:** HIGH (stack verified via pip dry-run; architecture patterns confirmed against official docs; pitfalls sourced from live GitHub issues)

---

## Executive Summary

v1.3 extends an already-working Python review pipeline with three independent capabilities: (A) Playwright-driven BO scraping that converts a back-office admin URL into a named CSV, (B) a Notion "task follow up" column write on every report publish, and (C) a Slack completion notifier. The core design insight from all four research files is that the existing CSV boundary is the right convergence point: both entry paths (URL scraping and manual CSV-drop) converge at `samples/[name].csv` before the pipeline sees them, so the entire review pipeline from Step 1 onward needs zero modification. Architecture recommends building the three capabilities in strict isolation phases (A through D) to guarantee the existing CSV-drop flow is never broken mid-rollout.

The recommended stack is: Playwright 1.59.0 (`pip install`) for BO scraping; stdlib `urllib.request` for both the Notion PATCH fallback and the Slack notifier. The stdlib-only Slack approach is the synthesis recommendation — a Slack incoming webhook POST is a trivial HTTPS JSON call requiring no SDK, which preserves the project's "no pip install for helpers" ethos while still delivering SLACK-01/02. `slack-sdk` remains a valid alternative if channel flexibility is needed later, but it is not the recommended starting point. Playwright is the one unavoidable pip install, and it is intentionally isolated to `scripts/extract_bo_page.py` so `structural_validator.py` remains stdlib-only and import-clean.

The highest-risk item is the Notion MCP `notion-update-page` bug (GitHub issue #153, fix merged in PR #173 but deployment status unconfirmed as of 2026-04-29). The safe synthesis: treat the MCP tool as untrusted for database page property writes; always use a direct HTTP PATCH via `urllib.request` as the primary path; add an assertion-based read-back after every write. Four questions cannot be resolved from research alone and must be addressed in a discuss-phase before any code is written: BO auth mechanism, "task follow up" column type, Slack channel/webhook URL, and stable BO CSS selectors.

---

## Open Questions — Discuss-Phase Required

These four blockers are identified consistently across all four research files. No implementation phase should start until each is resolved:

| # | Question | Blocks | How to Resolve |
|---|----------|--------|----------------|
| OQ-1 | What is the BO auth mechanism? (SSO, session cookie, JWT, MFA?) | INGEST-01, INGEST-04 | Ask the BO team or inspect the network tab during a manual BO login |
| OQ-2 | What is the "task follow up" column type in the Reports DB? (select, rich_text, status?) | NOTION-01 | Inspect via `mcp__claude_ai_Notion__notion-retrieve-database` before Phase C |
| OQ-3 | What is the Slack channel ID and how will the webhook URL be provisioned? | SLACK-01 | Confirm with Juan — channel ID (not name), and decide: bot token or incoming webhook |
| OQ-4 | What are the stable CSS/ARIA selectors for the BO translation grid and email/SMS tabs? | INGEST-01, INGEST-02 | Requires an inspection session on the actual BO page (headed Playwright + DevTools) |

---

## Key Findings

### Recommended Stack

The existing pipeline (Python 3.14.3 stdlib, Claude skill orchestration, Notion MCP, corrections system) is unchanged. v1.3 adds exactly two pip dependencies:

**Core technologies (new additions only):**
- **Playwright 1.59.0** — headless Chromium scraping of the BO admin SPA. The only viable option for a JavaScript-rendered BO interface; `requests + BeautifulSoup` cannot execute JS. Sync API (`sync_playwright`) matches the project's synchronous Python style. Verified: installs cleanly on Python 3.14.3 + macOS 15 arm64.
- **stdlib `urllib.request` (Slack)** — Slack incoming webhook POST. No SDK needed for a one-way outbound notification. Zero pip footprint. Keeps helper scripts consistent with the project ethos.
- **stdlib `urllib.request` (Notion)** — Notion REST API PATCH (`https://api.notion.com/v1/pages/{page_id}`). Direct HTTP bypass for the confirmed MCP bug. Uses the same `NOTION_API_KEY` already in the environment.

**Resolved contradiction — Slack transport:**
STACK.md recommends `slack-sdk 3.41.0`; ARCHITECTURE.md and FEATURES.md both recommend stdlib `urllib.request` to a Slack incoming webhook. **Recommendation: use stdlib `urllib.request`.** A webhook POST is 15 lines of standard Python, there is no channel-flexibility requirement that makes a bot token necessary for v1.3, and keeping helper scripts pip-free reduces onboarding friction. If channel targeting ever needs to be dynamic, promote to `slack-sdk` at that point.

**Resolved contradiction — Notion MCP bug:**
STACK.md acknowledges the bug but notes a fix was merged (PR #173). PITFALLS.md rates the fix as "deployment status unconfirmed" and warns the MCP can fail silently. **Recommendation: treat the MCP as untrusted for database property writes.** Always use direct HTTP PATCH as the primary implementation path. Add a post-write read-back assertion regardless of which path is used.

### Expected Features

**Must have — v1.3 table stakes (P1):**
- **INGEST-01** — URL to CSV extraction (Playwright, email tab, SMS tab if present)
- **INGEST-02** — Auto-named CSV derived from the page information block
- **INGEST-03** — Coexistence: existing CSV-drop flow unaffected at all phases
- **INGEST-04** — Session/auth reuse via Playwright `storage_state`; graceful fail on expiry
- **NOTION-01** — "Task follow up" column populated on every Notion report publish (applies to both URL and CSV-drop flows)
- **SLACK-01** — Completion message posted to configured Slack group channel
- **SLACK-02** — Message contains Notion page URL and run summary (error/warning counts)

**Should have — add after v1.3 core is stable (P2):**
- **INGEST-05** — Email and SMS as separate named CSVs when both tabs are non-empty
- **INGEST-06** — Session expiry detection with actionable re-auth prompt
- **SLACK-03** — Configurable webhook URL via `SLACK_WEBHOOK_URL` env var
- **NOTION-02** — Publish success/failure status in Slack message

**Defer to v1.4+:**
- Scheduler / cron / polling
- Diff / delta detection (only review what changed)
- BO write-back (push corrections into the BO)
- Multi-URL batch mode
- Slack thread replies per market

**Independence note:** NOTION-01 and SLACK-01/02 do not depend on INGEST-01. They extend the existing skill and fire whether the CSV arrived via URL extraction or manual drop. Phases C and D can be built and shipped independently of Phase A.

### Architecture Approach

The architecture uses the existing CSV file in `samples/` as the immutable convergence boundary between the two entry paths. The Playwright extractor (`scripts/extract_bo_page.py`) is a pure side-effecting script: it authenticates via a persisted `storage_state` JSON file, navigates the BO page, writes named CSV(s) to `samples/`, prints the path(s) to stdout, and exits. The review skill's Step 0 detects whether the argument is a URL or a file path, calls the extractor if it is a URL, then hands off to Step 1 — which is identical for both paths. Slack and Notion extensions live entirely in Step 6 of the existing skill.

**Major components:**
1. **`scripts/extract_bo_page.py`** (new) — Playwright URL-to-CSV extractor; reads `.playwright/auth/bo_state.json`; writes to `samples/`
2. **`scripts/_setup_bo_auth.py`** (new) — one-time interactive Playwright login; saves `bo_state.json`; never called from the skill
3. **`scripts/_notify_slack.py`** (new) — stdlib `urllib.request` POST to Slack incoming webhook; soft-fail; called from Step 6d
4. **`scripts/_prep_notion.py`** (extend) — add direct HTTP PATCH for "task follow up" property; bypasses MCP tool for this property
5. **`.claude/commands/review-translations.md`** (modify) — Step 0: URL mode detection + extractor call; Step 6c: extend properties payload; Step 6d: add Slack call
6. **`config/v1.3.json`** (new) — BO base URL, Slack webhook URL (sourced from env var), Playwright selectors

### Critical Pitfalls

1. **BO session cookie committed to git** — Add `.playwright/auth/` to `.gitignore` as the absolute first commit of Phase A, before any auth code is written. Run `git check-ignore -v` to confirm before proceeding. Recovery if committed: rotate the BO account password immediately, purge history with `git filter-repo`.

2. **Notion MCP `notion-update-page` silent failure** — The anyOf schema validation bug (issue #153) causes the MCP tool to silently no-op on database page property writes. Always use direct HTTP PATCH via `urllib.request` as the primary path. Always read-back the "task follow up" column value after writing to assert it matches the expected value.

3. **BO auth silently landing on the login page** — After `page.goto(bo_url)`, immediately assert the resulting URL does not contain `/login`. If it does, exit with `BOAuthExpiredError: rerun scripts/_setup_bo_auth.py`. Never allow a login-page CSV to enter the pipeline.

4. **Playwright selector brittleness on a live internal admin UI** — Use text-content and ARIA role selectors (`page.get_by_role("tab", name="Email")`) over CSS class selectors. Add a row-count assertion before writing any CSV — a partial extraction must raise an error, not produce a short file.

5. **CSV-drop flow broken mid-rollout** — Encode coexistence as an explicit acceptance criterion on every phase plan (A through D). After any change to `scripts/`, `config/`, or `review-translations.md`, run a smoke test of the CSV-drop path with a known-good CSV before committing.

---

## Implications for Roadmap

The four research files agree on a 4-phase build order. The ordering is dictated by two constraints: (a) the Playwright extraction path must be verified end-to-end before it is wired into the skill, and (b) NOTION-01 and SLACK-01/02 are independent of INGEST-01 and can be built after or in parallel. The discuss-phase must resolve OQ-1 through OQ-4 before any phase begins.

### Pre-work: Discuss-Phase (not a build phase)

**Rationale:** OQ-1 through OQ-4 are genuine blockers. Starting Phase A without knowing the BO auth mechanism or Phase C without knowing the Notion column type will produce wasted or incorrect code.
**Delivers:** Answers to all four open questions documented in the phase plan before any implementation starts.
**Addresses:** OQ-1 (BO auth), OQ-2 (Notion column type), OQ-3 (Slack channel/webhook), OQ-4 (BO selectors)

---

### Phase A — Playwright BO Extraction (URL to CSV on disk)

**Rationale:** The highest-risk, highest-unknowns phase. Must be built and validated in complete isolation before touching the skill. No downstream code should depend on it until it produces correct CSVs on real BO pages.
**Delivers:** `scripts/extract_bo_page.py` and `scripts/_setup_bo_auth.py`; correctly named, complete CSVs from a live BO URL; `.playwright/auth/` gitignored; coexistence verified.
**Addresses:** INGEST-01, INGEST-02, INGEST-04
**Avoids:** Pitfalls 1 (session cookie in git), 3 (silent login redirect), 4 (selector brittleness), and partial CSV entering the pipeline
**Coexistence gate:** CSV-drop smoke test must pass before Phase A is considered done.
**Research flag:** Requires an inspection spike on the actual BO page to determine stable selectors (OQ-4). Time-box to 1-2 hours; document in LEARNINGS before writing production selectors.

---

### Phase B — Skill Integration (URL Mode in Step 0)

**Rationale:** Only wires Phase A output into the skill once Phase A is proven. Step 0 detection is a small, isolated change; the rest of the pipeline is untouched.
**Delivers:** `review-translations.md` Step 0 extended with URL mode detection; end-to-end test confirming URL → extract → review → report produces identical output to CSV-drop flow.
**Addresses:** INGEST-01 (skill-integrated), INGEST-03 (coexistence maintained in the skill)
**Avoids:** Anti-pattern: modifying the skill before the extractor is proven end-to-end.
**Research flag:** Standard pattern — no additional research needed if Phase A is complete.

---

### Phase C — Notion Task Follow-Up Column Write

**Rationale:** Independent of INGEST. Can be built after Phase A or in parallel. Addresses a gap that affects every existing publish, not just the new URL-driven flow.
**Delivers:** "Task follow up" column populated on every Notion report page (URL-driven and CSV-drop). Post-write read-back assertion confirming the value was actually set.
**Addresses:** NOTION-01
**Avoids:** Pitfall 2 (Notion MCP silent failure) — direct HTTP PATCH is the primary path.
**Implementation note:** First task of Phase C is to call `mcp__claude_ai_Notion__notion-retrieve-database` and record the exact type of "task follow up" (OQ-2). Write the payload for that confirmed type.
**Research flag:** Standard pattern once column type is confirmed. Direct HTTP PATCH to Notion API is well-documented.

---

### Phase D — Slack Completion Notifier

**Rationale:** Fully additive. The notifier fires at the end of Step 6 regardless of how the CSV was produced. Zero risk to existing functionality when wrapped in a soft-fail block.
**Delivers:** `scripts/_notify_slack.py`; Slack message in the configured channel after every completed review run, containing the Notion page URL and run summary (SLACK-01, SLACK-02).
**Addresses:** SLACK-01, SLACK-02
**Avoids:** Slack webhook URL committed to git — use `SLACK_WEBHOOK_URL` env var; document the variable name in README/CLAUDE.md, never the value.
**Implementation note:** Soft-fail is mandatory — a Slack POST failure must never abort a completed review. The `.md` report on disk is always the canonical deliverable.
**Research flag:** Standard pattern — incoming webhook POST is well-documented. No research phase needed.

---

### Phase Ordering Rationale

- **A before B** — the convergence-point architecture requires the extractor to be validated independently before being wired into the skill. This is the single hard ordering constraint.
- **C and D are independent of A and B** — NOTION-01 and SLACK-01/02 extend Step 6 of the existing skill without touching the CSV or extraction logic. They could ship before Phase A if needed (e.g. if the BO auth is blocked by organizational delays).
- **Discuss-phase before all build phases** — OQ-1 through OQ-4 are genuine blockers. Attempting Phase A without OQ-1 (auth mechanism) or OQ-4 (selectors) produces throwaway code.
- **INGEST-05 (email+SMS split) deferred to P2** — Depends on confirming that SMS tabs are consistently populated in real BO pages; this is a field observation, not a research question.

---

### Research Flags

**Phases requiring deeper discovery before implementation:**
- **Phase A (BO extraction):** Requires a headed Playwright inspection session on the actual BO page to determine stable selectors (OQ-4). Cannot be substituted with external research.

**Phases with standard, well-documented patterns (skip research-phase):**
- **Phase B (skill integration):** Standard URL detection + Bash subprocess call. No research needed.
- **Phase C (Notion column write):** Direct HTTP PATCH is standard Notion API. One confirm step (OQ-2) is a lookup, not research.
- **Phase D (Slack notifier):** Stdlib webhook POST is fully documented. No research needed.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Both pip packages verified via dry-run on Python 3.14.3 + macOS 15 arm64. Stdlib alternatives confirmed working via official docs. |
| Features | HIGH | Existing system is well-understood. New features are small, bounded integrations with clear API contracts. |
| Architecture | HIGH | Convergence-point pattern confirmed against the existing skill definition and project structure. Code samples in ARCHITECTURE.md are complete and runnable. |
| Pitfalls | HIGH (Notion MCP bug, secrets), MEDIUM (BO-specific selectors) | Notion MCP issue #153 is a confirmed live GitHub issue. BO selector strategy is based on general Playwright best practices; exact selectors require live BO access to validate. |

**Overall confidence: HIGH** — with the explicit caveat that OQ-1 through OQ-4 contain unknowns that no external research can resolve. These require human input or a live BO inspection session.

### Gaps to Address

- **OQ-1 — BO auth mechanism:** Unknown until Juan or the BO team confirms it. If SSO with an external identity provider is involved, the Playwright login flow may involve redirects or MFA. Discover before Phase A begins.
- **OQ-2 — "Task follow up" column type:** Call `notion-retrieve-database` at the start of Phase C. The write payload format differs significantly by type; the wrong payload causes a silent Notion failure.
- **OQ-3 — Slack channel/webhook:** Juan must confirm the target channel ID and decide between an incoming webhook URL (recommended) or a bot token. Webhook provisioning happens in Slack app settings.
- **OQ-4 — BO selectors:** Requires a headed Playwright session on the real BO page. Cannot be predicted from external research. This is the #1 long-term maintenance risk for the Playwright extractor.
- **Notion MCP bug #153 deployment status:** PR #173 was merged but whether it has been deployed to the MCP server used by this project is unconfirmed. Treat as untrusted until a post-write read-back test on a real database page confirms the fix is live.

---

## Sources

### Primary (HIGH confidence)
- Playwright Python official docs (playwright.dev/python) — sync_playwright, storage_state, auth, selectors best practices
- Slack Incoming Webhooks docs (docs.slack.dev) — webhook POST format, channel lock-in behavior
- Notion REST API reference (developers.notion.com) — PATCH /pages/{id} property update body, API version 2026-03-11
- Project source files: `.claude/commands/review-translations.md`, `CLAUDE.md`, `.planning/ROADMAP.md` — existing pipeline structure confirmed

### Secondary (MEDIUM confidence)
- makenotion/notion-mcp-server GitHub issue #153 — schema validation bug on database page property updates; fix in PR #173, deployment status unconfirmed
- makenotion/notion-mcp-server GitHub issue #67 — body object parsed as string bug
- Playwright PyPI / pyproject.toml — Python 3.14.3 + macOS 15 arm64 compatibility confirmed via pip dry-run

### Tertiary (LOW confidence — requires field validation)
- BO-specific selector strategy — based on general Playwright best practices; must be validated against the actual BO admin UI
- BO auth mechanism — assumed session cookie; must be confirmed against the actual BO login flow

---

*Research completed: 2026-04-29*
*Ready for roadmap: yes — pending discuss-phase resolution of OQ-1 through OQ-4*
