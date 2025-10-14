"""Main orchestrator for Polymarket Trading Agent.

This module coordinates all stages of the research and reporting pipeline.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from agents.config import config
from agents.models import DailyRun, Opportunity
from agents.stages.market_fetcher import MarketFetcher
from agents.stages.market_filter import MarketFilter
from agents.stages.tier1_research import Tier1Researcher
from agents.stages.tier2_research import Tier2Researcher
from agents.stages.opportunity_analyzer import OpportunityAnalyzer
from agents.stages.report_generator import ReportGenerator
from agents.stages.email_sender import EmailSender, DataLogger

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrates the daily research workflow.

    Workflow:
    1. Fetch active markets
    2. Apply multi-stage filtering
    3. Tier 1 research (fast context)
    4. Tier 2 research (deep analysis)
    5. Opportunity analysis & scoring
    6. Report generation
    7. Email delivery and logging
    """

    def __init__(self):
        self.market_fetcher = MarketFetcher()
        self.market_filter = MarketFilter()
        self.tier1_researcher = Tier1Researcher()
        self.tier2_researcher = Tier2Researcher()
        self.opportunity_analyzer = OpportunityAnalyzer()
        self.report_generator = ReportGenerator()
        self.email_sender = EmailSender()
        self.data_logger = DataLogger()

        self.current_run: Optional[DailyRun] = None

    def run_daily_analysis(self) -> DailyRun:
        """
        Execute the complete daily analysis workflow.

        Returns:
            DailyRun object with results.
        """
        start_time = time.time()
        run_date = datetime.now(timezone.utc)

        logger.info("=" * 80)
        logger.info(f"Starting daily analysis run: {run_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info("=" * 80)

        errors = []
        opportunities = []

        try:
            # Stage 1: Fetch Markets
            stage_start = time.time()
            logger.info("\n[STAGE 1] Fetching markets...")
            markets = self.market_fetcher.fetch_all_markets()
            stage_duration = time.time() - stage_start
            logger.info(f"✓ Stage 1 complete: {len(markets)} markets fetched ({stage_duration:.1f}s)")

            # Stage 2: Filter Markets
            stage_start = time.time()
            logger.info("\n[STAGE 2] Filtering markets...")
            filtered_markets = self.market_filter.filter_markets(markets)
            stage_duration = time.time() - stage_start

            # Limit to configured maximum
            max_markets = config.scheduler.max_markets_to_filter
            if len(filtered_markets) > max_markets:
                logger.info(f"Limiting to {max_markets} markets (from {len(filtered_markets)})")
                # Sort by volume and take top N
                filtered_markets = sorted(filtered_markets, key=lambda m: m.volume, reverse=True)[:max_markets]

            logger.info(f"✓ Stage 2 complete: {len(filtered_markets)} markets after filtering ({stage_duration:.1f}s)")

            # Stage 3: Tier 1 Research
            stage_start = time.time()
            logger.info(f"\n[STAGE 3] Tier 1 research on {len(filtered_markets)} markets...")
            tier1_results = []

            for i, market in enumerate(filtered_markets, 1):
                try:
                    logger.info(f"  [{i}/{len(filtered_markets)}] Researching: {market.question[:60]}...")
                    result = self.tier1_researcher.research_market(market)
                    tier1_results.append((market, result))
                except Exception as e:
                    error_msg = f"Tier 1 research failed for market {market.id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Filter for Tier 2 candidates
            tier2_candidates = [
                (market, result) for market, result in tier1_results if result.proceed_to_tier2
            ]

            stage_duration = time.time() - stage_start
            logger.info(
                f"✓ Stage 3 complete: {len(tier2_candidates)} markets selected for deep research ({stage_duration:.1f}s)"
            )

            # Stage 4: Tier 2 Research
            stage_start = time.time()
            max_deep = config.scheduler.max_markets_for_deep_research

            if len(tier2_candidates) > max_deep:
                logger.info(f"Limiting deep research to {max_deep} markets")
                # Sort by preliminary edge if available
                tier2_candidates = sorted(
                    tier2_candidates,
                    key=lambda x: x[1].preliminary_edge or 0,
                    reverse=True,
                )[:max_deep]

            logger.info(f"\n[STAGE 4] Tier 2 deep research on {len(tier2_candidates)} markets...")
            tier2_results = []

            for i, (market, tier1_result) in enumerate(tier2_candidates, 1):
                try:
                    logger.info(f"  [{i}/{len(tier2_candidates)}] Deep research: {market.question[:60]}...")
                    result = self.tier2_researcher.research_market(market)
                    tier2_results.append((market, result))
                except Exception as e:
                    error_msg = f"Tier 2 research failed for market {market.id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            stage_duration = time.time() - stage_start
            logger.info(f"✓ Stage 4 complete: {len(tier2_results)} markets researched deeply ({stage_duration:.1f}s)")

            # Stage 5: Opportunity Analysis
            stage_start = time.time()
            logger.info(f"\n[STAGE 5] Analyzing {len(tier2_results)} opportunities...")

            for market, research in tier2_results:
                try:
                    opportunity = self.opportunity_analyzer.analyze_opportunity(market, research)
                    if opportunity:
                        opportunities.append(opportunity)
                except Exception as e:
                    error_msg = f"Opportunity analysis failed for market {market.id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Rank opportunities
            opportunities = self.opportunity_analyzer.rank_opportunities(opportunities)

            stage_duration = time.time() - stage_start
            logger.info(f"✓ Stage 5 complete: {len(opportunities)} opportunities identified ({stage_duration:.1f}s)")

            # Stage 6: Report Generation
            stage_start = time.time()
            logger.info("\n[STAGE 6] Generating report...")

            total_duration = time.time() - start_time
            estimated_cost = self._estimate_cost(len(filtered_markets), len(tier2_results))

            html_report = self.report_generator.generate_report(
                opportunities=opportunities,
                run_date=run_date,
                runtime_seconds=total_duration,
                total_markets_analyzed=len(filtered_markets),
                estimated_cost=estimated_cost,
                errors=errors,
            )

            stage_duration = time.time() - stage_start
            logger.info(f"✓ Stage 6 complete: Report generated ({stage_duration:.1f}s)")

            # Stage 7: Email Delivery
            stage_start = time.time()
            logger.info("\n[STAGE 7] Sending email report...")

            subject = f"Polymarket Research Report - {run_date.strftime('%Y-%m-%d')} - {len(opportunities)} Opportunities"

            email_sent = self.email_sender.send_report(
                html_content=html_report,
                subject=subject,
            )

            if email_sent:
                logger.info(f"✓ Stage 7 complete: Email sent ({time.time() - stage_start:.1f}s)")
            else:
                error_msg = "Failed to send email report"
                logger.error(error_msg)
                errors.append(error_msg)

        except Exception as e:
            error_msg = f"Critical error in daily analysis: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)

        # Create daily run record
        total_duration = time.time() - start_time

        daily_run = DailyRun(
            run_date=run_date,
            run_start_time=run_date,
            run_end_time=datetime.now(timezone.utc),
            markets_fetched=len(markets) if 'markets' in locals() else 0,
            markets_after_filtering=len(filtered_markets) if 'filtered_markets' in locals() else 0,
            markets_tier1_researched=len(tier1_results) if 'tier1_results' in locals() else 0,
            markets_tier2_researched=len(tier2_results) if 'tier2_results' in locals() else 0,
            opportunities_identified=len(opportunities),
            total_cost=estimated_cost if 'estimated_cost' in locals() else 0,
            opportunities=opportunities,
            errors=errors,
            timing={
                "total_duration": total_duration,
            },
        )

        # Log to file
        try:
            self.data_logger.log_daily_run(daily_run.model_dump())
        except Exception as e:
            logger.error(f"Failed to log daily run data: {e}")

        logger.info("\n" + "=" * 80)
        logger.info(f"Daily analysis complete!")
        logger.info(f"Total duration: {total_duration/60:.1f} minutes")
        logger.info(f"Opportunities found: {len(opportunities)}")
        logger.info(f"Errors: {len(errors)}")
        logger.info("=" * 80 + "\n")

        return daily_run

    def _estimate_cost(self, tier1_count: int, tier2_count: int) -> float:
        """
        Estimate API costs for the run.

        Args:
            tier1_count: Number of Tier 1 researches.
            tier2_count: Number of Tier 2 researches.

        Returns:
            Estimated cost in USD.
        """
        # Rough estimates based on token usage
        # Tier 1: ~2000 tokens @ $0.80/1M input + $4/1M output (Claude 3.5 Haiku) = ~$0.002 per market
        # Tier 2: ~8000 tokens @ $3/1M input + $15/1M output (Claude 3.5 Sonnet) = ~$0.04 per market
        # Tavily: ~$0.001 per search

        tier1_llm_cost = tier1_count * 0.002
        tier1_search_cost = tier1_count * 3 * 0.001  # 3 searches per market

        tier2_llm_cost = tier2_count * 0.04
        tier2_search_cost = tier2_count * 8 * 0.001  # 8 searches per market

        total = tier1_llm_cost + tier1_search_cost + tier2_llm_cost + tier2_search_cost

        return round(total, 2)
