import json
import logging
from typing import List, Tuple, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .models import MarketDecision

logger = logging.getLogger(__name__)

class StructuredOutputParser:
    """
    Parse Perplexity research output into structured market decisions.
    Uses GPT-4o-mini for reliable parsing (€0.02/call).
    """
    
    def __init__(self, model_id: str = 'gpt-4o-mini'):
        self.llm = ChatOpenAI(model=model_id, temperature=0)
        
    def parse_research_to_decisions(
        self, 
        research_text: str, 
        original_prompt: str,
        markets_data: List[Dict]
    ) -> Tuple[List[MarketDecision], float]:
        """
        Extract market decisions from research output using structured parsing.
        
        Args:
            research_text: Raw research output from Perplexity
            original_prompt: Original prompt sent to Perplexity
            markets_data: List of market data for validation
            
        Returns:
            Tuple of (market_decisions, unallocated_capital)
        """
        
        # Build validation context
        market_ids = [market['id'] for market in markets_data]
        market_context = "\n".join([
            f"- Market {market['id']}: {market['question']}"
            for market in markets_data
        ])
        
        structured_prompt = f"""You are a data extraction specialist. Extract investment decisions from the following research output.

**ORIGINAL RESEARCH PROMPT:**
{original_prompt[:1000]}...

**RESEARCH ANALYSIS OUTPUT:**
{research_text}

**AVAILABLE MARKETS FOR VALIDATION:**
{market_context}

**EXTRACTION TASK:**
Extract the market decisions from the research output. Each decision should include:

1. market_id (str): Must match one of the available market IDs
2. rationale (str): Detailed explanation (3-5 sentences minimum)
3. estimated_probability (float, 0-1): Probability estimate
4. confidence (int, 0-10): Confidence level
5. bet (float, -1 to +1): Bet amount (negative = bet against)

**VALIDATION RULES:**
- All market IDs must be from the available markets list
- Sum of |bet| values + unallocated_capital must equal 1.0
- estimated_probability must be between 0 and 1
- confidence must be between 0 and 10
- bet must be between -1 and 1

**OUTPUT FORMAT:**
Provide a JSON object with:
- "market_decisions": Array of market decisions
- "unallocated_capital": Float (0.0 to 1.0)

**EXAMPLE:**
{{
  "market_decisions": [
    {{
      "market_id": "12345",
      "rationale": "Based on recent polling data showing candidate X gaining momentum...",
      "estimated_probability": 0.65,
      "confidence": 7,
      "bet": 0.3
    }}
  ],
  "unallocated_capital": 0.7
}}

If no valid decisions can be extracted, return empty market_decisions array and unallocated_capital of 1.0."""

        try:
            messages = [
                SystemMessage(content="You are a precise data extraction specialist. Extract structured data from research text."),
                HumanMessage(content=structured_prompt)
            ]
            
            response = self.llm.invoke(messages)
            parsed_output = json.loads(response.content)
            
            # Validate and convert to MarketDecision objects
            market_decisions = []
            for decision_data in parsed_output.get('market_decisions', []):
                try:
                    # Validate market ID
                    if decision_data['market_id'] not in market_ids:
                        logger.warning(f"Invalid market ID: {decision_data['market_id']}")
                        continue
                    
                    decision = MarketDecision(
                        market_id=decision_data['market_id'],
                        rationale=decision_data['rationale'],
                        estimated_probability=float(decision_data['estimated_probability']),
                        confidence=int(decision_data['confidence']),
                        bet=float(decision_data['bet'])
                    )
                    
                    # Validate ranges
                    if not (0 <= decision.estimated_probability <= 1):
                        logger.warning(f"Invalid probability: {decision.estimated_probability}")
                        continue
                    if not (0 <= decision.confidence <= 10):
                        logger.warning(f"Invalid confidence: {decision.confidence}")
                        continue
                    if not (-1 <= decision.bet <= 1):
                        logger.warning(f"Invalid bet: {decision.bet}")
                        continue
                    
                    market_decisions.append(decision)
                    
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Invalid decision data: {e}")
                    continue
            
            unallocated_capital = float(parsed_output.get('unallocated_capital', 1.0))
            
            # Validate capital allocation
            total_allocated = sum(abs(decision.bet) for decision in market_decisions)
            total_capital = total_allocated + unallocated_capital
            
            if abs(total_capital - 1.0) > 0.01:  # Allow small floating point errors
                logger.warning(f"Capital allocation doesn't sum to 1.0: {total_capital}")
                # Normalize
                if total_capital > 0:
                    scale_factor = 1.0 / total_capital
                    for decision in market_decisions:
                        decision.bet *= scale_factor
                    unallocated_capital *= scale_factor
            
            logger.info(f"Parsed {len(market_decisions)} market decisions, unallocated: {unallocated_capital:.3f}")
            return market_decisions, unallocated_capital
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from structured output: {e}")
            logger.error(f"Raw response: {response.content}")
            return [], 1.0
            
        except Exception as e:
            logger.error(f"Structured parsing failed: {e}")
            return [], 1.0
    
    def validate_decisions(self, decisions: List[MarketDecision], markets_data: List[Dict]) -> List[str]:
        """
        Validate market decisions and return list of issues.
        
        Returns:
            List of validation error messages
        """
        issues = []
        market_ids = {market['id'] for market in markets_data}
        
        total_bet = 0
        for decision in decisions:
            # Check market ID
            if decision.market_id not in market_ids:
                issues.append(f"Invalid market ID: {decision.market_id}")
            
            # Check probability range
            if not (0 <= decision.estimated_probability <= 1):
                issues.append(f"Invalid probability for {decision.market_id}: {decision.estimated_probability}")
            
            # Check confidence range
            if not (0 <= decision.confidence <= 10):
                issues.append(f"Invalid confidence for {decision.market_id}: {decision.confidence}")
            
            # Check bet range
            if not (-1 <= decision.bet <= 1):
                issues.append(f"Invalid bet for {decision.market_id}: {decision.bet}")
            
            total_bet += abs(decision.bet)
        
        # Check total allocation
        if total_bet > 1.0:
            issues.append(f"Total allocation exceeds 1.0: {total_bet}")
        
        return issues
