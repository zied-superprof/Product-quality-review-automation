# External Integrations

**Analysis Date:** 2026-04-08

## APIs & External Services

**Not Applicable:**
- No external APIs, web services, or third-party cloud integrations
- All processing is local and self-contained
- Tool operates entirely on input CSV files and local configuration

## Data Storage

**Databases:**
- Not used - Tool is file-based only

**File Storage:**
- Local filesystem only
  - Input: `samples/` directory (user drops CSV files here)
  - Output: `reports/` directory (generated review reports in Markdown format)
  - Learning system: `corrections/corrections_log.json` in project root
  - Configuration: `config/` directory

**Caching:**
- None — state is stored in JSON files, not in-memory cache

## Authentication & Identity

**Auth Provider:**
- Not applicable - No external authentication required
- Tool operates with file system permissions only

## Monitoring & Observability

**Error Tracking:**
- None - Errors logged to stdout/stderr during execution
- Location: Python stderr output (script invocation logs)

**Logs:**
- Console-based only (no logging framework configured)
- Error messages printed to Python stderr via `file=sys.stderr`
- Success messages printed to stdout

## CI/CD & Deployment

**Hosting:**
- Local execution only (macOS tested)
- Not deployed to cloud or server infrastructure
- Requires Python 3.x runtime on user's machine

**CI Pipeline:**
- None - No automated CI/CD pipeline configured
- Manual execution via Claude skill `/review-translations`

## Environment Configuration

**Required env vars:**
- None - No environment variables used

**Secrets location:**
- Not applicable - No API keys, tokens, or credentials used
- File access controlled by filesystem permissions only

## Webhooks & Callbacks

**Incoming:**
- None - Tool receives no webhooks

**Outgoing:**
- None - Tool makes no external HTTP requests

## Claude Integration

**Single Integration Point:**
- Claude skill: `.claude/commands/review-translations.md`
  - Orchestrates the full review workflow
  - Calls `scripts/structural_validator.py` for deterministic checks
  - Performs AI-driven linguistic review inline
  - Generates and writes report output

**Data Exchange:**
- Python script outputs JSON to stdout
- Claude reads JSON and transforms into report Markdown
- No streaming, no long-lived connections

## Configuration Dependencies

**Internal Configuration Sources:**
- `config/label_patterns.json` - Template variable syntax and validation rules (loaded by validator)
- `config/tone_guidelines.json` - Formality and tone rules per language (used by Claude during AI review)
- `config/languages.json` - Language metadata (40+ languages, formality levels, encoding info)
- `config/variables.csv` - Complete variable catalog
- `corrections/corrections_log.json` - Accumulated learned rules from previous reviews

**Note:** These are all local files with no external dependencies or dynamic fetching.

## Import Dependencies

**Python Standard Library Only (Structural Validator):**
- `argparse` - CLI parsing
- `csv` - CSV reading
- `json` - JSON config loading and output writing
- `re` - Pattern matching
- `sys` - System interaction
- `unicodedata` - Unicode operations
- `collections.defaultdict` - Data structures
- `pathlib.Path` - File system abstraction

**Optional External Packages (PDF Generation):**
- `markdown` - Markdown to HTML conversion
- `weasyprint` - HTML to PDF rendering (optional)

**System Binaries (Fallback):**
- `cupsfilter` - CUPS printer system command (macOS/UNIX fallback for PDF generation)

## Security Model

**No sensitive data handling:**
- No API keys or credentials
- No external authentication
- No data transmission
- File access via standard OS permissions

**Data containment:**
- All data stays local in `samples/`, `reports/`, `corrections/` directories
- Configuration is static JSON/CSV files
- No network exposure

## Performance Characteristics

**No external dependencies** means:
- Instant startup (no package initialization)
- No network latency
- Deterministic execution (no remote service calls)
- Fully parallelizable by market if needed (currently sequential)

**Limitation:** AI-driven review tier depends on Claude API availability (skill execution), not external integrations.

---

*Integration audit: 2026-04-08*
