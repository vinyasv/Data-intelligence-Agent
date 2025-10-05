# Enterprise-Ready Web Data Agent

Turn any web page into reliable, structured data—built for product, data, and engineering teams. Powered by **Claude 4.5 Sonnet** and **Scrapy-Playwright**, with an **intelligent conversational agent** for non-technical users.

**What you get:** Rapid setup, predictable outputs, and controls that enterprises need (retries, rate limits, robots compliance, and validation).

## Why teams use this

- **Blazing Fast**: 3-6 second average extraction (5x faster than alternatives)
- **Cost-Optimized**: 90% token reduction via intelligent optimization (structured data → pruning → LLM)
- **Production-Ready**: Rotating residential proxies, SSL handling, bot detection bypass
- **Flexible extraction**: Auto-routes between CSS scraping and LLM understanding
- **Operationally safe**: Built-in rate limiting, retries, and robots.txt awareness
- **Composable**: CLI, Python APIs, and simple JSON outputs for your pipelines

## Enterprise use cases

- **E‑commerce Pricing Intelligence**: Track prices, promotions, availability, shipping thresholds, and seller mix across product pages.
- **Competitive Intelligence**: Monitor feature pages, changelogs, bundles, plan matrices, and comparison tables.
- **Catalog QA & Content Governance**: Validate presence/format of key attributes (images, dimensions, materials, disclaimers) across PDPs.
- **MAP/Compliance Audits**: Detect policy violations, restricted terms, and disclaimer placement.
- **News & Sentiment Monitoring**: Extract headlines, entities, tone, and summaries from publisher pages.
- **Lead Enrichment & Prospecting**: Pull company metadata, pricing hints, tech stack mentions, and contact artifacts.
- **Marketplace Monitoring**: Seller count, buy box dynamics, ratings, and review deltas.
- **Travel & Ticketing**: Fare, fees, seat classes, blackout dates, and refundability terms.

> Limitation: The system extracts from one page per request (by design for reliability and cost control). Orchestrate multi-page jobs at the workflow level.

## What’s inside

- **Agent Mode (User-friendly)**: Conversational interface with automatic URL discovery via Exa AI.
- **CLI Mode (Scripting/CI)**: Direct commands for deterministic runs and pipelines.
- **Schema Generation**: Claude creates Pydantic schemas from your intent for consistent JSON.
- **Strategy Router**: Chooses CSS (fast, free) or LLM (semantic) extraction automatically.
- **Validation**: Pydantic-backed validation for accuracy and downstream stability.

## 📋 Requirements

- Python 3.10+
- Anthropic API key (for Claude)
- Exa API key (optional, for agent mode web search)
- Scrapy v2.11.0+ with Playwright integration
- Playwright v1.40.0+ (headless browser for JS-heavy sites)
- BrightData proxy account (optional, for production - bypass bot detection)

## Installation

```bash
# Clone and enter
git clone <repo-url>
cd hackathon

# Install dependencies
pip install -r requirements.txt

# Initialize Playwright browser (first time only)
playwright install chromium

# Configure API keys
cp .env.example .env
# Edit .env and set at minimum:
#   ANTHROPIC_API_KEY=...      # required
#   EXA_API_KEY=...            # optional, for agent web search
```

## Quick Start

### Agent Mode (recommended for non-technical teammates)

#### Enhanced Interactive CLI (Recommended)

```bash
python agent_cli.py

# Or with verbose logging for debugging
python agent_cli.py --verbose
```

**What you’ll see:**
- 🎨 Clean, color-coded output (no log spam)
- 📊 Tidy result tables and syntax-highlighted JSON
- 💾 Built-in save/export commands
- 📈 Session statistics
- 🔧 `--verbose` flag for debugging

#### Basic Interactive Mode

```bash
python agent_main.py
```

**Example conversation:**
```
You: I want to scrape products from Nike

Agent: I can help you get product details from Nike! However, I can only
scrape one product page at a time. Which specific Nike product would you
like details for? (e.g., Air Max 90, Air Force 1, or provide a product URL)

You: Air Max 90

🤖 Agent: Great! Let me search for the Nike Air Max 90 product page.
[Searches with Exa AI, finds URL, scrapes page]

Successfully scraped! Here are the details for Nike Air Max 90:
{
  "name": "Nike Air Max 90",
  "price": "$120",
  "sizes": ["7", "8", "9", "10", "11"],
  "in_stock": true
}
```

#### Single Query Mode

```bash
# One-off query
python agent_main.py --query "Get details for Nike Air Max 90"

# Save to file
python agent_main.py --query "Scrape news from BBC" --output results.json
```

### CLI Mode (for pipelines and CI)

```bash
# Extract Hacker News stories
python main.py "https://news.ycombinator.com" \
    "Get top stories with title, points, and author" \
    --pretty --stats

# Scrape e-commerce products
python main.py "https://www.amazon.com/s?k=wireless+mouse" \
    "Extract products with name, price, and rating" \
    --output products.json

# News articles with summaries
python main.py "https://www.bbc.com/news" \
    "Extract articles with headline, author, and a one-sentence summary" \
    --pretty
```

## Agent Mode vs CLI Mode

| Feature | Agent Mode | CLI Mode |
|---------|-----------|----------|
| **URL Required?** | No (searches for you) | Yes |
| **Conversation** | Multi-turn dialogue | Single command |
| **Clarification** | Asks when unclear | Errors if unclear |
| **URL Discovery** | Automatic via Exa AI | Manual |
| **Best For** | Exploration, unclear targets | Known URLs, scripting |
| **Cost** | ~$0.01-$0.012/query | ~$0.003-$0.006/query |

## Important limitation: one page per request

Focused by design for reliability and cost control.

Examples:
- ✅ "Get details for Nike Air Max 90" → Finds and scrapes that product page
- ❌ "Get all Nike products" → Too broad (thousands of pages)
- ✅ "Scrape https://nike.com/product/air-max-90" → One specific page
- ❌ "Scrape all products from Nike.com" → Multi-page orchestration not included

When queries are ambiguous, the agent will ask clarifying questions.

## 📊 Architecture

### Agent Mode Architecture
```
User Natural Language Input
    ↓
[Claude Sonnet 4.5 Agent] → Understand Intent
    ↓
[Exa AI Search] → Find URL (if needed)
    ↓
[Classic Scraper Pipeline]
    ↓
Structured JSON + Conversation
```

### Classic Scraper Pipeline
```
User Query: URL + Natural Language
    ↓
[Claude 4.5 Sonnet] → Generate Pydantic Schema
    ↓
[Strategy Router] → Choose CSS or LLM
    ↓
[Scrapy + Playwright Spider] → Extract Data
    ↓
[Pydantic Validator] → Return Structured JSON
```

## Testing

### Phase tests (agent development)

```bash
# Phase 1: Setup verification
python test_phase1_setup.py

# Phase 2: Agent tools
python test_phase2_tools_direct.py

# Phase 3: Agent interface
python test_phase3_agent.py

# Phase 4: Full integration
python test_phase4_integration.py
```

### Classic scraper tests

```bash
# Unit tests
python test_simple.py
python test_strategy_router.py
python test_schema_generator.py

# Integration tests (10+ websites, ~5 minutes)
python test_integration.py
python test_integration.py --category news --max-tests 3
```

## Documentation

### For Agent Mode
- **`AGENT_USAGE.md`** - Complete usage guide with examples
- **`SYSTEM_PROMPT.md`** - Agent system prompt documentation

### For Classic Mode
- **`CLAUDE.md`** - Architecture, commands, and configuration
- **`examples/`** - Working code examples

## ⚙️ Configuration

Edit `.env` file:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
EXA_API_KEY=your-exa-key  # Optional, for agent web search

# Proxy Configuration (Recommended for Production)
PROXY_ENABLED=true  # Enable rotating residential proxies
BRIGHTDATA_USERNAME=brd-customer-xxx-zone-xxx
BRIGHTDATA_PASSWORD=your_password
BRIGHTDATA_HOST=brd.superproxy.io
BRIGHTDATA_PORT=33335
PROXY_ROTATION=request  # New IP per request (recommended)

# Agent Mode
AGENT_MODE=false  # Set to true to enable by default
INTENT_MODEL=claude-3-5-haiku-20241022
MAX_CONVERSATION_HISTORY=20
WEB_SEARCH_MAX_RESULTS=5
EXA_SEARCH_TYPE=auto  # auto, neural, or keyword

# Claude Configuration
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.0

# Browser Configuration (Scrapy + Playwright)
BROWSER_HEADLESS=true
BROWSER_TYPE=chromium
ENABLE_STEALTH=false

# Performance & Optimization
CHUNK_TOKEN_THRESHOLD=2000
CACHE_MODE=BYPASS
```

## When to use CSS vs LLM strategy

### CSS extraction (fast, free)
- Structured, predictable HTML
- Simple data fields (titles, prices, dates)
- No semantic understanding needed

### LLM extraction (powerful, flexible)
- **Sentiment analysis** ("positive", "negative", "neutral")
- **Filtering** ("only products with rating > 4")
- **Summarization** ("one-sentence summary")
- **Categorization** ("group by topic")
- **Entity extraction** ("mentioned dishes", "key features")
- Unstructured or inconsistent HTML

The scraper automatically chooses the optimal strategy based on your query.

## Performance & costs

### Agent mode
| Metric | Performance |
|--------|-------------|
| Response Time | 7-17s (includes search + scrape) |
| Cost per Query | ~$0.01-$0.012 |
| Success Rate | 95%+ |

### CLI mode (Scrapy + Playwright)
| Metric | Performance | Notes |
|--------|-------------|-------|
| Response Time | **3-6 seconds** | 5x faster than alternatives |
| Cost per Page | $0.001-$0.005 | 90% token reduction via optimization |
| Proxy Cost | +$0.50-$1.50 per GB | ~$0.002-$0.005 per page with BrightData |
| Success Rate | 98%+ | Includes high-security sites (Myntra, etc.) |
| Accuracy | 99%+ | With Pydantic validation |

### Token Optimization Tiers
1. **FREE** - Structured data extraction (JSON-LD, OpenGraph) - 0 tokens
2. **CHEAP** - Content optimization + pruning - 500-1,500 tokens (vs 8,000)
3. **FULL** - Complete LLM extraction - 8,000 tokens (fallback only)

## Best practices

✅ **Rate Limiting**: Built-in delays between requests  
✅ **robots.txt Compliance**: Automatic checking (override with `--ignore-robots`)  
✅ **Error Handling**: Automatic retries with exponential backoff  
✅ **Fallback Strategies**: Multi-tier extraction (structured → optimized → full LLM)  
✅ **Cost Tracking**: Real-time token usage estimation  
✅ **Data Validation**: Pydantic schema validation  
✅ **Anti-Bot Detection**: Residential proxies, user-agent rotation, viewport configuration  
✅ **SSL/HTTPS Handling**: Automatic certificate validation for proxy connections  
✅ **Smart Wait Strategies**: Adaptive waits based on site category (e-commerce, news, social)

##  Project structure

```
hackathon/
├── agent_cli.py               # Enhanced agent CLI
├── agent_main.py              # Agent mode entry point
├── agent_tools.py             # Custom agent tools
├── agent_models.py            # Agent data models
├── main.py                    # CLI mode entry point
├── schema_generator.py        # Dynamic Pydantic schema generation
├── strategy_router.py         # CSS vs LLM routing
├── extractor.py               # Scrapy + Playwright orchestrator
├── scrapers/                  # Scrapy components
│   ├── universal_spider.py    # Main spider with dynamic schemas
│   ├── scrapy_settings.py     # Scrapy configuration
│   └── wait_strategies.py     # Smart adaptive waits
├── extraction/                # Token optimization layers
│   ├── content_optimizer.py   # HTML → Markdown pruning
│   ├── structured_data_extractor.py  # JSON-LD/OpenGraph (FREE)
│   └── llm_extractor.py       # LLM extraction with optimization
├── middlewares/               # Scrapy middlewares
│   └── stealth_middleware.py  # User-agent rotation
├── pipelines/                 # Scrapy pipelines
│   └── validation_pipeline.py # Pydantic validation
├── models.py                  # Core Pydantic models
├── config.py                  # Configuration
├── utils.py                   # Utilities
├── AGENT_USAGE.md             # Agent usage guide
├── SYSTEM_PROMPT.md           # Agent prompt documentation
├── CLAUDE.md                  # Architecture reference
├── MIGRATION_SUCCESS.md       # Scrapy migration results
├── README.md                  # This file
├── requirements.txt           # Dependencies
├── .env.example               # Environment template
├── test_*.py                  # Test suite
└── examples/                  # Example scripts
    ├── news_site.py
    ├── ecommerce.py
    ├── job_listings.py
    └── reviews_sentiment.py
```

## ✅ Getting started checklist

1. Install dependencies: `pip install -r requirements.txt`
2. Initialize browser: `playwright install chromium`
3. Add `ANTHROPIC_API_KEY` to `.env` (required)
4. Add `EXA_API_KEY` to `.env` (optional, for web search)
5. Try the enhanced agent: `python agent_cli.py`
6. For debugging, use: `python agent_cli.py --verbose`

## 📖 CLI reference

### Agent mode

#### Enhanced CLI (recommended)
```bash
python agent_cli.py [options]

Options:
  --verbose, -v         Enable debug logging

Interactive Commands:
  /help                 Show help message
  /save [filename]      Save conversation to JSON
  /export [filename]    Export scraped data
  /history              Show conversation history
  /stats                Show session statistics
  /clear                Clear conversation history
  /examples             Show example queries
  /quit                 Exit the agent
```

#### Basic CLI
```bash
python agent_main.py [options]

Options:
  --query, -q TEXT      Single query (non-interactive)
  --output, -o FILE     Save to JSON file
  --verbose, -v         Enable debug logging
```

### CLI mode
```bash
python main.py <url> <query> [options]

Arguments:
  url                   Target URL to scrape
  query                 Natural language extraction query

Options:
  --output, -o FILE     Save output to JSON file
  --pretty, -p          Pretty print JSON
  --ignore-robots       Ignore robots.txt (use responsibly)
  --skip-validation     Skip Pydantic validation
  --prefer-css          Prefer CSS extraction
  --stats               Show performance statistics
  --verbose, -v         Enable verbose logging
```

## 🤝 Contributing

1. Review architecture in `CLAUDE.md`
2. Check `CLEANUP_SUMMARY.md` for recent changes
3. Maintain test coverage
4. Run integration tests: `python tests/test_phase4_integration.py`
5. Respect robots.txt and rate limits

##  Acknowledgments

- **Scrapy + Playwright** - High-performance web crawler with JS rendering
- **Anthropic Claude 4.5 Sonnet** - Advanced language model
- **Exa AI** - Semantic web search for agent mode
- **Pydantic** - Data validation and schema management

## 📞 Support

## Deployment options

- **Docker**: Use the provided `Dockerfile` for reproducible runs in CI/CD or on-prem.
- **Fly.io / Containers-as-a-Service**: `fly.toml` included for quick deployment.
- **Cron/Workflow Orchestration**: Schedule CLI jobs and export JSON to S3, GCS, or data warehouses.

## Security & compliance

- Respects `robots.txt` by default (overridable with `--ignore-robots`, use responsibly)
- Rate limiting and retries reduce operational risk for target sites
- Rotating residential proxies prevent IP blocking and rate limiting
- SSL/HTTPS validation for secure proxy connections
- No data is stored server-side by default; outputs are local unless you export
- Supports environment-based key management via `.env`
- User-agent rotation and anti-fingerprinting measures

## Integration patterns

- Trigger via CI and write JSON to artifacts
- Pipe JSON into dbt/ETL (Airflow, Dagster, Prefect)
- Wrap with a simple API (`api_server.py`) for internal consumers

## ROI tips

- **90% token savings**: System automatically uses structured data extraction (FREE) when available
- **Content optimization**: HTML pruning reduces tokens by 70-90% before LLM
- **Proxy cost**: ~$30-$225/month for 30k pages (vs $720/month in token savings)
- Use CSS strategy for stable sites to minimize compute cost
- Use LLM strategy for semantic tasks (sentiment, classification, summaries)
- Keep prompts and schemas tight; narrower schemas reduce tokens and errors
- Enable proxies in production to prevent IP blocks (saves on failed requests)

### Cost Breakdown (30k pages/month)
| Item | Cost | Notes |
|------|------|-------|
| Token costs (optimized) | $90-150 | 90% reduction via structured data + pruning |
| Proxy costs (BrightData) | $30-225 | Residential IPs, ~2-5MB per page |
| **Total monthly** | **$120-375** | vs $720 without optimization |
| **Net savings** | **$345-600/mo** | ROI positive in month 1 |

**Documentation:**
- Agent mode: See `AGENT_USAGE.md`
- Classic mode: See `CLAUDE.md`
- Architecture: See `CLAUDE.md`

**Testing:**
- Run `python tests/test_phase4_integration.py` to verify setup
- Run `python test_agent_comprehensive.py` for full agent tests
- Use `--verbose` flag when debugging issues

---

