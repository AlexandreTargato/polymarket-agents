"""Polymarket Trading Agent - Automated market research system."""

__version__ = "1.0.0"
__author__ = "Generated with Claude Code"

from agents.config import config
from agents.orchestrator import Orchestrator
from agents.scheduler import DailyScheduler

__all__ = [
    "config",
    "Orchestrator",
    "DailyScheduler",
]
