# Intelligent Web Scraper Agent - Usage Guide

## Quick Start

### Enhanced Interactive Mode (Recommended)

The best way to use the agent is with the enhanced CLI:

```bash
python agent_cli.py
```

This provides a rich, conversational interface with:
- 🎨 Color-coded output
- 📊 Formatted tables
- 🔍 Syntax-highlighted JSON
- 💾 Built-in commands (/save, /export, /stats)
- 📈 Session management

### Basic Interactive Mode

For a simpler interface without rich formatting:

```bash
python agent_main.py
```

This starts a basic conversational interface where you can chat naturally with the agent.

### Example Conversations

#### Example 1: Handling Ambiguous Requests (NEW!)

```
🧑 You: I want to scrape products from Nike

🤖 Agent: I can help you get product details from Nike! However, I can only
scrape one product page at a time. Which specific Nike product would you
like details for? (e.g., Air Max 90, Air Force 1, or provide a product URL)

🧑 You: Air Max 90

🤖 Agent: Great! Let me search for the Nike Air Max 90 product page.
[Agent uses web_search tool...]

I found the product page:
https://www.nike.com/t/air-max-90-mens-shoes

Should I scrape this page for product details?

🧑 You: Yes

🤖 Agent: [Agent uses scrape_url tool...]

✅ Successfully scraped! Here are the details for Nike Air Max 90:
{
  "product": {
    "name": "Nike Air Max 90",
    "price": "$120",
    "color": "White/Black",
    "sizes": ["7", "8", "9", "10", "11", "12"],
    "in_stock": true
  }
}
```

#### Example 2: URL Provided (Specific Page)

```
🧑 You: Scrape https://news.ycombinator.com for top stories with title and points

🤖 Agent: I'll scrape Hacker News for top stories with titles and points.
[Agent uses scrape_url tool...]

✅ Successfully scraped! Found 30 top stories:
{
  "stories": [
    {"title": "Show HN: My new project", "points": 342},
    {"title": "GPT-5 Released", "points": 1,245},
    ...
  ]
}
```

#### Example 3: Refinement

```
🧑 You: Get news from BBC

🤖 Agent: [Finds BBC News, scrapes articles...]

✅ Found 15 articles from BBC News.

🧑 You: Only about technology, and include summaries

🤖 Agent: I'll filter for technology news and add summaries.
[Agent re-scrapes with refined query...]

✅ Here are 5 technology articles with summaries...
```

---

## Command Line Options

### Enhanced CLI Commands

When using `python agent_cli.py`, you have access to interactive commands:

```bash
/help                 # Show help message
/save [filename]      # Save conversation to JSON
/export [filename]    # Export scraped data to JSON
/history              # Show conversation history
/stats                # Show session statistics
/clear                # Clear conversation history
/examples             # Show example queries
/quit                 # Exit the agent
```

**Examples:**
```bash
# During conversation:
> /save my_conversation.json
> /export results.json
> /stats
```

### Basic CLI Options

For `python agent_main.py`:

#### Single Query Mode

Run a single query without interactive mode:

```bash
python agent_main.py --query "Scrape products from Nike"
```

#### Save Output to File

```bash
python agent_main.py --query "Get news from BBC" --output results.json
```

This saves:
- The query
- Agent's response
- Conversation history
- Scraped data (if any)

#### Verbose Mode

Enable detailed logging:

```bash
python agent_main.py --verbose
# or
python agent_cli.py --verbose
```

#### Help

```bash
python agent_main.py --help
python agent_cli.py --help
```

---

## Important Limitation: One Page at a Time

**⚠️ The agent can only scrape ONE webpage per request.**

This means:
- ✅ "Scrape https://nike.com/product/air-max-90" → Works (one specific page)
- ❌ "Scrape all Nike products" → Won't work (multiple pages)
- ✅ "Get details for Nike Air Max 90" → Works (agent finds the specific product page)
- ❌ "Get all products from Nike.com" → Won't work (too many pages)

**What the agent will do:**
- Ask for clarification if your request is too broad
- Help you find the specific page you want
- Scrape that one page and extract the data

**Examples:**

```
User: "Get Nike products"
Agent: "Which specific Nike product would you like details for?"

User: "Scrape jobs from Indeed"
Agent: "I can only scrape one job posting at a time. Can you provide
       a specific job title and location, or a direct URL to a job posting?"

User: "Get news from BBC"
Agent: "Would you like me to scrape the BBC homepage, or a specific
       article? I can only extract from one page at a time."
```

---

## How It Works

### 1. Intent Understanding

The agent first analyzes your request to determine:
- Is a URL provided?
- What should it search for?
- What data to extract?
- Does it need clarification?

### 2. URL Discovery (if needed)

If you don't provide a URL, the agent uses **Exa AI search** to find relevant websites:
- Semantic/neural search understands intent
- Returns high-quality, ranked results
- Presents top options for you to choose

### 3. Data Extraction

The agent uses the existing scraper (from Phase 1 & 2) to:
- Generate Pydantic schema from your query
- Choose optimal extraction strategy (CSS or LLM)
- Extract structured data
- Validate results

### 4. Conversation & Refinement

The agent maintains conversation context:
- Remembers previous queries
- Handles multi-turn refinements
- Clarifies ambiguous requests
- Offers to export or modify results

---

## Configuration

### Required Environment Variables

```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-your-key-here
EXA_API_KEY=your-exa-key-here  # Optional for web search
```

### Optional Settings

```bash
# Agent Configuration
AGENT_MODE=true
INTENT_MODEL=claude-3-5-haiku-20241022
MAX_CONVERSATION_HISTORY=20
WEB_SEARCH_MAX_RESULTS=5
EXA_SEARCH_TYPE=auto  # auto, neural, or keyword

# Claude Configuration
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

---

## Tips & Best Practices

### 1. Be Specific

❌ "Get data from a website"
✅ "Scrape product names, prices, and ratings from https://example.com"

### 2. Provide Context

If you don't have a URL:
✅ "I want to scrape products from Nike's official store"
✅ "Find news articles about AI from TechCrunch"

### 3. Use Natural Language

The agent understands conversational requests:
- "I want to scrape..."
- "Get me the..."
- "Find job listings for..."
- "Extract all products with..."

### 4. Refine Iteratively

You can refine results in follow-up messages:
1. "Get news from BBC"
2. "Only technology news"
3. "Include summaries"

### 5. Confirm URLs

When the agent presents multiple URL options, always confirm which one to scrape.

---

## Comparison: CLI vs Agent Mode

### Classic CLI Mode (main.py)

```bash
python main.py "https://example.com" "Extract products with name and price" --pretty
```

**Pros:**
- Direct, no conversation
- Fast for known URLs
- Scriptable

**Cons:**
- Must provide exact URL
- No search capability
- No refinement
- No conversation context

### Agent Mode (agent_main.py)

```bash
python agent_main.py
> I want to scrape products from Nike
```

**Pros:**
- Natural language interface
- Automatic URL discovery
- Multi-turn conversations
- Intent understanding
- Refinement support

**Cons:**
- Slightly slower (LLM overhead)
- Requires more API calls
- More complex setup

---

## Troubleshooting

### "EXA_API_KEY not set"

**Problem:** Web search won't work without Exa API key.

**Solution:**
1. Get an API key from https://exa.ai
2. Add to `.env`: `EXA_API_KEY=your-key-here`
3. Or provide URLs directly (agent can still scrape)

### "Failed to initialize agent"

**Problem:** Missing ANTHROPIC_API_KEY.

**Solution:**
1. Check `.env` file exists
2. Verify `ANTHROPIC_API_KEY=sk-ant-...` is set
3. Make sure API key is valid

### Agent doesn't use tools

**Problem:** Tools not being called.

**Solution:**
1. Check allowed_tools configuration
2. Verify MCP server created correctly
3. Try more explicit requests: "Use web search to find..."

### Slow responses

**Problem:** Agent takes long time to respond.

**Solution:**
1. Use `--verbose` to see what's happening
2. Check network connection
3. Try simpler queries first
4. Consider using classic CLI mode for known URLs

---

## Advanced Usage

### Custom System Prompt

Modify `agent_main.py` → `_get_system_prompt()` to customize agent behavior.

### Adding New Tools

1. Create async function in `agent_tools.py` with proper signature
2. Add tool definition to `_get_tool_definitions()` in `agent_main.py`
3. Add tool execution logic in `chat()` method
4. Update system prompt to mention new tool

### Programmatic Usage

```python
from agent_main import AgentScraper
import asyncio

async def scrape_programmatically():
    agent = AgentScraper()
    response = await agent.single_query("Scrape products from Nike")
    print(response)

    # Access scraped data
    if agent.last_scraped_data:
        print(agent.last_scraped_data)

asyncio.run(scrape_programmatically())
```

---

## Cost Estimates

| Operation | Model | Est. Tokens | Cost |
|-----------|-------|-------------|------|
| Intent Classification | Haiku 3.5 | ~500 | $0.0001 |
| Web Search (Exa) | N/A | 0 | $0.001-$0.003 |
| Data Extraction | Sonnet 4.5 | ~2000 | $0.006 |
| Agent Orchestration | Sonnet 4.5 | ~1000 | $0.003 |
| **Total per Query** | Mixed | ~3500 | **~$0.01** |

**Note:** Costs are estimates. Actual costs depend on:
- Complexity of query
- Number of search results
- Size of scraped pages
- Conversation length

---

## Examples

See the `examples/` directory for complete working examples:

- `examples/agent_news.py` - Scraping news sites
- `examples/agent_ecommerce.py` - E-commerce products
- `examples/agent_jobs.py` - Job listings

---

## Frequently Asked Questions

### Can I use agent mode without Exa API key?

Yes, but you must provide URLs directly. The agent can still scrape and understand intent, just can't search for URLs.

### Does it remember previous conversations?

Yes, within the same session. History is limited to `MAX_CONVERSATION_HISTORY` messages (default: 20).

### Can I export results?

Yes, use `--output filename.json` in single-query mode, or ask the agent: "Export this to JSON"

### Is my data stored?

No, the agent only stores conversation history in memory for the current session. When you exit, everything is cleared.

### Can I run multiple agents in parallel?

Yes, each `AgentScraper()` instance is independent. You can create multiple agents for different tasks.

---

## Next Steps

1. **Try it out**: `python agent_main.py`
2. **Read examples**: Check `examples/` directory
3. **Customize**: Modify system prompt and tools
4. **Integrate**: Use programmatically in your projects

For more information, see:
- `CLAUDE.md` - Project architecture and implementation details
- `README.md` - Overall project documentation
