"""Expert review service for human-in-the-loop validation."""

from typing import Dict, List, Optional
import logging
from datetime import datetime
import uuid

from src.models.review import ExpertReview, ReviewStatus, ReviewItem
from src.models.project import Project, ProjectStatus

logger = logging.getLogger(__name__)


class ExpertReviewService:
    """Manage expert reviews of AI-generated takeoffs."""
    
    def __init__(self):
        self.reviews: Dict[str, ExpertReview] = {}
        self.review_queue: List[str] = []  # Project IDs waiting for review
    
    def create_review(
        self,
        project_id: str,
        takeoff_result: Dict,
        auto_approve_threshold: float = 0.95
    ) -> ExpertReview:
        """Create expert review for a takeoff."""
        review_id = str(uuid.uuid4())
        
        # Check if auto-approve (high confidence)
        overall_confidence = takeoff_result.get("confidence_scores", {}).get("overall", 0.0)
        
        if overall_confidence >= auto_approve_threshold:
            status = ReviewStatus.APPROVED
        else:
            status = ReviewStatus.PENDING
            self.review_queue.append(project_id)
        
        # Create review items from quantities
        items = []
        quantities = takeoff_result.get("quantities", {})
        confidence_scores = takeoff_result.get("confidence_scores", {})
        
        for trade, trade_quantities in quantities.items():
            if isinstance(trade_quantities, dict):
                trade_confidence = confidence_scores.get(trade, 0.85)
                
                for item, quantity in trade_quantities.items():
                    if isinstance(quantity, (int, float)):
                        items.append(ReviewItem(
                            trade=trade,
                            item=item,
                            ai_quantity=quantity,
                            confidence=trade_confidence,
                            flagged=trade_confidence < 0.7
                        ))
        
        review = ExpertReview(
            review_id=review_id,
            project_id=project_id,
            status=status,
            items=items,
            overall_confidence=overall_confidence
        )
        
        self.reviews[review_id] = review
        
        logger.info(f"Created review {review_id} for project {project_id} (status: {status})")
        return review
    
    def get_review(self, review_id: str) -> Optional[ExpertReview]:
        """Get review by ID."""
        return self.reviews.get(review_id)
    
    def get_review_by_project(self, project_id: str) -> Optional[ExpertReview]:
        """Get review by project ID."""
        for review in self.reviews.values():
            if review.project_id == project_id:
                return review
        return None
    
    def update_review(
        self,
        review_id: str,
        expert_id: str,
        expert_name: str,
        corrections: Dict,
        notes: Optional[str] = None,
        status: ReviewStatus = ReviewStatus.APPROVED
    ) -> bool:
        """Update expert review."""
        review = self.get_review(review_id)
        if not review:
            return False
        
        review.expert_id = expert_id
        review.expert_name = expert_name
        review.status = status
        review.review_notes = notes
        review.corrections = corrections
        review.reviewed_at = datetime.now()
        
        # Update quantities based on corrections
        for item in review.items:
            key = f"{item.trade}.{item.item}"
            if key in corrections:
                item.expert_quantity = corrections[key]
                item.flagged = False
        
        # Calculate time taken
        if review.created_at:
            delta = review.reviewed_at - review.created_at
            review.time_taken_minutes = delta.total_seconds() / 60
        
        logger.info(f"Updated review {review_id} by expert {expert_name}")
        return True
    
    def get_review_queue(self) -> List[ExpertReview]:
        """Get projects waiting for expert review."""
        queue = []
        for project_id in self.review_queue:
            review = self.get_review_by_project(project_id)
            if review and review.status == ReviewStatus.PENDING:
                queue.append(review)
        return queue
    
    def approve_review(self, review_id: str, expert_id: str, expert_name: str) -> bool:
        """Approve a review."""
        return self.update_review(
            review_id=review_id,
            expert_id=expert_id,
            expert_name=expert_name,
            corrections={},
            status=ReviewStatus.APPROVED
        )

