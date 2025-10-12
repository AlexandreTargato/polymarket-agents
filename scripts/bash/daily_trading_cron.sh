#!/bin/bash
# Daily Trading Analysis Cron Job
# Add this to your crontab: 0 8 * * * /path/to/this/script

cd /Users/valentinhenryleo/polymarket-agents
source .venv/bin/activate  # Adjust path if needed

# Run daily analysis
python scripts/python/daily_scheduler.py --email your-email@example.com

# Log the execution
echo "$(date): Daily trading analysis completed" >> logs/cron.log
