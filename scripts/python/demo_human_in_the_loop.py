#!/usr/bin/env python3
"""
Demo of Human-in-the-Loop Trading System

This creates mock recommendations to demonstrate the email and workflow
without requiring API calls or real market data.
"""

import os
import sys
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from scripts.python.human_in_the_loop_trader import MarketRecommendation, DailyRecommendations

def create_demo_recommendations():
    """Create demo market recommendations"""
    recommendations = [
        MarketRecommendation(
            market_id="demo_1",
            market_question="Will Bitcoin reach $100,000 by end of 2024?",
            current_price=0.45,
            estimated_probability=0.65,
            confidence=8,
            edge=0.20,
            recommended_position=150.0,
            risk_level="Medium",
            research_summary="Recent institutional adoption and ETF approvals have driven significant momentum. Historical patterns suggest strong Q4 performance...",
            rationale="Based on current adoption trends, regulatory clarity, and historical bull market patterns, there's a strong probability of Bitcoin reaching $100k. Key factors: 1) Institutional demand increasing, 2) Supply shock from halving, 3) Macro conditions improving.",
            days_to_resolution=80,
            volume_24h=250000,
            liquidity_score=0.9
        ),
        MarketRecommendation(
            market_id="demo_2",
            market_question="Will SpaceX successfully launch Starship to orbit before Q1 2025?",
            current_price=0.60,
            estimated_probability=0.75,
            confidence=7,
            edge=0.15,
            recommended_position=120.0,
            risk_level="Low",
            research_summary="SpaceX has completed multiple test flights with increasing success. Recent FAA approvals and hardware improvements indicate readiness...",
            rationale="Recent test data shows significant progress. SpaceX has demonstrated rapid iteration capability. Key factors: 1) FAA approval timeline, 2) Hardware improvements validated, 3) Launch window availability.",
            days_to_resolution=45,
            volume_24h=180000,
            liquidity_score=0.85
        ),
        MarketRecommendation(
            market_id="demo_3",
            market_question="Will the Federal Reserve cut interest rates in November 2024?",
            current_price=0.70,
            estimated_probability=0.55,
            confidence=6,
            edge=-0.15,
            recommended_position=80.0,
            risk_level="High",
            research_summary="Economic data shows mixed signals. Inflation trending down but employment remains strong. Fed communications suggest data-dependent approach...",
            rationale="Market may be overpricing the probability of a November cut. Key factors: 1) Inflation still above target, 2) Strong labor market, 3) Fed's cautious messaging suggests waiting for more data.",
            days_to_resolution=30,
            volume_24h=500000,
            liquidity_score=0.95
        )
    ]
    
    return DailyRecommendations(
        date=date.today(),
        recommendations=recommendations,
        total_expected_value=45.0,
        total_risk=350.0,
        research_cost=0.51,  # 3 markets × €0.17
        email_sent=False
    )

def print_demo_report(daily_recs):
    """Print demo report to console"""
    print("\n" + "="*60)
    print("📧 DAILY TRADING RECOMMENDATIONS - DEMO MODE")
    print("="*60)
    print(f"Date: {daily_recs.date}")
    print(f"Recommendations: {len(daily_recs.recommendations)}")
    print(f"Research Cost: €{daily_recs.research_cost:.2f}")
    print(f"Total Expected Value: €{daily_recs.total_expected_value:.2f}")
    print("\n" + "="*60)
    print("TOP MARKET OPPORTUNITIES")
    print("="*60)
    
    for i, rec in enumerate(daily_recs.recommendations, 1):
        confidence_emoji = "🟢" if rec.confidence >= 7 else "🟡" if rec.confidence >= 5 else "🔴"
        risk_emoji = {"Low": "✅", "Medium": "⚠️", "High": "❌"}.get(rec.risk_level, "❓")
        
        print(f"\n{i}. {rec.market_question}")
        print(f"   {confidence_emoji} Confidence: {rec.confidence}/10 | {risk_emoji} Risk: {rec.risk_level}")
        print(f"   📊 Current Price: {rec.current_price:.1%} | Our Estimate: {rec.estimated_probability:.1%}")
        print(f"   💰 Edge: {rec.edge:+.1%} | Recommended Position: ${rec.recommended_position:.0f}")
        print(f"   📅 Days to Resolution: {rec.days_to_resolution} | Volume 24h: ${rec.volume_24h:,.0f}")
        print(f"   📝 Research: {rec.research_summary}")
        print(f"   🎯 Rationale: {rec.rationale}")
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Review each recommendation carefully")
    print("2. Use web interface to approve/reject trades")
    print("3. Execute approved trades on Polymarket")
    print("4. Monitor performance and adjust strategy")
    print("\n💡 This is a DEMO. Real system will use live market data and AI research.")
    print("="*60 + "\n")

def main():
    """Main demo function"""
    print("\n🚀 Human-in-the-Loop Trading System - DEMO MODE")
    print("="*60)
    print("This demo shows what your daily recommendations will look like.")
    print("="*60)
    
    # Create demo recommendations
    daily_recs = create_demo_recommendations()
    
    # Print report
    print_demo_report(daily_recs)
    
    # Show email preview
    print("\n📧 EMAIL PREVIEW")
    print("="*60)
    print("Subject: Daily Trading Recommendations - " + str(daily_recs.date))
    print("\nYou would receive an HTML email with:")
    print("- Executive summary with key metrics")
    print("- Detailed analysis for each market")
    print("- Risk assessment and recommendations")
    print("- Quick action links for approval")
    print("="*60)
    
    print("\n✅ Demo complete!")
    print("\nTo run with real data:")
    print("1. Add OPENAI_API_KEY to .env for parsing")
    print("2. Run: python scripts/python/human_in_the_loop_trader.py --email your-email@example.com")
    print("3. Set up daily cron job for automation")

if __name__ == "__main__":
    main()
