from typing import List, Dict
from datetime import date
import logging

from .strategy_base import BaseStrategy, StrategyConfig, MarketOpportunity

logger = logging.getLogger(__name__)

class BalancedStrategy(BaseStrategy):
    """
    Balanced trading strategy focused on risk-adjusted returns.
    
    Characteristics:
    - Moderate confidence threshold (>5/10)
    - Medium position sizes (max 20%)
    - Moderate diversification (3-5 markets per event)
    - Moderate reserve capital (20%)
    - Kelly safety factor: 0.50
    """
    
    def __init__(self, capital: float):
        config = StrategyConfig(
            name='balanced',
            capital=capital,
            min_confidence=5,
            max_events=10,  # Research 10 events per week
            max_markets=25,  # Up to 25 markets total
            reserve_capital=0.20,  # Keep 20% unallocated
            kelly_safety_factor=0.50,  # Moderate Kelly
            max_position_size=0.20,  # Max 20% per position
            max_total_allocation=0.80  # Max 80% total allocation
        )
        super().__init__(config)
        
        logger.info(f"Initialized Balanced strategy with €{capital:.2f}")
    
    def analyze_markets(self, events: List[Dict], markets: List[Dict]) -> List[MarketOpportunity]:
        """
        Balanced market analysis with moderate requirements.
        
        Focus on:
        - Moderate-confidence opportunities
        - Good liquidity markets
        - Clear information edges (>5%)
        - Diversified across event types
        """
        opportunities = []
        
        # Filter events by volume and liquidity (lower threshold than conservative)
        medium_volume_events = [
            event for event in events 
            if event.get('volume', 0) > 50000  # $50k+ volume
        ]
        
        logger.info(f"Balanced: Analyzing {len(medium_volume_events)} medium-volume events")
        
        # Research top events (limited by max_events)
        events_to_research = medium_volume_events[:self.config.max_events]
        
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
                    # Apply balanced filters
                    if decision.confidence < self.config.min_confidence:
                        continue
                    
                    # Calculate edge
                    market = next((m for m in event_markets if m['id'] == decision.market_id), None)
                    if not market:
                        continue
                    
                    current_price = market.get('current_price', 0.5)
                    edge = decision.estimated_probability - current_price
                    
                    # Consider moderate edges (>5%)
                    if abs(edge) < 0.05:
                        continue
                    
                    # Check liquidity
                    liquidity_score = min(1.0, market.get('volume', 0) / 500000)  # Normalize to $500k
                    
                    opportunity = MarketOpportunity(
                        market_id=decision.market_id,
                        market_question=market.get('question', 'Unknown'),
                        current_price=current_price,
                        estimated_probability=decision.estimated_probability,
                        confidence=decision.confidence,
                        edge=edge,
                        volatility=market.get('volatility', 0.15),
                        liquidity_score=liquidity_score
                    )
                    
                    opportunities.append(opportunity)
                
            except Exception as e:
                logger.error(f"Error analyzing event {event.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Balanced: Found {len(opportunities)} opportunities")
        return opportunities
    
    def generate_trades(self, opportunities: List[MarketOpportunity]) -> Dict[str, float]:
        """
        Generate balanced trades with moderate position sizes.
        
        Strategy:
        - Use moderate Kelly factor (0.50)
        - Limit to max_markets positions
        - Balance between diversification and concentration
        """
        if not opportunities:
            return {}
        
        # Sort by expected value (confidence * edge)
        sorted_opportunities = sorted(
            opportunities,
            key=lambda x: x.confidence * abs(x.edge),
            reverse=True
        )
        
        # Limit to max_markets
        selected_opportunities = sorted_opportunities[:self.config.max_markets]
        
        # Use portfolio allocator with balanced settings
        allocation_result = self.portfolio_allocator.allocate_capital(selected_opportunities)
        
        logger.info(f"Balanced: Generated {len(allocation_result.allocations)} trades")
        logger.info(f"Balanced: Total allocated: €{sum(abs(a) for a in allocation_result.allocations.values()):.2f}")
        logger.info(f"Balanced: Unallocated: €{allocation_result.unallocated_capital:.2f}")
        
        return allocation_result.allocations
    
    def get_strategy_description(self) -> str:
        """Get human-readable strategy description"""
        return f"""
Balanced Strategy (€{self.config.capital:.2f}):
- Confidence threshold: {self.config.min_confidence}/10
- Max events per week: {self.config.max_events}
- Max markets: {self.config.max_markets}
- Reserve capital: {self.config.reserve_capital:.0%}
- Max position size: {self.config.max_position_size:.0%}
- Kelly safety factor: {self.config.kelly_safety_factor:.2f}

Focus: Optimal risk-adjusted returns with moderate risk
Target: Sharpe ratio > 1.5, max drawdown < 15%
"""
