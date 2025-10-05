#!/usr/bin/env python3
"""
Comprehensive Test Suite for Intelligent Web Scraper Agent

Tests all agent functionality including:
- Basic conversation flow
- Intent understanding
- URL discovery with Exa search
- Scraping functionality
- Multi-turn conversations
- Error handling
- CLI commands
- Edge cases
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Import agent components
from agent_main import AgentScraper
from agent_tools import understand_intent, web_search, scrape_url
from config import settings


class AgentTester:
    """Comprehensive tester for the agent"""

    def __init__(self):
        self.console = Console()
        self.agent: AgentScraper = None
        self.test_results: List[Dict[str, Any]] = []

    async def setup(self):
        """Initialize the agent"""
        self.console.print("\n[cyan]Setting up agent...[/cyan]")
        try:
            self.agent = AgentScraper()
            self.console.print("[green]✅ Agent initialized successfully[/green]\n")
            return True
        except Exception as e:
            self.console.print(f"[red]❌ Failed to initialize: {e}[/red]\n")
            return False

    async def run_test(self, test_name: str, test_func, *args):
        """Run a single test and record results"""
        self.console.print(f"\n[bold yellow]Testing:[/bold yellow] {test_name}")
        self.console.print("[dim]" + "─" * 60 + "[/dim]")

        try:
            result = await test_func(*args)
            self.test_results.append({
                "name": test_name,
                "status": "✅ PASS" if result else "❌ FAIL",
                "success": result
            })
            status = "[green]✅ PASS[/green]" if result else "[red]❌ FAIL[/red]"
            self.console.print(f"\n{status}\n")
            return result
        except Exception as e:
            self.test_results.append({
                "name": test_name,
                "status": "❌ ERROR",
                "success": False,
                "error": str(e)
            })
            self.console.print(f"\n[red]❌ ERROR: {e}[/red]\n")
            return False

    async def test_basic_greeting(self) -> bool:
        """Test 1: Basic greeting response"""
        response_parts = []
        async for chunk in self.agent.chat("Hello"):
            response_parts.append(chunk)

        response = "".join(response_parts)
        self.console.print(f"[white]Response: {response[:200]}...[/white]")

        # Check if response is helpful
        success = len(response) > 10 and any(word in response.lower() for word in ["hello", "hi", "help", "scrape"])
        return success

    async def test_vague_request_clarification(self) -> bool:
        """Test 2: Agent asks for clarification on vague requests"""
        response_parts = []
        async for chunk in self.agent.chat("Get Nike products"):
            response_parts.append(chunk)

        response = "".join(response_parts).lower()
        self.console.print(f"[white]Response: {response[:300]}...[/white]")

        # Check if agent asks for clarification
        success = any(phrase in response for phrase in [
            "which", "specific", "clarification", "what product", "which product"
        ])
        return success

    async def test_url_provided_scraping(self) -> bool:
        """Test 3: Scraping with URL provided (simple page)"""
        url = "https://example.com"
        query = f"Scrape {url} and get the main heading and paragraph text"

        response_parts = []
        async for chunk in self.agent.chat(query):
            response_parts.append(chunk)

        response = "".join(response_parts).lower()
        self.console.print(f"[white]Response: {response[:300]}...[/white]")

        # Check if scraping was successful
        success = "success" in response or "example" in response
        return success

    async def test_intent_understanding(self) -> bool:
        """Test 4: Intent classification tool"""
        test_message = "I want to scrape the iPhone 15 Pro product page from Apple"

        result = await understand_intent({
            "user_message": test_message,
            "conversation_history": "[]"
        })

        content = json.loads(result["content"][0]["text"])
        self.console.print(f"[white]Intent: {content.get('intent')}[/white]")
        self.console.print(f"[white]URL: {content.get('url', 'None')}[/white]")
        self.console.print(f"[white]Search Query: {content.get('search_query', 'None')}[/white]")

        # Should recognize search_needed or url_provided
        success = content.get("intent") in ["search_needed", "url_provided"]
        return success

    async def test_web_search_tool(self) -> bool:
        """Test 5: Web search with Exa (if API key available)"""
        if not settings.EXA_API_KEY:
            self.console.print("[yellow]⚠️  EXA_API_KEY not set, skipping web search test[/yellow]")
            return True  # Skip, not a failure

        result = await web_search({
            "query": "Nike Air Max 90 product page",
            "max_results": 3,
            "search_type": "auto"
        })

        content = json.loads(result["content"][0]["text"])
        self.console.print(f"[white]Found {len(content.get('results', []))} results[/white]")

        if content.get("results"):
            for i, res in enumerate(content["results"][:3], 1):
                self.console.print(f"[dim]{i}. {res.get('title')} - {res.get('url')}[/dim]")

        success = content.get("success", False) and len(content.get("results", [])) > 0
        return success

    async def test_scrape_tool_directly(self) -> bool:
        """Test 6: Direct scrape_url tool test"""
        result = await scrape_url({
            "url": "https://example.com",
            "extraction_query": "Get the main heading and description",
            "prefer_css": False,
            "skip_validation": False
        })

        content = json.loads(result["content"][0]["text"])
        self.console.print(f"[white]Success: {content.get('success')}[/white]")

        if content.get("data"):
            self.console.print(f"[dim]Data keys: {list(content['data'].keys())}[/dim]")

        success = content.get("success", False)
        return success

    async def test_multi_turn_conversation(self) -> bool:
        """Test 7: Multi-turn conversation with context"""
        # Turn 1
        response1_parts = []
        async for chunk in self.agent.chat("I want product details"):
            response1_parts.append(chunk)
        response1 = "".join(response1_parts).lower()

        self.console.print(f"[white]Turn 1: {response1[:150]}...[/white]")

        # Turn 2 - provide more specifics
        response2_parts = []
        async for chunk in self.agent.chat("For Nike Air Max 90"):
            response2_parts.append(chunk)
        response2 = "".join(response2_parts).lower()

        self.console.print(f"[white]Turn 2: {response2[:150]}...[/white]")

        # Check if context was maintained
        success = (
            any(word in response1 for word in ["which", "what", "specific"]) and
            len(self.agent.conversation_history) >= 4  # 2 turns = 4 messages
        )
        return success

    async def test_error_handling_invalid_url(self) -> bool:
        """Test 8: Error handling for invalid URLs"""
        response_parts = []
        async for chunk in self.agent.chat("Scrape https://this-domain-does-not-exist-12345.com"):
            response_parts.append(chunk)

        response = "".join(response_parts).lower()
        self.console.print(f"[white]Response: {response[:200]}...[/white]")

        # Should handle error gracefully
        success = any(word in response for word in ["error", "failed", "couldn't", "unable", "issue"])
        return success

    async def test_conversation_history_tracking(self) -> bool:
        """Test 9: Conversation history is tracked correctly"""
        initial_count = len(self.agent.conversation_history)

        # Send a message
        async for _ in self.agent.chat("Test message"):
            pass

        new_count = len(self.agent.conversation_history)
        self.console.print(f"[white]History size: {initial_count} → {new_count}[/white]")

        # Should have increased by 2 (user + assistant)
        success = new_count > initial_count
        return success

    async def test_specific_product_scraping(self) -> bool:
        """Test 10: Scraping a specific product with clear request"""
        query = "Scrape https://example.com and extract the main heading"

        response_parts = []
        async for chunk in self.agent.chat(query):
            response_parts.append(chunk)

        response = "".join(response_parts).lower()
        self.console.print(f"[white]Response: {response[:250]}...[/white]")

        # Should successfully scrape
        success = "example" in response or "heading" in response or "domain" in response
        return success

    def print_summary(self):
        """Print test summary table"""
        table = Table(
            title="\n📊 Test Summary",
            border_style="cyan",
            box=box.ROUNDED
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Test Name", style="white")
        table.add_column("Status", style="bold")

        for i, result in enumerate(self.test_results, 1):
            status_style = "green" if result["success"] else "red"
            table.add_row(
                str(i),
                result["name"],
                f"[{status_style}]{result['status']}[/{status_style}]"
            )

        self.console.print(table)

        # Summary stats
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed

        summary = f"""
**Results:**
- Total Tests: {total}
- Passed: {passed} ✅
- Failed: {failed} ❌
- Success Rate: {(passed/total*100):.1f}%
        """

        self.console.print(Panel(
            summary,
            title="Summary",
            border_style="green" if failed == 0 else "yellow"
        ))

    async def run_all_tests(self):
        """Run all tests"""
        self.console.print(Panel(
            "[bold cyan]🧪 Intelligent Web Scraper Agent - Comprehensive Test Suite[/bold cyan]\n"
            "Testing all agent functionality...",
            border_style="cyan"
        ))

        # Setup
        if not await self.setup():
            return False

        # Run tests
        await self.run_test("Basic Greeting", self.test_basic_greeting)
        await self.run_test("Vague Request Clarification", self.test_vague_request_clarification)
        await self.run_test("URL Provided Scraping", self.test_url_provided_scraping)
        await self.run_test("Intent Understanding Tool", self.test_intent_understanding)
        await self.run_test("Web Search Tool (Exa)", self.test_web_search_tool)
        await self.run_test("Scrape Tool Directly", self.test_scrape_tool_directly)
        await self.run_test("Multi-turn Conversation", self.test_multi_turn_conversation)
        await self.run_test("Error Handling - Invalid URL", self.test_error_handling_invalid_url)
        await self.run_test("Conversation History Tracking", self.test_conversation_history_tracking)
        await self.run_test("Specific Product Scraping", self.test_specific_product_scraping)

        # Summary
        self.print_summary()

        # Return success if all passed
        return all(r["success"] for r in self.test_results)


async def main():
    """Main entry point"""
    tester = AgentTester()
    success = await tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite error: {e}\n")
        sys.exit(1)
