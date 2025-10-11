# Research module for Polymarket Agents
from .models import MarketDecision, EventResearchResult
from .perplexity_research import PerplexityResearchAgent
from .structured_parser import StructuredOutputParser

__all__ = [
    'MarketDecision',
    'EventResearchResult',
    'PerplexityResearchAgent',
    'StructuredOutputParser'
]
