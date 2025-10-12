# Prompt System Update

## Overview
Updated the Perplexity AI research prompts to use the standardized format from `prompt.md`, removing the $1.0 capital constraint and allowing flexible bet sizing based on confidence and edge.

## Changes Made

### 1. Updated `agents/research/perplexity_research.py`

**Previous Prompt:**
- Simple market analysis request
- Basic probability estimates
- Fixed -1 to +1 bet range

**New Prompt (from prompt.md):**
- Structured event details with date, ID, title, description
- Detailed market summaries with IDs, questions, outcomes, descriptions
- Comprehensive analysis guidelines:
  - Web search for up-to-date information
  - Critical evaluation of sources
  - Verification of event resolution status
  - Focus on market mispricing
  - Base rates and probabilistic thinking
- Flexible capital allocation:
  - **Removed $1.0 constraint**
  - Bet amounts reflect confidence and edge
  - Can bet any amount that makes sense
  - Negative bets for betting against outcomes
- Standardized output format:
  - market_id
  - rationale (detailed, highlighting facts the market doesn't know)
  - estimated_probability (0-1)
  - confidence (0-10)
  - bet (flexible dollar amount, can be negative)

### 2. Key Improvements

#### Better Analysis Guidelines
```
- Use web search to gather up-to-date information about this event
- Be critical of sources, and be cautious of sensationalized headlines or partisan sources
- If some web search results appear to indicate the event's outcome directly, that would be weird because the event should still be unresolved: so double-check that they do not refer to another event, for instance unrelated or long past.
- Only place a bet when you estimate that the market is mispriced.
- Consider base rates, current information, and market efficiency
- Think probabilistically and embrace uncertainty
```

#### Flexible Bet Sizing
```
5. bet (float): The amount in dollars that you bet on this market (can be negative if you want to buy the opposite of the market). You can bet any amount that makes sense based on your confidence and edge.
```

**Before:** Limited to -1 to +1 range (representing fractions of $1)
**After:** Any dollar amount based on confidence and edge

#### Enhanced Rationale Requirements
```
2. rationale (str): Explanation for your decision and why you think this market is mispriced (or correctly priced if skipping). Write at least a few sentences. If you take a strong bet, make sure to highlight the facts you know/value that the market doesn't.
```

This ensures the AI provides detailed reasoning highlighting information asymmetries.

### 3. Integration with Human-in-the-Loop System

The updated prompt is automatically used by:
- `scripts/python/human_in_the_loop_trader.py` - Daily market analysis
- `agents/research/perplexity_research.py` - All Perplexity API calls
- Any future strategies using the research agent

### 4. Benefits

1. **Better Research Quality**: More structured prompts lead to more thorough analysis
2. **Flexible Position Sizing**: Can recommend larger positions for high-confidence, high-edge opportunities
3. **Detailed Rationales**: Forces the AI to explain what information edge it has identified
4. **Consistent Format**: All research follows the same standardized structure
5. **Probabilistic Thinking**: Emphasizes uncertainty and base rates

## Testing

The system has been tested and successfully:
- ✅ Discovers markets from Polymarket
- ✅ Filters for tradeable opportunities
- ✅ Runs Perplexity deep research with new prompt format
- ✅ Generates detailed recommendations with confidence scores
- ✅ Sends formatted email notifications
- ✅ Calculates position sizes based on Kelly Criterion

## Example Output

With the new prompt, recommendations include:
- **Market Question**: Clear description
- **Confidence**: 0-10 scale
- **Edge**: Percentage difference from market price
- **Recommended Position**: Dollar amount (not limited to $1)
- **Rationale**: Detailed explanation of mispricing
- **Risk Level**: Assessment based on confidence and edge

## Next Steps

1. Monitor recommendation quality over time
2. Adjust position sizing parameters if needed
3. Consider adding more analysis guidelines based on results
4. Track performance to validate the new prompt format

