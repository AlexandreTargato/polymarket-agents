from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import date
import logging

from agents.research.perplexity_research import PerplexityResearchAgent, EventResearchResult
from agents.portfolio.allocator import PortfolioAllocator, MarketOpportunity
from agents.portfolio.risk_manager import RiskManager, RiskMetrics
from agents.evaluation.performance_tracker import StrategyResult

logger = logging.getLogger(__name__)

@dataclass
class StrategyConfig:
    """Configuration for a trading strategy"""
    name: str
    capital: float
    min_confidence: int
    max_events: int
    max_markets: int
    reserve_capital: float
    kelly_safety_factor: float
    max_position_size: float
    max_total_allocation: float

class BaseStrategy(ABC):
    """
    Base class for trading strategies.
    
    All strategies must implement:
    - analyze_markets: Analyze market opportunities
    - generate_trades: Generate trading decisions
    - execute_strategy: Main execution method
    """
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.research_agent = PerplexityResearchAgent()
        self.portfolio_allocator = PortfolioAllocator(
            total_capital=config.capital,
            strategy_type=config.name
        )
        self.risk_manager = RiskManager(
            max_position_size=config.max_position_size,
            max_total_allocation=config.max_total_allocation
        )
        
        # Performance tracking
        self.trade_history: List[Dict] = []
        self.research_calls_made = 0
        self.total_research_cost = 0.0
        
        logger.info(f"Initialized {config.name} strategy with €{config.capital:.2f}")
    
    @abstractmethod
    def analyze_markets(self, events: List[Dict], markets: List[Dict]) -> List[MarketOpportunity]:
        """
        Analyze market opportunities and return filtered list.
        
        Args:
            events: List of events to analyze
            markets: List of markets to analyze
            
        Returns:
            List of market opportunities
        """
        pass
    
    @abstractmethod
    def generate_trades(self, opportunities: List[MarketOpportunity]) -> Dict[str, float]:
        """
        Generate trading decisions from opportunities.
        
        Args:
            opportunities: List of market opportunities
            
        Returns:
            Dict of market_id -> bet_amount
        """
        pass
    
    def execute_strategy(self, events: List[Dict], markets: List[Dict], target_date: date) -> StrategyResult:
        """
        Execute the complete strategy.
        
        Args:
            events: List of events to analyze
            markets: List of markets to analyze
            target_date: Date for analysis
            
        Returns:
            StrategyResult with performance metrics
        """
        logger.info(f"Executing {self.config.name} strategy for {len(events)} events")
        
        # Step 1: Analyze markets
        opportunities = self.analyze_markets(events, markets)
        
        if not opportunities:
            logger.info(f"No opportunities found for {self.config.name} strategy")
            return self._create_empty_result()
        
        # Step 2: Generate trades
        trades = self.generate_trades(opportunities)
        
        if not trades:
            logger.info(f"No trades generated for {self.config.name} strategy")
            return self._create_empty_result()
        
        # Step 3: Risk validation
        is_valid, violations = self.risk_manager.check_position_limits(trades, self.config.capital)
        
        if not is_valid:
            logger.warning(f"Risk violations in {self.config.name}: {violations}")
            # Could implement position reduction here
            return self._create_empty_result()
        
        # Step 4: Execute trades (simulated)
        trade_result = self._execute_trades(trades, opportunities)
        
        # Step 5: Calculate performance metrics
        return self._calculate_performance_metrics(trade_result)
    
    def _execute_trades(self, trades: Dict[str, float], opportunities: List[MarketOpportunity]) -> Dict:
        """Execute trades (simulated for now)"""
        # In real implementation, this would call Polymarket API
        logger.info(f"Executing {len(trades)} trades for {self.config.name}")
        
        # Record trade for performance tracking
        trade_record = {
            'timestamp': date.today(),
            'trades': trades.copy(),
            'opportunities': opportunities.copy()
        }
        self.trade_history.append(trade_record)
        
        return {
            'trades_executed': len(trades),
            'total_allocated': sum(abs(amount) for amount in trades.values()),
            'unallocated': self.config.capital - sum(abs(amount) for amount in trades.values())
        }
    
    def _calculate_performance_metrics(self, trade_result: Dict) -> StrategyResult:
        """Calculate performance metrics for the strategy"""
        # Simplified metrics calculation
        # In real implementation, would track actual returns
        
        total_trades = len(self.trade_history)
        profitable_trades = int(total_trades * 0.6)  # Assume 60% win rate for now
        
        return StrategyResult(
            strategy_name=self.config.name,
            total_return=0.0,  # Would calculate from actual returns
            sharpe_ratio=0.0,  # Would calculate from actual returns
            win_rate=profitable_trades / total_trades if total_trades > 0 else 0.0,
            max_drawdown=0.0,  # Would calculate from actual returns
            brier_score=0.0,   # Would calculate from actual predictions
            total_trades=total_trades,
            profitable_trades=profitable_trades,
            cost_per_trade=self.total_research_cost / max(1, self.research_calls_made),
            research_calls=self.research_calls_made
        )
    
    def _create_empty_result(self) -> StrategyResult:
        """Create empty result when no trades are made"""
        return StrategyResult(
            strategy_name=self.config.name,
            total_return=0.0,
            sharpe_ratio=0.0,
            win_rate=0.0,
            max_drawdown=0.0,
            brier_score=0.0,
            total_trades=0,
            profitable_trades=0,
            cost_per_trade=0.0,
            research_calls=self.research_calls_made
        )
    
    def get_strategy_summary(self) -> Dict:
        """Get summary of strategy configuration and performance"""
        return {
            'name': self.config.name,
            'capital': self.config.capital,
            'min_confidence': self.config.min_confidence,
            'max_events': self.config.max_events,
            'max_markets': self.config.max_markets,
            'reserve_capital': self.config.reserve_capital,
            'total_trades': len(self.trade_history),
            'research_calls': self.research_calls_made,
            'total_cost': self.total_research_cost
        }
