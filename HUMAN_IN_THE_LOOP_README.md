# Human-in-the-Loop Trading System

This system provides daily market recommendations via email and web interface for human approval before executing trades.

## Quick Start

### 1. Run Daily Analysis
```bash
python scripts/python/human_in_the_loop_trader.py --email your-email@example.com
```

### 2. Start Web Interface
```bash
python scripts/python/web_interface.py --email your-email@example.com --port 5000
```

### 3. Set Up Daily Automation
```bash
# Add to crontab for daily 8 AM execution
crontab -e
# Add: 0 8 * * * /path/to/scripts/bash/daily_trading_cron.sh
```

## Features

- **Daily Market Discovery**: Finds top 10 most profitable markets
- **Deep Research**: Uses Perplexity Sonar Deep Research (€0.17/call)
- **Email Notifications**: Sends daily recommendations via email
- **Web Interface**: Review and approve/reject trades
- **Risk Management**: Position limits and risk assessment
- **Performance Tracking**: Monitor results and costs

## Workflow

1. **Morning**: System runs market discovery and research
2. **Email**: You receive recommendations with analysis
3. **Review**: Use web interface to approve/reject trades
4. **Execute**: Approved trades are executed on Polymarket
5. **Monitor**: Track performance and adjust strategy

## Configuration

Edit `config/human_in_the_loop.yaml` to customize:
- Number of markets to analyze
- Confidence thresholds
- Position limits
- Email settings

## Cost Structure

- **Research**: €0.17 per market analyzed
- **Daily Cost**: ~€1.70 (10 markets)
- **Weekly Cost**: ~€12 (7 days)
- **Monthly Cost**: ~€50

## API Keys Required

- `PERPLEXITY_API_KEY`: For deep research
- `POLYGON_WALLET_PRIVATE_KEY`: For trading
- `OPENAI_API_KEY`: For parsing (optional)
- `EMAIL_USER` & `EMAIL_PASSWORD`: For notifications (optional)

## Troubleshooting

- Check logs in `logs/` directory
- Verify API keys in `.env` file
- Ensure email credentials are correct
- Check Polymarket API connectivity

## Support

For issues or questions, check the logs and verify your configuration.
