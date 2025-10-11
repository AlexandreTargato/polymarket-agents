import os
import yaml
import json
from typing import List, Dict, Optional
from datetime import date, datetime, timedelta
import logging
from pathlib import Path

from agents.application.enhanced_trader import EnhancedTrader
from agents.evaluation.performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

class StrategyTester:
    """
    Strategy testing harness for comparing multiple trading strategies.
    
    Features:
    - Run 3 strategies in parallel for 7 days
    - Track Sharpe ratio, returns, drawdown
    - Compare cost-effectiveness
    - Generate performance report
    - Select best strategy
    """
    
    def __init__(self, initial_capital: float = 50.0, test_duration_days: int = 7):
        self.initial_capital = initial_capital
        self.test_duration_days = test_duration_days
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize strategies with equal capital allocation
        self.strategies = {
            'conservative': EnhancedTrader('conservative', initial_capital / 3),
            'balanced': EnhancedTrader('balanced', initial_capital / 3),
            'aggressive': EnhancedTrader('aggressive', initial_capital / 3)
        }
        
        # Performance tracking
        self.performance_tracker = PerformanceTracker()
        
        # Results storage
        self.test_results: Dict[str, List[Dict]] = {
            'conservative': [],
            'balanced': [],
            'aggressive': []
        }
        
        # Create results directory
        self.results_dir = Path('./test_results')
        self.results_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initialized StrategyTester with €{initial_capital:.2f} for {test_duration_days} days")
        logger.info(f"Capital allocation: €{initial_capital/3:.2f} per strategy")
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        config_path = 'config/strategies.yaml'
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'capital': {'initial': 50.0, 'test_period_days': 7},
            'performance_targets': {
                'min_sharpe_ratio': 1.0,
                'min_win_rate': 0.60,
                'max_brier_score': 0.25
            }
        }
    
    def run_test_week(self) -> Dict[str, Dict]:
        """
        Run all 3 strategies in parallel for the test duration.
        
        Returns:
            Dict with performance results for each strategy
        """
        logger.info("Starting strategy comparison test...")
        logger.info(f"Test duration: {self.test_duration_days} days")
        logger.info(f"Total capital: €{self.initial_capital:.2f}")
        
        start_date = date.today()
        
        for day in range(self.test_duration_days):
            current_date = start_date + timedelta(days=day)
            logger.info(f"Running day {day + 1}/{self.test_duration_days}: {current_date}")
            
            # Run each strategy for the day
            for strategy_name, trader in self.strategies.items():
                try:
                    logger.info(f"Executing {strategy_name} strategy for {current_date}")
                    
                    # Execute strategy
                    result = trader.execute_portfolio_strategy(current_date)
                    
                    # Store result
                    self.test_results[strategy_name].append(result)
                    
                    # Record performance
                    if result.get('success', False):
                        strategy_result = result.get('strategy_result', {})
                        from agents.strategies.strategy_base import StrategyResult
                        
                        perf_result = StrategyResult(
                            strategy_name=strategy_name,
                            total_return=strategy_result.get('total_return', 0.0),
                            sharpe_ratio=strategy_result.get('sharpe_ratio', 0.0),
                            win_rate=strategy_result.get('win_rate', 0.0),
                            max_drawdown=strategy_result.get('max_drawdown', 0.0),
                            brier_score=strategy_result.get('brier_score', 0.0),
                            total_trades=strategy_result.get('total_trades', 0),
                            profitable_trades=strategy_result.get('profitable_trades', 0),
                            cost_per_trade=strategy_result.get('cost_per_trade', 0.0),
                            research_calls=strategy_result.get('research_calls', 0)
                        )
                        
                        self.performance_tracker.record_strategy_result(strategy_name, perf_result)
                    
                    logger.info(f"{strategy_name}: {result.get('strategy_result', {}).get('total_trades', 0)} trades")
                    
                except Exception as e:
                    logger.error(f"Error executing {strategy_name} strategy: {e}")
                    continue
        
        # Generate final results
        final_results = self._generate_final_results()
        
        # Save results to file
        self._save_results(final_results)
        
        logger.info("Strategy comparison test completed!")
        return final_results
    
    def _generate_final_results(self) -> Dict[str, Dict]:
        """Generate final performance results for all strategies"""
        results = {}
        
        for strategy_name in self.strategies.keys():
            # Get performance summary
            summary = self.performance_tracker.get_strategy_summary(strategy_name)
            
            if summary:
                results[strategy_name] = {
                    'performance_metrics': summary,
                    'daily_results': self.test_results[strategy_name],
                    'total_days': len(self.test_results[strategy_name]),
                    'successful_days': len([r for r in self.test_results[strategy_name] if r.get('success', False)])
                }
            else:
                results[strategy_name] = {
                    'performance_metrics': None,
                    'daily_results': self.test_results[strategy_name],
                    'total_days': len(self.test_results[strategy_name]),
                    'successful_days': 0
                }
        
        return results
    
    def _save_results(self, results: Dict[str, Dict]):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"strategy_test_results_{timestamp}.json"
        
        # Convert results to serializable format
        serializable_results = {}
        for strategy_name, strategy_results in results.items():
            serializable_results[strategy_name] = {
                'performance_metrics': strategy_results['performance_metrics'].__dict__ if strategy_results['performance_metrics'] else None,
                'daily_results': strategy_results['daily_results'],
                'total_days': strategy_results['total_days'],
                'successful_days': strategy_results['successful_days']
            }
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {results_file}")
    
    def get_best_strategy(self, metric: str = 'sharpe_ratio') -> Optional[str]:
        """Get the best performing strategy by metric"""
        return self.performance_tracker.get_best_strategy(metric)
    
    def generate_comparison_report(self) -> str:
        """Generate comprehensive comparison report"""
        report = []
        report.append("=" * 80)
        report.append("STRATEGY COMPARISON TEST RESULTS")
        report.append("=" * 80)
        report.append(f"Test Duration: {self.test_duration_days} days")
        report.append(f"Total Capital: €{self.initial_capital:.2f}")
        report.append(f"Capital per Strategy: €{self.initial_capital/3:.2f}")
        report.append(f"Test Date: {date.today()}")
        report.append("")
        
        # Get performance comparison
        comparison = self.performance_tracker.compare_strategies()
        
        if not comparison:
            report.append("No performance data available.")
            return "\n".join(report)
        
        # Sort strategies by Sharpe ratio
        sorted_strategies = sorted(
            comparison.items(),
            key=lambda x: x[1].sharpe_ratio,
            reverse=True
        )
        
        # Display results for each strategy
        for i, (strategy_name, metrics) in enumerate(sorted_strategies, 1):
            report.append(f"{i}. {strategy_name.upper()} STRATEGY:")
            report.append("-" * 50)
            report.append(f"Total Return:        {metrics.total_return:>8.2%}")
            report.append(f"Annualized Return:  {metrics.annualized_return:>8.2%}")
            report.append(f"Sharpe Ratio:       {metrics.sharpe_ratio:>8.2f}")
            report.append(f"Win Rate:           {metrics.win_rate:>8.2%}")
            report.append(f"Max Drawdown:       {metrics.max_drawdown:>8.2%}")
            report.append(f"Brier Score:        {metrics.brier_score:>8.4f}")
            report.append(f"Calmar Ratio:       {metrics.calmar_ratio:>8.2f}")
            report.append(f"Total Trades:       {metrics.total_trades:>8d}")
            report.append(f"Profitable Trades:  {metrics.profitable_trades:>8d}")
            report.append(f"Research Calls:     {metrics.research_calls:>8d}")
            report.append(f"Total Research Cost: €{metrics.total_research_cost:>7.2f}")
            report.append(f"Cost Efficiency:    {metrics.cost_efficiency:>8.2f}")
            report.append("")
        
        # Recommendations
        best_sharpe = self.get_best_strategy('sharpe_ratio')
        best_return = self.get_best_strategy('total_return')
        best_efficiency = self.get_best_strategy('cost_efficiency')
        
        report.append("RECOMMENDATIONS:")
        report.append("-" * 50)
        if best_sharpe:
            report.append(f"Best Risk-Adjusted Returns: {best_sharpe.upper()}")
        if best_return:
            report.append(f"Highest Total Returns: {best_return.upper()}")
        if best_efficiency:
            report.append(f"Most Cost-Efficient: {best_efficiency.upper()}")
        
        # Overall recommendation
        if best_sharpe:
            report.append("")
            report.append(f"OVERALL RECOMMENDATION: {best_sharpe.upper()}")
            report.append("(Based on Sharpe ratio - risk-adjusted returns)")
        
        # Cost analysis
        report.append("")
        report.append("COST ANALYSIS:")
        report.append("-" * 50)
        total_cost = sum(metrics.total_research_cost for metrics in comparison.values())
        report.append(f"Total Research Cost: €{total_cost:.2f}")
        report.append(f"Average Cost per Strategy: €{total_cost/len(comparison):.2f}")
        report.append(f"Cost per Day: €{total_cost/self.test_duration_days:.2f}")
        
        return "\n".join(report)
    
    def print_daily_summary(self, day: int, results: Dict[str, Dict]):
        """Print daily summary of results"""
        print(f"\n--- Day {day + 1} Summary ---")
        
        for strategy_name, result in results.items():
            trades = result.get('strategy_result', {}).get('total_trades', 0)
            return_pct = result.get('strategy_result', {}).get('total_return', 0.0) * 100
            print(f"{strategy_name.capitalize()}: {trades} trades, {return_pct:+.2f}% return")
    
    def run_single_strategy_test(self, strategy_name: str, days: int = 1) -> Dict:
        """Run a single strategy for testing purposes"""
        if strategy_name not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        trader = self.strategies[strategy_name]
        results = []
        
        for day in range(days):
            current_date = date.today() + timedelta(days=day)
            result = trader.execute_portfolio_strategy(current_date)
            results.append(result)
        
        return {
            'strategy': strategy_name,
            'days_tested': days,
            'results': results
        }
