"""Takeoff export endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
import logging
from pathlib import Path
import uuid

from src.services import project_service, takeoff_exporter  # Use shared singleton instances

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/{project_id}/excel")
async def export_to_excel(project_id: str):
    """Export takeoff to Excel."""
    project = project_service.get_project(project_id)
    if not project or not project.takeoff_result:
        raise HTTPException(status_code=404, detail="Takeoff not found")
    
    try:
        output_dir = Path("exports")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"takeoff_{project_id}_{uuid.uuid4().hex[:8]}.xlsx"
        
        await takeoff_exporter.export_to_excel(
            takeoff_result=project.takeoff_result.dict(),
            output_path=output_path
        )
        
        return FileResponse(
            path=output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"takeoff_{project_id}.xlsx"
        )
    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/csv")
async def export_to_csv(project_id: str):
    """Export takeoff to CSV."""
    project = project_service.get_project(project_id)
    if not project or not project.takeoff_result:
        raise HTTPException(status_code=404, detail="Takeoff not found")
    
    try:
        output_dir = Path("exports")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"takeoff_{project_id}_{uuid.uuid4().hex[:8]}.csv"
        
        await takeoff_exporter.export_to_csv(
            takeoff_result=project.takeoff_result.dict(),
            output_path=output_path
        )
        
        return FileResponse(
            path=output_path,
            media_type="text/csv",
            filename=f"takeoff_{project_id}.csv"
        )
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/pdf")
async def export_to_pdf(project_id: str):
    """Export takeoff to PDF."""
    project = project_service.get_project(project_id)
    if not project or not project.takeoff_result:
        raise HTTPException(status_code=404, detail="Takeoff not found")
    
    try:
        output_dir = Path("exports")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"takeoff_{project_id}_{uuid.uuid4().hex[:8]}.pdf"
        
        # For now, returns HTML (PDF conversion requires additional library)
        html_path = await takeoff_exporter.export_to_pdf(
            takeoff_result=project.takeoff_result.dict(),
            output_path=output_path
        )
        
        return FileResponse(
            path=html_path,
            media_type="text/html",
            filename=f"takeoff_{project_id}.html"
        )
    except Exception as e:
        logger.error(f"Error exporting to PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

