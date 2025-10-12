# Human-in-the-Loop Trading System - Quick Start Guide

## 🎉 Your System is Ready!

The human-in-the-loop trading system is fully implemented and tested. Here's how to use it.

## 📋 What You Have

### ✅ Core System
- **Daily Market Discovery**: Finds top 10 most profitable markets
- **AI Deep Research**: Perplexity analyzes each market (€0.17/market)
- **Email Notifications**: Daily recommendations sent to your inbox
- **Web Interface**: Review and approve/reject trades
- **Risk Management**: Position limits and safety checks

### ✅ Your API Keys (Tested & Working)
- **PERPLEXITY_API_KEY**: ✅ Working
- **POLYGON_WALLET_PRIVATE_KEY**: ✅ Working (Balance: 0.0 USDC - needs funding)
- **OPENAI_API_KEY**: ⚠️ Optional (for parsing, recommended)

## 🚀 Quick Start (3 Options)

### Option 1: Run Demo (No API Calls)
```bash
python scripts/python/demo_human_in_the_loop.py
```
Shows what your daily recommendations will look like.

### Option 2: Manual Daily Run
```bash
python scripts/python/human_in_the_loop_trader.py --email your-email@example.com
```
Runs market discovery and research, sends email with recommendations.

### Option 3: Web Interface
```bash
python scripts/python/web_interface.py --email your-email@example.com --port 5000
```
Then visit: `http://localhost:5000`

## 📧 Email Setup (Optional but Recommended)

Add to your `.env` file:
```bash
# Gmail Setup (Recommended)
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password  # Use App Password, not regular password
EMAIL_RECIPIENT=your-email@example.com
```

### How to Get Gmail App Password:
1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Generate App Password
4. Use that password in `.env`

## ⏰ Daily Automation

### Set up cron job for 8 AM daily execution:

```bash
# Edit crontab
crontab -e

# Add this line (adjust path if needed):
0 8 * * * cd /Users/valentinhenryleo/polymarket-agents && /Users/valentinhenryleo/miniconda3/bin/python scripts/python/daily_scheduler.py --email your-email@example.com >> logs/cron.log 2>&1
```

Or use the provided script:
```bash
# Make executable
chmod +x scripts/bash/daily_trading_cron.sh

# Edit the script to add your email
nano scripts/bash/daily_trading_cron.sh

# Add to crontab
crontab -e
# Add: 0 8 * * * /Users/valentinhenryleo/polymarket-agents/scripts/bash/daily_trading_cron.sh
```

## 📊 What Happens Daily

### Morning (8:00 AM):
1. **Market Discovery**: System finds top 10 markets
2. **AI Research**: Perplexity analyzes each (€1.70 total)
3. **Email Sent**: You receive recommendations

### Your Review:
4. **Check Email**: Review recommendations
5. **Approve/Reject**: Use web interface or manual review
6. **Execute Trades**: Approved trades execute on Polymarket

### Evening:
7. **Performance Tracking**: Monitor results
8. **Adjust Strategy**: Fine-tune based on outcomes

## 💰 Cost Structure

- **Daily**: €1.70 (10 markets × €0.17)
- **Weekly**: €12 (7 days)
- **Monthly**: €50

Compare to: €800/week with OpenAI o3-deep-research (99% savings!)

## 🎯 Daily Workflow Example

**Morning Email:**
```
Subject: Daily Trading Recommendations - 2024-10-12

TOP 10 MARKETS FOR TODAY:

1. Will Bitcoin reach $100k by end of 2024? - Confidence: 8/10
   Research: Recent institutional adoption and ETF approvals...
   Recommendation: Bet $150 on YES
   Risk: Medium

2. Will SpaceX launch Starship before Q1 2025? - Confidence: 7/10
   Research: Recent test data shows significant progress...
   Recommendation: Bet $120 on YES
   Risk: Low

...8 more recommendations
```

**Your Actions:**
1. Review each recommendation
2. Approve the ones you like
3. Reject the ones you don't
4. Execute approved trades

## 🛠️ Configuration

Edit `config/human_in_the_loop.yaml` to customize:
- Number of markets to analyze
- Confidence thresholds
- Position limits
- Email settings

## 📈 Performance Tracking

Results saved to:
- `logs/daily_results/` - Daily recommendation history
- `logs/daily_trading.log` - Execution logs
- `research_cache/` - Cached research (24h)

## 🔧 Troubleshooting

### No markets found
- Markets may be filtered out by criteria
- Relax filters in the trader script
- Check Polymarket API connectivity

### Email not sending
- Verify EMAIL_USER and EMAIL_PASSWORD in `.env`
- Use Gmail App Password, not regular password
- Check SMTP settings (default: Gmail)

### Perplexity API errors
- Check PERPLEXITY_API_KEY is valid
- Verify API quota/credits
- Check network connectivity

### No USDC balance
- Fund your Polygon wallet with USDC
- Get wallet address: Check your POLYGON_WALLET_PRIVATE_KEY
- Transfer USDC to that address

## 📚 Additional Resources

- **Strategy Documentation**: `TRADING_STRATEGY.md`
- **Implementation Details**: `IMPLEMENTATION_COMPLETE.md`
- **Human-in-the-Loop README**: `HUMAN_IN_THE_LOOP_README.md`
- **Strategy Explanation**: See the plan document for full details

## 🎊 You're Ready!

Your system is fully functional. Start with:
1. **Run demo** to see how it works
2. **Add email credentials** for notifications
3. **Fund wallet** with USDC for trading
4. **Set up cron job** for daily automation
5. **Start receiving recommendations!**

## 💡 Pro Tips

1. **Start Small**: Begin with small position sizes
2. **Monitor Performance**: Track win rate and returns
3. **Adjust Filters**: Fine-tune market selection criteria
4. **Review Research**: Always read the AI rationale
5. **Trust Your Judgment**: You have final say on all trades

---

**Questions?** Check the documentation or review the code in `scripts/python/human_in_the_loop_trader.py`

**Happy Trading!** 🚀
