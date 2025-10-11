import os
import json
import requests
from pathlib import Path
from datetime import date, datetime
from typing import Dict, List, Optional, Any
import logging

from .structured_parser import StructuredOutputParser
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
    
    def __init__(self, model_id: str = 'sonar-deep-research'):
        self.model_id = model_id
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable is required")
        
        self.url = "https://api.perplexity.ai/chat/completions"
        self.cache_dir = Path('./research_cache')
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache duration in hours
        self.cache_hours = 24
        
        # Initialize structured parser
        self.parser = StructuredOutputParser()
        
    def research_event(self, event_data: Dict, markets_data: List[Dict], target_date: date) -> EventResearchResult:
        """
        Research an entire event using Perplexity Sonar Deep Research.
        
        Args:
            event_data: Event information (id, title, description)
            markets_data: List of markets within the event
            target_date: Date for analysis
            
        Returns:
            EventResearchResult with market decisions and metadata
        """
        event_id = event_data.get('id', 'unknown')
        
        # Check cache first
        cached_result = self._load_from_cache(event_id, target_date)
        if cached_result:
            logger.info(f"Using cached research for event {event_id}")
            return cached_result
        
        logger.info(f"Researching event {event_id}: {event_data.get('title', 'Unknown')}")
        
        # Build comprehensive prompt
        prompt = self._build_research_prompt(event_data, markets_data, target_date)
        
        # Call Perplexity API
        try:
            response = self._call_perplexity_api(prompt)
            research_output = response["choices"][0]["message"]["content"]
            citations = response.get("citations", [])
            token_usage = response.get("usage", {})
            
            logger.info(f"Perplexity research completed for event {event_id}")
            logger.info(f"Token usage: {token_usage}")
            
        except Exception as e:
            logger.error(f"Perplexity API call failed for event {event_id}: {e}")
            raise
        
        # Parse structured output using the parser
        try:
            market_decisions, unallocated_capital = self.parser.parse_research_to_decisions(
                research_output, prompt, markets_data
            )
        except Exception as e:
            logger.error(f"Failed to parse research output for event {event_id}: {e}")
            # Fallback: return conservative decisions
            market_decisions = []
            unallocated_capital = 1.0
        
        # Create result
        result = EventResearchResult(
            event_id=event_id,
            event_title=event_data.get('title', 'Unknown'),
            market_decisions=market_decisions,
            unallocated_capital=unallocated_capital,
            citations=citations,
            token_usage=token_usage,
            research_timestamp=datetime.now()
        )
        
        # Cache result
        self._save_to_cache(event_id, target_date, result)
        
        return result
    
    def _call_perplexity_api(self, prompt: str) -> Dict:
        """Make API call to Perplexity"""
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        response = requests.post(self.url, json=payload, headers=headers, timeout=300)
        response.raise_for_status()
        
        return response.json()
    
    def _build_research_prompt(self, event_data: Dict, markets_data: List[Dict], target_date: date) -> str:
        """Build comprehensive research prompt in PrediBench style"""
        
        # Build market summaries
        market_summaries = []
        for market in markets_data:
            summary = f"""<market_{market['id']}>
Market ID: {market['id']}
Question: {market['question']}
Description: {market.get('description', 'No description available')}
Current Price: {market.get('current_price', 'N/A')}
Outcomes: {market.get('outcomes', 'Yes, No')}
Recent Price History: {market.get('price_history', 'No history available')}
</market_{market['id']}>"""
            market_summaries.append(summary)
        
        market_summaries_joined = "\n\n".join(market_summaries)
        
        return f"""You are an expert prediction-market analyst. You have been given $1.0 to allocate on the following event from the prediction market Polymarket.

<event_details>
- Date: {target_date.strftime("%B %d, %Y")}
- Event ID: {event_data.get('id', 'unknown')}
- Title: {event_data.get('title', 'Unknown Event')}
- Description: {event_data.get('description', 'No description available')}
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
- You have exactly $1.0 to allocate across ALL markets
- For EACH market, provide:
  1. market_id (str): The market ID
  2. rationale (str): Detailed explanation (3-5 sentences minimum) of why you think this market is mispriced or correctly priced
  3. estimated_probability (float, 0-1): Your true probability estimate for the market outcome
  4. confidence (int, 0-10): Your confidence in the estimated_probability and your bet
  5. bet (float, -1 to +1): Bet amount (negative = bet against the market)
- You can skip markets by setting bet = 0.0
- The sum of absolute values of bets + unallocated_capital must equal 1.0
- Example: If you bet 0.3 in market A, -0.2 in market B, and nothing on market C, your unallocated_capital should be 0.5, such that the sum is 0.3 + 0.2 + 0.5 = 1.0.
</capital_allocation_rules>

Provide your final answer as a JSON object with:
- "market_decisions": Array of market decisions (each with market_id, rationale, estimated_probability, confidence, bet)
- "unallocated_capital": Float (0.0 to 1.0) for capital not allocated to any market

Make sure to provide detailed rationales that highlight the specific facts and insights you discovered through your research."""
    
    
    def _load_from_cache(self, event_id: str, target_date: date) -> Optional[EventResearchResult]:
        """Load cached research result if exists and not expired"""
        cache_file = self.cache_dir / f"{event_id}_{target_date}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is still valid
            cache_timestamp = datetime.fromisoformat(cached_data['research_timestamp'])
            hours_since_cache = (datetime.now() - cache_timestamp).total_seconds() / 3600
            
            if hours_since_cache < self.cache_hours:
                # Reconstruct EventResearchResult
                market_decisions = [
                    MarketDecision(**decision) for decision in cached_data['market_decisions']
                ]
                
                return EventResearchResult(
                    event_id=cached_data['event_id'],
                    event_title=cached_data['event_title'],
                    market_decisions=market_decisions,
                    unallocated_capital=cached_data['unallocated_capital'],
                    citations=cached_data['citations'],
                    token_usage=cached_data['token_usage'],
                    research_timestamp=cache_timestamp
                )
            else:
                # Cache expired, remove file
                cache_file.unlink()
                
        except Exception as e:
            logger.warning(f"Failed to load cache for event {event_id}: {e}")
            if cache_file.exists():
                cache_file.unlink()
        
        return None
    
    def _save_to_cache(self, event_id: str, target_date: date, result: EventResearchResult):
        """Save research result to cache"""
        cache_file = self.cache_dir / f"{event_id}_{target_date}.json"
        
        try:
            # Convert to serializable format
            cache_data = {
                'event_id': result.event_id,
                'event_title': result.event_title,
                'market_decisions': [
                    {
                        'market_id': decision.market_id,
                        'rationale': decision.rationale,
                        'estimated_probability': decision.estimated_probability,
                        'confidence': decision.confidence,
                        'bet': decision.bet
                    }
                    for decision in result.market_decisions
                ],
                'unallocated_capital': result.unallocated_capital,
                'citations': result.citations,
                'token_usage': result.token_usage,
                'research_timestamp': result.research_timestamp.isoformat()
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.info(f"Cached research result for event {event_id}")
            
        except Exception as e:
            logger.warning(f"Failed to cache result for event {event_id}: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about cached research"""
        cache_files = list(self.cache_dir.glob("*.json"))
        
        total_files = len(cache_files)
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'total_cached_events': total_files,
            'total_cache_size_bytes': total_size,
            'cache_directory': str(self.cache_dir)
        }
