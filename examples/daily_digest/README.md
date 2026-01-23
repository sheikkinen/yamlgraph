# Daily Digest Example

A YAMLGraph example that showcases scheduled, long-running agents deployed on Fly.io.

> ✅ **Tested & Working** - Fetches ~50 HN articles, analyzes with Claude, and delivers HTML digest via email.

## What It Does

1. **Fetches** articles from Hacker News front page (~50 articles)
2. **Filters** to new articles (dedup with SQLite, 24h window)
3. **Extracts** content from article URLs (parallel with httpx)
4. **Analyzes** each article with LLM (map node with Claude)
5. **Ranks** top 8 stories by relevance to your topics
6. **Formats** as HTML email with summaries and insights
7. **Sends** via Resend API

## Architecture

```
┌─────────────────┐          ┌─────────────────────────────────┐
│  GitHub Action  │  HTTP    │  Fly.io Machine (Docker)        │
│  (cron: 06:00)  │─────────▶│  ┌───────────────────────────┐  │
│                 │  202 OK  │  │ FastAPI + SlowAPI         │  │
└─────────────────┘  <100ms  │  │   POST /run → 202 Accepted│  │
                             │  │     └─ BackgroundTasks    │  │
                             │  │         └─ graph.invoke() │  │
                             │  │             └─ SQLite vol │  │
                             │  └───────────────────────────┘  │
                             │                                 │
                             │  auto_stop: suspend (~$0/mo)   │
                             └─────────────────────────────────┘
```

The API returns `202 Accepted` immediately (<100ms) and runs the pipeline in the background. Results are delivered via email, not in the HTTP response.

## Local Development

### Prerequisites

```bash
# Install with digest extras
pip install -e ".[digest]"

# Or install dependencies individually
pip install feedparser resend beautifulsoup4 httpx python-dotenv

# Set up environment (.env file)
ANTHROPIC_API_KEY=your-key
RESEND_API_KEY=your-key
RECIPIENT_EMAIL=you@example.com
```

### Run Locally

```bash
# Dry run (no email sent)
python examples/daily_digest/run_digest.py --dry-run

# With specific topics
python examples/daily_digest/run_digest.py --topics "Rust,WebAssembly" --dry-run

# Send email (requires verified Resend domain or test domain)
python examples/daily_digest/run_digest.py --email you@example.com --topics "AI,Python,LangGraph"
```

> **Note**: With Resend's test domain (`resend.dev`), you can only send to the email address associated with your Resend account. For other recipients, verify your own domain at [resend.com/domains](https://resend.com/domains).

### Run Tests

```bash
pytest examples/daily_digest/tests/ -v
```

## Deployment to Fly.io

### 1. Create Fly.io App

```bash
cd examples/daily_digest
fly launch --name my-digest-agent
```

### 2. Set Secrets

```bash
fly secrets set ANTHROPIC_API_KEY=your-key
fly secrets set RESEND_API_KEY=your-key
fly secrets set DIGEST_API_TOKEN=$(openssl rand -hex 32)
fly secrets set RECIPIENT_EMAIL=you@example.com
fly secrets set DIGEST_FROM_EMAIL="YAMLGraph <yamlgraph-no-reply@resend.dev>"
```

### 3. Create Volume (for SQLite)

```bash
fly volumes create digest_data --size 1
```

### 4. Deploy

```bash
fly deploy
```

### 5. Set Up GitHub Action

Create `.github/workflows/daily.yml`:

```yaml
name: Daily Digest

on:
  schedule:
    - cron: '0 6 * * *'  # 6 AM UTC
  workflow_dispatch:

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger digest
        run: |
          curl -X POST \
            https://my-digest-agent.fly.dev/run \
            -H "Authorization: Bearer ${{ secrets.DIGEST_API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"topics": ["AI", "Python", "LangGraph"]}'
```

## File Structure

```
examples/daily_digest/
├── graph.yaml              # Pipeline definition (7 nodes)
├── run_digest.py           # CLI for local runs
├── test_email.py           # Standalone email test
├── prompts/
│   ├── analyze_article.yaml  # Per-article analysis prompt
│   └── rank_stories.yaml     # Ranking/selection prompt
├── templates/
│   └── digest.html         # Jinja2 email template
├── nodes/
│   ├── sources.py          # HN fetching (feedparser)
│   ├── filters.py          # Dedup + recency filter (SQLite)
│   ├── content.py          # Article extraction (httpx + BS4)
│   ├── formatting.py       # Jinja2 HTML rendering
│   └── email.py            # Resend API
├── api/
│   └── app.py              # FastAPI endpoint (Fly.io)
├── Dockerfile              # Container for Fly.io
├── fly.toml                # Fly.io config
└── tests/
    ├── conftest.py
    ├── test_sources.py
    ├── test_filters.py
    ├── test_content.py
    ├── test_formatting.py
    ├── test_email.py
    └── test_graph_integration.py
```

## Pipeline Flow

```
fetch_sources → filter_recent → fetch_content → analyze_all (map) → rank_stories → format_email → send_email
     ↓              ↓               ↓               ↓                   ↓              ↓            ↓
  ~50 HN         ~35-40          Extract        LLM analysis        Top 8           HTML        Resend
  articles       (dedup)          text          per article         ranked         digest        API
```

## Sample Output

The digest email includes:
- 📰 8 top-ranked stories with summaries
- 📌 Editor insights explaining relevance
- 📊 Relevance scores (0-100%)
- 🔗 Links to original articles

See [docs/digest-email.md](../../docs/digest-email.md) for an example digest.

## Security

- **Authentication**: Bearer token on `/run` endpoint
- **Rate Limiting**: 2 requests/hour via SlowAPI
- **Dedup**: SQLite prevents reprocessing same articles
- **HTTPS**: Enforced by Fly.io

## Cost

With Fly.io's `auto_stop: suspend`:
- **~$0/month** when not running
- Pay only for actual compute minutes (~2-3 min/run)
- Volume storage: $0.15/GB/month
- LLM costs: ~$0.02-0.05 per digest (Claude Haiku)
