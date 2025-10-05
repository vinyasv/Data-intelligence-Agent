# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Universal Web Scraper** powered by Claude 4.5 Sonnet and Crawl4AI v0.7.x. It extracts structured data from any website using natural language queries.

**Two Modes:**
1. **CLI Mode** (`main.py`): Direct command-line scraping with URL and query
2. **Agent Mode** (`agent_main.py` / `agent_cli.py`): Conversational AI interface with automatic URL discovery

### Core Architecture

**Classic Scraper Pipeline** (used by both modes):

1. **Schema Generation** (`schema_generator.py`): Claude 4.5 Sonnet generates Pydantic v2 models from natural language queries
2. **Strategy Routing** (`strategy_router.py`): Intelligent router chooses between CSS (fast, free) and LLM (powerful) extraction strategies
3. **Web Extraction** (`extractor.py`): Crawl4AI AsyncWebCrawler performs the actual scraping with retries and fallbacks
4. **Validation** (`main.py`): Pydantic validates extracted data against generated schema

**Agent Architecture** (agent mode only):

1. **Intent Understanding** (`agent_tools.py`): Claude Haiku analyzes user request to determine intent
2. **URL Discovery** (`agent_tools.py`): Exa AI semantic search finds relevant URLs when not provided
3. **Scraping Orchestration** (`agent_tools.py`): Wraps classic scraper pipeline as a tool
4. **Conversation Management** (`agent_main.py`): Multi-turn dialogue with context awareness

### Key Design Decisions

**Strategy Selection Logic** (`strategy_router.py:121-154`):
- Uses Claude Haiku (fast, cheap) to analyze if query requires semantic understanding
- Semantic queries (sentiment, summarization, filtering, categorization) → LLM strategy
- Complex schemas (nested objects, >10 fields) → LLM strategy
- Simple extraction → defaults to LLM (CSS requires manual selectors)

**Alternative Data Sources** (`extractor.py:375-414`):
- When main extraction fails, tries JSON-LD, OpenGraph meta tags, and data attributes
- Uses Claude to convert alternative sources to match user's desired schema

**JS-Heavy Site Detection** (`extractor.py:115-125`, `main.py:187-188`):
- Detects domains like 'abercrombie', 'nike', 'adidas' that use heavy client-side rendering
- Uses `networkidle` wait + UndetectedAdapter for better bot detection bypass
- Standard sites use `domcontentloaded` wait for faster scraping

## Common Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize Crawl4AI browser
crawl4ai-setup

# Verify installation
crawl4ai-doctor

# Configure API key
cp .env.example .env
# Then edit .env with your ANTHROPIC_API_KEY
```

### Running the Scraper

#### CLI Mode (Direct Scraping)
```bash
# Basic usage
python main.py <url> <query> [options]

# Examples
python main.py "https://news.ycombinator.com" "Get top stories with title, points, and author" --pretty
python main.py "https://example.com" "Extract products with name and price" --output results.json --stats
```

#### Agent Mode (Conversational Interface)

**Enhanced CLI (Recommended):**
```bash
# Rich, formatted interface with commands
python agent_cli.py

# With verbose logging
python agent_cli.py --verbose

# Interactive commands: /help, /save, /export, /history, /stats, /clear, /examples, /quit
```

**Basic Agent CLI:**
```bash
# Simple interactive mode
python agent_main.py

# Single query mode
python agent_main.py --query "Scrape products from Nike"

# With output file
python agent_main.py --query "Get news from BBC" --output results.json

# Verbose mode
python agent_main.py --verbose
```

### CLI Options
- `--output FILE` / `-o FILE`: Save to JSON file
- `--pretty` / `-p`: Pretty print JSON
- `--ignore-robots`: Override robots.txt (use responsibly)
- `--skip-validation`: Skip Pydantic validation
- `--prefer-css`: Prefer CSS strategy (requires manual selectors)
- `--stats`: Show performance metrics
- `--verbose` / `-v`: Enable debug logging

### Testing
```bash
# Phase 1: Setup verification
python test_phase1_setup.py

# Phase 2: Agent tools testing
python test_phase2_tools_direct.py

# Phase 3: Agent interface testing
python test_phase3_agent.py

# Classic scraper tests
python test_simple.py
python test_strategy_router.py
python test_schema_generator.py

# Integration tests (takes ~5 minutes)
python test_integration.py

# Test specific category or limit
python test_integration.py --category news
python test_integration.py --max-tests 3
```

### Running Examples
```bash
python examples/news_site.py          # BBC News, Hacker News
python examples/ecommerce.py          # Amazon, eBay products
python examples/job_listings.py       # Indeed, LinkedIn jobs
python examples/reviews_sentiment.py  # Yelp, Reddit sentiment
```

## Configuration

Environment variables in `.env`:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
EXA_API_KEY=your-exa-key-here  # Required for agent mode web search

# Agent Mode (optional - defaults in config.py)
AGENT_MODE=false
INTENT_MODEL=claude-3-5-haiku-20241022
MAX_CONVERSATION_HISTORY=20
WEB_SEARCH_MAX_RESULTS=5
EXA_SEARCH_TYPE=auto  # auto, neural, or keyword

# Claude Configuration (optional - defaults in config.py)
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.0

# Browser Configuration (optional)
BROWSER_HEADLESS=true
BROWSER_TYPE=chromium
ENABLE_STEALTH=false  # Disabled due to playwright_stealth compatibility

# Performance Tuning (optional)
CHUNK_TOKEN_THRESHOLD=2000
WORD_COUNT_THRESHOLD=10
CACHE_MODE=BYPASS
```

## Code Architecture Details

### Schema Generation (`schema_generator.py`)

- Uses Claude 4.5 Sonnet with zero-shot prompt to generate Pydantic v2 models
- Always creates item model + container model pattern (e.g., `Product` + `ProductList`)
- Compiles and validates generated code using `exec()` in isolated namespace
- Returns JSON schema for use by extraction strategies

### Strategy Router (`strategy_router.py`)

**Semantic Detection** (`_is_semantic_query`):
- Claude Haiku analyzes query for keywords: sentiment, summarization, filtering, categorization, comparisons
- Returns "SEMANTIC" or "CSS" decision
- Defaults to semantic (LLM) on error for safety

**LLM Strategy Creation** (`_create_llm_strategy`):
- Uses `input_format="markdown"` (not `fit_markdown` which has quality issues on e-commerce sites)
- `chunk_token_threshold=4000` for markdown efficiency
- `apply_chunking=False` for single-page scraping speed

### Web Extractor (`extractor.py`)

**Wait Strategy**:
- JS-heavy sites: `wait_until="networkidle"` + `delay_before_return_html=1.5s`
- Standard sites: `wait_until="domcontentloaded"` + `delay_before_return_html=0.5s`

**Retry Logic** (`extract` method):
- 3 retries with exponential backoff (2^attempt seconds)
- Falls back to alternative data sources (JSON-LD, meta tags, data attributes) on empty results

**List Response Handling** (`extractor.py:220-255`):
- LLM sometimes returns list instead of dict
- Finds first non-empty dict in list
- Converts to dict format for validation

### Main Entry Point (`main.py`)

**Orchestration Flow**:
1. Check robots.txt (optional, `--ignore-robots` to skip)
2. Generate schema from query
3. Route to optimal strategy
4. Extract with Crawl4AI
5. Validate with Pydantic
6. Output JSON with optional stats

**UndetectedAdapter Usage** (`main.py:187-190`):
- Automatically enabled for specific domains: abercrombie, nike, adidas, zara, hm.com
- Provides better bot detection bypass than standard stealth mode

### Agent Architecture (`agent_main.py`, `agent_tools.py`)

**Three Custom Tools** (defined with `@tool` decorator in `agent_tools.py`):

1. **`understand_intent`** (`agent_tools.py:17-102`):
   - Uses Claude 3.5 Haiku for fast, cheap intent classification
   - Classifies into: url_provided, search_needed, clarification_needed, refinement
   - Extracts URLs from user messages
   - Generates search queries and extraction queries
   - Handles errors gracefully with default clarification response

2. **`web_search`** (`agent_tools.py:105-207`):
   - Integrates Exa AI for semantic web search
   - Supports 3 modes: auto (intelligent), neural (semantic), keyword (traditional)
   - Returns results with: url, title, snippet, score, highlights, published_date
   - Fallback from neural → keyword on failure
   - Requires `EXA_API_KEY` environment variable

3. **`scrape_url`** (`agent_tools.py:210-286`):
   - Wraps existing `scrape()` function from `main.py`
   - Zero refactoring of scraper logic (maintains backward compatibility)
   - Calls full pipeline: schema generation → routing → extraction → validation
   - Returns structured JSON with success/error status
   - Propagates all scraper exceptions with error types

**AgentScraper Class** (`agent_main.py:27-143`):
- Initializes MCP server with 3 custom tools
- Manages conversation history (up to `MAX_CONVERSATION_HISTORY` messages)
- Provides streaming chat responses
- Tracks last scraped data for programmatic access
- Two usage modes: interactive (CLI chat) and single-query (non-interactive)

**System Prompt** (`agent_main.py:68-106`):
- Guides agent through workflow: understand_intent → web_search → scrape_url
- Emphasizes using tools (don't guess or make up data)
- Instructs to present URL options when multiple found
- Focuses on conversational, helpful interactions

## Error Handling

Custom exceptions in `models.py`:
- `ExtractionError`: Crawling/extraction failures
- `SchemaGenerationError`: Pydantic schema generation failures
- `StrategyRoutingError`: Strategy selection failures
- `ValidationError`: Pydantic validation failures

All exceptions are caught in `main.py:374-382` with proper error messages.

## Performance Considerations

- **CSS vs LLM**: CSS is free and fast but requires manual selectors; LLM is flexible but costs ~$0.003-$0.006 per page
- **Token Usage**: Estimated ~2000 tokens per page for LLM extraction
- **Wait Times**: JS-heavy sites take 1.5s extra; standard sites 0.5s
- **Chunking**: Disabled by default for speed; enable for 10k+ token pages

## Known Limitations

1. **Stealth Mode**: `ENABLE_STEALTH=false` due to `playwright_stealth` compatibility issues
   - Use `UndetectedAdapter` instead for bot detection bypass

2. **fit_markdown**: Disabled because it removes dynamic content (prices, images) on e-commerce sites
   - Uses regular markdown instead

3. **CSS Strategy**: Requires manual selector configuration; not auto-generated
   - System defaults to LLM for universal scraping

## Development Workflow

When adding new features:
1. Update relevant module (`schema_generator.py`, `strategy_router.py`, `extractor.py`)
2. Add tests in `test_*.py` files
3. Run integration tests: `python test_integration.py`
4. Update examples if user-facing
5. Test against diverse websites (news, e-commerce, jobs, reviews)
