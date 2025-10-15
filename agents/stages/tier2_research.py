"""Stage 4: Tier 2 Research - Deep analysis for promising markets."""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

import anthropic
from tavily import TavilyClient

from agents.config import config
from agents.models import (
    Market,
    Tier2Research,
    Source,
    ResearchFinding,
    ProbabilityEstimate,
    ConfidenceLevel,
    InformationQuality,
)

logger = logging.getLogger(__name__)


class Tier2Researcher:
    """
    Performs deep research (5-10 minutes per market).

    Process:
    1. Comprehensive information gathering (5-8 queries)
    2. Deep analysis with premium LLM
    3. Probability estimation with confidence intervals
    4. Source quality assessment
    5. Contrarian analysis
    """

    def __init__(self):
        self.config = config.research
        self.anthropic_client = anthropic.Anthropic(
            api_key=config.api.anthropic_api_key
        )
        self.tavily_client = TavilyClient(api_key=config.api.tavily_api_key)

    def research_market(self, market: Market) -> Tier2Research:
        """
        Perform Tier 2 deep research on a market.

        Args:
            market: Market to research.

        Returns:
            Tier2Research result.
        """
        start_time = time.time()

        logger.info(f"Starting Tier 2 DEEP research for market: {market.question}")

        # Step 1: Comprehensive information gathering
        sources = self._comprehensive_search(market)
        logger.debug(f"Gathered {len(sources)} sources")

        # Step 2: Assess source quality
        info_quality = self._assess_information_quality(sources)
        logger.debug(f"Information quality: {info_quality}")

        # Step 3: Deep analysis with premium LLM
        analysis = self._deep_analysis(market, sources)

        # Step 4: Extract key findings
        findings = self._extract_findings(analysis, sources)

        # Step 5: Probability estimation
        probability_estimate = self._estimate_probability(market, analysis, sources)

        duration = time.time() - start_time

        research = Tier2Research(
            market_id=market.id,
            question=market.question,
            research_timestamp=datetime.now(timezone.utc),
            model_estimate=probability_estimate,
            key_findings=findings,
            reasoning=analysis.get("reasoning", ""),
            base_rate=analysis.get("base_rate"),
            recent_developments=analysis.get("recent_developments", ""),
            risks_to_thesis=analysis.get("risks", []),
            sources=sources,
            information_quality=info_quality,
            research_duration_seconds=duration,
        )

        logger.info(
            f"Tier 2 complete for '{market.question[:50]}...': "
            f"estimate={probability_estimate.yes_probability:.2%}, duration={duration:.1f}s"
        )

        return research

    def _comprehensive_search(self, market: Market) -> list[Source]:
        """
        Comprehensive information gathering with diverse search strategy.

        Args:
            market: Market to research.

        Returns:
            List of Source objects.
        """
        # Generate diverse queries
        queries = self._generate_comprehensive_queries(market)
        logger.debug(f"Generated {len(queries)} comprehensive queries")

        all_sources = []
        seen_urls = set()

        for query in queries:
            try:
                # Use Tavily with different time windows
                search_params = {
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": 5,
                }

                search_result = self.tavily_client.search(**search_params)

                for result in search_result.get("results", []):
                    url = result.get("url")
                    if url in seen_urls:
                        continue

                    seen_urls.add(url)

                    source = Source(
                        url=url,
                        title=result.get("title", ""),
                        credibility=self._estimate_source_credibility(),
                        date=None,
                        snippet=result.get("content", "")[:1000],
                        relevance_score=result.get("score"),
                    )

                    all_sources.append(source)

                # Break after first successful search per query
                if search_result.get("results"):
                    break

            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")
                continue

        # Sort by credibility and relevance
        all_sources.sort(
            key=lambda s: (s.credibility, s.relevance_score or 0), reverse=True
        )

        # Return top sources
        return all_sources[: self.config.tier2_max_sources]

    def _generate_comprehensive_queries(self, market: Market) -> list[str]:
        """
        Generate 5-8 diverse search queries including contrarian views.

        Args:
            market: Market to research.

        Returns:
            List of search queries.
        """
        system_prompt = """You are a research strategist helping to comprehensively research a prediction market question.

Generate 5-8 diverse search queries that cover:
1. Recent news and developments
2. Official sources and announcements
3. Expert analysis and opinions
4. Historical precedents and base rates
5. Contrarian views ("Why X won't happen")
6. Statistical data and trends

Return ONLY the queries, one per line."""

        user_prompt = f"""Market Question: {market.question}

Description: {market.description}

Possible Outcomes: {", ".join(market.outcomes)}

Resolution Date: {market.end_date.strftime('%Y-%m-%d')}

Generate 5-8 comprehensive search queries."""

        try:
            response = self.anthropic_client.messages.create(
                model=self.config.tier2_model,
                max_tokens=400,
                temperature=0.4,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            queries_text = response.content[0].text.strip()
            queries = [q.strip() for q in queries_text.split("\n") if q.strip()]

            # Ensure we have at least one negative query
            has_negative = any(
                keyword in " ".join(queries).lower()
                for keyword in ["why not", "won't", "unlikely", "fail"]
            )

            if not has_negative and len(queries) < self.config.tier2_queries_per_market:
                queries.append(f"Why {market.question.lower()}")

            return queries[: self.config.tier2_queries_per_market]

        except Exception as e:
            logger.warning(f"Failed to generate queries: {e}, using fallback")
            # Fallback queries
            return [
                market.question,
                f"{market.question} news",
                f"{market.question} analysis",
                f"Why not {market.question.lower()}",
            ]

    def _estimate_source_credibility(self) -> int:
        """Estimate source credibility (same as Tier 1)."""
        return 5

    def _assess_information_quality(self, sources: list[Source]) -> InformationQuality:
        """
        Assess overall information quality.

        Args:
            sources: List of sources.

        Returns:
            InformationQuality enum.
        """
        if not sources:
            return InformationQuality.LOW

        avg_credibility = sum(s.credibility for s in sources) / len(sources)
        source_diversity = len(set(s.url.split("/")[2] for s in sources))

        if avg_credibility >= 4 and source_diversity >= 5:
            return InformationQuality.HIGH
        elif avg_credibility >= 3 and source_diversity >= 3:
            return InformationQuality.MEDIUM
        else:
            return InformationQuality.LOW

    def _deep_analysis(self, market: Market, sources: list[Source]) -> dict:
        """
        Deep analysis using premium LLM.

        Args:
            market: Market object.
            sources: Research sources.

        Returns:
            Dictionary with analysis results.
        """
        # Compile sources
        sources_text = "\n\n".join(
            [
                f"SOURCE {i+1} (Credibility: {s.credibility}/5)\nTitle: {s.title}\nURL: {s.url}\nContent: {s.snippet}"
                for i, s in enumerate(sources[:15])
            ]
        )

        system_prompt = """You are an expert forecasting analyst researching prediction market questions.

Conduct a comprehensive analysis following this framework:

1. CURRENT STATE: What is the current situation? What are the key facts?

2. HISTORICAL CONTEXT: What are relevant precedents? What is the base rate for this type of event?

3. KEY VARIABLES: What factors determine the outcome? What has changed recently? What could change before resolution?

4. PROBABILITY ESTIMATION: Synthesize all information and provide a probability estimate with reasoning. Weight by source credibility. Consider both sides.

5. CONTRARIAN ANALYSIS: Why might your estimate be wrong? What is the market possibly seeing that you're not? What would change your estimate?

6. RISKS TO THESIS: List specific risks that could invalidate your analysis.

Provide structured, objective analysis. Be conservative and acknowledge uncertainty."""

        user_prompt = f"""MARKET QUESTION: {market.question}

DESCRIPTION: {market.description}

POSSIBLE OUTCOMES: {", ".join(market.outcomes)}

CURRENT MARKET PRICES: {", ".join([f"{o}: {p:.1%}" for o, p in zip(market.outcomes, market.outcome_prices)])}

RESOLUTION DATE: {market.end_date.strftime('%Y-%m-%d')}

RESEARCH SOURCES:
{sources_text}

Provide your comprehensive analysis."""

        try:
            response = self.anthropic_client.messages.create(
                model=self.config.tier2_model,
                max_tokens=2000,
                temperature=0.2,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            analysis_text = response.content[0].text.strip()

            # Parse the analysis (simple parsing for now)
            return self._parse_analysis(analysis_text)

        except Exception as e:
            logger.error(f"Deep analysis failed: {e}")
            return {
                "reasoning": f"Analysis failed: {e}",
                "base_rate": None,
                "recent_developments": "",
                "risks": [],
            }

    def _parse_analysis(self, analysis_text: str) -> dict:
        """Parse the analysis text into structured components."""
        # Simple section extraction
        sections = {
            "reasoning": "",
            "base_rate": None,
            "recent_developments": "",
            "risks": [],
        }

        # Extract everything as reasoning for now
        sections["reasoning"] = analysis_text

        # Try to extract risks section
        if "risk" in analysis_text.lower():
            risk_start = analysis_text.lower().find("risk")
            risk_section = analysis_text[risk_start : risk_start + 500]
            # Extract bullet points or numbered items
            import re

            risks = re.findall(
                r"[-•\d]+[.)]\s*(.+?)(?=[-•\d]+[.)]|$)", risk_section, re.DOTALL
            )
            sections["risks"] = [r.strip() for r in risks if r.strip()][:5]

        return sections

    def _extract_findings(
        self, analysis: dict, sources: list[Source]
    ) -> list[ResearchFinding]:
        """
        Extract key findings from analysis.

        Args:
            analysis: Analysis results.
            sources: Research sources.

        Returns:
            List of ResearchFinding objects.
        """
        # For now, create findings from top sources
        findings = []

        for i, source in enumerate(sources[:5]):
            finding = ResearchFinding(
                finding=f"{source.title}: {source.snippet[:200]}...",
                sources=[source],
                importance=source.credibility,
            )
            findings.append(finding)

        return findings

    def _estimate_probability(
        self, market: Market, analysis: dict, sources: list[Source]
    ) -> ProbabilityEstimate:
        """
        Generate probability estimate with confidence intervals.

        Args:
            market: Market object.
            analysis: Analysis results.
            sources: Sources.

        Returns:
            ProbabilityEstimate object.
        """
        # Use LLM to extract probability from analysis
        system_prompt = """Extract the probability estimate from the analysis text.

Return a JSON object with:
{
  "yes_probability": <float between 0 and 1>,
  "confidence_interval_low": <float>,
  "confidence_interval_high": <float>,
  "confidence_level": "low" | "medium" | "medium-high" | "high"
}"""

        user_prompt = f"""Analysis: {analysis.get('reasoning', '')}

Market question has {len(market.outcomes)} outcomes: {', '.join(market.outcomes)}

Extract the probability estimate for the FIRST outcome ("{market.outcomes[0]}").

Return JSON only."""

        try:
            response = self.anthropic_client.messages.create(
                model=self.config.tier2_model,
                max_tokens=200,
                temperature=0.1,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            import json

            result = json.loads(response.content[0].text)

            return ProbabilityEstimate(
                yes_probability=float(result.get("yes_probability", 0.5)),
                confidence_interval_low=float(
                    result.get("confidence_interval_low", 0.4)
                ),
                confidence_interval_high=float(
                    result.get("confidence_interval_high", 0.6)
                ),
                confidence_level=ConfidenceLevel(
                    result.get("confidence_level", "medium")
                ),
            )

        except Exception as e:
            logger.warning(f"Failed to extract probability: {e}, using default")
            # Default conservative estimate
            return ProbabilityEstimate(
                yes_probability=0.5,
                confidence_interval_low=0.3,
                confidence_interval_high=0.7,
                confidence_level=ConfidenceLevel.LOW,
            )
