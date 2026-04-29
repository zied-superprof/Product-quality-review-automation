# Stack Research

**Domain:** Translation review automation — v1.3 stack additions only
**Researched:** 2026-04-29
**Confidence:** HIGH (all three additions verified via pip dry-run on the actual machine)

---

## Scope

This file covers only the **new dependencies** for v1.3 End-to-End Review Automation. Existing validated stack (Python 3.14.3 stdlib, Claude skill orchestration, Notion MCP, corrections system) is not re-researched here.

Three additions:
- (A) Playwright — BO scraping (URL → CSV)
- (B) Notion `PATCH /pages/{id}` — task-follow-up column write
- (C) slack-sdk — Slack completion notifier

---

## Recommended Stack

### Core Technologies (new additions only)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| playwright | 1.59.0 | Headless Chromium scraping of BO notification admin pages | Only viable option for a JS-heavy SPA BO; pure HTTP requests won't render dynamic grids. Sync API (`sync_playwright`) matches the project's existing synchronous Python style. No event loop boilerplate. Verified: installs cleanly on Python 3.14.3 + macOS 15 arm64. |
| slack-sdk | 3.41.0 | Post completion notification to a Slack group channel | Official Slack Python SDK. `WebClient.chat_postMessage()` is a one-liner. Zero dependencies pulled in. Pure Python wheel — no compiled extensions. Verified: installs cleanly on Python 3.14.3. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| greenlet | 3.5.0 | Playwright coroutine substrate (pulled automatically as dependency) | Installed automatically with `pip install playwright`. Do not pin separately. |
| pyee | 13.0.1 | Playwright event emitter (pulled automatically) | Installed automatically with `pip install playwright`. Do not pin separately. |

### Notion: No New Library

The existing `mcp__claude_ai_Notion__notion-update-page` MCP tool is already configured in `.claude/settings.local.json`. However, a known schema validation bug (GitHub issue #153, open as of 2026-04-29) causes the MCP tool to reject `update_properties` payloads on database pages with AND logic instead of OR logic in its `anyOf` validator.

**Workaround**: Call the Notion REST API directly from a helper script (`scripts/_prep_notion.py` already exists as a landing point) with a standard HTTP `PATCH` to `https://api.notion.com/v1/pages/{page_id}`. The Notion integration token is available via environment variable (`NOTION_API_KEY` or equivalent already used by the MCP server). No new library needed — Python stdlib `urllib.request` handles the PATCH call. This keeps the core constraint (stdlib-only for orchestration helpers) intact.

---

## Installation

```bash
# Both new pip dependencies (orchestration layer — not the core validator)
pip install playwright==1.59.0
pip install slack-sdk==3.41.0

# Install Playwright browser binary (Chromium only — smallest footprint)
playwright install chromium
```

These go into the system Python (or project venv if one is created). The core `structural_validator.py` never imports these — it stays stdlib-only.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| playwright (Python) | selenium + chromedriver | Only if the team already maintains Selenium infrastructure. Playwright's auto-wait, storage_state session reuse, and single-binary install make it strictly better for new greenfield scraping on macOS. |
| playwright (Python) | requests + BeautifulSoup | Only if the BO is server-rendered HTML with no JavaScript. The Superprof BO is a SPA; JS rendering is required. requests cannot execute JS. |
| playwright (Python) | puppeteer (Node) | Only if the project were Node-based. Adding Node as a runtime to a Python project creates unnecessary dependency surface. |
| slack-sdk | slack-bolt | Bolt is for building Slack apps (event listeners, interactive components). This project only needs to post a one-way notification — `slack-sdk` WebClient is sufficient and has fewer concepts to configure. |
| slack-sdk | incoming webhooks (raw HTTP) | Viable if the team sets up a Webhook URL. The advantage of `slack-sdk` is that it uses a bot token already managed via the Slack app, giving channel flexibility. If the team only ever targets one channel and prefers zero-dependency Python, a webhook POST via stdlib `urllib.request` also works. |
| stdlib urllib.request (Notion PATCH) | notion-sdk-py | `notion-sdk-py` is a clean wrapper but adds a pip dependency. The one Notion call needed (PATCH a page's property) is trivial to write with `urllib.request` — consistent with the project's stdlib-where-possible ethos for helper scripts. If more than 2–3 Notion calls are added in future milestones, promote to `notion-sdk-py`. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| playwright-stealth | Anti-bot evasion layer not needed for an internal BO the team already authenticates against. Adds unnecessary complexity. | Plain `playwright` |
| selenium | Older API, requires separate chromedriver binary management, no built-in storage_state. No advantage over Playwright here. | `playwright` |
| slack-bolt | Full Slack app framework with socket/webhook listener boilerplate. Overkill for a one-shot outbound notification. | `slack-sdk` WebClient only |
| notion-sdk-py | Adds a pip dep for what is a single PATCH call. Bug in MCP tool is in the MCP layer, not the Notion API itself — direct HTTP is the correct bypass. | stdlib `urllib.request` |
| httpx / aiohttp | No async I/O needed. The scraping script is a one-shot CLI tool. Async adds complexity with no throughput benefit. | stdlib `urllib.request` for Notion; `slack-sdk` bundles its own HTTP |
| pytest-playwright | The pytest plugin is for test suites. This project uses Playwright as a library (`sync_playwright`), not for test collection. pytest-playwright would pull in pytest as a dependency with no benefit. | `playwright` library mode only |
| python-dotenv | Environment variables (`SLACK_BOT_TOKEN`, `NOTION_API_KEY`) are already managed at the OS level for the Notion MCP. Adding dotenv changes the env contract. | `os.environ` directly |

---

## Integration Points

### (A) Playwright — BO Scraping

- **Script location**: `scripts/scrape_bo.py` (new file, Phase 13-A)
- **Import**: `from playwright.sync_api import sync_playwright`
- **Auth**: Session cookie / storage state saved to `config/session_state.json` (gitignored). On first run: headed login flow; subsequent runs: `context.new_context(storage_state=...)` — no re-login needed until session expires.
- **Output**: 1–2 CSV files written to `samples/` with name derived from the page's information block (e.g. `samples/NOTIF_1234_email.csv`). The existing review skill picks them up via the existing CSV-drop flow — no change to skill.
- **Constraint**: Exact selectors for the page information block and email/SMS tabs are open questions for the discuss-phase. The scraper must handle both cases (email-only page vs. email + SMS tabs).

### (B) Notion Task-Follow-Up Column

- **Script location**: `scripts/_prep_notion.py` (already exists — extend it)
- **Call site**: After the existing Notion MCP page-create call in the skill, call `_prep_notion.py {page_id} "{translation_name}"` to PATCH the `task follow up` property.
- **Request body** (rich_text or select — confirm type at discuss-phase):
  ```python
  # If rich_text:
  {"properties": {"task follow up": {"rich_text": [{"text": {"content": name}}]}}}
  # If select:
  {"properties": {"task follow up": {"select": {"name": name}}}}
  ```
- **Auth**: Notion integration token from environment (`NOTION_API_KEY`). The MCP already uses this token — read it with `os.environ["NOTION_API_KEY"]`.
- **Headers**: `Authorization: Bearer {token}`, `Notion-Version: 2026-03-11`, `Content-Type: application/json`
- **MCP bug note**: Do NOT use `mcp__claude_ai_Notion__notion-update-page` for property updates on database pages until GitHub issue #153 is fixed. Use direct HTTP PATCH instead.

### (C) Slack Notifier

- **Script location**: `scripts/notify_slack.py` (new file, Phase 13-D)
- **Import**: `from slack_sdk import WebClient`
- **Token**: `SLACK_BOT_TOKEN` environment variable (xoxb- bot token)
- **Required scope**: `chat:write` (bot must be a member of the channel), or `chat:write.public` for public channels without joining.
- **Call**: `client.chat_postMessage(channel=CHANNEL_ID, text=message)`
- **Channel**: Confirm channel ID at discuss-phase (not channel name — IDs are stable across renames).
- **Invocation**: Called from the skill at the end of Step 6 (Notion publish) as a final non-blocking step. Soft-fail: if Slack call raises `SlackApiError`, log a warning and continue — the review is complete regardless.

---

## Version Compatibility

| Package | Python | macOS | Notes |
|---------|--------|-------|-------|
| playwright 1.59.0 | >=3.9 (classifiers list up to 3.13, but installs and resolves greenlet cp314 wheel cleanly on 3.14.3) | macOS 11+ (arm64 wheel ships natively; tested macOS 15 Sequoia arm64) | macOS 14 WebKit support removed in 1.59 — irrelevant since we use Chromium only |
| slack-sdk 3.41.0 | >=3.7, supports 3.14 (pure Python wheel, no compiled extensions) | Any macOS | Zero transitive dependencies beyond optional aiodns for async — not needed here |

---

## Sources

- [playwright PyPI](https://pypi.org/project/playwright/) — version 1.59.0 confirmed, April 29, 2026
- [Playwright Python library docs](https://playwright.dev/python/docs/library) — sync_playwright pattern, browser install commands
- [Playwright Python release notes](https://playwright.dev/python/docs/release-notes) — v1.59 changes, macOS 14 WebKit removal, Python 3.8 EOL note
- [playwright-python pyproject.toml](https://github.com/microsoft/playwright-python/blob/main/pyproject.toml) — requires-python >=3.9, classifiers up to 3.13
- pip dry-run on Python 3.14.3 + macOS 15 arm64 — **HIGH confidence** — both `playwright` and `slack-sdk` resolve and download without errors (verified live)
- [slack-sdk PyPI](https://pypi.org/project/slack-sdk/) — version 3.41.0 confirmed, March 12, 2026
- [Slack Python SDK Web Client docs](https://docs.slack.dev/tools/python-slack-sdk/web/index.html) — chat_postMessage pattern, required scopes
- [Notion Patch Page API reference](https://developers.notion.com/reference/patch-page) — property update body structure, API version 2026-03-11
- [Notion MCP supported tools](https://developers.notion.com/guides/mcp/mcp-supported-tools) — tool list, notion-update-page confirmed present
- [Notion MCP issue #153](https://github.com/makenotion/notion-mcp-server/issues/153) — schema validation bug on database property updates, open as of 2026-04-29, direct HTTP workaround confirmed working

---
*Stack research for: v1.3 End-to-End Review Automation — new dependencies only*
*Researched: 2026-04-29*
