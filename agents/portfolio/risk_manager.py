"""
Risk management and monitoring for Polymarket trading.
"""

from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Risk management system for trading positions.
    """
    
    def __init__(self, max_position_size: float = 0.20, max_total_allocation: float = 0.80):
        self.max_position_size = max_position_size
        self.max_total_allocation = max_total_allocation
    
    def check_position_limits(self, trades: Dict[str, float], total_capital: float) -> Tuple[bool, List[str]]:
        """
        Check if trades violate position limits.
        
        Args:
            trades: Dict of market_id -> bet_amount
            total_capital: Total available capital
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        
        # Check individual position limits
        for market_id, bet_amount in trades.items():
            position_size = abs(bet_amount) / total_capital
            if position_size > self.max_position_size:
                violations.append(f"Position {market_id} exceeds limit: {position_size:.1%} > {self.max_position_size:.1%}")
        
        # Check total allocation limit
        total_allocated = sum(abs(amount) for amount in trades.values())
        total_allocation_ratio = total_allocated / total_capital
        if total_allocation_ratio > self.max_total_allocation:
            violations.append(f"Total allocation exceeds limit: {total_allocation_ratio:.1%} > {self.max_total_allocation:.1%}")
        
        is_valid = len(violations) == 0
        return is_valid, violations
    
    def calculate_portfolio_risk(self, trades: Dict[str, float], market_data: Dict[str, Dict]) -> Dict[str, float]:
        """
        Calculate portfolio risk metrics.
        
        Args:
            trades: Dict of market_id -> bet_amount
            market_data: Dict of market_id -> market_info
            
        Returns:
            Dict of risk metrics
        """
        if not trades:
            return {
                'total_exposure': 0.0,
                'max_position_weight': 0.0,
                'concentration_risk': 0.0,
                'correlation_risk': 0.0
            }
        
        total_exposure = sum(abs(amount) for amount in trades.values())
        position_weights = [abs(amount) / total_exposure for amount in trades.values()]
        
        # Maximum position weight
        max_position_weight = max(position_weights) if position_weights else 0.0
        
        # Concentration risk (Herfindahl index)
        concentration_risk = sum(w**2 for w in position_weights)
        
        # Correlation risk (simplified - assume markets are somewhat correlated)
        correlation_risk = min(0.5, len(trades) * 0.1)  # Mock correlation
        
        return {
            'total_exposure': total_exposure,
            'max_position_weight': max_position_weight,
            'concentration_risk': concentration_risk,
            'correlation_risk': correlation_risk
        }
