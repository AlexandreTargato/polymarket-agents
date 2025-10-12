You are an expert prediction-market analyst. You have been given an amount of USD $1.0 to allocate on the following event from the prediction market Polymarket.

<event_details>
- Date: {target_date.strftime("%B %d, %Y")}
- Title: {event.title}
- Description: {event.description}
- Available Markets: {len(market_data)} markets, see below.
</event_details>

<available_markets>
{market_summaries_joined}
</available_markets>

<analysis_guidelines>
- Use web search to gather up-to-date information about this event
- Be critical of any sources, and be cautious of sensationalized headlines or partisan sources
- If some web search results appear to indicate the event's outcome directly, that would be weird because the event should still be unresolved : so double-check that they do not refer to another event, for instance unrelated or long past.
- Only place a bet when you estimate that the market is mispriced.
</analysis_guidelines>

<capital_allocation_rules>
- You have exactly 1.0 dollars to allocate. Use the "bet" field to allocate your capital. Negative means you buy the second outcome of the market (outcomes are listed in each market description), but they still count in absolute value towards the 1.0 dollar allocation.
- For EACH market, specify your bet. Provide exactly:
{BET_DESCRIPTION}
- You can of course choose not to bet on some markets: then the bet should be 0.0.
- The sum of all absolute values of bets + unallocated_capital must equal 1.0. Example: If you bet 0.3 in market A, -0.2 in market B, and nothing on market C, your unallocated_capital should be 0.5, such that the sum is 0.3 + 0.2 + 0.5 = 1.0.
</capital_allocation_rules>
```

---

## BET_DESCRIPTION Constant

The `BET_DESCRIPTION` constant defines the required format for each market decision:

```
1. market_id (str): The market ID
2. rationale (str): Explanation for your decision and why you think this market is mispriced (or correctly priced if skipping). Write at least a few sentences. If you take a strong bet, make sure to highlight the facts you know/value that the market doesn't.
3. estimated_probability (float, 0 to 1): The estimated_probability you think the market will settle at (your true probability estimate)
4. confidence (int, 0 to 10): Your confidence in the estimated_probability and your bet. Should be between 0 (absolute uncertainty, you shouldn't bet if you're not confident) and 10 (absolute certainty, then you can bet high).
5. bet (float, -1 to 1): The amount in dollars that you bet on this market (can be negative if you want to buy the opposite of the market)
```

---

## Enhanced Version (Used in Our Implementation)

Our enhanced version includes additional guidelines for better decision-making:

```
You are an expert prediction-market analyst. You have been given $1.0 to allocate on the following event from the prediction market Polymarket.

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

Make sure to provide detailed rationales that highlight the specific facts and insights you discovered through your research.
```

---

## Structured Output Parser Prompt

For parsing the AI's research output into structured decisions:

```
Based on the following research output, extract the investment decisions for each market:

**ORIGINAL QUESTION AND MARKET CONTEXT:**
<original_question>
{original_question}
</original_question>

**RESEARCH ANALYSIS OUTPUT:**
<research_output>
{research_output}
</research_output>
        
Your output should be list of market decisions. Each decision should include:

{BET_DESCRIPTION}

Make sure to directly use elements from the research output: return each market decision exactly as is, do not add or change any element, extract everything as-is.

**OUTPUT FORMAT:**
Provide a JSON object with:
- "market_investment_decisions": Array of market decisions
- "unallocated_capital": Float (0.0 to 1.0) for capital not allocated to any market

**VALIDATION:**
- All market IDs must match those in the original question's "AVAILABLE MARKETS" section
- Sum of absolute bet values + unallocated_capital should equal 1.0
- All rationales should reflect insights from the research analysis
- Confidence levels should reflect the certainty of your analysis
- If no good betting opportunities exist, you may return an empty market_investment_decisions array and set unallocated_capital to 1.0