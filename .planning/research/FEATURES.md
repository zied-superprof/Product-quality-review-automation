# Feature Research

**Domain:** End-to-end translation review automation (input scraping + output notifications)
**Researched:** 2026-04-29
**Confidence:** HIGH (existing system well-understood; new integrations verified against official docs)

---

## Context

This research covers only the **new** v1.3 features. The existing CSV-drop pipeline, AI review, Notion report publishing, correction loop, and batch feedback routing are already shipped and out of scope.

The three new feature categories are:

| Category | REQ-ID prefix | Summary |
|----------|---------------|---------|
| BO scraping / input automation | INGEST | URL → CSV extraction via Playwright |
| Notion property write | NOTION | Populate "task follow up" column on publish |
| Slack notification | SLACK | Post completion message to group channel |

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that must be present for v1.3 to be a usable, complete release. If any of these are missing, the feature feels broken or half-done.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **INGEST-01** URL → CSV extraction | The whole point of v1.3 is removing the manual CSV export step. Without working extraction, the new entry point does not exist. | HIGH | Playwright must authenticate, click email/SMS tabs, parse translation grid. Selector discovery is the hard work. |
| **INGEST-02** Auto-naming from page info block | If the CSV is named `download.csv` or a timestamp, the report filename and Notion page title are garbage. Named files are a hard requirement for the downstream pipeline. | LOW | Translation name is on the page. Extraction is CSS selector work, not logic. |
| **INGEST-03** Coexistence with CSV-drop flow | Existing users (and existing tests) must not break. The two entry points must be additive, not mutually exclusive. | LOW | New `/review-translations-url` skill (or URL argument detection) sits alongside the existing skill. No shared state conflicts. |
| **INGEST-04** Session/auth reuse | Superprof BO requires login. Scraping fails entirely if the session is not maintained. Must not require Juan to log in on every run. | MEDIUM | Playwright `storage_state` pattern: log in once interactively, save to `.auth/bo-session.json`, reuse on every subsequent run. Session expiry needs detection + graceful re-auth prompt. |
| **NOTION-01** "Task follow up" column populated on publish | The column already exists on the Reports DB. If it is left blank, the Notion row is incomplete and Juan must fill it in manually — exactly what v1.3 is trying to eliminate. | LOW-MEDIUM | Column type must be confirmed (select vs rich_text vs title). MCP `notion-update-page` has a known schema-validation bug for database page properties (GitHub issue #153, closed via PR #173 — verify fix is deployed before relying on it). Fallback: direct Notion API PATCH call. |
| **SLACK-01** Completion message posted to group channel | A run that finishes silently gives no signal. The reviewer has no way to know a new Notion report is ready without polling. The whole point of the notifier is signal-on-completion. | LOW | Incoming webhook is sufficient. Webhook URL is a secret that must be stored outside version control. |
| **SLACK-02** Message contains Notion page link + summary | A "done" ping without a link forces the receiver to search Notion. The link is the actionable part. Summary (N errors, N warnings, markets count) gives triage context before opening the page. | LOW | Data is already available after Step 6d. No new computation required. |

### Differentiators (Valuable but Not Required for v1.3 to Ship)

Features that improve the experience meaningfully but whose absence does not make v1.3 feel broken.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **INGEST-05** Email + SMS as separate CSVs when both tabs present | Most notifications have both email and SMS variants. Producing one CSV per variant means each gets its own review report and Notion page — cleaner audit trail. | LOW | Logic: if SMS tab exists and is non-empty, write `[name]_sms.csv`; always write `[name]_email.csv`. The review pipeline already handles multiple CSV invocations. |
| **INGEST-06** Session expiry detection with graceful re-auth prompt | If the stored session has expired, the extraction silently fails or returns the login page HTML. Detection (check for redirect to login URL or page title "Login") turns a confusing failure into a clear prompt: "Session expired — re-authenticate." | LOW-MEDIUM | Adds ~15 lines of error-handling logic. The alternative (fail opaquely) is poor UX. |
| **NOTION-02** Notion publish confirmation in Slack message | Instead of just "run complete," the Slack message confirms whether Notion publish succeeded or fell back to local-only. Reduces the need to check the Notion page manually just to confirm it published. | LOW | One additional field in the Slack payload. Data already in scope at notification time. |
| **SLACK-03** Configurable webhook URL via config file or env var | Hardcoding a webhook URL in the skill definition or a config file is fragile (URL rotation, org changes). An env var or `config/slack.json` makes rotation a one-line change. | LOW | `SLACK_WEBHOOK_URL` env var is the canonical pattern. Stdlib `os.environ.get()` — no pip required. |

### Anti-Features (Do Not Build These in v1.3)

| Feature | Why Requested | Why It Is a Problem | What to Do Instead |
|---------|---------------|---------------------|--------------------|
| **Scheduler / cron / polling** | "Run automatically every time a notification is published" | Adds always-on infrastructure (cron job, daemon, cloud function) that has no existing host, creates race conditions if two runs overlap, and requires handling BO pagination/listing — which is out of scope. The current model is trigger-on-demand, which is correct for v1.3. | Keep the manual invocation model. Juan pastes the URL, runs the skill. |
| **Diff / delta detection** ("only review what changed") | Avoid re-reviewing unmodified languages | Requires storing a previous extraction and computing a diff per cell. Complex, fragile, and adds a new failure mode. The review pipeline already de-duplicates findings via the corrections log. | Run the full review every time. It is fast enough at current batch sizes. |
| **BO write-back** (push corrections into the BO) | Complete the loop by writing corrected translations back | This is Phase 3 scope (Backoffice Integration), not Phase 1. Premature write-back before the review quality is fully validated is a data-safety risk. | Defer to Phase 3 explicitly. |
| **Multi-URL batch mode** ("review 5 notifications at once") | Process an entire sprint's worth of notifications in one command | Multiplies Playwright session complexity, Notion page count, and Slack noise. Each notification is its own review report by design. | Run the skill once per notification. The loop is manual by intent. |
| **Slack thread replies per market** | Granular per-market status in Slack | Makes the Slack channel noisy and couples the notification format to the report structure. Slack is for "done + link," not a secondary report. | Put all detail in Notion. Slack message is a pointer, not a report. |
| **Playwright screenshot capture for debugging** | Useful when selectors break | Screenshots bloat `samples/` and require cleanup logic. Debugging-only value does not justify permanent infrastructure. | Use `page.pause()` or a headful run when debugging locally. Never add screenshots to the shipped script. |

---

## Feature Dependencies

```
INGEST-01 (URL → structured data)
    └──requires──> INGEST-04 (session/auth reuse)
    └──produces──> INGEST-02 (auto-named CSV)
                       └──feeds──> existing review pipeline (Step 1 onward)
                                       └──produces──> Notion page URL
                                                           └──required by──> SLACK-01/02
                                       └──produces──> NOTION-01 (task follow up write)

INGEST-05 (email + SMS split)
    └──enhances──> INGEST-01 (adds second output CSV)
    └──independent of──> NOTION-01, SLACK-01

INGEST-06 (session expiry detection)
    └──enhances──> INGEST-04

NOTION-01 (task follow up column)
    └──requires──> knowing translation name (from INGEST-02 OR from existing CSV filename)
    └──note: also applies to CSV-drop flow — INGEST-02 is not a prerequisite

SLACK-01/02 (completion notifier)
    └──requires──> Notion page URL (from existing Step 6d)
    └──requires──> run summary data (errors/warnings counts — already computed in Step 5)
    └──independent of──> INGEST-01 (fires whether entry point is URL or CSV-drop)

NOTION-02 (publish confirmation in Slack)
    └──enhances──> SLACK-01
    └──requires──> NOTION-01 success/failure status
```

### Dependency Notes

- **NOTION-01 is independent of INGEST-01.** The "task follow up" column write is a Notion publishing enhancement that applies to both the new URL-driven flow AND the existing CSV-drop flow. It should be implemented as an extension to Step 6 of the existing skill, not gated behind Playwright.

- **SLACK-01/02 are also independent of INGEST-01.** The notifier fires at end-of-run regardless of how the CSV was produced. This means SLACK can be implemented as a new Step 8 appended to the existing skill without touching the Playwright work at all.

- **INGEST-01 is the only feature that requires a new skill or a new entry path.** Everything else extends the existing `/review-translations` skill.

---

## MVP Definition

### v1.3 Must Ship With

These are the table-stakes features. v1.3 is not done without them.

- [x] **INGEST-01** — URL → CSV extraction (Playwright, email + SMS tabs, both content types)
- [x] **INGEST-02** — Auto-named CSV from page information block
- [x] **INGEST-03** — Coexistence: existing CSV-drop flow unaffected
- [x] **INGEST-04** — Session/auth reuse (`storage_state` pattern, graceful failure on expiry)
- [x] **NOTION-01** — "Task follow up" column populated on every report publish
- [x] **SLACK-01** — Completion message posted to configured group channel
- [x] **SLACK-02** — Message contains Notion page URL and run summary (counts)

### Add After v1.3 Core Works

Ship these once the core path is stable and tested on real BO pages.

- [ ] **INGEST-05** — Email + SMS as separate CSVs (add after confirming both tabs are consistently present and non-empty in real notifications)
- [ ] **INGEST-06** — Session expiry detection with re-auth prompt (add after first session expiry is encountered in practice)
- [ ] **SLACK-03** — Configurable webhook URL via env var (add if webhook URL ever needs rotation; low urgency)
- [ ] **NOTION-02** — Publish confirmation status in Slack message (add once NOTION-01 is stable and the failure rate is known)

### Defer to v1.4+

- Everything in the Anti-Features table above.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| INGEST-01 URL → CSV | HIGH | HIGH | P1 |
| INGEST-02 Auto-naming | HIGH | LOW | P1 |
| INGEST-03 Coexistence | HIGH | LOW | P1 |
| INGEST-04 Auth reuse | HIGH | MEDIUM | P1 |
| NOTION-01 Task follow up | HIGH | LOW-MEDIUM | P1 |
| SLACK-01 Completion ping | HIGH | LOW | P1 |
| SLACK-02 Link + summary | HIGH | LOW | P1 |
| INGEST-05 Email+SMS split | MEDIUM | LOW | P2 |
| INGEST-06 Expiry detection | MEDIUM | LOW | P2 |
| SLACK-03 Configurable URL | LOW | LOW | P2 |
| NOTION-02 Publish confirm | LOW | LOW | P2 |

---

## Hidden Complexity Notes

These are the places where v1.3 is harder than it looks. Each deserves explicit attention in the requirements phase.

### INGEST auth flow

The BO auth mechanism is unknown at research time (SSO, session cookie, JWT?). Playwright `storage_state` works for cookie- and localStorage-based auth. If the BO uses SSO with a separate identity provider, the login flow may involve redirects that Playwright can still handle, but the initial auth must be done in a headed (visible) browser — not headless — so Juan can complete any MFA or SSO step. The saved state is then reused headlessly. **Open question for requirements phase: what is the BO auth mechanism exactly?**

### INGEST selector fragility

Playwright selectors are brittle when the page structure changes. The BO admin is an internal Superprof tool — it will be updated. Selectors should target stable attributes (IDs, `data-*` attributes, ARIA labels) over positional CSS. **Requires an inspection session on the actual BO page before implementation.** This is why selector discovery is listed as an "open question" in ROADMAP.md and must be resolved in the discuss-phase.

### NOTION-01 column type

The "task follow up" column type on the Reports DB is unconfirmed. The write call differs significantly depending on type:
- `rich_text`: `{"rich_text": [{"type": "text", "text": {"content": "..."}}}]}`
- `select`: `{"select": {"name": "..."}}`
- `title`: cannot be set via update (it is the page name)

Additionally, the Notion MCP `notion-update-page` tool had a schema validation bug (GitHub issue #153) for database page property updates as of November 2025. A fix was merged (PR #173) but deployment status must be verified before the implementation phase. If unresolved, the fallback is a direct Notion API PATCH call via `urllib.request` (no pip required, maintains stdlib-adjacent simplicity).

### SLACK webhook secret management

The webhook URL is a credential. It must not be committed to the repo. The implementation must store it in one of: `config/slack.json` (gitignored), an environment variable (`SLACK_WEBHOOK_URL`), or a user prompt at first run. The skill spec must be explicit about where this value is read from. If it is missing, the step must fail with a clear error, not silently.

### Notion MCP publish in Slack

The Slack notifier needs the Notion page URL, which comes from Step 6d of the existing skill. The URL is available in the session context at notification time. No additional API call is required — it is a data-passing problem, not a new integration problem.

### Playwright pip dependency

Playwright requires `pip install playwright` + `playwright install chromium`. This breaks the project's **stdlib-only constraint** for the core validator — but Playwright is a new scraping script (`scripts/scrape_bo.py`), not the validator. The constraint was always scoped to `structural_validator.py`. The new script can have its own lightweight install step documented in README. This must be called out explicitly in requirements to avoid confusion.

---

## Sources

- [Playwright Python — Authentication](https://playwright.dev/python/docs/auth) — official docs, storage_state pattern. HIGH confidence.
- [Playwright Python — Installation](https://playwright.dev/python/docs/library) — pip install + browser binary install. HIGH confidence.
- [Notion MCP supported tools](https://developers.notion.com/guides/mcp/mcp-supported-tools) — notion-update-page tool capabilities. MEDIUM confidence (tool signature not fully specified).
- [Notion MCP notion-update-page bug #153](https://github.com/makenotion/notion-mcp-server/issues/153) — schema validation failure on database page property updates; fix proposed in PR #173. MEDIUM confidence (fix merged but deployment status unclear).
- [Notion API — working with databases](https://developers.notion.com/docs/working-with-databases) — property update format (rich_text, select, etc.). HIGH confidence.
- [Slack — sending messages using incoming webhooks](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/) — webhook URL pattern, POST format. HIGH confidence.
- [Slack webhook Python urllib stdlib pattern](https://keestalkstech.com/simple-python-code-to-send-message-to-slack-channel-without-packages/) — stdlib-compatible POST via `urllib.request`. MEDIUM confidence (pattern straightforward but not the canonical source).

---

*Feature research for: v1.3 End-to-End Review Automation (INGEST + NOTION + SLACK)*
*Researched: 2026-04-29*
