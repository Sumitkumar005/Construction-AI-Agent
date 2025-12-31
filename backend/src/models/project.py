"""Project and takeoff result models."""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """Project processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    AI_COMPLETE = "ai_complete"
    EXPERT_REVIEW = "expert_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TakeoffResult(BaseModel):
    """Complete takeoff result."""
    project_id: str
    status: ProjectStatus
    trades: List[str]  # Selected trades
    quantities: Dict[str, Dict]  # Trade -> quantities
    confidence_scores: Dict[str, float]
    verification_results: Dict
    expert_reviewed: bool = False
    expert_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    metadata: Dict = {}


class Project(BaseModel):
    """Project model."""
    project_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    file_path: str
    file_name: str
    file_size_mb: float
    selected_trades: List[str]
    status: ProjectStatus = ProjectStatus.UPLOADED
    takeoff_result: Optional[TakeoffResult] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    metadata: Dict = {}

