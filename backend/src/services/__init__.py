"""Shared service instances."""

from pathlib import Path
from src.services.project_service import ProjectService
from src.services.trade_extractor import TradeExtractor
from src.services.expert_review_service import ExpertReviewService
from src.services.takeoff_exporter import TakeoffExporter

# Shared singleton instances
# These are created once and reused across all routers
project_service = ProjectService(storage_path=Path("data/projects"))
trade_extractor = TradeExtractor()
review_service = ExpertReviewService()
takeoff_exporter = TakeoffExporter()

