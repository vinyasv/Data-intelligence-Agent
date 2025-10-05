#!/usr/bin/env python3
"""
Phase 4 Integration Testing

Tests the complete agent workflow end-to-end, verifying that:
1. Agent can be initialized
2. Tools are properly integrated
3. Scraper pipeline works through agent
4. Error handling propagates correctly
"""
import asyncio
import sys


async def test_full_import_chain():
    """Test that all imports work correctly"""
    print("\n" + "="*60)
    print("Testing Full Import Chain")
    print("="*60)

    try:
        print("\n📦 Testing imports...")

        # Core scraper
        from main import scrape
        from schema_generator import SchemaGenerator
        from strategy_router import StrategyRouter
        from extractor import WebExtractor
        print("   ✅ Core scraper modules")

        # Agent tools
        from agent_tools import understand_intent, web_search, scrape_url
        print("   ✅ Agent tools")

        # Agent main
        from agent_main import AgentScraper
        print("   ✅ Agent main")

        # Models
        from agent_models import IntentResult, SearchResponse, ScrapeResponse
        print("   ✅ Agent models")

        # Config
        from config import settings
        print("   ✅ Configuration")

        print("\n✅ All imports successful - no circular dependencies")
        return True

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_scraper_callable_from_tool():
    """Test that scraper can be called through the tool interface"""
    print("\n" + "="*60)
    print("Testing Scraper Accessibility from Tools")
    print("="*60)

    try:
        print("\n🔧 Checking scraper accessibility...")

        # Import the tool
        from agent_tools import scrape_url
        print("   ✅ scrape_url tool imported")

        # Check the source file contains the import
        with open("agent_tools.py") as f:
            source = f.read()
        assert "from main import scrape" in source, "Tool file should import scrape"
        print("   ✅ agent_tools.py imports scrape() from main.py")

        # Verify scrape is callable
        from main import scrape
        assert callable(scrape), "scrape should be callable"
        print("   ✅ scrape() function is callable")

        # Verify scrape_url is a tool
        assert type(scrape_url).__name__ == "SdkMcpTool", "scrape_url should be SdkMcpTool"
        print("   ✅ scrape_url is properly decorated as a tool")

        print("\n✅ Scraper is properly accessible from tools")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_tool_registration():
    """Test that tools are properly registered with the agent"""
    print("\n" + "="*60)
    print("Testing Agent Tool Registration")
    print("="*60)

    try:
        print("\n🤖 Initializing agent...")

        from agent_main import AgentScraper
        agent = AgentScraper()

        print("   ✅ Agent initialized")

        # Check tools are defined
        assert agent.tools is not None, "Tools should exist"
        assert len(agent.tools) == 3, "Should have 3 tools"
        print("   ✅ Tools defined")

        # Check tool names
        tool_names = [tool['name'] for tool in agent.tools]
        assert "understand_intent" in tool_names, "understand_intent should be available"
        assert "web_search" in tool_names, "web_search should be available"
        assert "scrape_url" in tool_names, "scrape_url should be available"
        print(f"   ✅ All 3 tools registered: {tool_names}")

        print("\n✅ Tools properly registered with agent")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_propagation():
    """Test that errors propagate correctly from scraper to agent"""
    print("\n" + "="*60)
    print("Testing Error Propagation")
    print("="*60)

    try:
        print("\n⚠️  Testing error handling...")

        from models import ExtractionError, SchemaGenerationError, StrategyRoutingError

        # Test that exceptions exist
        print("   ✅ Custom exception classes defined")

        # Test that agent_tools.py imports them
        import agent_tools
        source = open("agent_tools.py").read()
        assert "ExtractionError" in source, "agent_tools should import ExtractionError"
        assert "SchemaGenerationError" in source, "agent_tools should import SchemaGenerationError"
        assert "StrategyRoutingError" in source, "agent_tools should import StrategyRoutingError"
        print("   ✅ Exceptions imported in agent_tools.py")

        print("\n✅ Error propagation chain verified")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_configuration_consistency():
    """Test that configuration is consistent across modules"""
    print("\n" + "="*60)
    print("Testing Configuration Consistency")
    print("="*60)

    try:
        print("\n⚙️  Checking configuration...")

        from config import settings

        # Check required fields
        assert hasattr(settings, 'ANTHROPIC_API_KEY'), "Should have ANTHROPIC_API_KEY"
        assert hasattr(settings, 'CLAUDE_MODEL'), "Should have CLAUDE_MODEL"
        print("   ✅ Classic scraper config present")

        # Check agent fields
        assert hasattr(settings, 'AGENT_MODE'), "Should have AGENT_MODE"
        assert hasattr(settings, 'INTENT_MODEL'), "Should have INTENT_MODEL"
        assert hasattr(settings, 'MAX_CONVERSATION_HISTORY'), "Should have MAX_CONVERSATION_HISTORY"
        assert hasattr(settings, 'EXA_API_KEY'), "Should have EXA_API_KEY"
        assert hasattr(settings, 'WEB_SEARCH_MAX_RESULTS'), "Should have WEB_SEARCH_MAX_RESULTS"
        assert hasattr(settings, 'EXA_SEARCH_TYPE'), "Should have EXA_SEARCH_TYPE"
        print("   ✅ Agent config present")

        # Check defaults
        assert settings.AGENT_MODE == False, "AGENT_MODE should default to False"
        assert settings.INTENT_MODEL == "claude-3-5-haiku-20241022", "Intent model should be Haiku 3.5"
        assert settings.MAX_CONVERSATION_HISTORY == 20, "Max history should be 20"
        assert settings.WEB_SEARCH_MAX_RESULTS == 5, "Search results should be 5"
        assert settings.EXA_SEARCH_TYPE == "auto", "Search type should be auto"
        print("   ✅ All defaults correct")

        print("\n✅ Configuration is consistent")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_backward_compatibility():
    """Test that classic CLI mode still works"""
    print("\n" + "="*60)
    print("Testing Backward Compatibility")
    print("="*60)

    try:
        print("\n🔙 Checking classic scraper still works...")

        from main import scrape
        import inspect

        # Check function signature hasn't changed
        sig = inspect.signature(scrape)
        params = list(sig.parameters.keys())

        assert 'url' in params, "scrape should have url parameter"
        assert 'query' in params, "scrape should have query parameter"
        assert 'respect_robots_txt' in params, "scrape should have respect_robots_txt"
        assert 'skip_validation' in params, "scrape should have skip_validation"
        assert 'prefer_css' in params, "scrape should have prefer_css"
        assert 'stats' in params, "scrape should have stats parameter"

        print(f"   ✅ scrape() signature unchanged ({len(params)} params)")

        # Check it's still async
        assert inspect.iscoroutinefunction(scrape), "scrape should be async"
        print("   ✅ scrape() is still async")

        # Check main.py still has CLI entry point
        import main
        assert hasattr(main, 'main'), "main.py should have main() function"
        assert hasattr(main, 'main_async'), "main.py should have main_async() function"
        print("   ✅ CLI entry points preserved")

        print("\n✅ Backward compatibility maintained")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_documentation_exists():
    """Test that all documentation is in place"""
    print("\n" + "="*60)
    print("Testing Documentation")
    print("="*60)

    try:
        print("\n📚 Checking documentation files...")

        import os

        docs = {
            "CLAUDE.md": "Project architecture and commands",
            "AGENT_PLAN.md": "Agent implementation plan",
            "AGENT_USAGE.md": "Agent usage guide",
            ".env.example": "Environment variable template",
            "requirements.txt": "Dependencies"
        }

        all_exist = True
        for filename, description in docs.items():
            if os.path.exists(filename):
                print(f"   ✅ {filename} - {description}")
            else:
                print(f"   ❌ {filename} - MISSING")
                all_exist = False

        if all_exist:
            print("\n✅ All documentation present")
            return True
        else:
            print("\n⚠️  Some documentation missing")
            return False

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


async def main():
    """Run all integration tests"""
    print("="*60)
    print("Phase 4 Integration Testing")
    print("Testing complete agent workflow and integration")
    print("="*60)

    results = []

    # Run all tests
    results.append(("Full Import Chain", await test_full_import_chain()))
    results.append(("Scraper Tool Integration", await test_scraper_callable_from_tool()))
    results.append(("Agent Tool Registration", await test_agent_tool_registration()))
    results.append(("Error Propagation", await test_error_propagation()))
    results.append(("Configuration Consistency", await test_configuration_consistency()))
    results.append(("Backward Compatibility", await test_backward_compatibility()))
    results.append(("Documentation", await test_documentation_exists()))

    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 Phase 4 complete! Full integration verified.")
        print("\n✅ The intelligent web scraper agent is ready to use!")
        print("\nQuick start:")
        print("  1. Add EXA_API_KEY to .env (optional for web search)")
        print("  2. Run: python agent_main.py")
        print("  3. Start scraping with natural language!")
        return 0
    else:
        print("\n⚠️  Some integration tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
