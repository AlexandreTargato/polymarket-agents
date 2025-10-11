"""Daily scheduler for automated runs."""

import logging
import time
import schedule
from datetime import datetime

from agents.config import config
from agents.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class DailyScheduler:
    """
    Schedules and runs daily analysis.

    Default: Run at 8:00 AM, send email at 9:00 AM
    """

    def __init__(self):
        self.orchestrator = Orchestrator()
        self.cron_hour = config.scheduler.cron_hour
        self.cron_minute = config.scheduler.cron_minute

    def start(self):
        """Start the scheduler and run indefinitely."""
        logger.info("=" * 80)
        logger.info("Polymarket Trading Agent Scheduler Started")
        logger.info(f"Scheduled daily run: {self.cron_hour:02d}:{self.cron_minute:02d}")
        logger.info("=" * 80)

        # Schedule daily run
        schedule_time = f"{self.cron_hour:02d}:{self.cron_minute:02d}"
        schedule.every().day.at(schedule_time).do(self._run_daily_job)

        logger.info(f"\nWaiting for next scheduled run at {schedule_time}...")
        logger.info("Press Ctrl+C to stop\n")

        # Run immediately for testing (comment out for production)
        # logger.info("Running immediately for testing...")
        # self._run_daily_job()

        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("\nScheduler stopped by user")

    def _run_daily_job(self):
        """Execute the daily analysis job."""
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Scheduled job triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'=' * 80}\n")

        try:
            result = self.orchestrator.run_daily_analysis()
            logger.info(f"Daily job completed successfully")
            logger.info(f"Opportunities identified: {result.opportunities_identified}")
            logger.info(f"Total cost: ${result.total_cost:.2f}")

            return result

        except Exception as e:
            logger.error(f"Daily job failed: {e}", exc_info=True)

    def run_once(self):
        """Run the analysis once (for testing/manual execution)."""
        logger.info("Running analysis once...")
        return self.orchestrator.run_daily_analysis()
