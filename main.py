#!/usr/bin/env python3
"""
Polymarket Trading Agent - Main Entry Point

This agent performs daily automated research on Polymarket prediction markets
and identifies potential trading opportunities.

Usage:
    python main.py                  # Run once and exit
    python main.py --schedule       # Run on daily schedule
    python main.py --test           # Test mode (limited markets)
"""

import argparse
import logging
import sys
from pathlib import Path

from agents.config import config
from agents.scheduler import DailyScheduler


def setup_logging():
    """Configure logging for the application."""
    # Create logs directory
    log_dir = Path(config.logging.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        fmt='%(levelname)s: %(message)s'
    )

    # File handler (detailed logs)
    from datetime import datetime
    log_file = log_dir / f"{config.logging.log_file_prefix}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Console handler (simple logs)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.WARNING)

    return root_logger


def validate_config():
    """Validate required configuration."""
    errors = []

    # Check API keys
    if not config.api.anthropic_api_key:
        errors.append("ANTHROPIC_API_KEY not set")

    if not config.api.tavily_api_key:
        errors.append("TAVILY_API_KEY not set")

    # Check email config (only for scheduled runs)
    if not all([
        config.api.email_smtp_username,
        config.api.email_smtp_password,
        config.api.email_from,
        config.api.email_to,
    ]):
        logging.warning(
            "Email configuration incomplete. Email reports will not be sent. "
            "Set EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD, EMAIL_FROM, and EMAIL_TO environment variables."
        )

    if errors:
        logging.error("Configuration errors:")
        for error in errors:
            logging.error(f"  - {error}")
        return False

    return True


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Polymarket Trading Agent - Automated market research and opportunity identification'
    )
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run on daily schedule (default: run once and exit)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode (limit to 5 markets for faster testing)'
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging()

    logger.info("=" * 80)
    logger.info("Polymarket Trading Agent")
    logger.info("=" * 80)

    # Validate configuration
    if not validate_config():
        logger.error("Configuration validation failed. Exiting.")
        sys.exit(1)

    # Apply test mode settings
    if args.test:
        logger.info("\n*** TEST MODE ENABLED ***")
        logger.info("Limiting to 5 markets for faster testing\n")
        config.scheduler.max_markets_to_filter = 5
        config.scheduler.max_markets_for_deep_research = 3

    # Create scheduler
    scheduler = DailyScheduler()

    try:
        if args.schedule:
            # Run on schedule
            logger.info("Starting scheduled mode...")
            scheduler.start()
        else:
            # Run once
            logger.info("Running single analysis...")
            result = scheduler.run_once()

            # Print summary
            print("\n" + "=" * 80)
            print("ANALYSIS COMPLETE")
            print("=" * 80)
            print(f"Markets fetched: {result.markets_fetched}")
            print(f"Markets filtered: {result.markets_after_filtering}")
            print(f"Tier 1 researched: {result.markets_tier1_researched}")
            print(f"Tier 2 researched: {result.markets_tier2_researched}")
            print(f"Opportunities found: {result.opportunities_identified}")
            print(f"Total cost: ${result.total_cost:.2f}")

            if result.opportunities:
                print("\nTop Opportunities:")
                for i, opp in enumerate(result.opportunities[:5], 1):
                    print(f"\n{i}. {opp.question[:70]}...")
                    print(f"   Edge: {opp.edge:.1%} | Score: {opp.opportunity_score:.4f}")
                    print(f"   {opp.recommended_action} {opp.recommended_outcome}")

            if result.errors:
                print(f"\nErrors encountered: {len(result.errors)}")

            print("=" * 80 + "\n")

    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
