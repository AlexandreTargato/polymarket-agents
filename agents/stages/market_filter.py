"""Stage 2: Multi-Stage Filtering - Filter markets for research potential."""

import logging

from agents.config import config
from agents.models import Market

logger = logging.getLogger(__name__)


class MarketFilter:
    """
    Applies multi-stage filtering to narrow down markets worth researching.

    Filters markets based on:
    1. Category Selection
    2. Question Type
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

        logger.info(f"Filtering complete: {len(markets)} markets remain")
        return markets

    def _filter_categories(self, markets: list[Market]) -> list[Market]:
        """
        Filter 1: Category Selection

        Focus on: Politics, Business, Technology, Regulatory
        Exclude: Sports, Crypto, Entertainment
        """
        filtered = []
        for market in markets:
            # If no category, try to infer or skip
            if not market.category:
                # Skip markets with unknown category to be conservative
                continue

            # Exclude unwanted categories
            if market.category in self.config.exclude_categories:
                continue

            # If we have focus categories, only include those
            if self.config.focus_categories:
                if market.category in self.config.focus_categories:
                    filtered.append(m)
            else:
                # If no focus categories specified, include all non-excluded
                filtered.append(market)

        logger.debug(
            f"Category: {len(filtered)}/{len(markets)} passed "
            f"(focus={self.config.focus_categories}, exclude={self.config.exclude_categories})"
        )

        return filtered

    def _filter_question_type(self, markets: list[Market]) -> list[Market]:
        """
        TODO: Implement this filter

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
        return markets
