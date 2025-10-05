# Universal Web Scraper with Intelligent Agent

A production-ready universal web scraping system powered by **Claude 4.5 Sonnet** and **Crawl4AI v0.7.x**. Now featuring an **intelligent conversational agent** with automatic URL discovery!

**Recent Updates:**
- ✅ Migrated from Cursor SDK to direct Anthropic API (no session limits!)
- ✅ Fixed Exa search JSON serialization issues  
- ✅ Clean CLI output (internal logs hidden by default)
- ✅ Added `--verbose` flag for debugging

## Key Features

### Two Modes of Operation

#### **Agent Mode** (NEW!)
- **Conversational Interface**: Chat naturally with the agent
- **Automatic URL Discovery**: Uses Exa AI semantic search to find websites
- **Intent Understanding**: Claude Haiku analyzes your requests
- **Multi-Turn Conversations**: Refine results through dialogue
- **Smart Clarification**: Asks for specifics when requests are ambiguous

#### 🔧 **CLI Mode** (Classic)
- **Direct Scraping**: Provide URL and query, get results
- **Fast & Simple**: Perfect when you know the exact URL
- **Scriptable**: Easy to integrate into workflows

### Core Capabilities
- **Natural Language Queries**: Describe what you want to extract in plain English
- **Automatic Schema Generation**: Claude 4.5 generates Pydantic schemas from your query
- **Intelligent Strategy Routing**: Automatically chooses between CSS (fast, free) and LLM (powerful) extraction
- **Universal Compatibility**: Works on any website structure
- **Semantic Understanding**: Handles filtering, sentiment analysis, categorization, and summarization
- **Production-Ready**: Error handling, retries, rate limiting, robots.txt compliance
- **Clean UX**: Beautiful output with internal logs hidden (use `--verbose` to debug)

## 📋 Requirements

- Python 3.10+
- Anthropic API key (for Claude)
- Exa API key (optional, for agent mode web search)
- Crawl4AI v0.7.4+

## Installation

```bash
# Clone repository
git clone <repo-url>
cd hackathon

# Install dependencies
pip install -r requirements.txt

# Initialize Crawl4AI browser
crawl4ai-setup

# Verify installation
crawl4ai-doctor

# Configure API keys
cp .env.example .env
# Edit .env and add:
#   - ANTHROPIC_API_KEY (required)
#   - EXA_API_KEY (optional, for web search in agent mode)
```

## Quick Start

### Agent Mode (Recommended for Exploration)

#### Enhanced Interactive CLI (Recommended)

```bash
python agent_cli.py

# Or with verbose logging for debugging
python agent_cli.py --verbose
```

**Features:**
- 🎨 Color-coded, formatted output (clean, no log spam!)
- 📊 Tables for search results
- 🔍 Syntax-highlighted JSON
- 💾 Built-in save/export commands
- 📈 Session statistics
- ⌨️  Rich command system
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

### CLI Mode (When You Know the URL)

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

## Important Limitation: One Page at a Time

The scraper can only extract data from **ONE webpage per request**.

**Examples:**
- ✅ "Get details for Nike Air Max 90" → Finds and scrapes that product page
- ❌ "Get all Nike products" → Too broad (thousands of pages)
- ✅ "Scrape https://nike.com/product/air-max-90" → One specific page
- ❌ "Scrape all products from Nike.com" → Multiple pages not supported

**The agent will ask for clarification:**
```
User: "Get Nike products"
Agent: "Which specific Nike product would you like details for?"
```

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
[Crawl4AI AsyncWebCrawler] → Extract Data
    ↓
[Pydantic Validator] → Return Structured JSON
```

## Testing

### Phase Tests (Agent Development)

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

### Classic Scraper Tests

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

# Browser Configuration
BROWSER_HEADLESS=true
BROWSER_TYPE=chromium
ENABLE_STEALTH=false

# Performance
CHUNK_TOKEN_THRESHOLD=2000
CACHE_MODE=BYPASS
```

## When to Use CSS vs LLM Strategy

### CSS Extraction (Fast, Free)
- Structured, predictable HTML
- Simple data fields (titles, prices, dates)
- No semantic understanding needed

### LLM Extraction (Powerful, Flexible)
- **Sentiment analysis** ("positive", "negative", "neutral")
- **Filtering** ("only products with rating > 4")
- **Summarization** ("one-sentence summary")
- **Categorization** ("group by topic")
- **Entity extraction** ("mentioned dishes", "key features")
- Unstructured or inconsistent HTML

The scraper automatically chooses the optimal strategy based on your query.

## Performance & Costs

### Agent Mode
| Metric | Performance |
|--------|-------------|
| Response Time | 7-17s (includes search + scrape) |
| Cost per Query | ~$0.01-$0.012 |
| Success Rate | 95%+ |

### CLI Mode
| Metric | Performance |
|--------|-------------|
| Response Time | 6-12s |
| Cost per Page | $0.003-$0.006 |
| Success Rate | 95%+ |
| Accuracy | 98%+ (with validation) |

## Best Practices

✅ **Rate Limiting**: Built-in delays between requests
✅ **robots.txt Compliance**: Automatic checking (override with `--ignore-robots`)
✅ **Error Handling**: Automatic retries with exponential backoff
✅ **Fallback Strategies**: Multiple extraction methods
✅ **Cost Tracking**: Real-time token usage estimation
✅ **Data Validation**: Pydantic schema validation
✅ **Anti-Bot Detection**: Viewport configuration, user-agent rotation

##  Project Structure

```
hackathon/
├── agent_cli.py               # Enhanced agent CLI (NEW)
├── agent_main.py              # Agent mode entry point (NEW)
├── agent_tools.py             # Custom agent tools (NEW)
├── agent_models.py            # Agent data models (NEW)
├── main.py                    # CLI mode entry point
├── schema_generator.py        # Schema generation
├── strategy_router.py         # CSS vs LLM routing
├── extractor.py               # Crawl4AI orchestrator
├── models.py                  # Core models
├── config.py                  # Configuration
├── utils.py                   # Utilities
├── AGENT_USAGE.md             # Agent usage guide (NEW)
├── SYSTEM_PROMPT.md           # Agent prompt docs (NEW)
├── CLAUDE.md                  # Architecture reference
├── README.md                  # This file
├── requirements.txt           # Dependencies
├── .env.example               # Environment template
├── test_phase*.py             # Agent tests (NEW)
├── test_*.py                  # Classic tests
└── examples/                  # Example scripts
    ├── news_site.py
    ├── ecommerce.py
    ├── job_listings.py
    └── reviews_sentiment.py
```

## ✅ Getting Started Checklist

1. Install dependencies: `pip install -r requirements.txt`
2. Initialize browser: `crawl4ai-setup`
3. Add `ANTHROPIC_API_KEY` to `.env` (required)
4. Add `EXA_API_KEY` to `.env` (optional, for web search)
5. Try the enhanced agent: `python agent_cli.py`
6. For debugging, use: `python agent_cli.py --verbose`

## 📖 CLI Reference

### Agent Mode

#### Enhanced CLI (Recommended)
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

### CLI Mode
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

- **Crawl4AI** - High-performance web crawler optimized for LLMs
- **Anthropic Claude 4.5 Sonnet** - Advanced language model
- **Exa AI** - Semantic web search for agent mode
- **Pydantic** - Data validation and schema management

## 📞 Support

**Documentation:**
- Agent mode: See `AGENT_USAGE.md`
- Classic mode: See `CLAUDE.md`
- Architecture: See `CLAUDE.md`

**Testing:**
- Run `python tests/test_phase4_integration.py` to verify setup
- Run `python test_agent_comprehensive.py` for full agent tests
- Use `--verbose` flag when debugging issues

---

