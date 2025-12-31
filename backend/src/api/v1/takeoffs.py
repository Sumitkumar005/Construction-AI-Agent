"""Takeoff processing endpoints."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
import logging
import asyncio
from datetime import datetime

from src.services import project_service, trade_extractor, review_service  # Use shared singleton instances
from src.models.project import ProjectStatus
from src.models.trade import TradeType
from src.services.full_agent_pipeline import FullAgentPipeline
from src.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/takeoffs", tags=["takeoffs"])

# Full multi-agent pipeline with RAG integration
full_pipeline = FullAgentPipeline()


@router.post("/{project_id}/process")
async def process_takeoff(
    project_id: str,
    background_tasks: BackgroundTasks
):
    """Process takeoff for a project."""
    project = project_service.get_project(project_id)
    if not project:
        logger.error(f"Project not found: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")
    
    logger.info(f"Processing request for project {project_id}, current status: {project.status.value}")
    
    # Allow restarting if status is FAILED or CANCELLED
    # Also allow if UPLOADED (new project)
    # If stuck in PROCESSING (from crashed process), allow restart
    if project.status == ProjectStatus.PROCESSING:
        # If stuck in processing, allow restart (might be from a crashed process)
        logger.warning(f"Project {project_id} is already PROCESSING, but allowing restart (might be stuck)")
        # Update to FAILED first so we can restart
        project_service.update_project_status(project_id, ProjectStatus.FAILED)
    elif project.status in [ProjectStatus.COMPLETED, ProjectStatus.AI_COMPLETE, ProjectStatus.EXPERT_REVIEW]:
        error_msg = f"Cannot start processing. Current status: {project.status.value}"
        logger.warning(f"{error_msg} for project {project_id}")
        raise HTTPException(
            status_code=400,
            detail=error_msg
        )
    
    # Clear any previous cancellation flag
    project_service.clear_cancellation(project_id)
    
    # Update status
    project_service.update_project_status(project_id, ProjectStatus.PROCESSING)
    logger.info(f"Started processing for project {project_id}")
    
    # Process in background
    background_tasks.add_task(process_takeoff_async, project_id)
    
    return {
        "project_id": project_id,
        "status": "processing",
        "message": "Takeoff processing started"
    }


async def process_takeoff_async(project_id: str):
    """Async takeoff processing using full multi-agent pipeline with RAG."""
    try:
        project = project_service.get_project(project_id)
        if not project:
            return
        
        # Clear any previous cancellation flag
        project_service.clear_cancellation(project_id)
        
        start_time = datetime.now()
        
        # Check for cancellation before starting
        if project_service.is_cancelled(project_id):
            logger.info(f"Processing cancelled before start for project {project_id}")
            project_service.update_project_status(project_id, ProjectStatus.FAILED)
            return
        
        # ============================================
        # USE FULL MULTI-AGENT PIPELINE
        # ============================================
        logger.info(f"🚀 Starting full multi-agent pipeline for project {project_id}")
        
        # Send initial upload progress
        try:
            from src.api.main import send_progress_update
            client_id = f"client_{project_id}"
            await send_progress_update(client_id, "upload", 5, "File uploaded, starting processing...")
        except Exception as e:
            logger.debug(f"Could not send initial progress: {e}")
        
        # Create cancellation check function
        def check_cancelled():
            return project_service.is_cancelled(project_id)
        
        # Create progress callback for WebSocket updates
        async def progress_callback(stage: str, progress: int, message: str):
            try:
                from src.api.main import send_progress_update
                client_id = f"client_{project_id}"
                await send_progress_update(client_id, stage, progress, message)
                logger.debug(f"Progress: {stage} - {progress}% - {message}")
            except Exception as e:
                logger.debug(f"Could not send progress update: {e}")
        
        pipeline_results = await full_pipeline.process_takeoff(
            pdf_path=project.file_path,
            selected_trades=project.selected_trades,
            project_id=project_id,
            project_file_name=project.file_name,
            cancellation_check=check_cancelled,
            progress_callback=progress_callback
        )
        
        # Check for cancellation during pipeline
        if project_service.is_cancelled(project_id):
            logger.info(f"Processing cancelled during pipeline for project {project_id}")
            project_service.update_project_status(project_id, ProjectStatus.FAILED)
            return
        
        # Extract results from pipeline
        trade_results = pipeline_results.get("trade_quantities", {})
        verification_results = pipeline_results.get("verification", {})
        spec_reasoning_results = pipeline_results.get("spec_reasoning")
        
        # Calculate confidence scores from verification results
        confidence_scores = {}
        if verification_results and "checks" in verification_results:
            # Use verification confidence if available
            overall_confidence = verification_results.get("overall_confidence", 0.0)
            for trade_str in project.selected_trades:
                # Try to get trade-specific confidence from verification
                trade_check = verification_results.get("checks", {}).get("quantity_bounds", {}).get("category_results", {}).get(trade_str, {})
                if trade_check and "confidence" in trade_check:
                    confidence_scores[trade_str] = trade_check["confidence"]
                else:
                    confidence_scores[trade_str] = overall_confidence
        else:
            # Fallback: use default confidence
            for trade_str in project.selected_trades:
                confidence_scores[trade_str] = 0.8
        
        overall_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
        
        # Add spec reasoning to verification results if available
        if spec_reasoning_results:
            if not verification_results:
                verification_results = {}
            verification_results["spec_reasoning"] = {
                "compliance": spec_reasoning_results.get("compliance", {}),
                "reasoning": spec_reasoning_results.get("answer", ""),
                "confidence": spec_reasoning_results.get("confidence", 0.0),
                "citations": spec_reasoning_results.get("citations", [])
            }
        
        # Final cancellation check
        if project_service.is_cancelled(project_id):
            logger.info(f"Processing cancelled before completion for project {project_id}")
            project_service.update_project_status(project_id, ProjectStatus.FAILED)
            return
        
        # Create takeoff result
        from src.models.project import TakeoffResult
        takeoff_result = TakeoffResult(
            project_id=project_id,
            status=ProjectStatus.AI_COMPLETE,
            trades=project.selected_trades,
            quantities=trade_results,
            confidence_scores={
                **confidence_scores,
                "overall": overall_confidence
            },
            verification_results=verification_results,
            created_at=start_time,
            completed_at=datetime.now(),
            processing_time_seconds=(datetime.now() - start_time).total_seconds(),
            metadata={
                "pipeline_errors": pipeline_results.get("errors", []),
                "moondream_used": pipeline_results.get("moondream") is not None,
                "cv_used": pipeline_results.get("cv_analysis") is not None,
                "rag_used": spec_reasoning_results is not None
            }
        )
        
        # Create expert review
        review = review_service.create_review(project_id, takeoff_result.dict())
        
        # Update project
        if review.status.value == "approved":
            project_service.update_project_status(
                project_id,
                ProjectStatus.COMPLETED,
                takeoff_result
            )
        else:
            project_service.update_project_status(
                project_id,
                ProjectStatus.EXPERT_REVIEW,
                takeoff_result
            )
        
        # Clear cancellation flag on successful completion
        project_service.clear_cancellation(project_id)
        logger.info(f"✅ Full pipeline completed for project {project_id}: {overall_confidence:.2f} confidence")
        
    except asyncio.CancelledError:
        logger.info(f"Processing cancelled (asyncio) for project {project_id}")
        try:
            project_service.update_project_status(project_id, ProjectStatus.FAILED)
        except:
            pass
        project_service.clear_cancellation(project_id)
    except Exception as e:
        logger.error(f"Error processing takeoff for {project_id}: {e}", exc_info=True)
        try:
            project_service.update_project_status(project_id, ProjectStatus.FAILED)
        except Exception as update_error:
            logger.error(f"Failed to update project status to FAILED: {update_error}")
        project_service.clear_cancellation(project_id)


@router.post("/{project_id}/cancel")
async def cancel_takeoff(project_id: str):
    """Cancel processing for a project."""
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if already completed or cancelled
    if project.status in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED, ProjectStatus.AI_COMPLETE]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel project. Current status: {project.status.value}"
        )
    
    # If not processing, still allow cancellation (might be in a transitional state)
    if project.status != ProjectStatus.PROCESSING:
        logger.warning(f"Attempting to cancel project {project_id} with status {project.status}")
    
    success = project_service.cancel_processing(project_id)
    if not success and project.status == ProjectStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="Failed to cancel processing")
    
    # Update status to cancelled
    project_service.update_project_status(project_id, ProjectStatus.CANCELLED)
    
    return {
        "project_id": project_id,
        "status": "cancelled",
        "message": "Processing cancelled successfully"
    }


@router.get("/{project_id}")
async def get_takeoff(project_id: str):
    """Get takeoff result for a project."""
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Return project status and takeoff result if available
    response = {
        "project_id": project_id,
        "status": project.status.value,
        "project_status": project.status.value
    }
    
    if project.takeoff_result:
        response.update(project.takeoff_result.dict())
    else:
        # Return basic status info if takeoff not yet processed
        response.update({
            "message": "Takeoff processing in progress" if project.status == ProjectStatus.PROCESSING else "Takeoff not yet processed",
            "trades": project.selected_trades,
            "quantities": {},
            "confidence_scores": {}
        })
    
    return response

