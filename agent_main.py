#!/usr/bin/env python3
"""
Intelligent Agentic Web Scraper - Conversational Interface

Uses Anthropic SDK to provide natural language scraping through conversational AI.
"""
import asyncio
import json
from typing import AsyncGenerator, Optional, List, Dict, Any
from anthropic import Anthropic, AsyncAnthropic

from config import settings
from utils import logger


class AgentScraper:
    """
    Conversational web scraper agent using Anthropic SDK.

    Provides natural language interface for web scraping with:
    - Intent understanding
    - Automatic URL discovery via web search
    - Multi-turn conversations
    - Context-aware refinements
    """

    def __init__(self):
        """Initialize agent with Anthropic client and configuration"""
        logger.info("Initializing Agent Scraper...")

        # Initialize Anthropic client with YOUR API key
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        # Tool definitions
        self.tools = self._get_tool_definitions()

        # Conversation state
        self.conversation_history: List[Dict[str, Any]] = []
        self.last_scraped_data: Optional[Dict[str, Any]] = None

        logger.info("✅ Agent initialized successfully")

    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Define the tools available to the agent"""
        return [
            {
                "name": "understand_intent",
                "description": "Analyzes user input to determine their intent and what information is needed",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_message": {"type": "string", "description": "The user's message"},
                        "conversation_history": {"type": "string", "description": "JSON string of previous messages"}
                    },
                    "required": ["user_message"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for URLs based on user's description using Exa AI",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Number of results (default 5)"},
                        "search_type": {"type": "string", "description": "Search type: auto, neural, or keyword"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "scrape_url",
                "description": "Extract structured data from a URL using natural language query",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Target URL to scrape"},
                        "extraction_query": {"type": "string", "description": "What to extract"},
                        "prefer_css": {"type": "boolean", "description": "Prefer CSS extraction"},
                        "skip_validation": {"type": "boolean", "description": "Skip validation"}
                    },
                    "required": ["url", "extraction_query"]
                }
            }
        ]

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent"""
        return """You are an intelligent web scraping assistant. Your job is to help users extract data from websites through natural conversation.

**Your capabilities:**
1. Understand what the user wants to scrape
2. Find the right URL (search if needed)
3. Extract the requested data
4. Present results clearly

**Available tools:**
- `understand_intent`: Analyze user's request to determine what they want
- `web_search`: Find URLs when not provided by the user
- `scrape_url`: Extract data from a specific URL

**CRITICAL LIMITATION - READ CAREFULLY:**
- You can only scrape ONE webpage at a time
- Each scrape extracts data from a SINGLE URL only
- If a user asks for multiple products/items, you MUST:
  1. Ask which specific item they want
  2. Get the exact URL for that specific item
  3. Scrape only that one page
- Example: "Get Nike products" → Ask: "Which specific Nike product would you like details for?"

**Workflow:**
1. First, use `understand_intent` to analyze the user's request
2. **Check if the request is specific enough:**
   - ❌ TOO VAGUE: "Get product from Nike" (which product?)
   - ❌ TOO VAGUE: "Scrape jobs from Indeed" (which job/location?)
   - ✅ SPECIFIC: "Get the Nike Air Max 90 product details"
   - ✅ SPECIFIC: "Scrape https://nike.com/product/air-max-90"
3. **If request is vague, ask for clarification BEFORE searching:**
   - "Which specific product/item would you like details for?"
   - "Can you provide the product name, or a URL?"
   - "I can only scrape one page at a time - which one should I get?"
4. Once you have a specific target, use `web_search` to find the exact page (if no URL given)
5. When you have multiple URL options, present them to the user and ask which to use
6. Use `scrape_url` to extract data from that ONE specific page
7. Present results in a clear, formatted way

**Guidelines:**
- Be conversational and helpful
- **ALWAYS clarify ambiguous requests BEFORE searching/scraping:**
  - User: "Get Nike products" → You: "Which specific Nike product?"
  - User: "Scrape jobs" → You: "What job title and location?"
  - User: "Get news from BBC" → You: "The BBC homepage, or a specific section/article?"
- Always confirm the URL before scraping
- **Remember: ONE URL = ONE scrape** (cannot scrape multiple pages in one go)
- Present data in clean JSON format
- Offer to refine or export results
- If scraping fails, explain why and suggest alternatives

**Important:**
- Always use tools to gather information - don't guess or make up data
- When presenting URLs from search, show the top 3-5 options
- After scraping, summarize what was extracted (e.g., "Found product details for Nike Air Max 90")
- Be concise but informative
- Never promise to scrape multiple pages - you can only do one at a time"""

    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        Send a message to the agent and get streaming response.

        Args:
            user_message: User's natural language input

        Yields:
            Chunks of the agent's response
        """
        from agent_tools import understand_intent, web_search, scrape_url
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Truncate history if too long
        if len(self.conversation_history) > settings.MAX_CONVERSATION_HISTORY:
            # Keep system context but trim old messages
            self.conversation_history = self.conversation_history[-settings.MAX_CONVERSATION_HISTORY:]

        # User message logged at debug level only
        logger.debug(f"User: {user_message}")

        try:
            # Create messages for API call
            messages = self.conversation_history.copy()
            
            # Tool execution loop
            max_iterations = 10
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Call Claude with tools
                response = await self.client.messages.create(
                    model=settings.CLAUDE_MODEL,
                    max_tokens=settings.CLAUDE_MAX_TOKENS,
                    temperature=settings.CLAUDE_TEMPERATURE,
                    system=self._get_system_prompt(),
                    messages=messages,
                    tools=self.tools
                )
                
                # Process response
                assistant_content = []
                needs_tool_execution = False
                
                for block in response.content:
                    if block.type == "text":
                        # Stream text to user
                        yield block.text
                        assistant_content.append({"type": "text", "text": block.text})
                    
                    elif block.type == "tool_use":
                        needs_tool_execution = True
                        tool_name = block.name
                        tool_input = block.input
                        tool_use_id = block.id
                        
                        logger.debug(f"🔧 Tool called: {tool_name}")
                        
                        # Execute tool
                        try:
                            if tool_name == "understand_intent":
                                tool_result = await understand_intent(tool_input)
                            elif tool_name == "web_search":
                                tool_result = await web_search(tool_input)
                            elif tool_name == "scrape_url":
                                tool_result = await scrape_url(tool_input)
                                # Store scraped data
                                result_data = json.loads(tool_result["content"][0]["text"])
                                if result_data.get("success"):
                                    self.last_scraped_data = result_data.get("data")
                            else:
                                tool_result = {
                                    "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                                    "is_error": True
                                }
                        except Exception as e:
                            logger.error(f"Tool execution error: {e}")
                            tool_result = {
                                "content": [{"type": "text", "text": f"Tool error: {str(e)}"}],
                                "is_error": True
                            }
                        
                        # Add tool use and result to assistant content
                        assistant_content.append({
                            "type": "tool_use",
                            "id": tool_use_id,
                            "name": tool_name,
                            "input": tool_input
                        })
                        
                        # Add tool result to messages for next iteration
                        messages.append({
                            "role": "assistant",
                            "content": assistant_content
                        })
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": tool_result["content"][0]["text"]
                            }]
                        })
                        
                        # Reset assistant_content for next iteration
                        assistant_content = []
                        break  # Go to next iteration
                
                # If no tool execution needed, we're done
                if not needs_tool_execution:
                    # Store final assistant message
                    if assistant_content:
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": assistant_content[0]["text"] if assistant_content[0]["type"] == "text" else ""
                        })
                    break
                
                # Check stop reason
                if response.stop_reason == "end_turn":
                    break

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            logger.error(error_msg)
            yield error_msg

    async def interactive_mode(self):
        """
        Run interactive chat loop.
        """
        print("\n" + "="*70)
        print("🤖 Intelligent Web Scraper Agent")
        print("   Powered by Claude Sonnet 4.5 + Agent SDK + Exa Search")
        print("="*70)
        print("\nTell me what you want to scrape (or 'quit' to exit)")
        print("\n💡 Examples:")
        print("  - 'I want to scrape products from Nike'")
        print("  - 'Get job listings from Indeed for Python developers'")
        print("  - 'Find news articles about AI from TechCrunch'")
        print("  - 'Scrape https://news.ycombinator.com for top stories'")
        print("\n" + "="*70 + "\n")

        while True:
            try:
                # Get user input
                user_input = input("\n🧑 You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!\n")
                    break

                # Get agent response
                print("\n🤖 Agent: ", end="", flush=True)

                async for chunk in self.chat(user_input):
                    print(chunk, end="", flush=True)

                print()  # New line after response

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!\n")
                break
            except EOFError:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}")
                print(f"\n❌ Error: {str(e)}\n")

    async def single_query(self, query: str) -> str:
        """
        Execute a single query (non-interactive).

        Args:
            query: User's request

        Returns:
            Complete agent response
        """
        response_parts = []
        async for chunk in self.chat(query):
            response_parts.append(chunk)
        return "".join(response_parts)


async def main():
    """Main entry point for agent mode"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Intelligent Web Scraper Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended)
  python agent_main.py

  # Single query mode
  python agent_main.py --query "Scrape products from Nike.com"

  # With output file
  python agent_main.py --query "Get news from BBC" --output news.json

  # Verbose mode
  python agent_main.py --verbose
        """
    )

    parser.add_argument(
        "--query", "-q",
        help="Single query (non-interactive mode)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for results (JSON)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel("DEBUG")
    else:
        # Keep internal logs hidden for clean user experience
        logger.setLevel("WARNING")

    # Print banner
    if not args.query:
        print("\n" + "="*70)
        print("🕷️  Intelligent Web Scraper Agent")
        print("   Powered by Claude Sonnet 4.5 + Exa Search")
        print("="*70 + "\n")

    # Create agent
    try:
        agent = AgentScraper()
    except Exception as e:
        print(f"\n❌ Failed to initialize agent: {e}")
        print("\nPlease check:")
        print("  1. ANTHROPIC_API_KEY is set in .env")
        print("  2. All dependencies are installed (pip install -r requirements.txt)")
        return 1

    # Single query or interactive
    if args.query:
        # Single query mode
        try:
            response = await agent.single_query(args.query)

            if args.output:
                # Save to file
                output_data = {
                    "query": args.query,
                    "response": response,
                    "conversation_history": agent.conversation_history,
                    "scraped_data": agent.last_scraped_data
                }

                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)

                print(f"\n✅ Saved to {args.output}")
            else:
                print(response)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            return 1

    else:
        # Interactive mode
        try:
            await agent.interactive_mode()
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return 1

    return 0


if __name__ == "__main__":
    import sys
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
