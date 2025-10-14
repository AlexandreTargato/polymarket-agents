"""Stage 1: Market Fetching - Retrieve active markets from Polymarket."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
import httpx
import json


from agents.config import config
from agents.models import Market

logger = logging.getLogger(__name__)


class MarketFetcher:
    """Fetches active markets from Polymarket API."""

    def __init__(self):
        self.gamma_url = config.polymarket.gamma_url
        self.markets_endpoint = f"{self.gamma_url}/markets"
        self.timeout = 30.0

    def fetch_all_markets(self) -> list[Market]:
        """
        Fetch filtered markets from Polymarket API using query parameters.

        Returns:
            List of Market objects.
        """
        logger.info("Fetching filtered markets from Polymarket API...")

        start_date_min = (
            datetime.now(timezone.utc)
            - timedelta(days=config.filter.max_market_age_days)
        ).isoformat()
        start_date_max = (
            datetime.now(timezone.utc)
            - timedelta(days=config.filter.min_market_age_days)
        ).isoformat()
        min_resolution_date = (
            datetime.now(timezone.utc)
            + timedelta(days=config.filter.min_resolution_days)
        ).isoformat()
        max_resolution_date = (
            datetime.now(timezone.utc)
            + timedelta(days=config.filter.max_resolution_days)
        ).isoformat()

        params = {
            "closed": "false",  # Only active markets
            "end_date_min": min_resolution_date,
            "end_date_max": max_resolution_date,
            "limit": 100,  # Get up to 100 markets
            "liquidity_num_min": config.filter.min_liquidity,
            "volume_num_min": config.filter.min_volume,  # Filter by volume
            "start_date_min": start_date_min,
            "start_date_max": start_date_max,
        }

        # Note: liquidity_num_min and order parameters don't seem to work with the API
        # We'll do liquidity filtering and ordering in Python

        try:
            response = httpx.get(
                self.markets_endpoint, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            markets = []
            for market_data in data:
                try:
                    market = self._parse_market(market_data)
                    if market:
                        markets.append(market)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse market {market_data.get('id')}: {e}"
                    )
                    continue

            logger.info(
                f"Successfully fetched {len(markets)} markets (filtered by API)"
            )
            return markets

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching markets: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching markets: {e}")
            raise

    def _parse_market(self, data: dict) -> Optional[Market]:
        """
        Parse raw market data from API into Market model.

        Args:
            data: Raw market data from API.

        Returns:
            Market object or None if parsing fails.
        """
        try:
            # Extract basic fields
            market_id = str(data.get("id"))
            question = data.get("question", "")
            description = data.get("description", "")
            active = data.get("active", False)
            closed = data.get("closed", True)

            # Skip inactive or closed markets
            if not active or closed:
                return None

            # Parse dates
            end_date = self._parse_date(data.get("endDate"))
            start_date = self._parse_date(data.get("startDate"))

            if not end_date:
                logger.debug(f"Market {market_id} has no end date, skipping")
                return None

            # Extract metrics - use numeric versions if available
            volume = float(data.get("volumeNum", data.get("volume", 0)))
            liquidity = float(data.get("liquidityNum", data.get("liquidity", 0)))

            # Extract outcomes - handle both string and list formats
            outcomes_raw = data.get("outcomes", [])
            if isinstance(outcomes_raw, str):
                try:
                    outcomes = json.loads(outcomes_raw)
                except json.JSONDecodeError:
                    logger.debug(
                        f"Market {market_id} has invalid outcomes JSON, skipping"
                    )
                    return None
            else:
                outcomes = outcomes_raw

            if not outcomes or not isinstance(outcomes, list):
                logger.debug(f"Market {market_id} has invalid outcomes, skipping")
                return None

            # Extract outcome prices - handle both string and list formats
            outcome_prices_raw = data.get("outcomePrices", [])
            if isinstance(outcome_prices_raw, str):
                try:
                    outcome_prices = json.loads(outcome_prices_raw)
                except json.JSONDecodeError:
                    logger.debug(
                        f"Market {market_id} has invalid outcome prices JSON, skipping"
                    )
                    return None
            else:
                outcome_prices = outcome_prices_raw

            if not outcome_prices or len(outcome_prices) != len(outcomes):
                logger.debug(
                    f"Market {market_id} has mismatched outcome prices, skipping"
                )
                return None

            # Convert outcome prices to floats
            outcome_prices = [float(price) for price in outcome_prices]

            # Extract token IDs - handle both string and list formats
            clob_token_ids_raw = data.get("clobTokenIds", [])
            if isinstance(clob_token_ids_raw, str):
                # Parse JSON string

                try:
                    clob_token_ids = json.loads(clob_token_ids_raw)
                except json.JSONDecodeError:
                    logger.debug(
                        f"Market {market_id} has invalid token IDs JSON, skipping"
                    )
                    return None
            else:
                clob_token_ids = clob_token_ids_raw

            if not clob_token_ids:
                logger.debug(f"Market {market_id} has no token IDs, skipping")
                return None

            clob_token_ids = [str(token_id) for token_id in clob_token_ids]

            # Calculate age and time to resolution
            now = datetime.now(timezone.utc)
            age_hours = None
            if start_date:
                age_hours = (now - start_date).total_seconds() / 3600

            days_until_resolution = (end_date - now).total_seconds() / 86400

            # Create market object
            market = Market(
                id=market_id,
                question=question,
                description=description,
                end_date=end_date,
                start_date=start_date,
                volume=volume,
                liquidity=liquidity,
                active=active,
                outcomes=outcomes,
                outcome_prices=outcome_prices,
                clob_token_ids=clob_token_ids,
                category=self._extract_category(data),
                tags=data.get("tags", []),
                resolution_source=data.get("resolutionSource"),
                age_hours=age_hours,
                days_until_resolution=days_until_resolution,
            )

            return market

        except Exception as e:
            logger.debug(f"Error parsing market: {e}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse date string to datetime object.

        Args:
            date_str: ISO format date string.

        Returns:
            datetime object or None.
        """
        if not date_str:
            return None

        try:
            # Try parsing ISO format with timezone
            if date_str.endswith("Z"):
                date_str = date_str[:-1] + "+00:00"

            dt = datetime.fromisoformat(date_str)

            # Ensure timezone aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return dt

        except Exception as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
            return None

    def _extract_category(self, data: dict) -> Optional[str]:
        """
        Extract category from market data.

        Args:
            data: Raw market data.

        Returns:
            Category string or None.
        """
        # First try to get category directly from the data
        category = data.get("tags")
        if category:
            return category

        # Try to get category from events
        events = data.get("events", [])
        if events and isinstance(events, list) and len(events) > 0:
            event = events[0]
            if isinstance(event, dict):
                event_category = event.get("category")
                if event_category:
                    return event_category

        # Try to get category from tags
        tags = data.get("tags", [])
        if tags and isinstance(tags, list) and len(tags) > 0:
            if isinstance(tags[0], dict):
                return tags[0].get("label")
            return str(tags[0])

        # Try to infer category from question
        question = data.get("question", "").lower()

        if any(
            keyword in question
            for keyword in [
                "election",
                "president",
                "congress",
                "senate",
                "vote",
                "biden",
                "trump",
                "republican",
                "democrat",
            ]
        ):
            return "Politics"
        elif any(
            keyword in question
            for keyword in [
                "company",
                "stock",
                "ceo",
                "earnings",
                "revenue",
                "fed",
                "recession",
                "economy",
            ]
        ):
            return "Business"
        elif any(
            keyword in question
            for keyword in [
                "technology",
                "ai",
                "software",
                "tech",
                "openai",
                "google",
                "apple",
            ]
        ):
            return "Technology"
        elif any(
            keyword in question
            for keyword in [
                "regulation",
                "sec",
                "fda",
                "law",
                "legal",
                "court",
                "supreme",
            ]
        ):
            return "Regulatory"
        elif any(
            keyword in question
            for keyword in [
                "bitcoin",
                "ethereum",
                "crypto",
                "btc",
                "eth",
                "tether",
                "usdt",
            ]
        ):
            return "Crypto"
        elif any(
            keyword in question
            for keyword in [
                "game",
                "match",
                "championship",
                "tournament",
                "soccer",
                "football",
                "basketball",
            ]
        ):
            return "Sports"

        return None

    def get_market_by_id(self, market_id: str) -> Optional[Market]:
        """
        Fetch a specific market by ID.

        Args:
            market_id: Market ID.

        Returns:
            Market object or None.
        """
        try:
            params = {"id": market_id}
            response = httpx.get(
                self.markets_endpoint, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if not data or len(data) == 0:
                return None

            return self._parse_market(data[0])

        except Exception as e:
            logger.error(f"Error fetching market {market_id}: {e}")
            return None
