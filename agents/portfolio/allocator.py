import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

from agents.research.perplexity_research import MarketDecision

logger = logging.getLogger(__name__)

@dataclass
class MarketOpportunity:
    """Represents a trading opportunity with risk metrics"""
    market_id: str
    market_question: str
    current_price: float
    estimated_probability: float
    confidence: int
    edge: float  # estimated_probability - current_price
    volatility: float = 0.0
    liquidity_score: float = 1.0

@dataclass
class AllocationResult:
    """Result of portfolio allocation"""
    allocations: Dict[str, float]  # market_id -> bet_amount
    unallocated_capital: float
    total_expected_value: float
    portfolio_sharpe: float
    risk_metrics: Dict[str, float]

class PortfolioAllocator:
    """
    Portfolio allocator using Kelly Criterion with safety factors.
    
    Features:
    - Kelly Criterion position sizing
    - Multi-market allocation optimization
    - Event-level diversification
    - Strategy-specific safety factors (0.25-0.75)
    """
    
    def __init__(self, total_capital: float, strategy_type: str = 'balanced'):
        self.total_capital = total_capital
        self.strategy_type = strategy_type
        
        # Strategy-specific parameters
        self.strategy_config = {
            'conservative': {
                'kelly_safety_factor': 0.25,
                'max_position_size': 0.15,
                'max_total_allocation': 0.70,
                'min_edge_threshold': 0.10,
                'min_confidence': 7
            },
            'balanced': {
                'kelly_safety_factor': 0.50,
                'max_position_size': 0.20,
                'max_total_allocation': 0.80,
                'min_edge_threshold': 0.05,
                'min_confidence': 5
            },
            'aggressive': {
                'kelly_safety_factor': 0.75,
                'max_position_size': 0.30,
                'max_total_allocation': 0.90,
                'min_edge_threshold': 0.03,
                'min_confidence': 4
            }
        }
        
        self.config = self.strategy_config[strategy_type]
    
    def allocate_capital(self, opportunities: List[MarketOpportunity]) -> AllocationResult:
        """
        Allocate capital across market opportunities using Kelly Criterion.
        
        Args:
            opportunities: List of market opportunities
            
        Returns:
            AllocationResult with allocations and risk metrics
        """
        if not opportunities:
            return AllocationResult(
                allocations={},
                unallocated_capital=self.total_capital,
                total_expected_value=0.0,
                portfolio_sharpe=0.0,
                risk_metrics={}
            )
        
        # Filter opportunities by strategy criteria
        filtered_opportunities = self._filter_opportunities(opportunities)
        
        if not filtered_opportunities:
            logger.info("No opportunities meet strategy criteria")
            return AllocationResult(
                allocations={},
                unallocated_capital=self.total_capital,
                total_expected_value=0.0,
                portfolio_sharpe=0.0,
                risk_metrics={}
            )
        
        # Calculate Kelly-optimal positions
        kelly_positions = self._calculate_kelly_positions(filtered_opportunities)
        
        # Apply position limits and scaling
        final_allocations = self._apply_position_limits(kelly_positions)
        
        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(final_allocations, filtered_opportunities)
        
        return AllocationResult(
            allocations=final_allocations,
            unallocated_capital=self.total_capital - sum(abs(amount) for amount in final_allocations.values()),
            total_expected_value=portfolio_metrics['expected_value'],
            portfolio_sharpe=portfolio_metrics['sharpe_ratio'],
            risk_metrics=portfolio_metrics
        )
    
    def _filter_opportunities(self, opportunities: List[MarketOpportunity]) -> List[MarketOpportunity]:
        """Filter opportunities based on strategy criteria"""
        filtered = []
        
        for opp in opportunities:
            # Check minimum edge threshold
            if abs(opp.edge) < self.config['min_edge_threshold']:
                continue
            
            # Check minimum confidence
            if opp.confidence < self.config['min_confidence']:
                continue
            
            # Check liquidity (if available)
            if opp.liquidity_score < 0.5:  # Minimum liquidity threshold
                continue
            
            filtered.append(opp)
        
        logger.info(f"Filtered {len(opportunities)} opportunities to {len(filtered)}")
        return filtered
    
    def _calculate_kelly_positions(self, opportunities: List[MarketOpportunity]) -> Dict[str, float]:
        """Calculate Kelly-optimal position sizes"""
        kelly_positions = {}
        
        for opp in opportunities:
            # Kelly formula: f = (bp - q) / b
            # where b = odds, p = probability, q = 1-p
            
            if opp.current_price <= 0 or opp.current_price >= 1:
                continue
            
            # Calculate odds (decimal odds)
            odds = 1.0 / opp.current_price
            
            # Kelly fraction
            if opp.edge > 0:  # Betting for
                kelly_fraction = opp.edge / (odds - 1)
            else:  # Betting against
                kelly_fraction = abs(opp.edge) / (odds - 1)
            
            # Apply safety factor
            safe_kelly = kelly_fraction * self.config['kelly_safety_factor']
            
            # Convert to dollar amount
            position_size = safe_kelly * self.total_capital
            
            # Apply direction
            if opp.edge > 0:
                kelly_positions[opp.market_id] = position_size
            else:
                kelly_positions[opp.market_id] = -position_size
        
        return kelly_positions
    
    def _apply_position_limits(self, kelly_positions: Dict[str, float]) -> Dict[str, float]:
        """Apply position size limits and scaling"""
        final_allocations = {}
        
        # Apply individual position limits
        for market_id, position in kelly_positions.items():
            max_position_value = self.config['max_position_size'] * self.total_capital
            capped_position = max(-max_position_value, min(max_position_value, position))
            final_allocations[market_id] = capped_position
        
        # Check total allocation limit
        total_allocated = sum(abs(amount) for amount in final_allocations.values())
        max_total_allocation = self.config['max_total_allocation'] * self.total_capital
        
        if total_allocated > max_total_allocation:
            # Scale down all positions proportionally
            scale_factor = max_total_allocation / total_allocated
            for market_id in final_allocations:
                final_allocations[market_id] *= scale_factor
            
            logger.info(f"Scaled down allocations by factor {scale_factor:.3f}")
        
        return final_allocations
    
    def _calculate_portfolio_metrics(
        self, 
        allocations: Dict[str, float], 
        opportunities: List[MarketOpportunity]
    ) -> Dict[str, float]:
        """Calculate portfolio risk metrics"""
        
        if not allocations:
            return {
                'expected_value': 0.0,
                'variance': 0.0,
                'sharpe_ratio': 0.0,
                'max_position_weight': 0.0,
                'concentration_ratio': 0.0
            }
        
        # Create opportunity lookup
        opp_lookup = {opp.market_id: opp for opp in opportunities}
        
        # Calculate expected value
        expected_value = 0.0
        for market_id, bet_amount in allocations.items():
            if market_id in opp_lookup:
                opp = opp_lookup[market_id]
                if bet_amount > 0:  # Betting for
                    expected_payout = bet_amount * (1.0 / opp.current_price)
                    expected_value += opp.estimated_probability * expected_payout - bet_amount
                else:  # Betting against
                    expected_payout = abs(bet_amount) * (1.0 / (1.0 - opp.current_price))
                    expected_value += (1.0 - opp.estimated_probability) * expected_payout - abs(bet_amount)
        
        # Calculate variance (simplified)
        variance = 0.0
        for market_id, bet_amount in allocations.items():
            if market_id in opp_lookup:
                opp = opp_lookup[market_id]
                # Simplified variance calculation
                variance += (bet_amount * opp.volatility) ** 2
        
        # Calculate Sharpe ratio
        sharpe_ratio = expected_value / np.sqrt(variance) if variance > 0 else 0.0
        
        # Calculate concentration metrics
        position_weights = [abs(amount) / self.total_capital for amount in allocations.values()]
        max_position_weight = max(position_weights) if position_weights else 0.0
        
        # Herfindahl concentration ratio
        concentration_ratio = sum(w**2 for w in position_weights)
        
        return {
            'expected_value': expected_value,
            'variance': variance,
            'sharpe_ratio': sharpe_ratio,
            'max_position_weight': max_position_weight,
            'concentration_ratio': concentration_ratio
        }
    
    def calculate_position_size(self, confidence: int, edge: float, volatility: float = 0.0) -> float:
        """
        Calculate optimal position size for a single market.
        
        Args:
            confidence: Confidence level (0-10)
            edge: Probability edge (estimated_prob - market_price)
            volatility: Market volatility (0-1)
            
        Returns:
            Optimal position size as fraction of capital
        """
        # Base Kelly calculation
        if abs(edge) < self.config['min_edge_threshold']:
            return 0.0
        
        # Adjust for confidence
        confidence_factor = confidence / 10.0
        
        # Adjust for volatility (higher volatility = smaller position)
        volatility_factor = 1.0 / (1.0 + volatility)
        
        # Calculate position size
        base_position = abs(edge) * self.config['kelly_safety_factor']
        adjusted_position = base_position * confidence_factor * volatility_factor
        
        # Apply position limits
        max_position = self.config['max_position_size']
        return min(adjusted_position, max_position)
