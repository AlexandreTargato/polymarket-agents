import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    """Risk metrics for portfolio monitoring"""
    portfolio_value: float
    daily_return: float
    cumulative_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    current_drawdown: float
    var_95: float  # Value at Risk (95% confidence)
    max_position_weight: float
    concentration_ratio: float

@dataclass
class PositionRisk:
    """Risk metrics for individual position"""
    market_id: str
    position_size: float
    position_weight: float
    daily_pnl: float
    unrealized_pnl: float
    risk_contribution: float

class RiskManager:
    """
    Risk management system for portfolio monitoring and control.
    
    Features:
    - Position limits enforcement
    - Drawdown monitoring
    - Sharpe ratio tracking
    - Value at Risk calculation
    - Concentration risk monitoring
    """
    
    def __init__(
        self, 
        max_position_size: float = 0.20,
        max_total_allocation: float = 0.80,
        max_drawdown_threshold: float = 0.15,
        var_confidence: float = 0.95
    ):
        self.max_position_size = max_position_size
        self.max_total_allocation = max_total_allocation
        self.max_drawdown_threshold = max_drawdown_threshold
        self.var_confidence = var_confidence
        
        # Portfolio history for risk calculations
        self.portfolio_history: List[Dict] = []
        self.peak_value = 0.0
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0
        
        # Risk limits
        self.risk_limits = {
            'max_position_weight': max_position_size,
            'max_total_allocation': max_total_allocation,
            'max_drawdown': max_drawdown_threshold,
            'min_sharpe_ratio': 0.5,
            'max_concentration': 0.5
        }
    
    def check_position_limits(self, allocations: Dict[str, float], total_capital: float) -> Tuple[bool, List[str]]:
        """
        Check if allocations violate position limits.
        
        Args:
            allocations: Dict of market_id -> bet_amount
            total_capital: Total available capital
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        
        # Check individual position limits
        for market_id, bet_amount in allocations.items():
            position_weight = abs(bet_amount) / total_capital
            
            if position_weight > self.max_position_size:
                violations.append(
                    f"Position {market_id} exceeds limit: {position_weight:.3f} > {self.max_position_size:.3f}"
                )
        
        # Check total allocation limit
        total_allocated = sum(abs(amount) for amount in allocations.values())
        total_allocation_ratio = total_allocated / total_capital
        
        if total_allocation_ratio > self.max_total_allocation:
            violations.append(
                f"Total allocation exceeds limit: {total_allocation_ratio:.3f} > {self.max_total_allocation:.3f}"
            )
        
        # Check concentration risk
        if allocations:
            position_weights = [abs(amount) / total_capital for amount in allocations.values()]
            concentration_ratio = sum(w**2 for w in position_weights)  # Herfindahl index
            
            if concentration_ratio > self.risk_limits['max_concentration']:
                violations.append(
                    f"Portfolio too concentrated: {concentration_ratio:.3f} > {self.risk_limits['max_concentration']:.3f}"
                )
        
        return len(violations) == 0, violations
    
    def update_portfolio_value(self, current_value: float, timestamp: datetime = None):
        """Update portfolio value and calculate risk metrics"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Calculate daily return
        daily_return = 0.0
        if self.portfolio_history:
            previous_value = self.portfolio_history[-1]['value']
            daily_return = (current_value - previous_value) / previous_value
        
        # Update peak and drawdown
        if current_value > self.peak_value:
            self.peak_value = current_value
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = (self.peak_value - current_value) / self.peak_value
            self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
        
        # Add to history
        self.portfolio_history.append({
            'timestamp': timestamp,
            'value': current_value,
            'daily_return': daily_return,
            'drawdown': self.current_drawdown
        })
        
        # Keep only last 252 days (1 year) for calculations
        if len(self.portfolio_history) > 252:
            self.portfolio_history = self.portfolio_history[-252:]
    
    def calculate_risk_metrics(self) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        if len(self.portfolio_history) < 2:
            return RiskMetrics(
                portfolio_value=0.0,
                daily_return=0.0,
                cumulative_return=0.0,
                volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                current_drawdown=0.0,
                var_95=0.0,
                max_position_weight=0.0,
                concentration_ratio=0.0
            )
        
        current_value = self.portfolio_history[-1]['value']
        initial_value = self.portfolio_history[0]['value']
        
        # Calculate returns
        daily_returns = [entry['daily_return'] for entry in self.portfolio_history[1:]]
        cumulative_return = (current_value - initial_value) / initial_value
        
        # Calculate volatility (annualized)
        volatility = np.std(daily_returns) * np.sqrt(252) if len(daily_returns) > 1 else 0.0
        
        # Calculate Sharpe ratio (assuming risk-free rate = 0)
        mean_return = np.mean(daily_returns) * 252  # Annualized
        sharpe_ratio = mean_return / volatility if volatility > 0 else 0.0
        
        # Calculate Value at Risk (95% confidence)
        var_95 = np.percentile(daily_returns, (1 - self.var_confidence) * 100) if daily_returns else 0.0
        
        return RiskMetrics(
            portfolio_value=current_value,
            daily_return=daily_returns[-1] if daily_returns else 0.0,
            cumulative_return=cumulative_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=self.max_drawdown,
            current_drawdown=self.current_drawdown,
            var_95=var_95,
            max_position_weight=0.0,  # Will be calculated separately
            concentration_ratio=0.0   # Will be calculated separately
        )
    
    def check_risk_limits(self, risk_metrics: RiskMetrics) -> Tuple[bool, List[str]]:
        """Check if portfolio violates risk limits"""
        violations = []
        
        # Check drawdown limit
        if risk_metrics.current_drawdown > self.max_drawdown_threshold:
            violations.append(
                f"Current drawdown exceeds limit: {risk_metrics.current_drawdown:.3f} > {self.max_drawdown_threshold:.3f}"
            )
        
        # Check Sharpe ratio
        if risk_metrics.sharpe_ratio < self.risk_limits['min_sharpe_ratio']:
            violations.append(
                f"Sharpe ratio below minimum: {risk_metrics.sharpe_ratio:.3f} < {self.risk_limits['min_sharpe_ratio']:.3f}"
            )
        
        # Check volatility (if too high)
        if risk_metrics.volatility > 0.5:  # 50% annual volatility threshold
            violations.append(
                f"Volatility too high: {risk_metrics.volatility:.3f} > 0.5"
            )
        
        return len(violations) == 0, violations
    
    def calculate_position_risks(
        self, 
        allocations: Dict[str, float], 
        market_data: Dict[str, Dict],
        total_capital: float
    ) -> List[PositionRisk]:
        """Calculate risk metrics for individual positions"""
        position_risks = []
        
        for market_id, bet_amount in allocations.items():
            if market_id not in market_data:
                continue
            
            market = market_data[market_id]
            position_weight = abs(bet_amount) / total_capital
            
            # Calculate daily PnL (simplified)
            daily_pnl = 0.0  # Would need price history for actual calculation
            unrealized_pnl = 0.0  # Would need current vs entry price
            
            # Risk contribution (simplified)
            risk_contribution = position_weight * market.get('volatility', 0.1)
            
            position_risk = PositionRisk(
                market_id=market_id,
                position_size=bet_amount,
                position_weight=position_weight,
                daily_pnl=daily_pnl,
                unrealized_pnl=unrealized_pnl,
                risk_contribution=risk_contribution
            )
            
            position_risks.append(position_risk)
        
        return position_risks
    
    def should_reduce_positions(self, risk_metrics: RiskMetrics) -> bool:
        """Determine if positions should be reduced due to risk"""
        # Reduce positions if drawdown is approaching limit
        if risk_metrics.current_drawdown > self.max_drawdown_threshold * 0.8:
            return True
        
        # Reduce positions if Sharpe ratio is very low
        if risk_metrics.sharpe_ratio < 0.0:
            return True
        
        # Reduce positions if volatility is extremely high
        if risk_metrics.volatility > 1.0:  # 100% annual volatility
            return True
        
        return False
    
    def get_position_reduction_factor(self, risk_metrics: RiskMetrics) -> float:
        """Calculate factor by which to reduce positions (0.0 to 1.0)"""
        if not self.should_reduce_positions(risk_metrics):
            return 1.0
        
        # Calculate reduction factor based on risk metrics
        drawdown_factor = max(0.5, 1.0 - risk_metrics.current_drawdown / self.max_drawdown_threshold)
        sharpe_factor = max(0.3, min(1.0, risk_metrics.sharpe_ratio / 1.0))
        volatility_factor = max(0.5, 1.0 - risk_metrics.volatility)
        
        # Take the minimum factor (most conservative)
        reduction_factor = min(drawdown_factor, sharpe_factor, volatility_factor)
        
        return max(0.1, reduction_factor)  # Minimum 10% of positions
    
    def reset_risk_tracking(self):
        """Reset risk tracking (useful for new strategies)"""
        self.portfolio_history = []
        self.peak_value = 0.0
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0
