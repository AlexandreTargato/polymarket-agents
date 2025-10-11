from typing import List, Dict
from datetime import date
import logging

from .strategy_base import BaseStrategy, StrategyConfig, MarketOpportunity

logger = logging.getLogger(__name__)

class ConservativeStrategy(BaseStrategy):
    """
    Conservative trading strategy focused on risk minimization.
    
    Characteristics:
    - High confidence threshold (>7/10)
    - Small position sizes (max 15%)
    - High diversification (5+ markets)
    - Large reserve capital (30%)
    - Kelly safety factor: 0.25
    """
    
    def __init__(self, capital: float):
        config = StrategyConfig(
            name='conservative',
            capital=capital,
            min_confidence=7,
            max_events=7,  # Research 7 events per week
            max_markets=15,  # Up to 15 markets total
            reserve_capital=0.30,  # Keep 30% unallocated
            kelly_safety_factor=0.25,  # Very conservative Kelly
            max_position_size=0.15,  # Max 15% per position
            max_total_allocation=0.70  # Max 70% total allocation
        )
        super().__init__(config)
        
        logger.info(f"Initialized Conservative strategy with €{capital:.2f}")
    
    def analyze_markets(self, events: List[Dict], markets: List[Dict]) -> List[MarketOpportunity]:
        """
        Conservative market analysis with high confidence requirements.
        
        Focus on:
        - High-confidence opportunities only
        - Well-established markets with good liquidity
        - Clear information edges (>10%)
        """
        opportunities = []
        
        # Filter events by volume and liquidity
        high_volume_events = [
            event for event in events 
            if event.get('volume', 0) > 100000  # $100k+ volume
        ]
        
        logger.info(f"Conservative: Analyzing {len(high_volume_events)} high-volume events")
        
        # Research top events (limited by max_events)
        events_to_research = high_volume_events[:self.config.max_events]
        
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
                    # Apply conservative filters
                    if decision.confidence < self.config.min_confidence:
                        continue
                    
                    # Calculate edge
                    market = next((m for m in event_markets if m['id'] == decision.market_id), None)
                    if not market:
                        continue
                    
                    current_price = market.get('current_price', 0.5)
                    edge = decision.estimated_probability - current_price
                    
                    # Only consider significant edges (>10%)
                    if abs(edge) < 0.10:
                        continue
                    
                    # Check liquidity
                    liquidity_score = min(1.0, market.get('volume', 0) / 1000000)  # Normalize to $1M
                    
                    opportunity = MarketOpportunity(
                        market_id=decision.market_id,
                        market_question=market.get('question', 'Unknown'),
                        current_price=current_price,
                        estimated_probability=decision.estimated_probability,
                        confidence=decision.confidence,
                        edge=edge,
                        volatility=market.get('volatility', 0.1),
                        liquidity_score=liquidity_score
                    )
                    
                    opportunities.append(opportunity)
                
            except Exception as e:
                logger.error(f"Error analyzing event {event.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Conservative: Found {len(opportunities)} opportunities")
        return opportunities
    
    def generate_trades(self, opportunities: List[MarketOpportunity]) -> Dict[str, float]:
        """
        Generate conservative trades with small position sizes.
        
        Strategy:
        - Use very conservative Kelly factor (0.25)
        - Limit to max_markets positions
        - Ensure high diversification
        """
        if not opportunities:
            return {}
        
        # Sort by confidence and edge
        sorted_opportunities = sorted(
            opportunities,
            key=lambda x: (x.confidence, abs(x.edge)),
            reverse=True
        )
        
        # Limit to max_markets
        selected_opportunities = sorted_opportunities[:self.config.max_markets]
        
        # Use portfolio allocator with conservative settings
        allocation_result = self.portfolio_allocator.allocate_capital(selected_opportunities)
        
        logger.info(f"Conservative: Generated {len(allocation_result.allocations)} trades")
        logger.info(f"Conservative: Total allocated: €{sum(abs(a) for a in allocation_result.allocations.values()):.2f}")
        logger.info(f"Conservative: Unallocated: €{allocation_result.unallocated_capital:.2f}")
        
        return allocation_result.allocations
    
    def get_strategy_description(self) -> str:
        """Get human-readable strategy description"""
        return f"""
Conservative Strategy (€{self.config.capital:.2f}):
- Confidence threshold: {self.config.min_confidence}/10
- Max events per week: {self.config.max_events}
- Max markets: {self.config.max_markets}
- Reserve capital: {self.config.reserve_capital:.0%}
- Max position size: {self.config.max_position_size:.0%}
- Kelly safety factor: {self.config.kelly_safety_factor:.2f}

Focus: Capital preservation with steady, low-risk returns
Target: Sharpe ratio > 1.0, max drawdown < 10%
"""
