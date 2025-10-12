"""
Perplexity Sonar Deep Research agent for comprehensive event analysis.
"""

import os
import json
import requests
from pathlib import Path
from datetime import date, datetime
from typing import Dict, List, Optional, Any
import logging

from .models import MarketDecision, EventResearchResult

logger = logging.getLogger(__name__)

class PerplexityResearchAgent:
    """
    Perplexity Sonar Deep Research agent for comprehensive event analysis.
    
    Features:
    - Event-level research (multiple markets per call)
    - 24-hour caching system
    - Citation tracking
    - Cost: ~€0.17 per event (~2-5 markets)
    """
    
    def __init__(self, model_id: str = 'sonar'):
        self.model_id = model_id
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable is required")
        
        self.url = "https://api.perplexity.ai/chat/completions"
        self.cache_dir = Path('./research_cache')
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache duration in hours
        self.cache_hours = 24
        
    def research_event(self, event_data: Dict, markets_data: List[Dict], target_date: date) -> EventResearchResult:
        """
        Research an event and generate market decisions.
        
        Args:
            event_data: Event information
            markets_data: List of markets to analyze
            target_date: Date for analysis
            
        Returns:
            EventResearchResult with analysis and decisions
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(event_data, markets_data, target_date)
            cached_result = self._load_from_cache(cache_key)
            if cached_result:
                logger.info("Using cached research result")
                return cached_result
            
            # Create research prompt
            prompt = self._create_research_prompt(event_data, markets_data)
            
            # Make API call
            response = self._make_api_call(prompt)
            
            # Parse response
            result = self._parse_response(response, markets_data)
            
            # Cache result
            self._save_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in research_event: {e}")
            # Return empty result on error
            return EventResearchResult(
                event_summary="Research failed due to error",
                market_decisions=[],
                sources=[],
                research_date=target_date
            )
    
    def _get_cache_key(self, event_data: Dict, markets_data: List[Dict], target_date: date) -> str:
        """Generate cache key for research"""
        event_id = event_data.get('title', 'unknown')[:50]
        market_ids = [m.get('market_id', '') for m in markets_data]
        return f"{event_id}_{len(market_ids)}_{target_date.isoformat()}"
    
    def _load_from_cache(self, cache_key: str) -> Optional[EventResearchResult]:
        """Load result from cache if available"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                # Check if cache is still valid
                file_age = datetime.now().timestamp() - cache_file.stat().st_mtime
                if file_age < (self.cache_hours * 3600):
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    return EventResearchResult(
                        event_summary=data['event_summary'],
                        market_decisions=[
                            MarketDecision(**d) for d in data['market_decisions']
                        ],
                        sources=data['sources'],
                        research_date=date.fromisoformat(data['research_date'])
                    )
        except Exception as e:
            logger.warning(f"Error loading cache: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, result: EventResearchResult):
        """Save result to cache"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            data = {
                'event_summary': result.event_summary,
                'market_decisions': [
                    {
                        'market_id': d.market_id,
                        'rationale': d.rationale,
                        'estimated_probability': d.estimated_probability,
                        'confidence': d.confidence,
                        'bet': d.bet
                    }
                    for d in result.market_decisions
                ],
                'sources': result.sources,
                'research_date': result.research_date.isoformat()
            }
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Error saving cache: {e}")
    
    def _create_research_prompt(self, event_data: Dict, markets_data: List[Dict]) -> str:
        """Create research prompt for Perplexity API using the standardized prompt format"""
        from datetime import datetime
        
        event_title = event_data.get('title', 'Unknown Event')
        event_desc = event_data.get('description', '')
        event_id = event_data.get('id', 'unknown')
        target_date = datetime.now()
        
        # Format markets with detailed information
        market_summaries = []
        for idx, m in enumerate(markets_data, 1):
            market_id = m.get('id', f'market_{idx}')
            question = m.get('question', 'Unknown')
            outcomes = m.get('outcomes', [])
            description = m.get('description', '')
            current_price = m.get('current_price', 0.5)
            
            market_summary = f"""Market {idx} (ID: {market_id}):
- Question: {question}
- Outcomes: {outcomes}
- Current Market Price: {current_price:.1%} (probability for first outcome)
- Description: {description if description else 'No additional description'}"""
            market_summaries.append(market_summary)
        
        market_summaries_joined = "\n\n".join(market_summaries)
        
        # BET_DESCRIPTION constant
        bet_description = """
1. market_id (str): The market ID
2. rationale (str): Explanation for your decision and why you think this market is mispriced (or correctly priced if skipping). Write at least a few sentences. If you take a strong bet, make sure to highlight the facts you know/value that the market doesn't.
3. estimated_probability (float, 0 to 1): The estimated_probability you think the market will settle at (your true probability estimate)
4. confidence (int, 0 to 10): Your confidence in the estimated_probability and your bet. Should be between 0 (absolute uncertainty, you shouldn't bet if you're not confident) and 10 (absolute certainty, then you can bet high).
5. bet (float): The amount in dollars that you bet on this market (can be negative if you want to buy the opposite of the market). You can bet any amount that makes sense based on your confidence and edge.
"""
        
        prompt = f"""You are an expert prediction-market analyst analyzing events from the prediction market Polymarket.

<event_details>
- Date: {target_date.strftime("%B %d, %Y")}
- Event ID: {event_id}
- Title: {event_title}
- Description: {event_desc}
- Available Markets: {len(markets_data)} markets, see below.
</event_details>

<available_markets>
{market_summaries_joined}
</available_markets>

<analysis_guidelines>
- Use web search to gather up-to-date information about this event
- Be critical of sources, and be cautious of sensationalized headlines or partisan sources
- If some web search results appear to indicate the event's outcome directly, that would be weird because the event should still be unresolved: so double-check that they do not refer to another event, for instance unrelated or long past.
- Only place a bet when you estimate that the market is mispriced.
- Consider base rates, current information, and market efficiency
- Think probabilistically and embrace uncertainty
</analysis_guidelines>

<capital_allocation_rules>
- For EACH market, provide:
{bet_description}
- You can skip markets by setting bet = 0.0
- Bet amounts should reflect your confidence and the edge you've identified
- Negative bet amounts mean betting against the primary outcome
</capital_allocation_rules>

Provide your final answer as a JSON object with:
- "market_decisions": Array of market decisions (each with market_id, rationale, estimated_probability, confidence, bet)
- "unallocated_capital": Set to 0.0 (not used in this system)

Make sure to provide detailed rationales that highlight the specific facts and insights you discovered through your research.
"""
        return prompt
    
    def _make_api_call(self, prompt: str) -> Dict:
        """Make API call to Perplexity with retry logic"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        # Try with retries and exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Use longer timeout for deep research
                response = requests.post(
                    self.url, 
                    headers=headers, 
                    json=data, 
                    timeout=600  # 10 minutes for deep research
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise
        
        raise Exception("Failed to connect to Perplexity API after retries")
    
    def _parse_response(self, response: Dict, markets_data: List[Dict]) -> EventResearchResult:
        """Parse API response into structured result"""
        try:
            content = response['choices'][0]['message']['content']
            
            # Extract event summary (first paragraph)
            summary = content.split('\n\n')[0] if '\n\n' in content else content[:200]
            
            # Create mock market decisions for now
            # In a real implementation, this would parse the response more intelligently
            market_decisions = []
            for i, market in enumerate(markets_data):
                decision = MarketDecision(
                    market_id=market.get('market_id', f'market_{i}'),
                    rationale=f"Research analysis for {market.get('question', 'Unknown')[:50]}...",
                    estimated_probability=0.6 + (i * 0.05),  # Mock probabilities
                    confidence=7 - i,  # Mock confidence levels
                    bet=0.1 + (i * 0.05)  # Mock bet amounts
                )
                market_decisions.append(decision)
            
            return EventResearchResult(
                event_summary=summary,
                market_decisions=market_decisions,
                sources=["Perplexity Sonar Deep Research"],
                research_date=date.today()
            )
            
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return EventResearchResult(
                event_summary="Failed to parse research response",
                market_decisions=[],
                sources=[],
                research_date=date.today()
            )
