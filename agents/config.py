"""Configuration management for Polymarket Trading Agent."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class PolymarketConfig(BaseModel):
    """Polymarket API configuration."""

    gamma_url: str = "https://gamma-api.polymarket.com"
    clob_url: str = "https://clob.polymarket.com"
    chain_id: int = 137  # Polygon mainnet
    polygon_rpc: str = "https://polygon-rpc.com"
    exchange_address: str = "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e"
    neg_risk_exchange_address: str = "0xC5d563A36AE78145C45a50134d48A1215220f80a"
    usdc_address: str = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    ctf_address: str = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"


class FilterConfig(BaseModel):
    """Market filtering configuration."""

    min_volume: float = Field(
        default=10000.0, description="Minimum market volume in USD"
    )
    min_liquidity: float = Field(
        default=5000.0, description="Minimum market liquidity in USD"
    )
    min_resolution_days: int = Field(
        default=7, description="Minimum days until resolution"
    )
    max_resolution_days: int = Field(
        default=30, description="Maximum days until resolution"
    )
    min_market_age_days: int = Field(
        default=1, description="Minimum market age in days"
    )
    max_market_age_days: int = Field(
        default=14, description="Maximum market age in days (2 weeks)"
    )

    # Categories to focus on
    focus_categories: list[str] = Field(
        default=["Politics", "Business", "Technology", "Regulatory"],
        description="Categories to focus research on",
    )

    # Categories to exclude
    exclude_categories: list[str] = Field(
        default=["Sports", "Crypto", "Entertainment"],
        description="Categories to exclude",
    )

    # Maximum outcomes for multiple choice markets
    max_outcomes: int = Field(
        default=4, description="Maximum number of outcomes for multiple choice markets"
    )


class ResearchConfig(BaseModel):
    """Research configuration."""

    # Tier 1 (Fast) Research
    tier1_timeout_seconds: int = Field(
        default=90, description="Timeout for Tier 1 research per market"
    )
    tier1_max_sources: int = Field(
        default=10, description="Maximum sources to scan in Tier 1"
    )
    tier1_queries_per_market: int = Field(
        default=3, description="Number of search queries per market"
    )
    tier1_model: str = Field(
        default="claude-3-5-haiku-20241022", description="Model for Tier 1 analysis"
    )

    # Tier 2 (Deep) Research
    tier2_timeout_seconds: int = Field(
        default=600, description="Timeout for Tier 2 research per market"
    )
    tier2_max_sources: int = Field(
        default=20, description="Maximum sources to scan in Tier 2"
    )
    tier2_queries_per_market: int = Field(
        default=8, description="Number of search queries per market"
    )
    tier2_model: str = Field(
        default="claude-3-5-sonnet-20241022", description="Model for Tier 2 analysis"
    )

    # Research thresholds
    min_edge_for_deep_research: float = Field(
        default=0.10, description="Minimum edge to proceed to Tier 2"
    )
    min_source_quality: int = Field(
        default=3, description="Minimum source quality rating (1-5)"
    )


class OpportunityConfig(BaseModel):
    """Opportunity scoring configuration."""

    min_edge_for_report: float = Field(
        default=0.05, description="Minimum edge to include in report"
    )
    min_confidence_score: float = Field(
        default=0.5, description="Minimum confidence score"
    )
    min_opportunity_score: float = Field(
        default=0.03, description="Minimum opportunity score"
    )

    # Scoring weights
    source_quality_weight: float = Field(
        default=0.25, description="Weight for source quality"
    )
    information_recency_weight: float = Field(
        default=0.20, description="Weight for information recency"
    )
    consensus_weight: float = Field(
        default=0.20, description="Weight for source consensus"
    )
    base_rate_weight: float = Field(
        default=0.20, description="Weight for base rate alignment"
    )
    reasoning_clarity_weight: float = Field(
        default=0.15, description="Weight for reasoning clarity"
    )


class EmailConfig(BaseModel):
    """Email configuration."""

    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")

    from_email: Optional[str] = Field(default=None, description="From email address")
    to_email: Optional[str] = Field(default=None, description="To email address")

    send_time_hour: int = Field(default=9, description="Hour to send report (0-23)")
    send_time_minute: int = Field(default=0, description="Minute to send report (0-59)")


class SchedulerConfig(BaseModel):
    """Scheduler configuration."""

    cron_hour: int = Field(default=8, description="Hour to run daily cron (0-23)")
    cron_minute: int = Field(default=0, description="Minute to run daily cron (0-59)")
    timezone: str = Field(default="UTC", description="Timezone for scheduling")

    max_daily_cost: float = Field(
        default=50.0, description="Maximum daily API cost in USD"
    )
    max_markets_to_filter: int = Field(
        default=25, description="Maximum markets to filter down to"
    )
    max_markets_for_deep_research: int = Field(
        default=8, description="Maximum markets for deep research"
    )


class APIConfig(BaseModel):
    """API keys and credentials."""

    anthropic_api_key: str = Field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    tavily_api_key: str = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))
    newsapi_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("NEWSAPI_API_KEY")
    )
    polygon_wallet_private_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("POLYGON_WALLET_PRIVATE_KEY")
    )

    # Email credentials
    email_smtp_username: Optional[str] = Field(
        default_factory=lambda: os.getenv("EMAIL_SMTP_USERNAME")
    )
    email_smtp_password: Optional[str] = Field(
        default_factory=lambda: os.getenv("EMAIL_SMTP_PASSWORD")
    )
    email_from: Optional[str] = Field(default_factory=lambda: os.getenv("EMAIL_FROM"))
    email_to: Optional[str] = Field(default_factory=lambda: os.getenv("EMAIL_TO"))


class LoggingConfig(BaseModel):
    """Logging configuration."""

    log_level: str = Field(default="INFO", description="Logging level")
    log_dir: str = Field(default="logs", description="Directory for log files")
    log_file_prefix: str = Field(
        default="polymarket_agent", description="Prefix for log files"
    )

    # Data logging
    data_log_dir: str = Field(
        default="data/logs", description="Directory for data logs"
    )
    enable_json_logging: bool = Field(
        default=True, description="Enable JSON-formatted logs"
    )


class Config(BaseModel):
    """Main configuration object."""

    polymarket: PolymarketConfig = Field(default_factory=PolymarketConfig)
    filter: FilterConfig = Field(default_factory=FilterConfig)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    opportunity: OpportunityConfig = Field(default_factory=OpportunityConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Override email config with API config values
        if self.api.email_smtp_username:
            self.email.smtp_username = self.api.email_smtp_username
        if self.api.email_smtp_password:
            self.email.smtp_password = self.api.email_smtp_password
        if self.api.email_from:
            self.email.from_email = self.api.email_from
        if self.api.email_to:
            self.email.to_email = self.api.email_to


# Global config instance
config = Config()
