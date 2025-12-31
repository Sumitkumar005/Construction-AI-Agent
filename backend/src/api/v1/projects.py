"""Project management endpoints."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
import logging
import os
from pathlib import Path
import uuid

from src.services import project_service  # Use shared singleton instance
from src.models.project import ProjectStatus
from src.models.trade import TradeType
from src.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=dict)
async def create_project(
    file: UploadFile = File(...),
    trades: str = Form(...),  # Comma-separated trade list
    name: Optional[str] = Form(None),
    created_by: Optional[str] = Form(None)
):
    """Create a new project and upload document."""
    try:
        # Parse trades
        selected_trades = [t.strip() for t in trades.split(",") if t.strip()]
        
        # Validate trades
        valid_trades = [t.value for t in TradeType]
        invalid_trades = [t for t in selected_trades if t not in valid_trades]
        if invalid_trades:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trades: {', '.join(invalid_trades)}"
            )
        
        # Save file
        file_id = str(uuid.uuid4())
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Sanitize filename to prevent path traversal
        safe_filename = os.path.basename(file.filename)
        file_path = upload_dir / f"{file_id}_{safe_filename}"
        
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        # Validate file size
        if file_size_mb > settings.max_file_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file_size_mb:.2f}MB exceeds maximum {settings.max_file_size_mb}MB"
            )
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create project
        project = project_service.create_project(
            file_name=file.filename,
            file_path=str(file_path),
            file_size_mb=file_size_mb,
            selected_trades=selected_trades,
            name=name,
            created_by=created_by
        )
        
        return {
            "project_id": project.project_id,
            "status": project.status,
            "message": "Project created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get project details."""
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project.dict()


@router.get("/")
async def list_projects(
    created_by: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """List projects."""
    status_enum = None
    if status:
        try:
            status_enum = ProjectStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    projects = project_service.list_projects(
        created_by=created_by,
        status=status_enum,
        limit=limit
    )
    
    return {"projects": [p.dict() for p in projects], "total": len(projects)}


@router.get("/trades/supported")
async def get_supported_trades():
    """Get list of supported trades."""
    from src.models.trade import TRADE_CONFIGS
    
    trades = []
    for trade_type, config in TRADE_CONFIGS.items():
        trades.append({
            "id": trade_type.value,
            "name": trade_type.value.replace("_", " ").title(),
            "enabled": config.enabled,
            "unit": config.unit_of_measure
        })
    
    return {"trades": trades}

