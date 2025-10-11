#!/usr/bin/env python3
"""
Polymarket Agents Enhanced Trading System - Demo

This script demonstrates the enhanced trading system without requiring API keys.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def demo_strategy_configurations():
    """Demonstrate strategy configurations"""
    print("🎯 STRATEGY CONFIGURATIONS")
    print("=" * 50)
    
    from agents.strategies import ConservativeStrategy, BalancedStrategy, AggressiveStrategy
    
    strategies = [
        ("Conservative", ConservativeStrategy, 16.67),
        ("Balanced", BalancedStrategy, 16.67),
        ("Aggressive", AggressiveStrategy, 16.67)
    ]
    
    for name, strategy_class, capital in strategies:
        print(f"\n{name} Strategy (€{capital:.2f}):")
        print("-" * 30)
        
        # Create strategy instance (this will fail without API keys, but we can show config)
        try:
            strategy = strategy_class(capital)
            print(strategy.get_strategy_description())
        except Exception as e:
            print(f"Configuration loaded (API keys required for execution)")
            print(f"Error: {e}")

def demo_portfolio_management():
    """Demonstrate portfolio management concepts"""
    print("\n\n📊 PORTFOLIO MANAGEMENT")
    print("=" * 50)
    
    from agents.portfolio.allocator import PortfolioAllocator, MarketOpportunity
    
    # Create sample opportunities
    opportunities = [
        MarketOpportunity(
            market_id="12345",
            market_question="Will Candidate X win the election?",
            current_price=0.60,
            estimated_probability=0.70,
            confidence=8,
            edge=0.10,
            volatility=0.15,
            liquidity_score=0.9
        ),
        MarketOpportunity(
            market_id="67890",
            market_question="Will the stock market rise this month?",
            current_price=0.45,
            estimated_probability=0.55,
            confidence=6,
            edge=0.10,
            volatility=0.20,
            liquidity_score=0.8
        )
    ]
    
    # Test different strategies
    strategies = ['conservative', 'balanced', 'aggressive']
    
    for strategy_type in strategies:
        print(f"\n{strategy_type.upper()} Strategy Allocation:")
        print("-" * 30)
        
        allocator = PortfolioAllocator(total_capital=50.0, strategy_type=strategy_type)
        result = allocator.allocate_capital(opportunities)
        
        print(f"Total allocated: €{sum(abs(a) for a in result.allocations.values()):.2f}")
        print(f"Unallocated: €{result.unallocated_capital:.2f}")
        print(f"Expected value: €{result.total_expected_value:.2f}")
        print(f"Portfolio Sharpe: {result.portfolio_sharpe:.2f}")
        
        for market_id, amount in result.allocations.items():
            print(f"  Market {market_id}: €{amount:.2f}")

def demo_risk_management():
    """Demonstrate risk management concepts"""
    print("\n\n🛡️ RISK MANAGEMENT")
    print("=" * 50)
    
    from agents.portfolio.risk_manager import RiskManager
    
    risk_manager = RiskManager(
        max_position_size=0.20,
        max_total_allocation=0.80,
        max_drawdown_threshold=0.15
    )
    
    # Test position limits
    test_allocations = {
        "market1": 15.0,  # 30% of €50
        "market2": 10.0,  # 20% of €50
        "market3": 5.0    # 10% of €50
    }
    
    is_valid, violations = risk_manager.check_position_limits(test_allocations, 50.0)
    
    print(f"Test allocations: {test_allocations}")
    print(f"Valid: {is_valid}")
    if violations:
        print(f"Violations: {violations}")
    
    # Simulate portfolio value updates
    print("\nPortfolio value tracking:")
    risk_manager.update_portfolio_value(50.0)  # Initial
    risk_manager.update_portfolio_value(52.0)  # +4%
    risk_manager.update_portfolio_value(48.0)  # -7.7%
    risk_manager.update_portfolio_value(45.0)  # -6.25%
    
    metrics = risk_manager.calculate_risk_metrics()
    print(f"Current drawdown: {metrics.current_drawdown:.2%}")
    print(f"Max drawdown: {metrics.max_drawdown:.2%}")
    print(f"Sharpe ratio: {metrics.sharpe_ratio:.2f}")

def demo_performance_tracking():
    """Demonstrate performance tracking"""
    print("\n\n📈 PERFORMANCE TRACKING")
    print("=" * 50)
    
    from agents.evaluation.performance_tracker import PerformanceTracker, StrategyResult
    
    tracker = PerformanceTracker()
    
    # Simulate some results
    strategies = ['conservative', 'balanced', 'aggressive']
    
    for i, strategy_name in enumerate(strategies):
        result = StrategyResult(
            strategy_name=strategy_name,
            total_return=0.05 + i * 0.02,  # 5%, 7%, 9%
            sharpe_ratio=1.0 + i * 0.5,    # 1.0, 1.5, 2.0
            win_rate=0.60 + i * 0.05,     # 60%, 65%, 70%
            max_drawdown=0.10 - i * 0.02,  # 10%, 8%, 6%
            brier_score=0.20 - i * 0.02,  # 0.20, 0.18, 0.16
            total_trades=10 + i * 5,      # 10, 15, 20
            profitable_trades=6 + i * 3,  # 6, 9, 12
            cost_per_trade=0.17,
            research_calls=5 + i * 2      # 5, 7, 9
        )
        
        tracker.record_strategy_result(strategy_name, result)
    
    # Generate comparison report
    report = tracker.generate_performance_report()
    print(report)

def demo_cost_analysis():
    """Demonstrate cost analysis with Perplexity"""
    print("\n\n💰 COST ANALYSIS")
    print("=" * 50)
    
    print("Perplexity Sonar Deep Research Pricing:")
    print("- Cost per call: €0.17")
    print("- Weekly budget: €20 (very conservative)")
    print()
    
    strategies = [
        ("Conservative", 7, 15),
        ("Balanced", 10, 25),
        ("Aggressive", 10, 25)
    ]
    
    total_cost = 0
    for strategy_name, events_per_week, max_markets in strategies:
        weekly_cost = events_per_week * 0.17
        total_cost += weekly_cost
        
        print(f"{strategy_name} Strategy:")
        print(f"  Events per week: {events_per_week}")
        print(f"  Max markets: {max_markets}")
        print(f"  Weekly cost: €{weekly_cost:.2f}")
        print(f"  Markets analyzed: {events_per_week * 3:.0f}-{events_per_week * 5:.0f}")  # 2-5 markets per event
        print()
    
    print(f"Total weekly cost: €{total_cost:.2f}")
    print(f"Cost per day: €{total_cost/7:.2f}")
    print(f"Budget utilization: {total_cost/20:.1%}")
    print()
    print("Comparison with OpenAI o3-deep-research:")
    print("- OpenAI cost: €75-150 per call")
    print("- Perplexity cost: €0.17 per call")
    print(f"- Cost reduction: {(1 - 0.17/100)*100:.1f}%")

def main():
    print("🚀 Polymarket Agents Enhanced Trading System - Demo")
    print("=" * 60)
    print("This demo shows the enhanced trading system capabilities")
    print("without requiring API keys or live market data.")
    print()
    
    demo_strategy_configurations()
    demo_portfolio_management()
    demo_risk_management()
    demo_performance_tracking()
    demo_cost_analysis()
    
    print("\n" + "=" * 60)
    print("🎉 DEMO COMPLETED!")
    print()
    print("Next steps to run live tests:")
    print("1. Set PERPLEXITY_API_KEY and OPENAI_API_KEY in .env file")
    print("2. Run: python scripts/python/run_strategy_test.py --strategy all")
    print("3. Analyze results and select best strategy")
    print()
    print("Key benefits of this enhanced system:")
    print("✅ 99.8% cost reduction with Perplexity vs OpenAI")
    print("✅ 10x market coverage (20-30 events vs 2-3 events)")
    print("✅ Better diversification (40-150 markets vs 6-15 markets)")
    print("✅ Portfolio-based allocation with Kelly Criterion")
    print("✅ Multi-strategy comparison and selection")
    print("✅ Comprehensive risk management")

if __name__ == "__main__":
    main()
