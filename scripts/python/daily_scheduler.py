#!/usr/bin/env python3
"""
Daily Scheduler for Human-in-the-Loop Trading System

This script sets up automated daily execution of the trading analysis
and can be run as a cron job or scheduled task.
"""

import os
import sys
import logging
from datetime import datetime, time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from scripts.python.human_in_the_loop_trader import HumanInTheLoopTrader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_trading.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DailyTradingScheduler:
    """Scheduler for daily trading analysis"""
    
    def __init__(self, email_recipient: str):
        self.email_recipient = email_recipient
        self.trader = HumanInTheLoopTrader(email_recipient=email_recipient)
        
    def run_daily_analysis(self):
        """Run the daily trading analysis"""
        try:
            logger.info("Starting scheduled daily trading analysis...")
            
            # Run the analysis
            daily_recs = self.trader.run_daily_analysis()
            
            # Log results
            logger.info(f"Daily analysis completed:")
            logger.info(f"  - Recommendations: {len(daily_recs.recommendations)}")
            logger.info(f"  - Research cost: €{daily_recs.research_cost:.2f}")
            logger.info(f"  - Email sent: {daily_recs.email_sent}")
            
            # Save results to file
            self._save_daily_results(daily_recs)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in daily analysis: {e}")
            return False
    
    def _save_daily_results(self, daily_recs):
        """Save daily results to file"""
        try:
            results_dir = Path("logs/daily_results")
            results_dir.mkdir(exist_ok=True)
            
            filename = f"daily_results_{daily_recs.date.strftime('%Y-%m-%d')}.json"
            filepath = results_dir / filename
            
            # Convert to serializable format
            results_data = {
                'date': daily_recs.date.isoformat(),
                'recommendations': [
                    {
                        'market_id': rec.market_id,
                        'market_question': rec.market_question,
                        'current_price': rec.current_price,
                        'estimated_probability': rec.estimated_probability,
                        'confidence': rec.confidence,
                        'edge': rec.edge,
                        'recommended_position': rec.recommended_position,
                        'risk_level': rec.risk_level,
                        'research_summary': rec.research_summary,
                        'rationale': rec.rationale,
                        'days_to_resolution': rec.days_to_resolution,
                        'volume_24h': rec.volume_24h,
                        'liquidity_score': rec.liquidity_score
                    }
                    for rec in daily_recs.recommendations
                ],
                'total_expected_value': daily_recs.total_expected_value,
                'total_risk': daily_recs.total_risk,
                'research_cost': daily_recs.research_cost,
                'email_sent': daily_recs.email_sent
            }
            
            import json
            with open(filepath, 'w') as f:
                json.dump(results_data, f, indent=2)
            
            logger.info(f"Daily results saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving daily results: {e}")

def main():
    """Main function for scheduled execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Daily Trading Scheduler')
    parser.add_argument('--email', required=True, help='Email address to send recommendations to')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no email)')
    
    args = parser.parse_args()
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Initialize scheduler
    scheduler = DailyTradingScheduler(email_recipient=args.email)
    
    # Run analysis
    success = scheduler.run_daily_analysis()
    
    if success:
        print("Daily trading analysis completed successfully")
        sys.exit(0)
    else:
        print("Daily trading analysis failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
