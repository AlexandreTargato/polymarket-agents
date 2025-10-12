#!/usr/bin/env python3
"""
Setup Script for Human-in-the-Loop Trading System

This script helps you set up the human-in-the-loop trading system
with email notifications and web interface.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

def setup_environment():
    """Set up the environment for human-in-the-loop trading"""
    print("🚀 Setting up Human-in-the-Loop Trading System")
    print("=" * 50)
    
    # Check required environment variables
    required_vars = [
        'PERPLEXITY_API_KEY',
        'POLYGON_WALLET_PRIVATE_KEY'
    ]
    
    optional_vars = [
        'OPENAI_API_KEY',
        'EMAIL_USER',
        'EMAIL_PASSWORD',
        'EMAIL_RECIPIENT'
    ]
    
    print("\n📋 Checking Environment Variables:")
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Missing (REQUIRED)")
            missing_required.append(var)
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"⚠️  {var}: Missing (Optional)")
            missing_optional.append(var)
    
    if missing_required:
        print(f"\n❌ Missing required variables: {', '.join(missing_required)}")
        print("Please add these to your .env file before continuing.")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional variables: {', '.join(missing_optional)}")
        print("These are recommended for full functionality.")
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating Directories:")
    
    directories = [
        "logs",
        "logs/daily_results",
        "research_cache",
        "scripts/python/templates"
    ]
    
    for directory in directories:
        dir_path = Path(__file__).parent.parent.parent / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")

def create_cron_script():
    """Create a cron script for daily execution"""
    print("\n⏰ Creating Daily Cron Script:")
    
    cron_script = """#!/bin/bash
# Daily Trading Analysis Cron Job
# Add this to your crontab: 0 8 * * * /path/to/this/script

cd /Users/valentinhenryleo/polymarket-agents
source .venv/bin/activate  # Adjust path if needed

# Run daily analysis
python scripts/python/daily_scheduler.py --email your-email@example.com

# Log the execution
echo "$(date): Daily trading analysis completed" >> logs/cron.log
"""
    
    cron_path = Path(__file__).parent.parent.parent / "scripts" / "bash" / "daily_trading_cron.sh"
    cron_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(cron_path, 'w') as f:
        f.write(cron_script)
    
    # Make executable
    os.chmod(cron_path, 0o755)
    
    print(f"✅ Created: {cron_path}")
    print("   To set up daily execution at 8 AM:")
    print(f"   crontab -e")
    print(f"   Add: 0 8 * * * {cron_path}")

def create_config_file():
    """Create configuration file for the system"""
    print("\n⚙️  Creating Configuration File:")
    
    config = {
        "human_in_the_loop": {
            "email_recipient": os.getenv('EMAIL_RECIPIENT', 'your-email@example.com'),
            "max_markets": 10,
            "min_confidence": 5,
            "min_edge": 0.05,
            "daily_analysis_time": "08:00",
            "web_interface_port": 5000,
            "web_interface_host": "127.0.0.1"
        },
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "user": os.getenv('EMAIL_USER', ''),
            "password": os.getenv('EMAIL_PASSWORD', '')
        },
        "research": {
            "cost_per_call": 0.17,
            "cache_hours": 24,
            "max_retries": 3
        },
        "trading": {
            "max_position_size": 0.20,
            "max_total_allocation": 0.80,
            "min_volume_24h": 1000,
            "min_days_to_resolution": 1,
            "max_days_to_resolution": 90
        }
    }
    
    config_path = Path(__file__).parent.parent.parent / "config" / "human_in_the_loop.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"✅ Created: {config_path}")

def create_readme():
    """Create README for the human-in-the-loop system"""
    print("\n📖 Creating Documentation:")
    
    readme_content = """# Human-in-the-Loop Trading System

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
"""
    
    readme_path = Path(__file__).parent.parent.parent / "HUMAN_IN_THE_LOOP_README.md"
    
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"✅ Created: {readme_path}")

def test_system():
    """Test the system setup"""
    print("\n🧪 Testing System Setup:")
    
    try:
        # Test imports
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from scripts.python.human_in_the_loop_trader import HumanInTheLoopTrader
        
        print("✅ Core modules import successfully")
        
        # Test trader initialization
        trader = HumanInTheLoopTrader(email_recipient="test@example.com")
        print("✅ Trader initialization successful")
        
        # Test market discovery
        markets = trader.discover_top_markets()
        print(f"✅ Market discovery: Found {len(markets)} markets")
        
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("Human-in-the-Loop Trading System Setup")
    print("=" * 40)
    
    # Step 1: Check environment
    if not setup_environment():
        print("\n❌ Setup failed: Missing required environment variables")
        return False
    
    # Step 2: Create directories
    create_directories()
    
    # Step 3: Create cron script
    create_cron_script()
    
    # Step 4: Create config file
    create_config_file()
    
    # Step 5: Create documentation
    create_readme()
    
    # Step 6: Test system
    if test_system():
        print("\n🎉 Setup Complete!")
        print("\nNext Steps:")
        print("1. Add your email credentials to .env file")
        print("2. Run: python scripts/python/human_in_the_loop_trader.py --email your-email@example.com")
        print("3. Start web interface: python scripts/python/web_interface.py --email your-email@example.com")
        print("4. Set up daily cron job for automation")
        return True
    else:
        print("\n❌ Setup completed with errors. Check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
