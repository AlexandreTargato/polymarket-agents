"""Stage 3: Tier 1 Research - Fast context gathering for filtered markets."""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

import anthropic
from typing import Any
try:
    from openai import OpenAI  # type: ignore
except Exception:  # OpenAI optional
    OpenAI = None  # type: ignore
from tavily import TavilyClient

from agents.config import config
from agents.models import Market, Tier1Research, Source

logger = logging.getLogger(__name__)


class Tier1Researcher:
    """
    Performs fast context research (60-90 seconds per market).

    Process:
    1. Form 2-3 targeted search queries
    2. Run web searches (prioritize last 7 days)
    3. Quick LLM analysis with lightweight model
    4. Preliminary assessment of research potential
    """

    def __init__(self):
        self.config = config.research
        self.use_openai = bool(getattr(config.api, "openai_api_key", None)) and OpenAI is not None
        if self.use_openai:
            self.openai_client = OpenAI(api_key=getattr(config.api, "openai_api_key", None))  # type: ignore
        else:
            self.anthropic_client = anthropic.Anthropic(
                api_key=config.api.anthropic_api_key
            )
        self.tavily_client = TavilyClient(api_key=config.api.tavily_api_key)

    def research_market(self, market: Market) -> Tier1Research:
        """
        Perform Tier 1 research on a market.

        Args:
            market: Market to research.

        Returns:
            Tier1Research result.
        """
        start_time = time.time()

        logger.info(f"Starting Tier 1 research for market: {market.question}")

        # Step 1: Form search queries
        queries = self._form_search_queries(market)
        logger.debug(f"Generated queries: {queries}")

        # Step 2: Run searches
        sources = self._run_searches(queries)
        logger.debug(f"Found {len(sources)} sources")

        # Step 3: Quick LLM analysis
        analysis = self._analyze_context(market, sources)

        # Step 4: Make decision
        decision = self._make_decision(market, sources, analysis)

        duration = time.time() - start_time

        research = Tier1Research(
            market_id=market.id,
            research_timestamp=datetime.now(timezone.utc),
            queries_used=queries,
            sources_found=sources,
            summary=analysis.get("summary", ""),
            recent_developments=analysis.get("recent_developments", False),
            quality_sources_available=len(sources) >= 3,
            proceed_to_tier2=decision["proceed"],
            reasoning=decision["reasoning"],
            preliminary_edge=decision.get("preliminary_edge"),
            research_duration_seconds=duration,
        )

        logger.info(
            f"Tier 1 complete for '{market.question[:50]}...': "
            f"proceed={research.proceed_to_tier2}, duration={duration:.1f}s"
        )

        return research

    def _form_search_queries(self, market: Market) -> list[str]:
        """
        Form 2-3 targeted search queries based on the market question.

        Args:
            market: Market object.

        Returns:
            List of search query strings.
        """
        # Use LLM to generate intelligent queries
        system_prompt = """You are a research assistant helping to find relevant information about prediction market questions.
Generate 2-3 specific, targeted search queries that would help determine the outcome of the question.

Focus on:
- Recent news and developments
- Official announcements
- Expert analysis
- Key facts and data

Return ONLY the queries, one per line."""

        user_prompt = f"""Market Question: {market.question}

Description: {market.description}

Resolution Date: {market.end_date.strftime('%Y-%m-%d')}

Generate 2-3 search queries that would help research this question."""

        try:
            if self.use_openai:
                response = self.openai_client.chat.completions.create(
                    model=self.config.tier1_model_openai or "gpt-4o-mini",
                    temperature=0.3,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=200,
                )
                queries_text = (response.choices[0].message.content or "").strip()
            else:
                response = self.anthropic_client.messages.create(
                    model=self.config.tier1_model,
                    max_tokens=200,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                queries_text = response.content[0].text.strip()
            queries = [q.strip() for q in queries_text.split("\n") if q.strip()]

            # Limit to configured number
            queries = queries[: self.config.tier1_queries_per_market]

            return queries if queries else [market.question]

        except Exception as e:
            logger.warning(f"Failed to generate queries with LLM: {e}, using fallback")
            # Fallback: use question directly
            return [market.question]

    def _run_searches(self, queries: list[str]) -> list[Source]:
        """
        Run web searches for all queries and collect sources.

        Args:
            queries: List of search queries.

        Returns:
            List of Source objects.
        """
        all_sources = []
        seen_urls = set()

        for query in queries:
            try:
                # Use Tavily for web search
                search_result = self.tavily_client.search(
                    query=query,
                    max_results=5,
                )

                for result in search_result.get("results", []):
                    url = result.get("url")
                    if url in seen_urls:
                        continue

                    seen_urls.add(url)

                    source = Source(
                        url=url,
                        title=result.get("title", ""),
                        credibility=self._estimate_source_credibility(),
                        date=None,  # Tavily doesn't always provide dates
                        snippet=result.get("content", "")[:500],
                        relevance_score=result.get("score"),
                    )

                    all_sources.append(source)

            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")
                continue

        # Sort by relevance and credibility
        all_sources.sort(
            key=lambda s: (s.credibility, s.relevance_score or 0), reverse=True
        )

        # Limit to max sources
        return all_sources[: self.config.tier1_max_sources]

    def _estimate_source_credibility(self) -> int:
        """
        Estimate source credibility (1-5) based on URL.
        Todo: implement a clever way to estimate source credibility based on the url and content.

        Args:
            url: Source URL.

        Returns:
            Credibility score 1-5.
        """

        return 5

    def _analyze_context(self, market: Market, sources: list[Source]) -> dict:
        """
        Quick LLM analysis of gathered context.

        Args:
            market: Market object.
            sources: List of sources found.

        Returns:
            Dictionary with analysis results.
        """
        if not sources:
            return {
                "summary": "No sources found for analysis.",
                "recent_developments": False,
            }

        # Compile sources for LLM
        sources_text = "\n\n".join(
            [
                f"Source {i+1}: {s.title}\nURL: {s.url}\n{s.snippet}"
                for i, s in enumerate(sources[:5])
            ]
        )

        system_prompt = """You are a research analyst evaluating whether information about a prediction market question suggests it might be mispriced.

Provide a brief 2-3 sentence summary focusing on:
1. Current status of the situation
2. Any recent material developments
3. Whether the market might have incomplete information

Be concise and objective."""

        user_prompt = f"""Market Question: {market.question}

Current Market Prices: {", ".join([f"{o}: {p:.1%}" for o, p in zip(market.outcomes, market.outcome_prices)])}

Sources Found:
{sources_text}

Provide your analysis."""

        try:
            if self.use_openai:
                response = self.openai_client.chat.completions.create(
                    model=self.config.tier1_model_openai or "gpt-4o-mini",
                    max_tokens=300,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                summary = (response.choices[0].message.content or "").strip()
            else:
                response = self.anthropic_client.messages.create(
                    model=self.config.tier1_model,
                    max_tokens=300,
                    temperature=0.2,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )

                summary = response.content[0].text.strip()

            # Check for keywords indicating recent developments
            recent_keywords = [
                "recent",
                "just",
                "announced",
                "yesterday",
                "today",
                "breaking",
                "new",
                "latest",
            ]
            recent_developments = any(
                keyword in summary.lower() for keyword in recent_keywords
            )

            return {"summary": summary, "recent_developments": recent_developments}

        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}")
            return {
                "summary": f"Found {len(sources)} sources but analysis failed.",
                "recent_developments": False,
            }

    def _make_decision(
        self, market: Market, sources: list[Source], analysis: dict
    ) -> dict:
        """
        Decide whether to proceed to Tier 2 research.

        Args:
            market: Market object.
            sources: Sources found.
            analysis: Analysis results.

        Returns:
            Dictionary with decision and reasoning.
        """
        proceed = False
        reasoning_parts = []
        preliminary_edge = None

        # Check 1: Do we have quality sources?
        quality_sources = [
            s for s in sources if s.credibility >= self.config.min_source_quality
        ]
        if len(quality_sources) < 2:
            reasoning_parts.append("Insufficient quality sources found")
            return {
                "proceed": False,
                "reasoning": "; ".join(reasoning_parts),
            }

        reasoning_parts.append(f"Found {len(quality_sources)} quality sources")

        # Check 2: Recent developments?
        if analysis.get("recent_developments"):
            reasoning_parts.append("Recent material developments detected")
            proceed = True

        # Check 3: Source diversity
        unique_domains = len(set(s.url.split("/")[2] for s in sources))
        if unique_domains >= 3:
            reasoning_parts.append(f"Good source diversity ({unique_domains} domains)")
            proceed = True

        # Check 4: Look for keywords suggesting mispricing
        mispricing_keywords = [
            "underestimate",
            "overestimate",
            "likely",
            "unlikely",
            "probable",
            "improbable",
            "expect",
            "unexpected",
        ]

        summary_lower = analysis.get("summary", "").lower()
        if any(keyword in summary_lower for keyword in mispricing_keywords):
            reasoning_parts.append("Analysis suggests potential mispricing")
            proceed = True

        # If we still haven't decided to proceed, check minimum criteria
        if not proceed:
            if len(sources) >= 5 and len(quality_sources) >= 3:
                reasoning_parts.append("Sufficient sources for deeper analysis")
                proceed = True
            else:
                reasoning_parts.append("Insufficient indicators for deep research")

        return {
            "proceed": proceed,
            "reasoning": "; ".join(reasoning_parts),
            "preliminary_edge": preliminary_edge,
        }
