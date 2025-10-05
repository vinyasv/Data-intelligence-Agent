#!/usr/bin/env python3
"""
Enhanced CLI Interface for Intelligent Web Scraper Agent

Provides a rich, conversational interface with:
- Color-coded output
- Formatted tables for search results
- Syntax-highlighted JSON
- Progress indicators
- Command system
- Session management
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.prompt import Prompt

from agent_main import AgentScraper
from utils import logger


class EnhancedAgentCLI:
    """Enhanced CLI interface for the web scraper agent"""

    def __init__(self):
        self.console = Console()
        self.agent: Optional[AgentScraper] = None
        self.session_data: List[Dict[str, Any]] = []
        self.start_time = datetime.now()

    def print_banner(self):
        """Display welcome banner"""
        banner = """
# 🤖 Intelligent Web Scraper Agent
## Powered by Claude Sonnet 4.5 + Exa Search

Talk to me naturally to scrape any website!
        """
        self.console.print(Panel(
            Markdown(banner),
            border_style="cyan",
            box=box.DOUBLE
        ))

    def print_help(self):
        """Display help information"""
        help_text = """
## Available Commands

- `/help` - Show this help message
- `/save [filename]` - Save conversation to JSON file
- `/export [filename]` - Export scraped data to JSON
- `/history` - Show conversation history
- `/stats` - Show session statistics
- `/clear` - Clear conversation history
- `/quit` or `/exit` - Exit the agent

## Example Queries

- "I want to scrape products from Nike"
- "Get job listings from Indeed for Python developers"
- "Find news articles about AI from TechCrunch"
- "Scrape https://news.ycombinator.com for top stories"

## Tips

- The agent can only scrape ONE page at a time
- If your request is vague, the agent will ask for clarification
- You can refine results through follow-up questions
        """
        self.console.print(Panel(
            Markdown(help_text),
            title="Help",
            border_style="blue"
        ))

    def print_examples(self):
        """Display example usage"""
        examples = Table(
            title="💡 Example Conversations",
            border_style="green",
            box=box.ROUNDED
        )
        examples.add_column("Scenario", style="cyan", no_wrap=True)
        examples.add_column("What to say", style="yellow")

        examples.add_row(
            "Find a product",
            "I want to scrape the Nike Air Max 90 product details"
        )
        examples.add_row(
            "Scrape a URL",
            "Scrape https://news.ycombinator.com for top stories"
        )
        examples.add_row(
            "Search & scrape",
            "Find and scrape tech news from TechCrunch"
        )
        examples.add_row(
            "Refine results",
            "Only show articles from this week with summaries"
        )

        self.console.print(examples)

    async def initialize_agent(self):
        """Initialize the agent with progress indicator"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Initializing agent..."),
            console=self.console
        ) as progress:
            progress.add_task("init", total=None)
            try:
                self.agent = AgentScraper()
                self.console.print("✅ [green]Agent initialized successfully![/green]\n")
                return True
            except Exception as e:
                self.console.print(f"[red]❌ Failed to initialize agent: {e}[/red]")
                self.console.print("\n[yellow]Please check:[/yellow]")
                self.console.print("  1. ANTHROPIC_API_KEY is set in .env")
                self.console.print("  2. All dependencies are installed")
                return False

    def save_conversation(self, filename: Optional[str] = None):
        """Save conversation to JSON file"""
        if not filename:
            filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            "timestamp": self.start_time.isoformat(),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "conversation": self.agent.conversation_history if self.agent else [],
            "session_data": self.session_data
        }

        Path(filename).write_text(json.dumps(data, indent=2, ensure_ascii=False))
        self.console.print(f"✅ [green]Saved conversation to {filename}[/green]")

    def export_data(self, filename: Optional[str] = None):
        """Export scraped data to JSON file"""
        if not self.agent or not self.agent.last_scraped_data:
            self.console.print("[yellow]⚠️  No scraped data to export[/yellow]")
            return

        if not filename:
            filename = f"scraped_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        Path(filename).write_text(
            json.dumps(self.agent.last_scraped_data, indent=2, ensure_ascii=False)
        )
        self.console.print(f"✅ [green]Exported data to {filename}[/green]")

    def show_history(self):
        """Display conversation history"""
        if not self.agent or not self.agent.conversation_history:
            self.console.print("[yellow]No conversation history yet[/yellow]")
            return

        history_table = Table(
            title="Conversation History",
            border_style="blue",
            box=box.SIMPLE
        )
        history_table.add_column("#", style="dim", width=4)
        history_table.add_column("Role", style="cyan", width=10)
        history_table.add_column("Message", style="white")

        for i, msg in enumerate(self.agent.conversation_history, 1):
            role = msg["role"].capitalize()
            content = msg["content"]
            if len(content) > 100:
                content = content[:97] + "..."
            history_table.add_row(str(i), role, content)

        self.console.print(history_table)

    def show_stats(self):
        """Display session statistics"""
        if not self.agent:
            return

        stats = Table(title="Session Statistics", border_style="magenta")
        stats.add_column("Metric", style="cyan")
        stats.add_column("Value", style="yellow")

        duration = datetime.now() - self.start_time
        stats.add_row("Session Duration", str(duration).split('.')[0])
        stats.add_row("Messages Exchanged", str(len(self.agent.conversation_history)))
        stats.add_row("Scraping Requests", str(len(self.session_data)))

        if self.agent.last_scraped_data:
            stats.add_row("Last Scraped", "✅ Data available")
        else:
            stats.add_row("Last Scraped", "❌ No data")

        self.console.print(stats)

    def display_json(self, data: Dict[str, Any], title: str = "Result"):
        """Display JSON with syntax highlighting"""
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title=title, border_style="green"))

    async def handle_command(self, command: str) -> bool:
        """
        Handle special commands.

        Returns:
            bool: True if should continue, False if should exit
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if cmd in ['/quit', '/exit', '/q']:
            self.console.print("\n[cyan]👋 Goodbye![/cyan]\n")
            return False

        elif cmd == '/help':
            self.print_help()

        elif cmd == '/save':
            self.save_conversation(arg)

        elif cmd == '/export':
            self.export_data(arg)

        elif cmd == '/history':
            self.show_history()

        elif cmd == '/stats':
            self.show_stats()

        elif cmd == '/clear':
            if self.agent:
                self.agent.conversation_history = []
                self.session_data = []
            self.console.print("✅ [green]Conversation history cleared[/green]")

        elif cmd == '/examples':
            self.print_examples()

        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")
            self.console.print("[yellow]Type /help for available commands[/yellow]")

        return True

    async def chat_loop(self):
        """Main conversational loop"""
        self.console.print(
            "[dim]Type your message or use /help for commands, /quit to exit[/dim]\n"
        )

        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]🧑 You[/bold cyan]").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    should_continue = await self.handle_command(user_input)
                    if not should_continue:
                        break
                    continue

                # Chat with agent
                self.console.print("\n[bold magenta]🤖 Agent[/bold magenta]: ", end="")

                response_parts = []
                async for chunk in self.agent.chat(user_input):
                    self.console.print(chunk, end="", style="white")
                    response_parts.append(chunk)

                # Store in session data
                self.session_data.append({
                    "timestamp": datetime.now().isoformat(),
                    "user": user_input,
                    "agent": "".join(response_parts)
                })

                self.console.print()  # New line after response

            except KeyboardInterrupt:
                self.console.print("\n\n[cyan]👋 Interrupted. Goodbye![/cyan]\n")
                break
            except EOFError:
                self.console.print("\n\n[cyan]👋 Goodbye![/cyan]\n")
                break
            except Exception as e:
                logger.error(f"Error in chat loop: {e}")
                self.console.print(f"\n[red]❌ Error: {str(e)}[/red]\n")

    async def run(self):
        """Main entry point"""
        self.print_banner()

        # Initialize agent
        if not await self.initialize_agent():
            return 1

        # Show examples
        self.print_examples()

        # Start chat loop
        await self.chat_loop()

        # Offer to save on exit
        if self.agent and self.agent.conversation_history:
            save = Prompt.ask(
                "\n[yellow]Save conversation before exiting?[/yellow]",
                choices=["y", "n"],
                default="n"
            )
            if save == "y":
                self.save_conversation()

        return 0


async def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced CLI for Intelligent Web Scraper Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode with rich interface
  python agent_cli.py

  # Verbose mode
  python agent_cli.py --verbose
        """
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel("DEBUG")
    else:
        # Keep internal logs hidden for clean user experience
        logger.setLevel("WARNING")

    cli = EnhancedAgentCLI()
    return await cli.run()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
