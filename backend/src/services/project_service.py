"""Project management service."""

from typing import Dict, List, Optional
import logging
from datetime import datetime
import uuid
from pathlib import Path

from src.models.project import Project, ProjectStatus, TakeoffResult
from src.models.trade import TradeType

logger = logging.getLogger(__name__)


class ProjectService:
    """Manage projects and takeoffs."""
    
    def __init__(self, storage_path: Path = Path("data/projects")):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.projects: Dict[str, Project] = {}
        self.cancellation_flags: Dict[str, bool] = {}  # Track cancellation requests
    
    def create_project(
        self,
        file_name: str,
        file_path: str,
        file_size_mb: float,
        selected_trades: List[str],
        name: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Project:
        """Create a new project."""
        project_id = str(uuid.uuid4())
        
        project = Project(
            project_id=project_id,
            name=name or file_name,
            file_path=file_path,
            file_name=file_name,
            file_size_mb=file_size_mb,
            selected_trades=selected_trades,
            status=ProjectStatus.UPLOADED,
            created_by=created_by
        )
        
        self.projects[project_id] = project
        self._save_project(project)
        
        logger.info(f"Created project: {project_id}")
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        if project_id in self.projects:
            return self.projects[project_id]
        
        # Try to load from storage
        project_file = self.storage_path / f"{project_id}.json"
        if project_file.exists():
            # In production, would deserialize from JSON
            pass
        
        return None
    
    def update_project_status(
        self,
        project_id: str,
        status: ProjectStatus,
        takeoff_result: Optional[TakeoffResult] = None
    ) -> bool:
        """Update project status."""
        project = self.get_project(project_id)
        if not project:
            return False
        
        project.status = status
        project.updated_at = datetime.now()
        
        if takeoff_result:
            project.takeoff_result = takeoff_result
        
        self._save_project(project)
        return True
    
    def list_projects(
        self,
        created_by: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
        limit: int = 50
    ) -> List[Project]:
        """List projects with filters."""
        projects = list(self.projects.values())
        
        if created_by:
            projects = [p for p in projects if p.created_by == created_by]
        
        if status:
            projects = [p for p in projects if p.status == status]
        
        # Sort by created_at descending
        projects.sort(key=lambda p: p.created_at, reverse=True)
        
        return projects[:limit]
    
    def cancel_processing(self, project_id: str) -> bool:
        """Cancel processing for a project."""
        project = self.get_project(project_id)
        if not project:
            return False
        
        if project.status != ProjectStatus.PROCESSING:
            return False
        
        self.cancellation_flags[project_id] = True
        logger.info(f"Cancellation requested for project: {project_id}")
        return True
    
    def is_cancelled(self, project_id: str) -> bool:
        """Check if processing is cancelled for a project."""
        return self.cancellation_flags.get(project_id, False)
    
    def clear_cancellation(self, project_id: str):
        """Clear cancellation flag for a project."""
        self.cancellation_flags.pop(project_id, None)
    
    def _save_project(self, project: Project):
        """Save project to storage."""
        # In production, would serialize to JSON/database
        pass

