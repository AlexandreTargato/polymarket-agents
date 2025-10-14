# Polymarket Trading Agent - Research System

An automated research system that identifies potential trading opportunities on Polymarket by comparing AI-powered deep research findings against current market pricing.

## Overview

This agent performs daily automated research on Polymarket prediction markets and sends a comprehensive email report at 9:00 AM with actionable insights. The system is designed to exploit information asymmetry by systematically researching questions that require deep analysis.

## Architecture

The system implements a 7-stage pipeline:

1. **Market Fetching** - Retrieve active markets from Polymarket API
2. **Multi-Stage Filtering** - Apply 5 filters to narrow down to 15-25 markets
3. **Tier 1 Research** - Fast context gathering (60-90s per market)
4. **Tier 2 Research** - Deep analysis (5-10 min per market)
5. **Opportunity Analysis** - Calculate edge, confidence, and opportunity scores
6. **Report Generation** - Create HTML email report
7. **Delivery & Logging** - Send email and log results

## Features

- **Intelligent Filtering**: Multi-stage filtering based on volume, liquidity, time horizon, category, and market maturity
- **Two-Tier Research**: Fast initial screening followed by deep analysis for promising markets
- **Source Quality Assessment**: Automatic credibility scoring and source diversity analysis
- **Confidence Scoring**: Multi-factor confidence calculation considering source quality, recency, consensus, and reasoning
- **Risk Analysis**: Identifies red flags and green flags for each opportunity
- **HTML Email Reports**: Beautiful, mobile-responsive email reports with detailed findings
- **Data Logging**: Tracks all runs for performance analysis and model improvement
- **Cost Tracking**: Estimates and monitors daily API costs

## Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd agents

# Create virtual environment
python3.9 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
# Required
ANTHROPIC_API_KEY="your-anthropic-key"
TAVILY_API_KEY="your-tavily-key"

# For email reports
EMAIL_SMTP_USERNAME="your-email@gmail.com"
EMAIL_SMTP_PASSWORD="your-app-password"
EMAIL_FROM="your-email@gmail.com"
EMAIL_TO="recipient@email.com"
```

**Getting API Keys:**
- Anthropic: https://console.anthropic.com/
- Tavily: https://tavily.com/

**For Gmail:**
1. Enable 2-factor authentication
2. Generate an app password: https://myaccount.google.com/apppasswords
3. Use the app password in EMAIL_SMTP_PASSWORD

### 3. Run the Agent

```bash
# Run once (for testing)
python main.py

# Run on daily schedule (8:00 AM analysis, 9:00 AM email)
python main.py --schedule

# Test mode (faster, limited markets)
python main.py --test
```

## Docker Deployment

### Build the Image

```bash
docker build -t polymarket-agent .
```

### Run Once

```bash
docker run --env-file .env polymarket-agent
```

### Run on Schedule

```bash
docker run -d \
  --name polymarket-agent \
  --env-file .env \
  --restart unless-stopped \
  polymarket-agent \
  python main.py --schedule
```

### View Logs

```bash
docker logs -f polymarket-agent
```

## Project Structure

```
agents/
├── agents/
│   ├── config.py              # Configuration management
│   ├── models.py              # Pydantic data models
│   ├── orchestrator.py        # Main workflow orchestrator
│   ├── scheduler.py           # Daily scheduler
│   └── stages/
│       ├── market_fetcher.py      # Stage 1: Fetch markets
│       ├── market_filter.py       # Stage 2: Filter markets
│       ├── tier1_research.py      # Stage 3: Fast research
│       ├── tier2_research.py      # Stage 4: Deep research
│       ├── opportunity_analyzer.py # Stage 5: Scoring
│       ├── report_generator.py    # Stage 6: HTML reports
│       └── email_sender.py        # Stage 7: Email & logging
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── Dockerfile                 # Docker configuration
└── .env.example              # Environment template
```

## Configuration

The system is highly configurable via `agents/config.py`. Key settings:

### Filtering Criteria
- `min_volume`: $10,000 (minimum market volume)
- `min_liquidity`: $5,000 (minimum liquidity)
- `min_resolution_days`: 7 days
- `max_resolution_days`: 30 days
- `focus_categories`: Politics, Business, Technology, Regulatory

### Research Settings
- `tier1_model`: "claude-3-5-haiku-20241022" (fast analysis)
- `tier2_model`: "claude-3-5-sonnet-20241022" (deep analysis)
- `tier1_queries_per_market`: 3
- `tier2_queries_per_market`: 8

### Opportunity Thresholds
- `min_edge_for_report`: 5% (minimum edge to report)
- `min_confidence_score`: 0.5 (minimum confidence)
- `min_opportunity_score`: 0.03 (minimum overall score)

### Scheduling
- `cron_hour`: 8 (run at 8:00 AM)
- `send_time_hour`: 9 (email at 9:00 AM)
- `max_daily_cost`: $50 (cost cap)

## Cost Estimates

Typical daily costs with Anthropic Claude:
- **Tier 1 Research** (20 markets): ~$0.04 (Claude 3.5 Haiku)
- **Tier 2 Research** (6 markets): ~$0.24 (Claude 3.5 Sonnet)
- **Tavily Searches**: ~$0.10
- **Total**: ~$0.40/day (~$12/month)

## Filtering Pipeline

The system applies 5 sequential filters:

1. **Volume & Liquidity**: Ensures tradeable markets
2. **Time Horizon**: 7-30 days until resolution
3. **Category**: Focus on researchable categories
4. **Question Type**: Binary/factual questions preferred
5. **Market Maturity**: 12 hours to 2 weeks old

Expected funnel: 500+ markets → 15-25 filtered markets → 5-8 deep research

## Research Process

### Tier 1 (Fast - 60-90s per market)
1. Generate 2-3 targeted search queries
2. Run web searches (last 7 days prioritized)
3. Quick analysis with Claude 3.5 Haiku
4. Decide if worth deep research

### Tier 2 (Deep - 5-10 min per market)
1. Generate 5-8 comprehensive queries (including contrarian)
2. Multi-timeframe searches (7d, 30d, all time)
3. Deep analysis with Claude 3.5 Sonnet using structured framework
4. Probability estimation with confidence intervals
5. Source quality assessment
6. Risk analysis

## Opportunity Scoring

**Opportunity Score** = Edge × Confidence × Liquidity Factor

Where:
- **Edge** = |Model Probability - Market Probability|
- **Confidence** = Weighted average of:
  - Source Quality (25%)
  - Information Recency (20%)
  - Consensus Level (20%)
  - Base Rate Alignment (20%)
  - Reasoning Clarity (15%)
- **Liquidity Factor** = min(1.0, liquidity / $10,000)

## Email Reports

Reports include:
- **Executive Summary**: Key metrics and top opportunities
- **High Priority Opportunities**: Detailed analysis with sources
- **Medium Priority**: Condensed findings
- **System Metrics**: Runtime, costs, errors

Each opportunity shows:
- Model vs Market probability
- Edge and opportunity score
- Key findings with sources
- Reasoning and analysis
- Red flags and green flags
- Direct link to Polymarket

## Data Logging

All runs are logged to `data/logs/` as JSON files:
- Full market and research data
- Opportunity details and scores
- Timing breakdown
- Errors encountered

Use logged data to:
- Track model accuracy over time
- Calculate Brier scores
- Identify best question types
- Refine filtering criteria

## Best Practices

### For Production
1. Start with test mode to validate setup
2. Monitor first few runs closely
3. Set up cost alerts with your APIs
4. Review email reports daily
5. Track accuracy as markets resolve
6. Adjust filters based on results

### Safety Features
- Hard cost caps prevent runaway spending
- Extensive error handling and logging
- Conservative probability estimates
- Red flag identification
- Human-in-the-loop (reports only, no auto-trading)

## Troubleshooting

### Email Not Sending
- Verify SMTP credentials
- Check firewall/network settings
- For Gmail, ensure app password is used
- Check logs for SMTP errors

### High API Costs
- Reduce `max_markets_to_filter`
- Reduce `max_markets_for_deep_research`
- Use cheaper models for Tier 1
- Increase filtering thresholds

### No Opportunities Found
- Lower `min_edge_for_report`
- Lower `min_confidence_score`
- Expand `focus_categories`
- Adjust time horizon

## Future Enhancements

- Real-time monitoring for major price swings
- Category-specific research templates
- Automated outcome tracking
- Performance attribution analysis
- Integration with DeFi protocols for execution
- Machine learning for filter optimization

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE.md](LICENSE.md)

## Disclaimer

This system provides research and analysis only. It does not provide financial advice. Always conduct your own due diligence before trading. Trading prediction markets involves risk. Past performance does not guarantee future results.

Polymarket's Terms of Service prohibit trading by US persons and persons from certain other jurisdictions. Ensure you comply with all applicable laws and regulations.

## Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review data logs in `data/logs/`
3. Open an issue on GitHub
4. Consult the strategy document in `strategy/strategy.md`

---

**Generated with Claude Code** 🤖
