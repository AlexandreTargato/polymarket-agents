"""Stage 2: Multi-Stage Filtering - Filter markets for research potential."""

import logging
from typing import Optional

from agents.config import config
from agents.models import Market

logger = logging.getLogger(__name__)


class MarketFilter:
    """
    Applies multi-stage filtering to narrow down markets worth researching.

    Filters markets based on:
    1. Volume & Liquidity
    2. Time Horizon
    3. Category Selection
    4. Question Type
    5. Market Maturity
    """

    def __init__(self):
        self.config = config.filter

    def filter_markets(self, markets: list[Market]) -> list[Market]:
        """
        Apply filters that can't be done via API parameters.

        Args:
            markets: List of markets from API (already filtered for active/closed status).

        Returns:
            List of filtered markets (15-25 expected).
        """
        logger.info(f"Starting filtering with {len(markets)} markets")

        # Filter 1: Category Selection (can't be done via API)
        markets = self._filter_categories(markets)
        logger.info(f"After category filter: {len(markets)} markets")

        # Filter 2: Question Type (can't be done via API)
        markets = self._filter_question_type(markets)
        logger.info(f"After question type filter: {len(markets)} markets")

        logger.info(f"Filtering complete: {len(markets)} markets remain")
        return markets

    def _filter_categories(self, markets: list[Market]) -> list[Market]:
        """
        Filter 1: Category Selection

        Focus on: Politics, Business, Technology, Regulatory
        Exclude: Sports, Crypto, Entertainment
        """
        filtered = []
        for m in markets:
            # If no category, try to infer or skip
            if not m.category:
                # Skip markets with unknown category to be conservative
                continue

            # Exclude unwanted categories
            if m.category in self.config.exclude_categories:
                continue

            # If we have focus categories, only include those
            if self.config.focus_categories:
                if m.category in self.config.focus_categories:
                    filtered.append(m)
            else:
                # If no focus categories specified, include all non-excluded
                filtered.append(m)

        logger.debug(
            f"Category: {len(filtered)}/{len(markets)} passed "
            f"(focus={self.config.focus_categories}, exclude={self.config.exclude_categories})"
        )

        return filtered

    def _filter_question_type(self, markets: list[Market]) -> list[Market]:
        """
        Filter 2: Question Type

        Prefer:
        - Binary outcomes
        - Factual resolutions
        - Objective criteria

        Exclude:
        - Multiple choice with >4 options
        - Subjective resolution criteria
        - Entertainment/celebrity questions
        """
        filtered = []
        for m in markets:
            # Check number of outcomes
            if len(m.outcomes) > self.config.max_outcomes:
                continue

            # Check for subjective keywords in question
            question_lower = m.question.lower()
            subjective_keywords = [
                "best",
                "greatest",
                "favorite",
                "opinion",
                "popular",
                "trending",
                "celebrity",
                "famous",
            ]

            if any(keyword in question_lower for keyword in subjective_keywords):
                continue

            # Check for entertainment keywords
            entertainment_keywords = [
                "movie",
                "film",
                "actor",
                "actress",
                "album",
                "song",
                "grammy",
                "oscar",
                "emmy",
            ]

            if any(keyword in question_lower for keyword in entertainment_keywords):
                continue

            # Prefer binary outcomes but allow up to max_outcomes
            filtered.append(m)

        logger.debug(
            f"Question Type: {len(filtered)}/{len(markets)} passed "
            f"(max_outcomes={self.config.max_outcomes})"
        )

        return filtered

    def get_filter_stats(self, original_count: int, filtered_count: int) -> dict:
        """
        Get filtering statistics.

        Args:
            original_count: Number of markets before filtering.
            filtered_count: Number of markets after filtering.

        Returns:
            Dictionary with filter statistics.
        """
        return {
            "original_count": original_count,
            "filtered_count": filtered_count,
            "filtered_out": original_count - filtered_count,
            "retention_rate": (
                filtered_count / original_count if original_count > 0 else 0
            ),
            "config": {
                "min_volume": self.config.min_volume,
                "min_liquidity": self.config.min_liquidity,
                "resolution_days": f"{self.config.min_resolution_days}-{self.config.max_resolution_days}",
                "market_age_hours": f"{self.config.min_market_age_hours}-{self.config.max_market_age_hours}",
                "focus_categories": self.config.focus_categories,
                "exclude_categories": self.config.exclude_categories,
            },
        }
