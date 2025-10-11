#!/usr/bin/env python3
"""
Polymarket Agents Strategy Testing CLI

Run strategy comparison tests with different configurations.
"""

import os
import sys
import argparse
import logging
from datetime import date
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.python.test_strategies import StrategyTester
from agents.application.enhanced_trader import EnhancedTrader

def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/strategy_test.log')
        ]
    )

def main():
    parser = argparse.ArgumentParser(description='Polymarket Agents Strategy Testing')
    
    parser.add_argument(
        '--capital', 
        type=float, 
        default=50.0,
        help='Initial capital for testing (default: 50.0)'
    )
    
    parser.add_argument(
        '--days', 
        type=int, 
        default=7,
        help='Test duration in days (default: 7)'
    )
    
    parser.add_argument(
        '--strategy',
        choices=['conservative', 'balanced', 'aggressive', 'all'],
        default='all',
        help='Strategy to test (default: all)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--paper-trading',
        action='store_true',
        default=True,
        help='Enable paper trading mode (default: True)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    logger.info("Starting Polymarket Agents Strategy Testing")
    logger.info(f"Capital: €{args.capital:.2f}")
    logger.info(f"Duration: {args.days} days")
    logger.info(f"Strategy: {args.strategy}")
    logger.info(f"Paper Trading: {args.paper_trading}")
    
    try:
        if args.strategy == 'all':
            # Run full strategy comparison
            logger.info("Running full strategy comparison test...")
            
            tester = StrategyTester(
                initial_capital=args.capital,
                test_duration_days=args.days
            )
            
            results = tester.run_test_week()
            
            # Generate and print report
            report = tester.generate_comparison_report()
            print("\n" + report)
            
            # Get best strategy recommendation
            best_strategy = tester.get_best_strategy('sharpe_ratio')
            if best_strategy:
                print(f"\n🎯 RECOMMENDED STRATEGY: {best_strategy.upper()}")
                print("   Based on highest Sharpe ratio (risk-adjusted returns)")
            
        else:
            # Run single strategy test
            logger.info(f"Running single strategy test: {args.strategy}")
            
            trader = EnhancedTrader(args.strategy, args.capital)
            
            print(f"\n{args.strategy.upper()} STRATEGY TEST")
            print("=" * 50)
            print(trader.get_strategy_description())
            
            # Run for specified days
            for day in range(args.days):
                current_date = date.today()
                print(f"\nDay {day + 1}: {current_date}")
                
                result = trader.execute_portfolio_strategy(current_date)
                
                if result.get('success', False):
                    strategy_result = result.get('strategy_result', {})
                    print(f"  Trades: {strategy_result.get('total_trades', 0)}")
                    print(f"  Return: {strategy_result.get('total_return', 0.0):.2%}")
                    print(f"  Sharpe: {strategy_result.get('sharpe_ratio', 0.0):.2f}")
                else:
                    print(f"  Error: {result.get('error', 'Unknown error')}")
            
            # Get performance summary
            summary = trader.get_performance_summary()
            print(f"\nPerformance Summary:")
            print(f"  Total Trades: {summary.get('total_trades', 0)}")
            print(f"  Research Calls: {summary.get('research_calls', 0)}")
            print(f"  Total Cost: €{summary.get('total_cost', 0.0):.2f}")
        
        logger.info("Strategy testing completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
