"""Expert review models."""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    """Review status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"


class ReviewItem(BaseModel):
    """Individual item for review."""
    trade: str
    item: str
    ai_quantity: float
    expert_quantity: Optional[float] = None
    confidence: float
    flagged: bool = False
    notes: Optional[str] = None


class ExpertReview(BaseModel):
    """Expert review model."""
    review_id: str
    project_id: str
    status: ReviewStatus = ReviewStatus.PENDING
    items: List[ReviewItem] = []
    overall_confidence: float
    expert_id: Optional[str] = None
    expert_name: Optional[str] = None
    review_notes: Optional[str] = None
    corrections: Dict = {}
    created_at: datetime = Field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    time_taken_minutes: Optional[float] = None

