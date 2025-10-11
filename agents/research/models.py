from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional

@dataclass
class MarketDecision:
    """Structured market decision from research"""
    market_id: str
    rationale: str
    estimated_probability: float
    confidence: int
    bet: float

@dataclass
class EventResearchResult:
    """Complete research result for an event"""
    event_id: str
    event_title: str
    market_decisions: List[MarketDecision]
    unallocated_capital: float
    citations: List[str]
    token_usage: Dict[str, int]
    research_timestamp: datetime
