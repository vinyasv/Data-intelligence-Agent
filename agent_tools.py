"""
Agent Tools Module

Custom tools for the conversational web scraper agent.
Implements three core tools:
1. understand_intent - Analyzes user requests
2. web_search - Finds URLs using Exa AI
3. scrape_url - Extracts data from websites
"""
import json
from typing import Dict, Any
from anthropic import Anthropic

from config import settings
from utils import logger


# Tool 1: Intent Understanding
async def understand_intent(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classifies user intent into:
    - url_provided: User gave a URL, ready to scrape
    - search_needed: Need to search for URL
    - clarification_needed: Ambiguous request
    - refinement: Modifying previous request

    Args:
        args: Dict containing:
            - user_message: The user's natural language input
            - conversation_history: JSON string of previous conversation

    Returns:
        Tool response with intent classification
    """
    logger.info("🧠 Analyzing user intent...")

    try:
        # Use Claude Haiku (fast, cheap) to analyze intent
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        prompt = f"""Analyze this user message and classify the intent.

User message: {args['user_message']}
Conversation history: {args.get('conversation_history', '[]')}

Determine:
1. Is a URL provided? If yes, extract it.
2. If no URL, what should we search for?
3. What do they want to extract?
4. Is the request clear or needs clarification?

Return ONLY valid JSON (no markdown, no explanations):
{{
    "intent": "search_needed" | "url_provided" | "clarification_needed" | "refinement",
    "url": "extracted URL or null",
    "search_query": "what to search for or null",
    "extraction_query": "what to extract",
    "needs_clarification": boolean,
    "clarification_question": "question to ask user or null"
}}
"""

        response = client.messages.create(
            model=settings.INTENT_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        response_text = response.content[0].text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text

        intent_data = json.loads(response_text)

        logger.info(f"   Intent: {intent_data.get('intent')}")

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(intent_data, indent=2)
            }]
        }

    except Exception as e:
        logger.error(f"Intent analysis failed: {e}")
        # Default to clarification on error
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "intent": "clarification_needed",
                    "needs_clarification": True,
                    "clarification_question": "Could you please rephrase your request? I want to make sure I understand what you need."
                }, indent=2)
            }]
        }


# Tool 2: Web Search with Exa
async def web_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for URLs matching the query using Exa's AI-powered search.

    Exa provides:
    - Neural/semantic search for intent-based queries
    - Keyword search for exact matches
    - Auto mode that intelligently chooses best method
    - High-quality results with summaries and highlights

    Args:
        args: Dict containing:
            - query: Search query
            - max_results: Number of results (default 5)
            - search_type: "auto", "neural", or "keyword" (default "auto")

    Returns:
        Tool response with search results
    """
    from exa_py import Exa

    query = args["query"]
    max_results = args.get("max_results", settings.WEB_SEARCH_MAX_RESULTS)
    search_type = args.get("search_type", settings.EXA_SEARCH_TYPE)

    logger.info(f"🔍 Searching Exa for: {query}")
    logger.info(f"   Mode: {search_type}, Max results: {max_results}")

    try:
        # Check if API key is set
        if not settings.EXA_API_KEY:
            raise ValueError("EXA_API_KEY not set in environment variables")

        # Initialize Exa client
        exa = Exa(api_key=settings.EXA_API_KEY)

        # Perform search with highlights for better context
        search_results = exa.search_and_contents(
            query,
            type=search_type,
            num_results=max_results,
            text={"max_characters": 500},  # Get snippet
            highlights=True  # Get key excerpts
        )

        # Format results
        results = []
        for result in search_results.results:
            results.append({
                "url": result.url,
                "title": result.title,
                "snippet": result.text[:500] if result.text else "",
                "published_date": result.published_date if hasattr(result, 'published_date') else None,
                "score": result.score if hasattr(result, 'score') else None,
                "highlights": result.highlights if hasattr(result, 'highlights') else []
            })

        logger.info(f"   Found {len(results)} results")

        # Convert CostDollars object to float if present
        cost_value = None
        if hasattr(search_results, 'cost_dollars') and search_results.cost_dollars:
            try:
                # CostDollars has a value attribute or can be converted to float
                cost_value = float(search_results.cost_dollars)
            except (TypeError, ValueError, AttributeError):
                cost_value = None

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "query": query,
                    "search_type": search_results.resolved_search_type if hasattr(search_results, 'resolved_search_type') else search_type,
                    "results": results,
                    "cost": cost_value
                }, indent=2)
            }]
        }

    except Exception as e:
        logger.error(f"Web search failed: {e}")

        # Fallback: try keyword search if neural failed
        if search_type == "neural":
            logger.info("   Retrying with keyword search...")
            try:
                args["search_type"] = "keyword"
                return await web_search(args)
            except:
                pass  # Fall through to error response

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": str(e),
                    "suggestion": "Check EXA_API_KEY is set correctly or provide a direct URL"
                }, indent=2)
            }],
            "is_error": True
        }


# Tool 3: Scrape URL
async def scrape_url(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wraps the scraper by running it in a subprocess to avoid event loop conflicts.

    This is the bridge between the agent and existing scraper.
    Runs scraper in isolated subprocess to prevent asyncio/Twisted reactor conflicts.

    Args:
        args: Dict containing:
            - url: Target URL to scrape
            - extraction_query: Natural language description of what to extract
            - prefer_css: Prefer CSS extraction (optional, default False)
            - skip_validation: Skip Pydantic validation (optional, default False)

    Returns:
        Tool response with scraped data
    """
    import asyncio
    import os
    import sys

    url = args["url"]
    extraction_query = args["extraction_query"]

    # Prepare subprocess input
    scraper_input = {
        "url": url,
        "query": extraction_query,
        "options": {
            "respect_robots_txt": True,
            "skip_validation": args.get("skip_validation", False),
            "prefer_css": args.get("prefer_css", False)
        }
    }

    try:
        # Get path to scraper subprocess script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        scraper_script = os.path.join(script_dir, "scraper_subprocess.py")

        logger.info(f"🔧 Running scraper in subprocess: {url}")

        # Run scraper in subprocess
        process = await asyncio.create_subprocess_exec(
            sys.executable,  # Use same Python interpreter
            scraper_script,
            json.dumps(scraper_input),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait for completion with timeout (120 seconds)
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=120.0
            )

            # Log stderr for debugging
            if stderr:
                stderr_text = stderr.decode('utf-8')
                logger.debug(f"Subprocess stderr: {stderr_text}")

        except asyncio.TimeoutError:
            logger.error(f"⏱️  Scraper subprocess timeout after 120s for {url}")
            process.kill()
            await process.wait()
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "url": url,
                        "error": "Scraper timeout (120s exceeded)"
                    }, indent=2)
                }],
                "is_error": True
            }

        # Parse result
        if process.returncode == 0:
            stdout_text = stdout.decode('utf-8')
            logger.debug(f"Subprocess stdout: {stdout_text[:500]}")
            result = json.loads(stdout_text)

            if result.get("success"):
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "success": True,
                            "url": url,
                            "data": result["data"]
                        }, indent=2)
                    }]
                }
            else:
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "success": False,
                            "url": url,
                            "error": result.get("error", "Unknown error"),
                            "error_type": result.get("error_type", "UnknownError")
                        }, indent=2)
                    }],
                    "is_error": True
                }
        else:
            # Non-zero exit code
            error_output = stderr.decode('utf-8') if stderr else "No error output"
            logger.error(f"Scraper subprocess failed: {error_output}")

            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "url": url,
                        "error": f"Scraper process failed: {error_output[:500]}"
                    }, indent=2)
                }],
                "is_error": True
            }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse scraper output: {e}")
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "url": url,
                    "error": f"Invalid JSON from scraper: {str(e)}"
                }, indent=2)
            }],
            "is_error": True
        }

    except Exception as e:
        logger.error(f"Scraper subprocess error: {e}")
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "url": url,
                    "error": f"Unexpected error: {str(e)}"
                }, indent=2)
            }],
            "is_error": True
        }
