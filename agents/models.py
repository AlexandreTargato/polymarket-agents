"""Data models for Polymarket Trading Agent."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence level enum."""

    LOW = "low"
    MEDIUM = "medium"
    MEDIUM_HIGH = "medium-high"
    HIGH = "high"


class InformationQuality(str, Enum):
    """Information quality enum."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Market(BaseModel):
    """Market data model."""

    id: str
    question: str
    description: str
    end_date: datetime
    start_date: Optional[datetime] = None

    # Market metrics
    volume: float
    liquidity: float
    active: bool

    # Outcomes
    outcomes: list[str]
    outcome_prices: list[float]

    # Token IDs for trading
    clob_token_ids: list[str]

    # Categories and tags
    category: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    # Resolution
    resolution_source: Optional[str] = None

    # Computed fields
    age_hours: Optional[float] = None
    days_until_resolution: Optional[float] = None


class Source(BaseModel):
    """Research source model."""

    url: str
    title: str
    credibility: int = Field(ge=1, le=5, description="Credibility rating 1-5")
    date: Optional[datetime] = None
    snippet: Optional[str] = None
    relevance_score: Optional[float] = None


class ResearchFinding(BaseModel):
    """Individual research finding."""

    finding: str
    sources: list[Source]
    importance: int = Field(ge=1, le=5, description="Importance rating 1-5")


class ProbabilityEstimate(BaseModel):
    """Probability estimate with confidence interval."""

    yes_probability: float = Field(ge=0.0, le=1.0)
    confidence_interval_low: float = Field(ge=0.0, le=1.0)
    confidence_interval_high: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel


class Tier1Research(BaseModel):
    """Tier 1 (Fast) research results."""

    market_id: str
    research_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Search results
    queries_used: list[str]
    sources_found: list[Source]

    # Quick analysis
    summary: str
    recent_developments: bool
    quality_sources_available: bool

    # Decision
    proceed_to_tier2: bool
    reasoning: str
    preliminary_edge: Optional[float] = None

    # Timing
    research_duration_seconds: float


class Tier2Research(BaseModel):
    """Tier 2 (Deep) research results."""

    market_id: str
    question: str
    research_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Model estimate
    model_estimate: ProbabilityEstimate

    # Detailed analysis
    key_findings: list[ResearchFinding]
    reasoning: str
    base_rate: Optional[str] = None
    recent_developments: str

    # Risk analysis
    risks_to_thesis: list[str]

    # Sources
    sources: list[Source]
    information_quality: InformationQuality

    # Timing
    research_duration_seconds: float


class ConfidenceScore(BaseModel):
    """Confidence score breakdown."""

    source_quality: float = Field(ge=0.0, le=1.0)
    information_recency: float = Field(ge=0.0, le=1.0)
    consensus_level: float = Field(ge=0.0, le=1.0)
    base_rate_alignment: float = Field(ge=0.0, le=1.0)
    reasoning_clarity: float = Field(ge=0.0, le=1.0)

    overall_score: float = Field(ge=0.0, le=1.0)


class Opportunity(BaseModel):
    """Trading opportunity model."""

    market_id: str
    question: str

    # Market data
    market: Market

    # Research
    tier2_research: Tier2Research

    # Model vs Market
    model_probability: float
    market_probability: float
    edge: float

    # Scoring
    confidence_score: ConfidenceScore
    liquidity_factor: float
    opportunity_score: float

    # Recommendation
    recommended_action: str
    recommended_outcome: str

    # Risk flags
    red_flags: list[str] = Field(default_factory=list)
    green_flags: list[str] = Field(default_factory=list)

    # Links
    polymarket_url: str


class DailyRun(BaseModel):
    """Daily run results model."""

    run_date: datetime
    run_start_time: datetime
    run_end_time: Optional[datetime] = None

    # Counts
    markets_fetched: int
    markets_after_filtering: int
    markets_tier1_researched: int
    markets_tier2_researched: int
    opportunities_identified: int

    # Costs
    total_cost: float

    # Results
    opportunities: list[Opportunity] = Field(default_factory=list)

    # Errors
    errors: list[str] = Field(default_factory=list)

    # Timing breakdown
    timing: dict[str, float] = Field(default_factory=dict)
