#!/usr/bin/env python3
"""
Human-in-the-Loop Daily Trading Recommendations

This system discovers the top 10 most profitable markets daily, runs deep research,
and sends email recommendations for human approval before executing trades.
"""

import os
import sys
import json
import smtplib
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.polymarket.polymarket import Polymarket
from agents.polymarket.gamma import GammaMarketClient
from agents.research.perplexity_research import PerplexityResearchAgent, EventResearchResult
from agents.portfolio.allocator import PortfolioAllocator, MarketOpportunity
from agents.portfolio.risk_manager import RiskManager
from agents.evaluation.performance_tracker import StrategyResult

logger = logging.getLogger(__name__)

@dataclass
class MarketRecommendation:
    """A trading recommendation for human review"""
    market_id: str
    market_question: str
    current_price: float
    estimated_probability: float
    confidence: int
    edge: float
    recommended_position: float
    risk_level: str
    research_summary: str
    rationale: str
    days_to_resolution: int
    volume_24h: float
    liquidity_score: float

@dataclass
class DailyRecommendations:
    """Daily set of market recommendations"""
    date: date
    recommendations: List[MarketRecommendation]
    total_expected_value: float
    total_risk: float
    research_cost: float
    email_sent: bool = False

class HumanInTheLoopTrader:
    """
    Human-in-the-loop trading system that provides daily recommendations
    for human approval before executing trades.
    """
    
    def __init__(self, 
                 email_recipient: str,
                 smtp_server: str = "smtp.gmail.com",
                 smtp_port: int = 587,
                 max_markets: int = 10,
                 min_confidence: int = 5,
                 min_edge: float = 0.05):
        
        self.email_recipient = email_recipient
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.max_markets = max_markets
        self.min_confidence = min_confidence
        self.min_edge = min_edge
        
        # Initialize components
        self.polymarket = Polymarket()
        self.gamma = GammaMarketClient()
        self.research_agent = PerplexityResearchAgent()
        self.portfolio_allocator = PortfolioAllocator(total_capital=1000.0, strategy_type='balanced')
        self.risk_manager = RiskManager(max_position_size=0.20, max_total_allocation=0.80)
        
        # Email credentials
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
        if not self.email_user or not self.email_password:
            logger.warning("Email credentials not found. Email notifications will be disabled.")
        
        # Performance tracking
        self.daily_recommendations: List[DailyRecommendations] = []
        self.approved_trades: List[Dict] = []
        self.total_research_cost = 0.0
        
        logger.info(f"Initialized Human-in-the-Loop Trader for {email_recipient}")
    
    def discover_top_markets(self) -> List[Dict]:
        """
        Discover and filter the top most profitable markets.
        
        Returns:
            List of market dictionaries sorted by profitability potential
        """
        logger.info("Discovering top markets...")
        
        try:
            # Get all current active markets from Gamma API
            markets = self.gamma.get_all_current_markets(limit=100)
            logger.info(f"Found {len(markets)} active markets")
            
            # Filter markets by basic criteria
            filtered_markets = []
            for market in markets:
                # Basic filtering criteria
                if self._is_market_tradeable(market):
                    filtered_markets.append(market)
            
            logger.info(f"Filtered to {len(filtered_markets)} tradeable markets")
            
            # Sort by profitability potential (volume, liquidity, time to resolution)
            sorted_markets = sorted(
                filtered_markets,
                key=lambda m: self._calculate_market_score(m),
                reverse=True
            )
            
            # Return top markets
            top_markets = sorted_markets[:self.max_markets * 2]  # Get more for research filtering
            logger.info(f"Selected top {len(top_markets)} markets for research")
            
            return top_markets
            
        except Exception as e:
            logger.error(f"Error discovering markets: {e}")
            return []
    
    def _is_market_tradeable(self, market) -> bool:
        """Check if a market meets basic tradeability criteria"""
        try:
            # Check if market is active
            if not market.get('active', False):
                return False
            
            # Check if market is closed
            if market.get('closed', False):
                return False
            
            # Check if market is archived
            if market.get('archived', False):
                return False
            
            # Check minimum volume (relaxed for testing)
            volume_24h = market.get('volume24hr', 0)
            if volume_24h < 100:  # $100 minimum volume (relaxed)
                return False
            
            # Check time to resolution
            end_date = market.get('endDate')
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    days_to_resolution = (end_dt - datetime.now()).days
                    # Exclude expired markets (allow future markets up to 1 year)
                    if days_to_resolution < 1 or days_to_resolution > 365:  # 1-365 days
                        return False
                except:
                    return False
            
            # Check if market has valid outcomes
            outcomes = market.get('outcomes', [])
            if len(outcomes) < 2:
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error checking market tradeability: {e}")
            return False
    
    def _calculate_market_score(self, market) -> float:
        """Calculate a score for market profitability potential"""
        try:
            # Volume score (higher is better)
            volume_24h = market.get('volume24hr', 0)
            volume_score = min(volume_24h / 100000, 1.0)  # Cap at $100k
            
            # Liquidity score (based on liquidity field)
            liquidity = market.get('liquidityNum', 0)
            liquidity_score = min(liquidity / 50000, 1.0)  # Cap at $50k
            
            # Time score (prefer markets with 3-30 days to resolution)
            time_score = 0.5  # Default neutral
            end_date = market.get('endDate')
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    days_to_resolution = (end_dt - datetime.now()).days
                    if 3 <= days_to_resolution <= 30:
                        time_score = 1.0
                    elif 1 <= days_to_resolution <= 60:
                        time_score = 0.8
                except:
                    pass
            
            # Question quality score (simple heuristic)
            question_score = 0.5
            question = market.get('question', '')
            if question and len(question) > 20:
                question_score = 0.8
            
            # Combined score
            total_score = (volume_score * 0.3 + liquidity_score * 0.3 + time_score * 0.3 + question_score * 0.1)
            return total_score
            
        except Exception as e:
            logger.warning(f"Error calculating market score: {e}")
            return 0.0
    
    def research_markets(self, markets) -> List[MarketRecommendation]:
        """
        Run deep research on the top markets and generate recommendations.
        
        Args:
            markets: List of market dictionaries to research
            
        Returns:
            List of market recommendations
        """
        logger.info(f"Researching {len(markets)} markets...")
        
        recommendations = []
        research_cost = 0.0
        
        for i, market in enumerate(markets[:self.max_markets]):
            try:
                logger.info(f"Researching market {i+1}/{self.max_markets}: {(market.get('question', 'Unknown'))[:50]}...")
                
                # Get actual market price from outcomePrices (first outcome, usually "Yes")
                outcome_prices = market.get('outcomePrices', [])
                if isinstance(outcome_prices, str):
                    import json
                    outcome_prices = json.loads(outcome_prices)
                
                current_price = float(outcome_prices[0]) if outcome_prices else 0.5
                logger.info(f"Market price: {current_price:.2%}")
                
                # Create event data for research
                event_data = {
                    'title': market.get('question', 'Unknown Market'),
                    'description': market.get('description', ''),
                    'markets': [{
                        'question': market.get('question', ''),
                        'outcomes': market.get('outcomes', []),
                        'market_id': str(market.get('id', '')),
                        'current_price': current_price
                    }]
                }
                
                # Run research
                research_result = self.research_agent.research_event(
                    event_data, 
                    event_data['markets'], 
                    date.today()
                )
                
                research_cost += 0.17  # Perplexity cost per call
                
                # Convert research result to recommendation
                if research_result.market_decisions:
                    decision = research_result.market_decisions[0]  # Take first decision
                    
                    recommendation = MarketRecommendation(
                        market_id=str(market.get('id', '')),
                        market_question=market.get('question', ''),
                        current_price=current_price,
                        estimated_probability=decision.estimated_probability,
                        confidence=decision.confidence,
                        edge=decision.estimated_probability - current_price,
                        recommended_position=self._calculate_position_size(decision, market, current_price),
                        risk_level=self._assess_risk_level(decision, market, current_price),
                        research_summary=research_result.event_summary,  # Full summary, not truncated
                        rationale=decision.rationale,  # Full rationale
                        days_to_resolution=self._calculate_days_to_resolution(market),
                        volume_24h=market.get('volume24hr', 0),
                        liquidity_score=self._calculate_liquidity_score(market)
                    )
                    
                    # Only include recommendations that meet minimum criteria
                    if (recommendation.confidence >= self.min_confidence and 
                        abs(recommendation.edge) >= self.min_edge):
                        recommendations.append(recommendation)
                        logger.info(f"Added recommendation: {recommendation.market_question[:30]}... (Confidence: {recommendation.confidence}, Edge: {recommendation.edge:.3f})")
                    else:
                        logger.info(f"Skipped market due to low confidence/edge: {recommendation.confidence}/{recommendation.edge:.3f}")
                
            except Exception as e:
                logger.error(f"Error researching market {i+1}: {e}")
                continue
        
        self.total_research_cost += research_cost
        logger.info(f"Generated {len(recommendations)} recommendations (Cost: €{research_cost:.2f})")
        
        return recommendations
    
    def _calculate_position_size(self, decision, market, current_price) -> float:
        """Calculate recommended position size based on Kelly Criterion"""
        try:
            edge = abs(decision.estimated_probability - current_price)
            confidence_factor = decision.confidence / 10.0
            
            # Kelly-inspired position sizing with safety factor
            base_position = edge * 0.5 * confidence_factor  # 50% Kelly safety factor
            max_position = 0.20  # 20% max position
            
            return min(base_position * 1000, max_position * 1000)  # Convert to dollar amount
            
        except Exception as e:
            logger.warning(f"Error calculating position size: {e}")
            return 0.0
    
    def _assess_risk_level(self, decision, market, current_price) -> str:
        """Assess risk level of the recommendation"""
        try:
            confidence = decision.confidence
            edge = abs(decision.estimated_probability - current_price)
            volume = market.get('volume24hr', 0)
            
            risk_score = 0
            
            # Confidence factor (higher confidence = lower risk)
            if confidence >= 8:
                risk_score -= 2
            elif confidence >= 6:
                risk_score -= 1
            
            # Edge factor (higher edge = lower risk)
            if edge >= 0.15:
                risk_score -= 2
            elif edge >= 0.10:
                risk_score -= 1
            
            # Volume factor (higher volume = lower risk)
            if volume >= 50000:
                risk_score -= 1
            elif volume < 5000:
                risk_score += 1
            
            # Determine risk level
            if risk_score <= -3:
                return "Low"
            elif risk_score <= 0:
                return "Medium"
            else:
                return "High"
                
        except Exception as e:
            logger.warning(f"Error assessing risk level: {e}")
            return "Medium"
    
    def _calculate_days_to_resolution(self, market) -> int:
        """Calculate days until market resolution"""
        try:
            end_date = market.get('endDate')
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                return (end_dt - datetime.now()).days
            return 0
        except:
            return 0
    
    def _calculate_liquidity_score(self, market) -> float:
        """Calculate liquidity score for the market"""
        try:
            # Use liquidity field from Gamma API
            liquidity = market.get('liquidityNum', 0)
            if liquidity >= 50000:
                return 1.0
            elif liquidity >= 10000:
                return 0.8
            elif liquidity >= 1000:
                return 0.6
            else:
                return 0.4
        except:
            return 0.5
    
    def send_daily_recommendations(self, recommendations: List[MarketRecommendation]) -> bool:
        """
        Send daily email with market recommendations.
        
        Args:
            recommendations: List of market recommendations
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.email_user or not self.email_password:
            logger.warning("Email credentials not available. Skipping email notification.")
            return False
        
        try:
            # Create email content
            subject = f"Daily Trading Recommendations - {date.today().strftime('%Y-%m-%d')}"
            
            # Create HTML email body
            html_body = self._create_email_html(recommendations)
            text_body = self._create_email_text(recommendations)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_user
            msg['To'] = self.email_recipient
            
            # Add text and HTML parts
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Daily recommendations email sent to {self.email_recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _create_email_html(self, recommendations: List[MarketRecommendation]) -> str:
        """Create HTML email content with full detailed information"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 900px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
                .header h1 {{ margin: 0; font-size: 32px; }}
                .header p {{ margin: 5px 0; opacity: 0.9; }}
                .market {{ border: 1px solid #e0e0e0; margin: 20px 0; padding: 25px; border-radius: 8px; background-color: #fafafa; }}
                .high-confidence {{ border-left: 6px solid #28a745; background-color: #f8fff9; }}
                .medium-confidence {{ border-left: 6px solid #ffc107; background-color: #fffef8; }}
                .low-confidence {{ border-left: 6px solid #dc3545; background-color: #fff8f8; }}
                .market h3 {{ color: #333; margin-top: 0; font-size: 20px; line-height: 1.4; }}
                .metrics {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; padding: 15px; background-color: white; border-radius: 5px; }}
                .metric {{ padding: 10px; }}
                .metric-label {{ font-size: 12px; color: #666; text-transform: uppercase; font-weight: 600; }}
                .metric-value {{ font-size: 18px; color: #333; font-weight: bold; margin-top: 5px; }}
                .risk-low {{ color: #28a745; }}
                .risk-medium {{ color: #ffc107; }}
                .risk-high {{ color: #dc3545; }}
                .positive-edge {{ color: #28a745; font-weight: bold; }}
                .negative-edge {{ color: #dc3545; font-weight: bold; }}
                .section {{ margin: 20px 0; padding: 15px; background-color: white; border-radius: 5px; }}
                .section-title {{ font-size: 14px; color: #667eea; text-transform: uppercase; font-weight: 600; margin-bottom: 10px; }}
                .section-content {{ color: #444; line-height: 1.6; white-space: pre-wrap; }}
                .footer {{ margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 5px; text-align: center; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Daily Trading Recommendations</h1>
                    <p><strong>Date:</strong> {date.today().strftime('%B %d, %Y')}</p>
                    <p><strong>Markets Analyzed:</strong> {len(recommendations)} | <strong>Research Cost:</strong> €{len(recommendations) * 0.17:.2f}</p>
                </div>
        """
        
        if not recommendations:
            html += "<p style='text-align: center; padding: 40px; color: #666;'><strong>No profitable opportunities found today.</strong></p>"
        else:
            html += f"<h2 style='color: #333; margin-bottom: 30px;'>📊 Top {len(recommendations)} Market Opportunities</h2>"
            
            for i, rec in enumerate(recommendations, 1):
                confidence_class = "high-confidence" if rec.confidence >= 7 else "medium-confidence" if rec.confidence >= 5 else "low-confidence"
                risk_class = f"risk-{rec.risk_level.lower()}"
                edge_class = "positive-edge" if rec.edge > 0 else "negative-edge"
                
                html += f"""
                <div class="market {confidence_class}">
                    <h3>#{i} {rec.market_question}</h3>
                    
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-label">Confidence</div>
                            <div class="metric-value">{rec.confidence}/10</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Risk Level</div>
                            <div class="metric-value {risk_class}">{rec.risk_level}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Current Market Price</div>
                            <div class="metric-value">{rec.current_price:.1%}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Our Estimate</div>
                            <div class="metric-value">{rec.estimated_probability:.1%}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Edge</div>
                            <div class="metric-value {edge_class}">{rec.edge:+.1%}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Recommended Position</div>
                            <div class="metric-value">${rec.recommended_position:.0f}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Days to Resolution</div>
                            <div class="metric-value">{rec.days_to_resolution}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">24h Volume</div>
                            <div class="metric-value">${rec.volume_24h:,.0f}</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">📝 Research Summary</div>
                        <div class="section-content">{rec.research_summary}</div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">💡 Why This Trade Makes Sense</div>
                        <div class="section-content">{rec.rationale}</div>
                    </div>
                    
                    <div style="margin-top: 15px; padding: 10px; background-color: #e8f4f8; border-radius: 5px; font-size: 13px; color: #555;">
                        <strong>Market ID:</strong> {rec.market_id} | <strong>Liquidity Score:</strong> {rec.liquidity_score:.2f}
                    </div>
                </div>
                """
        
        html += """
                <div class="footer">
                    <h3 style="margin-top: 0; color: #333;">⚠️ Important Notes</h3>
                    <p>This is a <strong>human-in-the-loop system</strong>. No trades will be executed automatically.</p>
                    <p>Review each recommendation carefully and make your own decision based on your risk tolerance.</p>
                    <p style="margin-top: 20px; font-size: 12px; color: #999;">
                        Generated by Polymarket AI Trading System | Powered by Perplexity Deep Research
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_email_text(self, recommendations: List[MarketRecommendation]) -> str:
        """Create plain text email content with full details"""
        text = f"""
================================================================================
DAILY TRADING RECOMMENDATIONS - {date.today().strftime('%B %d, %Y')}
================================================================================

Markets Analyzed: {len(recommendations)}
Research Cost: €{len(recommendations) * 0.17:.2f}

"""
        
        if not recommendations:
            text += "No profitable opportunities found today.\n"
        else:
            text += f"TOP {len(recommendations)} MARKET OPPORTUNITIES:\n\n"
            
            for i, rec in enumerate(recommendations, 1):
                text += f"""
{'='*80}
#{i} {rec.market_question}
{'='*80}

KEY METRICS:
  • Confidence: {rec.confidence}/10
  • Risk Level: {rec.risk_level}
  • Current Market Price: {rec.current_price:.1%}
  • Our Probability Estimate: {rec.estimated_probability:.1%}
  • Edge: {rec.edge:+.1%}
  • Recommended Position Size: ${rec.recommended_position:.0f}
  • Days to Resolution: {rec.days_to_resolution}
  • 24h Trading Volume: ${rec.volume_24h:,.0f}
  • Liquidity Score: {rec.liquidity_score:.2f}

RESEARCH SUMMARY:
{rec.research_summary}

WHY THIS TRADE MAKES SENSE:
{rec.rationale}

Market ID: {rec.market_id}

"""
        
        text += """
================================================================================
IMPORTANT NOTES
================================================================================
This is a HUMAN-IN-THE-LOOP system. No trades will be executed automatically.

Review each recommendation carefully and make your own decision based on:
  • Your risk tolerance
  • Your available capital
  • Your own research and analysis
  • Current market conditions

Generated by Polymarket AI Trading System | Powered by Perplexity Deep Research

"""
        
        return text
    
    def run_daily_analysis(self) -> DailyRecommendations:
        """
        Run the complete daily analysis workflow.
        
        Returns:
            DailyRecommendations object with all results
        """
        logger.info("Starting daily analysis...")
        
        # Step 1: Discover top markets
        markets = self.discover_top_markets()
        
        if not markets:
            logger.warning("No markets found for analysis")
            return DailyRecommendations(
                date=date.today(),
                recommendations=[],
                total_expected_value=0.0,
                total_risk=0.0,
                research_cost=0.0
            )
        
        # Step 2: Research markets
        recommendations = self.research_markets(markets)
        
        # Step 3: Calculate metrics
        total_expected_value = sum(rec.recommended_position * rec.edge for rec in recommendations)
        total_risk = sum(rec.recommended_position for rec in recommendations)
        research_cost = len(recommendations) * 0.17
        
        # Step 4: Create daily recommendations object
        daily_recs = DailyRecommendations(
            date=date.today(),
            recommendations=recommendations,
            total_expected_value=total_expected_value,
            total_risk=total_risk,
            research_cost=research_cost
        )
        
        # Step 5: Send email
        email_sent = self.send_daily_recommendations(recommendations)
        daily_recs.email_sent = email_sent
        
        # Step 6: Store results
        self.daily_recommendations.append(daily_recs)
        
        logger.info(f"Daily analysis complete: {len(recommendations)} recommendations, €{research_cost:.2f} cost")
        
        return daily_recs
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of the human-in-the-loop system"""
        if not self.daily_recommendations:
            return {"message": "No daily analyses completed yet"}
        
        total_recommendations = sum(len(rec.recommendations) for rec in self.daily_recommendations)
        total_research_cost = sum(rec.research_cost for rec in self.daily_recommendations)
        avg_recommendations_per_day = total_recommendations / len(self.daily_recommendations)
        
        return {
            "days_analyzed": len(self.daily_recommendations),
            "total_recommendations": total_recommendations,
            "avg_recommendations_per_day": avg_recommendations_per_day,
            "total_research_cost": total_research_cost,
            "avg_daily_cost": total_research_cost / len(self.daily_recommendations),
            "emails_sent": sum(1 for rec in self.daily_recommendations if rec.email_sent),
            "total_expected_value": sum(rec.total_expected_value for rec in self.daily_recommendations)
        }


def main():
    """Main function to run daily analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Human-in-the-Loop Daily Trading Analysis')
    parser.add_argument('--email', required=True, help='Email address to send recommendations to')
    parser.add_argument('--max-markets', type=int, default=10, help='Maximum number of markets to analyze')
    parser.add_argument('--min-confidence', type=int, default=5, help='Minimum confidence level')
    parser.add_argument('--min-edge', type=float, default=0.05, help='Minimum edge threshold')
    
    args = parser.parse_args()
    
    # Initialize trader
    trader = HumanInTheLoopTrader(
        email_recipient=args.email,
        max_markets=args.max_markets,
        min_confidence=args.min_confidence,
        min_edge=args.min_edge
    )
    
    # Run daily analysis
    try:
        daily_recs = trader.run_daily_analysis()
        
        print(f"\n{'='*60}")
        print(f"DAILY ANALYSIS COMPLETE - {daily_recs.date}")
        print(f"{'='*60}")
        print(f"Recommendations Generated: {len(daily_recs.recommendations)}")
        print(f"Research Cost: €{daily_recs.research_cost:.2f}")
        print(f"Total Expected Value: €{daily_recs.total_expected_value:.2f}")
        print(f"Email Sent: {'Yes' if daily_recs.email_sent else 'No'}")
        
        if daily_recs.recommendations:
            print(f"\nTop Recommendations:")
            for i, rec in enumerate(daily_recs.recommendations[:3], 1):
                print(f"{i}. {rec.market_question[:50]}... (Confidence: {rec.confidence}, Edge: {rec.edge:+.1%})")
        
        # Show performance summary
        summary = trader.get_performance_summary()
        print(f"\nPerformance Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        logger.error(f"Error in daily analysis: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
