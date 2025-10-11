import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for strategy evaluation"""
    strategy_name: str
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    win_rate: float
    max_drawdown: float
    current_drawdown: float
    brier_score: float
    calmar_ratio: float
    sortino_ratio: float
    total_trades: int
    profitable_trades: int
    avg_trade_return: float
    cost_per_trade: float
    research_calls: int
    total_research_cost: float
    cost_efficiency: float  # Return per euro spent on research

@dataclass
class StrategyResult:
    """Result of strategy execution"""
    strategy_name: str
    total_return: float
    sharpe_ratio: float
    win_rate: float
    max_drawdown: float
    brier_score: float
    total_trades: int
    profitable_trades: int
    cost_per_trade: float
    research_calls: int

class PerformanceTracker:
    """
    Performance tracking system for strategy evaluation.
    
    Features:
    - Sharpe ratio calculation (primary metric)
    - Win rate and drawdown tracking
    - Brier score for calibration
    - Cost per trade analysis
    - Comprehensive performance comparison
    """
    
    def __init__(self):
        self.strategy_results: Dict[str, List[StrategyResult]] = {}
        self.performance_history: Dict[str, List[PerformanceMetrics]] = {}
        
    def record_strategy_result(self, strategy_name: str, result: StrategyResult):
        """Record a strategy execution result"""
        if strategy_name not in self.strategy_results:
            self.strategy_results[strategy_name] = []
        
        self.strategy_results[strategy_name].append(result)
        
        # Calculate and store performance metrics
        metrics = self._calculate_performance_metrics(strategy_name, result)
        
        if strategy_name not in self.performance_history:
            self.performance_history[strategy_name] = []
        
        self.performance_history[strategy_name].append(metrics)
        
        logger.info(f"Recorded result for {strategy_name}: Sharpe={metrics.sharpe_ratio:.3f}, Return={metrics.total_return:.3f}")
    
    def _calculate_performance_metrics(self, strategy_name: str, result: StrategyResult) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        
        # Basic metrics from result
        total_return = result.total_return
        sharpe_ratio = result.sharpe_ratio
        win_rate = result.win_rate
        max_drawdown = result.max_drawdown
        brier_score = result.brier_score
        
        # Calculate additional metrics
        annualized_return = total_return * 52  # Assuming weekly results
        
        # Calmar ratio (annualized return / max drawdown)
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0.0
        
        # Sortino ratio (simplified - would need downside deviation)
        sortino_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0.0
        
        # Trade metrics
        avg_trade_return = total_return / max(1, result.total_trades)
        
        # Cost metrics
        total_research_cost = result.research_calls * 0.17  # €0.17 per Perplexity call
        cost_efficiency = total_return / max(0.01, total_research_cost)  # Return per euro spent
        
        return PerformanceMetrics(
            strategy_name=strategy_name,
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            current_drawdown=0.0,  # Would track current drawdown
            brier_score=brier_score,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            total_trades=result.total_trades,
            profitable_trades=result.profitable_trades,
            avg_trade_return=avg_trade_return,
            cost_per_trade=result.cost_per_trade,
            research_calls=result.research_calls,
            total_research_cost=total_research_cost,
            cost_efficiency=cost_efficiency
        )
    
    def get_strategy_summary(self, strategy_name: str) -> Optional[PerformanceMetrics]:
        """Get latest performance summary for a strategy"""
        if strategy_name not in self.performance_history:
            return None
        
        history = self.performance_history[strategy_name]
        if not history:
            return None
        
        return history[-1]  # Return latest metrics
    
    def compare_strategies(self) -> Dict[str, PerformanceMetrics]:
        """Compare all strategies and return latest metrics"""
        comparison = {}
        
        for strategy_name in self.performance_history:
            summary = self.get_strategy_summary(strategy_name)
            if summary:
                comparison[strategy_name] = summary
        
        return comparison
    
    def get_best_strategy(self, metric: str = 'sharpe_ratio') -> Optional[str]:
        """
        Get the best performing strategy by metric.
        
        Args:
            metric: Metric to optimize ('sharpe_ratio', 'total_return', 'win_rate', etc.)
        """
        comparison = self.compare_strategies()
        
        if not comparison:
            return None
        
        # Find strategy with best metric
        best_strategy = None
        best_value = float('-inf')
        
        for strategy_name, metrics in comparison.items():
            value = getattr(metrics, metric, 0.0)
            if value > best_value:
                best_value = value
                best_strategy = strategy_name
        
        return best_strategy
    
    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        comparison = self.compare_strategies()
        
        if not comparison:
            return "No performance data available."
        
        report = []
        report.append("=" * 80)
        report.append("STRATEGY PERFORMANCE COMPARISON")
        report.append("=" * 80)
        
        # Sort strategies by Sharpe ratio
        sorted_strategies = sorted(
            comparison.items(),
            key=lambda x: x[1].sharpe_ratio,
            reverse=True
        )
        
        for strategy_name, metrics in sorted_strategies:
            report.append(f"\n{strategy_name.upper()} STRATEGY:")
            report.append("-" * 40)
            report.append(f"Total Return:        {metrics.total_return:>8.2%}")
            report.append(f"Annualized Return:  {metrics.annualized_return:>8.2%}")
            report.append(f"Sharpe Ratio:       {metrics.sharpe_ratio:>8.2f}")
            report.append(f"Win Rate:           {metrics.win_rate:>8.2%}")
            report.append(f"Max Drawdown:       {metrics.max_drawdown:>8.2%}")
            report.append(f"Brier Score:        {metrics.brier_score:>8.4f}")
            report.append(f"Calmar Ratio:       {metrics.calmar_ratio:>8.2f}")
            report.append(f"Total Trades:       {metrics.total_trades:>8d}")
            report.append(f"Profitable Trades:  {metrics.profitable_trades:>8d}")
            report.append(f"Avg Trade Return:   {metrics.avg_trade_return:>8.2%}")
            report.append(f"Research Calls:     {metrics.research_calls:>8d}")
            report.append(f"Total Research Cost: €{metrics.total_research_cost:>7.2f}")
            report.append(f"Cost Efficiency:    {metrics.cost_efficiency:>8.2f}")
        
        # Recommendations
        best_sharpe = self.get_best_strategy('sharpe_ratio')
        best_return = self.get_best_strategy('total_return')
        best_efficiency = self.get_best_strategy('cost_efficiency')
        
        report.append("\n" + "=" * 80)
        report.append("RECOMMENDATIONS")
        report.append("=" * 80)
        
        if best_sharpe:
            report.append(f"Best Risk-Adjusted Returns: {best_sharpe.upper()}")
        if best_return:
            report.append(f"Highest Total Returns: {best_return.upper()}")
        if best_efficiency:
            report.append(f"Most Cost-Efficient: {best_efficiency.upper()}")
        
        # Overall recommendation
        if best_sharpe:
            report.append(f"\nOVERALL RECOMMENDATION: {best_sharpe.upper()}")
            report.append("(Based on Sharpe ratio - risk-adjusted returns)")
        
        return "\n".join(report)
    
    def get_performance_trends(self, strategy_name: str, days: int = 7) -> Dict[str, List[float]]:
        """Get performance trends over time"""
        if strategy_name not in self.performance_history:
            return {}
        
        history = self.performance_history[strategy_name]
        recent_history = history[-days:] if len(history) >= days else history
        
        trends = {
            'returns': [m.total_return for m in recent_history],
            'sharpe_ratios': [m.sharpe_ratio for m in recent_history],
            'win_rates': [m.win_rate for m in recent_history],
            'drawdowns': [m.max_drawdown for m in recent_history],
            'cost_efficiency': [m.cost_efficiency for m in recent_history]
        }
        
        return trends
