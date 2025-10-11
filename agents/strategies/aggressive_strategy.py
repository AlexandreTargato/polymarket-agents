from typing import List, Dict
from datetime import date
import logging

from .strategy_base import BaseStrategy, StrategyConfig, MarketOpportunity

logger = logging.getLogger(__name__)

class AggressiveStrategy(BaseStrategy):
    """
    Aggressive trading strategy focused on maximum returns.
    
    Characteristics:
    - Lower confidence threshold (>4/10)
    - Larger position sizes (max 30%)
    - Lower diversification (1-3 markets per event)
    - Small reserve capital (10%)
    - Kelly safety factor: 0.75
    """
    
    def __init__(self, capital: float):
        config = StrategyConfig(
            name='aggressive',
            capital=capital,
            min_confidence=4,
            max_events=10,  # Research 10 events per week
            max_markets=25,  # Up to 25 markets total
            reserve_capital=0.10,  # Keep only 10% unallocated
            kelly_safety_factor=0.75,  # Aggressive Kelly
            max_position_size=0.30,  # Max 30% per position
            max_total_allocation=0.90  # Max 90% total allocation
        )
        super().__init__(config)
        
        logger.info(f"Initialized Aggressive strategy with €{capital:.2f}")
    
    def analyze_markets(self, events: List[Dict], markets: List[Dict]) -> List[MarketOpportunity]:
        """
        Aggressive market analysis with lower requirements.
        
        Focus on:
        - Lower-confidence opportunities (but still profitable)
        - Any liquid markets
        - Small information edges (>3%)
        - Maximum market coverage
        """
        opportunities = []
        
        # Filter events by volume (lower threshold than balanced)
        low_volume_events = [
            event for event in events 
            if event.get('volume', 0) > 25000  # $25k+ volume
        ]
        
        logger.info(f"Aggressive: Analyzing {len(low_volume_events)} low-volume events")
        
        # Research top events (limited by max_events)
        events_to_research = low_volume_events[:self.config.max_events]
        
        for event in events_to_research:
            try:
                # Get markets for this event
                event_markets = [
                    market for market in markets 
                    if market.get('event_id') == event.get('id')
                ]
                
                if not event_markets:
                    continue
                
                # Research the event
                research_result = self.research_agent.research_event(
                    event_data=event,
                    markets_data=event_markets,
                    target_date=date.today()
                )
                
                self.research_calls_made += 1
                self.total_research_cost += 0.17  # €0.17 per Perplexity call
                
                # Convert research results to opportunities
                for decision in research_result.market_decisions:
                    # Apply aggressive filters (lower thresholds)
                    if decision.confidence < self.config.min_confidence:
                        continue
                    
                    # Calculate edge
                    market = next((m for m in event_markets if m['id'] == decision.market_id), None)
                    if not market:
                        continue
                    
                    current_price = market.get('current_price', 0.5)
                    edge = decision.estimated_probability - current_price
                    
                    # Consider small edges (>3%)
                    if abs(edge) < 0.03:
                        continue
                    
                    # Check liquidity (lower threshold)
                    liquidity_score = min(1.0, market.get('volume', 0) / 250000)  # Normalize to $250k
                    
                    opportunity = MarketOpportunity(
                        market_id=decision.market_id,
                        market_question=market.get('question', 'Unknown'),
                        current_price=current_price,
                        estimated_probability=decision.estimated_probability,
                        confidence=decision.confidence,
                        edge=edge,
                        volatility=market.get('volatility', 0.20),
                        liquidity_score=liquidity_score
                    )
                    
                    opportunities.append(opportunity)
                
            except Exception as e:
                logger.error(f"Error analyzing event {event.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Aggressive: Found {len(opportunities)} opportunities")
        return opportunities
    
    def generate_trades(self, opportunities: List[MarketOpportunity]) -> Dict[str, float]:
        """
        Generate aggressive trades with larger position sizes.
        
        Strategy:
        - Use aggressive Kelly factor (0.75)
        - Limit to max_markets positions
        - Concentrate on highest-value opportunities
        """
        if not opportunities:
            return {}
        
        # Sort by expected value (confidence * edge * liquidity)
        sorted_opportunities = sorted(
            opportunities,
            key=lambda x: x.confidence * abs(x.edge) * x.liquidity_score,
            reverse=True
        )
        
        # Limit to max_markets
        selected_opportunities = sorted_opportunities[:self.config.max_markets]
        
        # Use portfolio allocator with aggressive settings
        allocation_result = self.portfolio_allocator.allocate_capital(selected_opportunities)
        
        logger.info(f"Aggressive: Generated {len(allocation_result.allocations)} trades")
        logger.info(f"Aggressive: Total allocated: €{sum(abs(a) for a in allocation_result.allocations.values()):.2f}")
        logger.info(f"Aggressive: Unallocated: €{allocation_result.unallocated_capital:.2f}")
        
        return allocation_result.allocations
    
    def get_strategy_description(self) -> str:
        """Get human-readable strategy description"""
        return f"""
Aggressive Strategy (€{self.config.capital:.2f}):
- Confidence threshold: {self.config.min_confidence}/10
- Max events per week: {self.config.max_events}
- Max markets: {self.config.max_markets}
- Reserve capital: {self.config.reserve_capital:.0%}
- Max position size: {self.config.max_position_size:.0%}
- Kelly safety factor: {self.config.kelly_safety_factor:.2f}

Focus: Maximum returns with higher risk tolerance
Target: Sharpe ratio > 2.0, max drawdown < 20%
"""
