"""
Data models for research results
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import date

@dataclass
class MarketDecision:
    """A trading decision for a specific market"""
    market_id: str
    rationale: str
    estimated_probability: float
    confidence: int
    bet: float

@dataclass
class EventResearchResult:
    """Result of researching an event with multiple markets"""
    event_summary: str
    market_decisions: List[MarketDecision]
    sources: List[str]
    research_date: date
