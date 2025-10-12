"""
Performance tracking and evaluation for trading strategies.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)

@dataclass
class StrategyResult:
    """Result of a trading strategy execution"""
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
    Track and evaluate trading strategy performance.
    """
    
    def __init__(self):
        self.strategy_results: List[StrategyResult] = []
        self.trade_history: List[Dict] = []
    
    def add_strategy_result(self, result: StrategyResult):
        """Add a strategy result to tracking"""
        self.strategy_results.append(result)
        logger.info(f"Added result for {result.strategy_name}: {result.total_return:.2%} return")
    
    def get_performance_summary(self) -> Dict[str, any]:
        """Get summary of all strategy performance"""
        if not self.strategy_results:
            return {"message": "No strategy results available"}
        
        # Calculate aggregate metrics
        total_trades = sum(r.total_trades for r in self.strategy_results)
        total_profitable = sum(r.profitable_trades for r in self.strategy_results)
        avg_return = sum(r.total_return for r in self.strategy_results) / len(self.strategy_results)
        avg_sharpe = sum(r.sharpe_ratio for r in self.strategy_results) / len(self.strategy_results)
        
        return {
            "total_strategies": len(self.strategy_results),
            "total_trades": total_trades,
            "total_profitable_trades": total_profitable,
            "overall_win_rate": total_profitable / total_trades if total_trades > 0 else 0.0,
            "average_return": avg_return,
            "average_sharpe_ratio": avg_sharpe,
            "best_strategy": max(self.strategy_results, key=lambda r: r.sharpe_ratio).strategy_name,
            "worst_strategy": min(self.strategy_results, key=lambda r: r.sharpe_ratio).strategy_name
        }
    
    def get_strategy_comparison(self) -> List[Dict[str, any]]:
        """Get detailed comparison of all strategies"""
        return [
            {
                "name": r.strategy_name,
                "return": r.total_return,
                "sharpe_ratio": r.sharpe_ratio,
                "win_rate": r.win_rate,
                "max_drawdown": r.max_drawdown,
                "total_trades": r.total_trades,
                "cost_per_trade": r.cost_per_trade
            }
            for r in self.strategy_results
        ]
