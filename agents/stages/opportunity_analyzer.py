"""Stage 5: Opportunity Analysis & Scoring - Compare model estimates to market prices."""

import logging
from typing import Optional

from agents.config import config
from agents.models import (
    Market,
    Tier2Research,
    Opportunity,
    ConfidenceScore,
    InformationQuality,
    ConfidenceLevel,
)

logger = logging.getLogger(__name__)


class OpportunityAnalyzer:
    """
    Analyzes research results and identifies trading opportunities.

    Process:
    1. Calculate edge (model vs market)
    2. Calculate confidence score
    3. Calculate opportunity score
    4. Identify red/green flags
    5. Generate recommendation
    """

    def __init__(self):
        self.config = config.opportunity

    def analyze_opportunity(self, market: Market, research: Tier2Research) -> Optional[Opportunity]:
        """
        Analyze a market with research to identify trading opportunity.

        Args:
            market: Market object.
            research: Tier 2 research results.

        Returns:
            Opportunity object if viable, None otherwise.
        """
        logger.info(f"Analyzing opportunity for: {market.question}")

        # Calculate edge
        model_prob = research.model_estimate.yes_probability
        market_prob = market.outcome_prices[0]  # Assume first outcome is "YES"
        edge = abs(model_prob - market_prob)

        logger.debug(
            f"Edge calculation: model={model_prob:.2%}, market={market_prob:.2%}, edge={edge:.2%}"
        )

        # Check minimum edge threshold
        if edge < self.config.min_edge_for_report:
            logger.info(f"Edge {edge:.2%} below threshold {self.config.min_edge_for_report:.2%}, skipping")
            return None

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(research)
        logger.debug(f"Confidence score: {confidence_score.overall_score:.2f}")

        # Check minimum confidence
        if confidence_score.overall_score < self.config.min_confidence_score:
            logger.info(
                f"Confidence {confidence_score.overall_score:.2f} below threshold "
                f"{self.config.min_confidence_score:.2f}, skipping"
            )
            return None

        # Calculate liquidity factor
        liquidity_factor = min(1.0, market.liquidity / 10000.0)

        # Calculate opportunity score
        opportunity_score = edge * confidence_score.overall_score * liquidity_factor

        logger.debug(f"Opportunity score: {opportunity_score:.4f}")

        # Check minimum opportunity score
        if opportunity_score < self.config.min_opportunity_score:
            logger.info(
                f"Opportunity score {opportunity_score:.4f} below threshold "
                f"{self.config.min_opportunity_score:.4f}, skipping"
            )
            return None

        # Identify flags
        red_flags = self._identify_red_flags(market, research)
        green_flags = self._identify_green_flags(market, research)

        # Generate recommendation
        recommendation = self._generate_recommendation(model_prob, market_prob, edge, confidence_score)

        # Create opportunity
        opportunity = Opportunity(
            market_id=market.id,
            question=market.question,
            market=market,
            tier2_research=research,
            model_probability=model_prob,
            market_probability=market_prob,
            edge=edge,
            confidence_score=confidence_score,
            liquidity_factor=liquidity_factor,
            opportunity_score=opportunity_score,
            recommended_action=recommendation["action"],
            recommended_outcome=recommendation["outcome"],
            red_flags=red_flags,
            green_flags=green_flags,
            polymarket_url=f"https://polymarket.com/market/{market.id}",
        )

        logger.info(
            f"Opportunity identified: {recommendation['action']} {recommendation['outcome']} "
            f"(score={opportunity_score:.4f}, edge={edge:.2%})"
        )

        return opportunity

    def _calculate_confidence_score(self, research: Tier2Research) -> ConfidenceScore:
        """
        Calculate confidence score based on multiple factors.

        Args:
            research: Research results.

        Returns:
            ConfidenceScore object.
        """
        # 1. Source Quality (0-1)
        avg_source_credibility = (
            sum(s.credibility for s in research.sources) / len(research.sources)
            if research.sources
            else 0
        )
        source_quality = avg_source_credibility / 5.0  # Normalize to 0-1

        # 2. Information Recency (0-1)
        # For now, use information quality as proxy
        info_quality_map = {
            InformationQuality.HIGH: 1.0,
            InformationQuality.MEDIUM: 0.6,
            InformationQuality.LOW: 0.3,
        }
        information_recency = info_quality_map[research.information_quality]

        # 3. Consensus Level (0-1)
        # Check source diversity
        unique_domains = len(set(s.url.split("/")[2] for s in research.sources)) if research.sources else 0
        consensus_level = min(1.0, unique_domains / 5.0)

        # 4. Base Rate Alignment (0-1)
        # For now, use model confidence level as proxy
        confidence_map = {
            ConfidenceLevel.HIGH: 1.0,
            ConfidenceLevel.MEDIUM_HIGH: 0.8,
            ConfidenceLevel.MEDIUM: 0.6,
            ConfidenceLevel.LOW: 0.4,
        }
        base_rate_alignment = confidence_map[research.model_estimate.confidence_level]

        # 5. Reasoning Clarity (0-1)
        # Based on length and structure of reasoning
        reasoning_length = len(research.reasoning)
        if reasoning_length > 1000:
            reasoning_clarity = 1.0
        elif reasoning_length > 500:
            reasoning_clarity = 0.8
        elif reasoning_length > 200:
            reasoning_clarity = 0.6
        else:
            reasoning_clarity = 0.4

        # Calculate weighted overall score
        overall_score = (
            source_quality * self.config.source_quality_weight
            + information_recency * self.config.information_recency_weight
            + consensus_level * self.config.consensus_weight
            + base_rate_alignment * self.config.base_rate_weight
            + reasoning_clarity * self.config.reasoning_clarity_weight
        )

        return ConfidenceScore(
            source_quality=source_quality,
            information_recency=information_recency,
            consensus_level=consensus_level,
            base_rate_alignment=base_rate_alignment,
            reasoning_clarity=reasoning_clarity,
            overall_score=overall_score,
        )

    def _identify_red_flags(self, market: Market, research: Tier2Research) -> list[str]:
        """
        Identify risk factors that should reduce confidence.

        Args:
            market: Market object.
            research: Research results.

        Returns:
            List of red flag descriptions.
        """
        red_flags = []

        # Low source diversity
        if research.sources:
            unique_domains = len(set(s.url.split("/")[2] for s in research.sources))
            if unique_domains < 3:
                red_flags.append(f"Low source diversity (only {unique_domains} unique sources)")

        # High uncertainty
        ci_width = (
            research.model_estimate.confidence_interval_high
            - research.model_estimate.confidence_interval_low
        )
        if ci_width > 0.4:
            red_flags.append(f"Wide confidence interval ({ci_width:.1%})")

        # Low model confidence
        if research.model_estimate.confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM]:
            red_flags.append(f"Low model confidence ({research.model_estimate.confidence_level.value})")

        # Low information quality
        if research.information_quality == InformationQuality.LOW:
            red_flags.append("Low information quality")

        # Resolves very soon
        if market.days_until_resolution and market.days_until_resolution < 7:
            red_flags.append(f"Resolves very soon ({market.days_until_resolution:.1f} days)")

        # High volume markets (harder to beat)
        if market.volume > 100000:
            red_flags.append(f"High volume market (${market.volume:,.0f})")

        return red_flags

    def _identify_green_flags(self, market: Market, research: Tier2Research) -> list[str]:
        """
        Identify positive factors that increase confidence.

        Args:
            market: Market object.
            research: Research results.

        Returns:
            List of green flag descriptions.
        """
        green_flags = []

        # High quality sources
        if research.sources:
            high_quality = sum(1 for s in research.sources if s.credibility >= 4)
            if high_quality >= 3:
                green_flags.append(f"{high_quality} high-quality sources")

        # Good source diversity
        if research.sources:
            unique_domains = len(set(s.url.split("/")[2] for s in research.sources))
            if unique_domains >= 5:
                green_flags.append(f"Good source diversity ({unique_domains} sources)")

        # High model confidence
        if research.model_estimate.confidence_level in [
            ConfidenceLevel.HIGH,
            ConfidenceLevel.MEDIUM_HIGH,
        ]:
            green_flags.append(f"High model confidence ({research.model_estimate.confidence_level.value})")

        # Recent developments
        if research.recent_developments:
            green_flags.append("Recent material developments found")

        # High information quality
        if research.information_quality == InformationQuality.HIGH:
            green_flags.append("High-quality information available")

        # Good liquidity
        if market.liquidity > 10000:
            green_flags.append(f"Good liquidity (${market.liquidity:,.0f})")

        # Multiple convergent findings
        if len(research.key_findings) >= 5:
            green_flags.append(f"{len(research.key_findings)} key findings")

        return green_flags

    def _generate_recommendation(
        self, model_prob: float, market_prob: float, edge: float, confidence: ConfidenceScore
    ) -> dict:
        """
        Generate trading recommendation.

        Args:
            model_prob: Model probability estimate.
            market_prob: Current market price.
            edge: Calculated edge.
            confidence: Confidence score.

        Returns:
            Dictionary with action and outcome.
        """
        # Determine direction
        if model_prob > market_prob:
            action = "BUY"
            outcome = "YES"
            strength = "Strong" if edge > 0.15 and confidence.overall_score > 0.7 else "Moderate"
        else:
            action = "BUY"
            outcome = "NO"
            strength = "Strong" if edge > 0.15 and confidence.overall_score > 0.7 else "Moderate"

        return {
            "action": f"{strength} {action}",
            "outcome": outcome,
        }

    def rank_opportunities(self, opportunities: list[Opportunity]) -> list[Opportunity]:
        """
        Rank opportunities by opportunity score.

        Args:
            opportunities: List of opportunities.

        Returns:
            Sorted list of opportunities (highest score first).
        """
        return sorted(opportunities, key=lambda o: o.opportunity_score, reverse=True)
