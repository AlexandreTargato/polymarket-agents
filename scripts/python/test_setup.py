#!/usr/bin/env python3
"""
Simple test script to verify the enhanced trading system setup.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from agents.research.perplexity_research import PerplexityResearchAgent
        print("✅ PerplexityResearchAgent imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PerplexityResearchAgent: {e}")
        return False
    
    try:
        from agents.research.structured_parser import StructuredOutputParser
        print("✅ StructuredOutputParser imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import StructuredOutputParser: {e}")
        return False
    
    try:
        from agents.portfolio.allocator import PortfolioAllocator
        print("✅ PortfolioAllocator imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PortfolioAllocator: {e}")
        return False
    
    try:
        from agents.portfolio.risk_manager import RiskManager
        print("✅ RiskManager imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import RiskManager: {e}")
        return False
    
    try:
        from agents.strategies import ConservativeStrategy, BalancedStrategy, AggressiveStrategy
        print("✅ Strategy classes imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import strategy classes: {e}")
        return False
    
    try:
        from agents.evaluation.performance_tracker import PerformanceTracker
        print("✅ PerformanceTracker imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PerformanceTracker: {e}")
        return False
    
    try:
        from agents.application.enhanced_trader import EnhancedTrader
        print("✅ EnhancedTrader imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import EnhancedTrader: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    config_path = Path('config/strategies.yaml')
    if config_path.exists():
        print("✅ Configuration file exists")
        
        import yaml
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            print("✅ Configuration loaded successfully")
            print(f"   Initial capital: €{config.get('capital', {}).get('initial', 'N/A')}")
            print(f"   Test duration: {config.get('capital', {}).get('test_period_days', 'N/A')} days")
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            return False
    else:
        print("❌ Configuration file not found")
        return False
    
    return True

def test_environment():
    """Test environment variables"""
    print("\nTesting environment...")
    
    required_vars = ['PERPLEXITY_API_KEY', 'OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set these in your .env file or environment")
        return False
    else:
        print("✅ All required environment variables are set")
    
    return True

def test_strategy_initialization():
    """Test strategy initialization"""
    print("\nTesting strategy initialization...")
    
    try:
        from agents.strategies import ConservativeStrategy, BalancedStrategy, AggressiveStrategy
        
        # Test Conservative strategy
        conservative = ConservativeStrategy(16.67)
        print("✅ Conservative strategy initialized")
        
        # Test Balanced strategy
        balanced = BalancedStrategy(16.67)
        print("✅ Balanced strategy initialized")
        
        # Test Aggressive strategy
        aggressive = AggressiveStrategy(16.67)
        print("✅ Aggressive strategy initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize strategies: {e}")
        return False

def main():
    print("Polymarket Agents Enhanced Trading System - Setup Test")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Run tests
    all_tests_passed &= test_imports()
    all_tests_passed &= test_configuration()
    all_tests_passed &= test_environment()
    all_tests_passed &= test_strategy_initialization()
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! System is ready for testing.")
        print("\nNext steps:")
        print("1. Set your API keys in .env file")
        print("2. Run: python scripts/python/run_strategy_test.py --strategy all")
        print("3. Analyze results and select best strategy")
    else:
        print("❌ SOME TESTS FAILED. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install missing dependencies: pip install -r requirements.txt")
        print("- Set required environment variables")
        print("- Check file permissions and paths")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
