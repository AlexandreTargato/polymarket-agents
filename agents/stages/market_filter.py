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
        Apply all filters sequentially to narrow down markets.

        Args:
            markets: List of all markets.

        Returns:
            List of filtered markets (15-25 expected).
        """
        logger.info(f"Starting filtering with {len(markets)} markets")

        # Filter 1: Volume & Liquidity
        markets = self._filter_volume_liquidity(markets)
        logger.info(f"After volume & liquidity filter: {len(markets)} markets")

        # Filter 2: Time Horizon
        markets = self._filter_time_horizon(markets)
        logger.info(f"After time horizon filter: {len(markets)} markets")

        # Filter 3: Category Selection
        markets = self._filter_categories(markets)
        logger.info(f"After category filter: {len(markets)} markets")

        # Filter 4: Question Type
        markets = self._filter_question_type(markets)
        logger.info(f"After question type filter: {len(markets)} markets")

        # Filter 5: Market Maturity
        markets = self._filter_market_maturity(markets)
        logger.info(f"After market maturity filter: {len(markets)} markets")

        logger.info(f"Filtering complete: {len(markets)} markets remain")
        return markets

    def _filter_volume_liquidity(self, markets: list[Market]) -> list[Market]:
        """
        Filter 1: Volume & Liquidity

        Requirements:
        - Minimum volume: $10,000
        - Minimum liquidity: $5,000
        """
        filtered = [
            m
            for m in markets
            if m.volume >= self.config.min_volume and m.liquidity >= self.config.min_liquidity
        ]

        logger.debug(
            f"Volume & Liquidity: {len(filtered)}/{len(markets)} passed "
            f"(min_volume=${self.config.min_volume}, min_liquidity=${self.config.min_liquidity})"
        )

        return filtered

    def _filter_time_horizon(self, markets: list[Market]) -> list[Market]:
        """
        Filter 2: Time Horizon

        Requirements:
        - Resolves in 7-30 days
        - Avoid <7 days (too little time) or >30 days (too much uncertainty)
        """
        filtered = []
        for m in markets:
            if m.days_until_resolution is None:
                continue

            if (
                self.config.min_resolution_days
                <= m.days_until_resolution
                <= self.config.max_resolution_days
            ):
                filtered.append(m)

        logger.debug(
            f"Time Horizon: {len(filtered)}/{len(markets)} passed "
            f"({self.config.min_resolution_days}-{self.config.max_resolution_days} days)"
        )

        return filtered

    def _filter_categories(self, markets: list[Market]) -> list[Market]:
        """
        Filter 3: Category Selection

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
        Filter 4: Question Type

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

    def _filter_market_maturity(self, markets: list[Market]) -> list[Market]:
        """
        Filter 5: Market Maturity

        Prefer: Markets open for 24-72 hours
        Avoid: Brand new (<12 hours) or stale (>2 weeks old)

        Rationale: New markets may not have found equilibrium; old markets likely efficient
        """
        filtered = []
        for m in markets:
            if m.age_hours is None:
                # If we don't know age, be conservative and skip
                # (unless we want to include them by default)
                continue

            if self.config.min_market_age_hours <= m.age_hours <= self.config.max_market_age_hours:
                filtered.append(m)

        logger.debug(
            f"Market Maturity: {len(filtered)}/{len(markets)} passed "
            f"({self.config.min_market_age_hours}-{self.config.max_market_age_hours} hours)"
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
            "retention_rate": filtered_count / original_count if original_count > 0 else 0,
            "config": {
                "min_volume": self.config.min_volume,
                "min_liquidity": self.config.min_liquidity,
                "resolution_days": f"{self.config.min_resolution_days}-{self.config.max_resolution_days}",
                "market_age_hours": f"{self.config.min_market_age_hours}-{self.config.max_market_age_hours}",
                "focus_categories": self.config.focus_categories,
                "exclude_categories": self.config.exclude_categories,
            },
        }
