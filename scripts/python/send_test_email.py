#!/usr/bin/env python3
"""
Quick script to test email sending with existing recommendations
"""
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def send_test_email():
    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD')
    email_recipient = "valentin.henryleo@gmail.com"
    
    if not email_user or not email_password:
        print(f"❌ Email credentials not found!")
        print(f"EMAIL_USER: {email_user}")
        print(f"EMAIL_PASSWORD: {'*' * len(email_password) if email_password else 'None'}")
        return False
    
    print(f"✅ Email credentials found")
    print(f"From: {email_user}")
    print(f"To: {email_recipient}")
    
    # Create email
    msg = EmailMessage()
    msg['Subject'] = '📊 Polymarket Daily Recommendations - October 12, 2025'
    msg['From'] = email_user
    msg['To'] = email_recipient
    
    # HTML body with the recommendations
    html_body = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .header { background: #4CAF50; color: white; padding: 20px; text-align: center; }
            .summary { background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }
            .recommendation { background: white; border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px; }
            .confidence { color: #4CAF50; font-weight: bold; }
            .edge { color: #2196F3; font-weight: bold; }
            .risk { color: #FF9800; }
            .footer { margin-top: 30px; padding: 20px; background: #f5f5f5; text-align: center; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Daily Market Recommendations</h1>
            <p>October 12, 2025</p>
        </div>
        
        <div class="summary">
            <h2>📈 Daily Summary</h2>
            <ul>
                <li><strong>Recommendations Generated:</strong> 5</li>
                <li><strong>Research Cost:</strong> €0.85</li>
                <li><strong>Total Expected Value:</strong> €17.50</li>
                <li><strong>Average Confidence:</strong> 7/10</li>
            </ul>
        </div>
        
        <h2>🎯 Top Recommendations</h2>
        
        <div class="recommendation">
            <h3>1. Will Israel first announce ceasefire on October 8?</h3>
            <p><span class="confidence">Confidence: 7/10</span> | <span class="edge">Edge: +10.0%</span></p>
            <p><strong>Recommendation:</strong> This market shows potential value based on current geopolitical analysis.</p>
            <p class="risk"><strong>Risk Level:</strong> Medium - Geopolitical events can be unpredictable</p>
        </div>
        
        <div class="recommendation">
            <h3>2. Will Monad perform an airdrop by December 31?</h3>
            <p><span class="confidence">Confidence: 7/10</span> | <span class="edge">Edge: +10.0%</span></p>
            <p><strong>Recommendation:</strong> Crypto airdrop prediction with solid fundamentals.</p>
            <p class="risk"><strong>Risk Level:</strong> Medium - Crypto project timelines can shift</p>
        </div>
        
        <div class="recommendation">
            <h3>3. Will Bitcoin reach $140,000 by December 31, 2025?</h3>
            <p><span class="confidence">Confidence: 7/10</span> | <span class="edge">Edge: +10.0%</span></p>
            <p><strong>Recommendation:</strong> Bullish Bitcoin prediction based on market analysis.</p>
            <p class="risk"><strong>Risk Level:</strong> Medium - Crypto markets are highly volatile</p>
        </div>
        
        <div class="footer">
            <p><strong>⚠️ Important:</strong> These are AI-generated recommendations based on deep research. Always do your own research and never invest more than you can afford to lose.</p>
            <p>This is an automated email from your Polymarket Human-in-the-Loop Trading System.</p>
        </div>
    </body>
    </html>
    """
    
    # Text version
    text_body = """
POLYMARKET DAILY RECOMMENDATIONS
October 12, 2025

DAILY SUMMARY
=============
Recommendations Generated: 5
Research Cost: €0.85
Total Expected Value: €17.50
Average Confidence: 7/10

TOP RECOMMENDATIONS
===================

1. Will Israel first announce ceasefire on October 8?
   Confidence: 7/10 | Edge: +10.0%
   Risk Level: Medium - Geopolitical events can be unpredictable

2. Will Monad perform an airdrop by December 31?
   Confidence: 7/10 | Edge: +10.0%
   Risk Level: Medium - Crypto project timelines can shift

3. Will Bitcoin reach $140,000 by December 31, 2025?
   Confidence: 7/10 | Edge: +10.0%
   Risk Level: Medium - Crypto markets are highly volatile

⚠️ IMPORTANT: These are AI-generated recommendations based on deep research.
Always do your own research and never invest more than you can afford to lose.

This is an automated email from your Polymarket Human-in-the-Loop Trading System.
    """
    
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype='html')
    
    # Send email
    try:
        print(f"🔄 Connecting to SMTP server...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            print(f"🔐 Logging in...")
            server.login(email_user, email_password)
            print(f"📧 Sending email...")
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to {email_recipient}!")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

if __name__ == "__main__":
    send_test_email()

