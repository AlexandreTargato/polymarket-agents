#!/usr/bin/env python3
"""
Simple Web Interface for Human Trade Approval

This creates a simple web interface where you can review daily recommendations
and approve/reject trades before execution.
"""

import os
import sys
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from scripts.python.human_in_the_loop_trader import HumanInTheLoopTrader, MarketRecommendation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

class TradeApprovalInterface:
    """Web interface for trade approval"""
    
    def __init__(self, email_recipient: str):
        self.email_recipient = email_recipient
        self.trader = HumanInTheLoopTrader(email_recipient=email_recipient)
        self.pending_recommendations: List[MarketRecommendation] = []
        self.approved_trades: List[Dict] = []
        self.rejected_trades: List[Dict] = []
        
    def load_today_recommendations(self) -> bool:
        """Load today's recommendations from file"""
        try:
            results_dir = Path("logs/daily_results")
            if not results_dir.exists():
                return False
                
            filename = f"daily_results_{date.today().strftime('%Y-%m-%d')}.json"
            filepath = results_dir / filename
            
            if not filepath.exists():
                return False
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Convert back to MarketRecommendation objects
            self.pending_recommendations = []
            for rec_data in data['recommendations']:
                rec = MarketRecommendation(
                    market_id=rec_data['market_id'],
                    market_question=rec_data['market_question'],
                    current_price=rec_data['current_price'],
                    estimated_probability=rec_data['estimated_probability'],
                    confidence=rec_data['confidence'],
                    edge=rec_data['edge'],
                    recommended_position=rec_data['recommended_position'],
                    risk_level=rec_data['risk_level'],
                    research_summary=rec_data['research_summary'],
                    rationale=rec_data['rationale'],
                    days_to_resolution=rec_data['days_to_resolution'],
                    volume_24h=rec_data['volume_24h'],
                    liquidity_score=rec_data['liquidity_score']
                )
                self.pending_recommendations.append(rec)
            
            logger.info(f"Loaded {len(self.pending_recommendations)} recommendations for today")
            return True
            
        except Exception as e:
            logger.error(f"Error loading recommendations: {e}")
            return False
    
    def approve_trade(self, market_id: str, position_size: float) -> bool:
        """Approve a trade for execution"""
        try:
            # Find the recommendation
            recommendation = None
            for rec in self.pending_recommendations:
                if rec.market_id == market_id:
                    recommendation = rec
                    break
            
            if not recommendation:
                return False
            
            # Create approved trade record
            approved_trade = {
                'market_id': market_id,
                'market_question': recommendation.market_question,
                'approved_position': position_size,
                'original_recommendation': position_size,
                'approval_time': datetime.now().isoformat(),
                'status': 'approved'
            }
            
            self.approved_trades.append(approved_trade)
            
            # Remove from pending
            self.pending_recommendations = [r for r in self.pending_recommendations if r.market_id != market_id]
            
            logger.info(f"Approved trade: {market_id} for ${position_size}")
            return True
            
        except Exception as e:
            logger.error(f"Error approving trade: {e}")
            return False
    
    def reject_trade(self, market_id: str, reason: str = "") -> bool:
        """Reject a trade"""
        try:
            # Find the recommendation
            recommendation = None
            for rec in self.pending_recommendations:
                if rec.market_id == market_id:
                    recommendation = rec
                    break
            
            if not recommendation:
                return False
            
            # Create rejected trade record
            rejected_trade = {
                'market_id': market_id,
                'market_question': recommendation.market_question,
                'rejection_time': datetime.now().isoformat(),
                'reason': reason,
                'status': 'rejected'
            }
            
            self.rejected_trades.append(rejected_trade)
            
            # Remove from pending
            self.pending_recommendations = [r for r in self.pending_recommendations if r.market_id != market_id]
            
            logger.info(f"Rejected trade: {market_id} - {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error rejecting trade: {e}")
            return False
    
    def execute_approved_trades(self) -> Dict[str, Any]:
        """Execute all approved trades"""
        try:
            if not self.approved_trades:
                return {"message": "No approved trades to execute", "success": False}
            
            executed_trades = []
            failed_trades = []
            
            for trade in self.approved_trades:
                try:
                    # Here you would call the actual trading execution
                    # For now, we'll simulate it
                    execution_result = {
                        'market_id': trade['market_id'],
                        'position': trade['approved_position'],
                        'execution_time': datetime.now().isoformat(),
                        'status': 'executed'
                    }
                    
                    executed_trades.append(execution_result)
                    logger.info(f"Executed trade: {trade['market_id']}")
                    
                except Exception as e:
                    failed_trades.append({
                        'market_id': trade['market_id'],
                        'error': str(e)
                    })
                    logger.error(f"Failed to execute trade {trade['market_id']}: {e}")
            
            # Clear approved trades
            self.approved_trades = []
            
            return {
                "success": True,
                "executed_trades": executed_trades,
                "failed_trades": failed_trades,
                "total_executed": len(executed_trades)
            }
            
        except Exception as e:
            logger.error(f"Error executing trades: {e}")
            return {"message": f"Error executing trades: {e}", "success": False}

# Initialize the interface
interface = TradeApprovalInterface(email_recipient=os.getenv('EMAIL_RECIPIENT', 'your-email@example.com'))

@app.route('/')
def index():
    """Main dashboard page"""
    # Load today's recommendations
    interface.load_today_recommendations()
    
    return render_template('dashboard.html',
                         recommendations=interface.pending_recommendations,
                         approved_trades=interface.approved_trades,
                         rejected_trades=interface.rejected_trades)

@app.route('/recommendations')
def recommendations():
    """View all pending recommendations"""
    return render_template('recommendations.html',
                         recommendations=interface.pending_recommendations)

@app.route('/approve/<market_id>', methods=['POST'])
def approve_trade(market_id):
    """Approve a specific trade"""
    try:
        data = request.get_json()
        position_size = float(data.get('position_size', 0))
        
        if interface.approve_trade(market_id, position_size):
            return jsonify({"success": True, "message": "Trade approved"})
        else:
            return jsonify({"success": False, "message": "Failed to approve trade"})
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/reject/<market_id>', methods=['POST'])
def reject_trade(market_id):
    """Reject a specific trade"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        if interface.reject_trade(market_id, reason):
            return jsonify({"success": True, "message": "Trade rejected"})
        else:
            return jsonify({"success": False, "message": "Failed to reject trade"})
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/execute', methods=['POST'])
def execute_trades():
    """Execute all approved trades"""
    try:
        result = interface.execute_approved_trades()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/run-analysis', methods=['POST'])
def run_analysis():
    """Run daily analysis manually"""
    try:
        daily_recs = interface.trader.run_daily_analysis()
        interface.load_today_recommendations()
        
        return jsonify({
            "success": True,
            "message": f"Analysis complete: {len(daily_recs.recommendations)} recommendations",
            "recommendations_count": len(daily_recs.recommendations),
            "research_cost": daily_recs.research_cost
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/status')
def api_status():
    """API endpoint for status information"""
    return jsonify({
        "pending_recommendations": len(interface.pending_recommendations),
        "approved_trades": len(interface.approved_trades),
        "rejected_trades": len(interface.rejected_trades),
        "last_analysis": date.today().isoformat()
    })

# Create templates directory and HTML templates
def create_templates():
    """Create HTML templates for the web interface"""
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Dashboard template
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Trading Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .card { background-color: white; padding: 20px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .recommendation { border-left: 5px solid #3498db; margin: 15px 0; padding: 15px; }
        .high-confidence { border-left-color: #27ae60; }
        .medium-confidence { border-left-color: #f39c12; }
        .low-confidence { border-left-color: #e74c3c; }
        .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 3px; cursor: pointer; }
        .btn-approve { background-color: #27ae60; color: white; }
        .btn-reject { background-color: #e74c3c; color: white; }
        .btn-primary { background-color: #3498db; color: white; }
        .btn-execute { background-color: #8e44ad; color: white; }
        .stats { display: flex; justify-content: space-around; margin: 20px 0; }
        .stat { text-align: center; padding: 20px; background-color: white; border-radius: 5px; }
        .risk-low { color: #27ae60; font-weight: bold; }
        .risk-medium { color: #f39c12; font-weight: bold; }
        .risk-high { color: #e74c3c; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Daily Trading Dashboard</h1>
            <p>{{ date.today().strftime('%Y-%m-%d') }} - Human-in-the-Loop Trading System</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <h3>{{ recommendations|length }}</h3>
                <p>Pending Recommendations</p>
            </div>
            <div class="stat">
                <h3>{{ approved_trades|length }}</h3>
                <p>Approved Trades</p>
            </div>
            <div class="stat">
                <h3>{{ rejected_trades|length }}</h3>
                <p>Rejected Trades</p>
            </div>
        </div>
        
        <div class="card">
            <h2>Quick Actions</h2>
            <button class="btn btn-primary" onclick="runAnalysis()">Run Daily Analysis</button>
            <button class="btn btn-execute" onclick="executeTrades()" {% if approved_trades|length == 0 %}disabled{% endif %}>Execute Approved Trades</button>
        </div>
        
        {% if recommendations %}
        <div class="card">
            <h2>Today's Recommendations</h2>
            {% for rec in recommendations %}
            <div class="recommendation {% if rec.confidence >= 7 %}high-confidence{% elif rec.confidence >= 5 %}medium-confidence{% else %}low-confidence{% endif %}">
                <h3>{{ rec.market_question }}</h3>
                <p><strong>Confidence:</strong> {{ rec.confidence }}/10 | <strong>Risk:</strong> <span class="risk-{{ rec.risk_level.lower() }}">{{ rec.risk_level }}</span></p>
                <p><strong>Current Price:</strong> {{ "%.1f"|format(rec.current_price * 100) }}% | <strong>Our Estimate:</strong> {{ "%.1f"|format(rec.estimated_probability * 100) }}% | <strong>Edge:</strong> {{ "%+.1f"|format(rec.edge * 100) }}%</p>
                <p><strong>Recommended Position:</strong> ${{ "%.0f"|format(rec.recommended_position) }}</p>
                <p><strong>Days to Resolution:</strong> {{ rec.days_to_resolution }} | <strong>Volume 24h:</strong> ${{ "{:,.0f}"|format(rec.volume_24h) }}</p>
                <p><strong>Research:</strong> {{ rec.research_summary }}</p>
                <p><strong>Rationale:</strong> {{ rec.rationale }}</p>
                
                <div style="margin-top: 15px;">
                    <button class="btn btn-approve" onclick="approveTrade('{{ rec.market_id }}', {{ rec.recommended_position }})">Approve</button>
                    <button class="btn btn-reject" onclick="rejectTrade('{{ rec.market_id }}')">Reject</button>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="card">
            <h2>No Recommendations Available</h2>
            <p>Run the daily analysis to get today's market recommendations.</p>
        </div>
        {% endif %}
        
        {% if approved_trades %}
        <div class="card">
            <h2>Approved Trades</h2>
            {% for trade in approved_trades %}
            <div class="recommendation" style="border-left-color: #27ae60;">
                <h3>{{ trade.market_question }}</h3>
                <p><strong>Position:</strong> ${{ "%.0f"|format(trade.approved_position) }}</p>
                <p><strong>Approved:</strong> {{ trade.approval_time }}</p>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    
    <script>
        function approveTrade(marketId, positionSize) {
            fetch(`/approve/${marketId}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({position_size: positionSize})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            });
        }
        
        function rejectTrade(marketId) {
            const reason = prompt('Reason for rejection (optional):');
            fetch(`/reject/${marketId}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({reason: reason || 'No reason provided'})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            });
        }
        
        function executeTrades() {
            if (confirm('Execute all approved trades?')) {
                fetch('/execute', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`Executed ${data.total_executed} trades successfully!`);
                        location.reload();
                    } else {
                        alert('Error: ' + data.message);
                    }
                });
            }
        }
        
        function runAnalysis() {
            if (confirm('Run daily analysis? This will research new markets.')) {
                fetch('/run-analysis', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`Analysis complete: ${data.recommendations_count} recommendations found (Cost: €${data.research_cost.toFixed(2)})`);
                        location.reload();
                    } else {
                        alert('Error: ' + data.message);
                    }
                });
            }
        }
    </script>
</body>
</html>
    """
    
    with open(templates_dir / 'dashboard.html', 'w') as f:
        f.write(dashboard_html)
    
    logger.info("Created web interface templates")

def main():
    """Main function to run the web interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Human-in-the-Loop Web Interface')
    parser.add_argument('--email', required=True, help='Email address for recommendations')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the web interface on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    
    args = parser.parse_args()
    
    # Update the interface email
    interface.email_recipient = args.email
    
    # Create templates
    create_templates()
    
    # Load today's recommendations
    interface.load_today_recommendations()
    
    print(f"Starting web interface on http://{args.host}:{args.port}")
    print(f"Email recipient: {args.email}")
    
    app.run(host=args.host, port=args.port, debug=True)

if __name__ == "__main__":
    main()
