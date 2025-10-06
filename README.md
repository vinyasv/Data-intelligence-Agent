# AI Web Data Agent

**Extract structured data from any website using natural language.** Powered by Claude 4.5 Sonnet, this production-ready scraper converts web pages into reliable JSON with intelligent extraction strategies, bot detection bypass, and built-in validation.

**Built for teams that need:** Competitive intelligence, pricing monitoring, content aggregation, lead enrichment, and automated data pipelines—without writing custom scrapers for each site.

**Two modes:** Conversational agent for exploration (auto-finds URLs) or direct CLI for scripting and CI/CD integration.

## Features

- **Natural language extraction** – Describe what you want, get structured JSON back
- **Intelligent routing** – Auto-selects between CSS (fast, free) and LLM (semantic) strategies
- **Production-ready** – Rotating residential proxies, bot detection bypass, SSL handling
- **Cost-optimized** – 90% token reduction via structured data extraction and content pruning
- **Fast** – 3-6 second average response time (5x faster than alternatives)
- **Validated** – Pydantic schema validation ensures data quality
- **Compliant** – Respects robots.txt, built-in rate limiting, exponential backoff retries

## Use Cases

E-commerce pricing, competitive intelligence, news monitoring, lead enrichment, catalog QA, marketplace tracking, sentiment analysis, content governance.

> **Scope:** Extracts from one page per request (by design for reliability). Orchestrate multi-page workflows at the application level.

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize Playwright browser
playwright install chromium

# Configure API key
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-...
```

### Agent Mode (Conversational)

Recommended for exploration and when you don't have a URL.

```bash
# Start interactive agent
python agent_cli.py

# Example conversation:
You: "Get product details for Nike Air Max 90"
Agent: [Searches for URL, scrapes page, returns JSON]
```

**Single query mode:**
```bash
python agent_main.py --query "Scrape top stories from Hacker News" --output results.json
```

### CLI Mode (Direct Scraping)

Best for known URLs, scripting, and CI/CD pipelines.

```bash
# Basic usage
python main.py "<url>" "<what to extract>" --pretty

# Example
python main.py "https://news.ycombinator.com" \
    "Get top 5 stories with title, points, and author" \
    --pretty --stats
```

## Configuration

Required: `ANTHROPIC_API_KEY` in `.env`

Optional (for production):
- `EXA_API_KEY` – Web search for agent mode
- `PROXY_ENABLED=true` – Enable rotating residential proxies
- `BRIGHTDATA_USERNAME`, `BRIGHTDATA_PASSWORD` – Proxy credentials

See `.env.example` for full configuration options.

## How It Works

1. **Schema Generation** – Claude creates a Pydantic schema from your natural language query
2. **Strategy Selection** – Router chooses CSS (fast, free) or LLM (semantic) extraction
3. **Web Extraction** – Scrapy + Playwright fetches content with retries and fallbacks
4. **Data Validation** – Pydantic validates extracted data against schema
5. **Return JSON** – Structured, validated JSON ready for your pipeline

**Agent mode adds:** Intent understanding → URL discovery (via Exa AI) → Conversational interface

## Performance

| Metric | Agent Mode | CLI Mode |
|--------|-----------|----------|
| Response Time | 8-17s | 3-6s |
| Cost per Query | ~$0.01 | ~$0.003-$0.006 |
| Success Rate | 95%+ | 98%+ |

**Token Optimization:**
1. FREE – Structured data extraction (JSON-LD, OpenGraph)
2. CHEAP – Content pruning (500-1,500 tokens vs 8,000)
3. FULL – Complete LLM extraction (fallback only)

## Examples

```bash
# News headlines
python main.py "https://news.ycombecker.com" \
    "Extract top 5 stories with title and points"

# E-commerce products
python main.py "https://example.com/product/123" \
    "Get product name, price, and availability"

# Sentiment analysis
python main.py "https://example.com/reviews" \
    "Extract reviews with rating and sentiment (positive/negative)"

# Agent mode - auto-finds URL
python agent_main.py --query "Get Nike Air Max 90 product details"
```

## Documentation

- **`AGENT_USAGE.md`** – Complete agent guide with examples
- **`CLAUDE.md`** – Architecture, commands, and configuration
- **`examples/`** – Working code examples for common use cases

## Testing

```bash
# Verify setup
python test_phase1_setup.py

# Integration tests
python test_integration.py

# Agent tests
python test_phase4_integration.py
```

## Deployment

- **Fly.io** – `fly.toml` included for quick deployment
- **Docker** – `Dockerfile` for reproducible container builds
- **API Server** – `api_server.py` for conversational web interface

**Production deployment:**
```bash
fly deploy --app your-app-name
```

## License

MIT

---

**Built with:** Claude 4.5 Sonnet • Scrapy + Playwright • Pydantic • Exa AI

