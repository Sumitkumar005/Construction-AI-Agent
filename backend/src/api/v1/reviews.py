"""Expert review endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
import logging

from src.services import project_service, review_service  # Use shared singleton instances
from src.models.review import ReviewStatus
from src.models.project import ProjectStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])


class ReviewUpdateRequest(BaseModel):
    expert_id: str
    expert_name: str
    corrections: dict = {}
    notes: Optional[str] = None
    status: str = "approved"


@router.get("/queue")
async def get_review_queue():
    """Get projects waiting for expert review."""
    queue = review_service.get_review_queue()
    return {
        "queue": [r.dict() for r in queue],
        "count": len(queue)
    }


@router.get("/{review_id}")
async def get_review(review_id: str):
    """Get review details."""
    review = review_service.get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return review.dict()


@router.get("/project/{project_id}")
async def get_review_by_project(project_id: str):
    """Get review for a project."""
    review = review_service.get_review_by_project(project_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return review.dict()


@router.post("/{review_id}/approve")
async def approve_review(review_id: str, request: ReviewUpdateRequest):
    """Approve a review."""
    success = review_service.approve_review(
        review_id=review_id,
        expert_id=request.expert_id,
        expert_name=request.expert_name
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Update project status
    review = review_service.get_review(review_id)
    if review:
        project_service.update_project_status(
            review.project_id,
            ProjectStatus.COMPLETED
        )
    
    return {"message": "Review approved", "review_id": review_id}


@router.post("/{review_id}/update")
async def update_review(review_id: str, request: ReviewUpdateRequest):
    """Update expert review with corrections."""
    try:
        status = ReviewStatus(request.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
    
    success = review_service.update_review(
        review_id=review_id,
        expert_id=request.expert_id,
        expert_name=request.expert_name,
        corrections=request.corrections,
        notes=request.notes,
        status=status
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Update project status
    review = review_service.get_review(review_id)
    if review and status == ReviewStatus.APPROVED:
        project_service.update_project_status(
            review.project_id,
            ProjectStatus.COMPLETED
        )
    
    return {"message": "Review updated", "review_id": review_id}

