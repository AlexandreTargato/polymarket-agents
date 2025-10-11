import os
import yaml
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime
import logging

from agents.polymarket.polymarket import Polymarket
from agents.polymarket.gamma import GammaMarketClient
from agents.research.perplexity_research import PerplexityResearchAgent
from agents.portfolio.allocator import PortfolioAllocator, MarketOpportunity
from agents.portfolio.risk_manager import RiskManager
from agents.strategies import ConservativeStrategy, BalancedStrategy, AggressiveStrategy
from agents.evaluation.performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

class EnhancedTrader:
    """
    Enhanced trading system with portfolio-based allocation and multi-strategy support.
    
    Features:
    - Event-level research using Perplexity Sonar Deep Research
    - Multi-market portfolio allocation
    - Risk management and position limits
    - Strategy comparison and selection
    - Performance tracking and reporting
    """
    
    def __init__(self, strategy_type: str = 'balanced', capital: float = None):
        self.strategy_type = strategy_type
        self.capital = capital or float(os.getenv('INITIAL_CAPITAL', 50.0))
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize core components
        self.polymarket = Polymarket()
        self.gamma = GammaMarketClient()
        self.research_agent = PerplexityResearchAgent()
        
        # Initialize strategy
        self.strategy = self._initialize_strategy(strategy_type, self.capital)
        
        # Initialize performance tracking
        self.performance_tracker = PerformanceTracker()
        
        logger.info(f"Initialized EnhancedTrader with {strategy_type} strategy (€{self.capital:.2f})")
    
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
            'research': {
                'model': 'sonar-deep-research',
                'parser_model': 'gpt-4o-mini',
                'cache_hours': 24,
                'min_event_volume': 25000
            },
            'risk_management': {
                'max_position_size': 0.30,
                'max_total_allocation': 0.90,
                'max_drawdown_threshold': 0.20
            }
        }
    
    def _initialize_strategy(self, strategy_type: str, capital: float):
        """Initialize the specified strategy"""
        if strategy_type == 'conservative':
            return ConservativeStrategy(capital)
        elif strategy_type == 'balanced':
            return BalancedStrategy(capital)
        elif strategy_type == 'aggressive':
            return AggressiveStrategy(capital)
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    def execute_portfolio_strategy(self, target_date: date = None) -> Dict:
        """
        Execute the complete portfolio-based trading strategy.
        
        Args:
            target_date: Date for analysis (defaults to today)
            
        Returns:
            Dict with execution results and performance metrics
        """
        if target_date is None:
            target_date = date.today()
        
        logger.info(f"Executing {self.strategy_type} portfolio strategy for {target_date}")
        
        try:
            # Step 1: Get tradeable events
            events = self._get_tradeable_events()
            logger.info(f"Found {len(events)} tradeable events")
            
            if not events:
                logger.warning("No tradeable events found")
                return self._create_empty_result()
            
            # Step 2: Get markets for events
            markets = self._get_markets_for_events(events)
            logger.info(f"Found {len(markets)} markets across all events")
            
            if not markets:
                logger.warning("No markets found for events")
                return self._create_empty_result()
            
            # Step 3: Execute strategy
            strategy_result = self.strategy.execute_strategy(events, markets, target_date)
            
            # Step 4: Record performance
            self.performance_tracker.record_strategy_result(self.strategy_type, strategy_result)
            
            # Step 5: Generate execution report
            execution_report = self._generate_execution_report(strategy_result, events, markets)
            
            logger.info(f"Strategy execution completed: {strategy_result.total_trades} trades")
            
            return execution_report
            
        except Exception as e:
            logger.error(f"Error executing portfolio strategy: {e}")
            return self._create_error_result(str(e))
    
    def _get_tradeable_events(self) -> List[Dict]:
        """Get tradeable events from Polymarket"""
        try:
            # Use existing Polymarket client to get events
            events = self.polymarket.get_all_tradeable_events()
            
            # Convert to dict format for compatibility
            event_dicts = []
            for event in events:
                if hasattr(event, 'json'):
                    event_data = event.json()
                else:
                    event_data = str(event)
                
                # Parse event data (simplified)
                event_dict = {
                    'id': getattr(event, 'id', 'unknown'),
                    'title': getattr(event, 'title', 'Unknown Event'),
                    'description': getattr(event, 'description', 'No description'),
                    'volume': getattr(event, 'volume', 0),
                    'markets': getattr(event, 'markets', [])
                }
                event_dicts.append(event_dict)
            
            # Filter by volume threshold
            min_volume = self.config.get('research', {}).get('min_event_volume', 25000)
            filtered_events = [
                event for event in event_dicts 
                if event.get('volume', 0) >= min_volume
            ]
            
            return filtered_events
            
        except Exception as e:
            logger.error(f"Error getting tradeable events: {e}")
            return []
    
    def _get_markets_for_events(self, events: List[Dict]) -> List[Dict]:
        """Get markets for the given events"""
        markets = []
        
        for event in events:
            try:
                # Get markets for this event
                event_markets = self.gamma.get_current_markets(limit=10)
                
                for market in event_markets:
                    market_dict = {
                        'id': str(market.id),
                        'event_id': event['id'],
                        'question': market.question,
                        'description': market.description,
                        'current_price': market.current_price,
                        'outcomes': market.outcomes,
                        'volume': market.volume,
                        'volatility': 0.1  # Default volatility
                    }
                    markets.append(market_dict)
                    
            except Exception as e:
                logger.error(f"Error getting markets for event {event.get('id', 'unknown')}: {e}")
                continue
        
        return markets
    
    def _generate_execution_report(self, strategy_result, events: List[Dict], markets: List[Dict]) -> Dict:
        """Generate comprehensive execution report"""
        return {
            'execution_timestamp': datetime.now().isoformat(),
            'strategy_type': self.strategy_type,
            'capital': self.capital,
            'events_analyzed': len(events),
            'markets_analyzed': len(markets),
            'strategy_result': {
                'total_return': strategy_result.total_return,
                'sharpe_ratio': strategy_result.sharpe_ratio,
                'win_rate': strategy_result.win_rate,
                'max_drawdown': strategy_result.max_drawdown,
                'brier_score': strategy_result.brier_score,
                'total_trades': strategy_result.total_trades,
                'profitable_trades': strategy_result.profitable_trades,
                'research_calls': strategy_result.research_calls,
                'cost_per_trade': strategy_result.cost_per_trade
            },
            'performance_summary': self.performance_tracker.get_strategy_summary(self.strategy_type),
            'success': True
        }
    
    def _create_empty_result(self) -> Dict:
        """Create empty result when no trades are made"""
        return {
            'execution_timestamp': datetime.now().isoformat(),
            'strategy_type': self.strategy_type,
            'capital': self.capital,
            'events_analyzed': 0,
            'markets_analyzed': 0,
            'strategy_result': {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'max_drawdown': 0.0,
                'brier_score': 0.0,
                'total_trades': 0,
                'profitable_trades': 0,
                'research_calls': 0,
                'cost_per_trade': 0.0
            },
            'success': True,
            'message': 'No opportunities found'
        }
    
    def _create_error_result(self, error_message: str) -> Dict:
        """Create error result"""
        return {
            'execution_timestamp': datetime.now().isoformat(),
            'strategy_type': self.strategy_type,
            'capital': self.capital,
            'error': error_message,
            'success': False
        }
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary for the current strategy"""
        summary = self.performance_tracker.get_strategy_summary(self.strategy_type)
        if summary:
            return summary
        else:
            return {
                'strategy_name': self.strategy_type,
                'total_trades': 0,
                'research_calls': 0,
                'total_cost': 0.0
            }
    
    def get_strategy_comparison(self) -> str:
        """Get strategy comparison report"""
        return self.performance_tracker.generate_performance_report()
    
    def switch_strategy(self, new_strategy_type: str) -> bool:
        """Switch to a different strategy"""
        if new_strategy_type not in ['conservative', 'balanced', 'aggressive']:
            logger.error(f"Invalid strategy type: {new_strategy_type}")
            return False
        
        try:
            self.strategy_type = new_strategy_type
            self.strategy = self._initialize_strategy(new_strategy_type, self.capital)
            logger.info(f"Switched to {new_strategy_type} strategy")
            return True
        except Exception as e:
            logger.error(f"Error switching strategy: {e}")
            return False
    
    def get_strategy_description(self) -> str:
        """Get human-readable strategy description"""
        return self.strategy.get_strategy_description()
