"""FastAPI application for the Construction Document Intelligence System."""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional
import logging
import os
import json
from pathlib import Path
import uuid
import asyncio
from datetime import datetime

from src.orchestration.agent_graph import ConstructionAgentSystem
from src.reports.report_generator import ReportGenerator
from src.api.v1 import projects_router, takeoffs_router, reviews_router, exports_router
from src.core.config import settings
from src.core.middleware import LoggingMiddleware, ErrorHandlingMiddleware

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Construction Document Intelligence API",
    description="AI Agent System for analyzing construction documents",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Initialize agent system
agent_system = ConstructionAgentSystem()
report_generator = ReportGenerator()

# Include API v1 routes
app.include_router(projects_router)
app.include_router(takeoffs_router)
app.include_router(reviews_router)
app.include_router(exports_router)

# Create directories
UPLOAD_DIR = Path("uploads")
REPORTS_DIR = Path("reports")
UPLOAD_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Construction Document Intelligence API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agents_initialized": True,
        "timestamp": datetime.now().isoformat()
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back or process message
            await manager.send_personal_message({
                "type": "message",
                "data": json.loads(data)
            }, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def send_progress_update(client_id: str, stage: str, progress: int, message: str):
    """Send progress update via WebSocket."""
    await manager.broadcast({
        "type": "progress",
        "client_id": client_id,
        "stage": stage,
        "progress": progress,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })


@app.post("/process-document")
async def process_document(
    file: UploadFile = File(...),
    spec_docs: Optional[List[UploadFile]] = File(None),
    client_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """
    Process a construction document through the full agent pipeline.
    """
    client_id = client_id or str(uuid.uuid4())
    
    try:
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            
            # Check file size
            file_size_mb = len(content) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large: {file_size_mb:.2f}MB (max: {settings.max_file_size_mb}MB)"
                )
            
            f.write(content)
        
        logger.info(f"Processing document: {file_path} for client {client_id}")
        
        # Send initial progress
        await send_progress_update(client_id, "upload", 10, "File uploaded successfully")
        
        # Save spec docs if provided
        spec_doc_paths = []
        if spec_docs:
            await send_progress_update(client_id, "specs", 15, "Processing specification documents...")
            for spec_doc in spec_docs:
                spec_id = str(uuid.uuid4())
                spec_path = UPLOAD_DIR / f"{spec_id}_{spec_doc.filename}"
                with open(spec_path, "wb") as f:
                    f.write(await spec_doc.read())
                spec_doc_paths.append(str(spec_path))
        
        # Process document with progress updates
        async def process_with_updates():
            try:
                await send_progress_update(client_id, "extraction", 20, "Extracting document content...")
                await asyncio.sleep(0.1)  # Allow WebSocket to send
                
                await send_progress_update(client_id, "quantity", 40, "Extracting quantities...")
                await asyncio.sleep(0.1)
                
                await send_progress_update(client_id, "cv", 60, "Analyzing floor plans...")
                await asyncio.sleep(0.1)
                
                await send_progress_update(client_id, "specs", 75, "Reasoning over specifications...")
                await asyncio.sleep(0.1)
                
                await send_progress_update(client_id, "verification", 90, "Verifying results...")
                
                results = await agent_system.process_document(
                    pdf_path=str(file_path),
                    spec_docs=spec_doc_paths if spec_doc_paths else None
                )
                
                await send_progress_update(client_id, "complete", 100, "Processing complete!")
                
                return results
            except Exception as e:
                await send_progress_update(client_id, "error", 0, f"Error: {str(e)}")
                raise
        
        results = await process_with_updates()
        results["client_id"] = client_id
        results["file_id"] = file_id
        
        # Cleanup in background
        if background_tasks:
            background_tasks.add_task(cleanup_file, file_path)
            for spec_path in spec_doc_paths:
                background_tasks.add_task(cleanup_file, Path(spec_path))
        
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        await send_progress_update(client_id, "error", 0, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-report")
async def generate_report(
    results: dict,
    format: str = "html"  # html, pdf, markdown
):
    """Generate professional report from analysis results."""
    try:
        report_path = await report_generator.generate_report(
            results=results,
            format=format,
            output_dir=REPORTS_DIR
        )
        
        return FileResponse(
            path=report_path,
            media_type="application/pdf" if format == "pdf" else "text/html",
            filename=Path(report_path).name
        )
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results/{file_id}")
async def get_results(file_id: str):
    """Get stored results by file ID."""
    # In production, would fetch from database
    return {"message": "Results retrieval not implemented", "file_id": file_id}


@app.post("/extract-quantities")
async def extract_quantities(file: UploadFile = File(...)):
    """Extract quantities from a construction document."""
    try:
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        from src.agents.extraction_agent import ExtractionAgent
        from src.agents.quantity_agent import QuantityTakeoffAgent
        
        extraction_agent = ExtractionAgent()
        quantity_agent = QuantityTakeoffAgent()
        
        extraction_results = await extraction_agent.extract_document(str(file_path))
        
        pages = extraction_results.get("pages", [])
        document_text = "\n\n".join([p.get("text", "") for p in pages])
        
        quantity_results = await quantity_agent.extract_quantities(document_text)
        
        cleanup_file(file_path)
        
        return JSONResponse(content={
            "quantities": quantity_results,
            "extraction_metadata": extraction_results.get("metadata", {})
        })
        
    except Exception as e:
        logger.error(f"Error extracting quantities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-floor-plan")
async def analyze_floor_plan(file: UploadFile = File(...)):
    """Analyze a floor plan image using Computer Vision."""
    try:
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        from src.agents.cv_agent import ComputerVisionAgent
        
        cv_agent = ComputerVisionAgent()
        results = await cv_agent.analyze_floor_plan(str(file_path))
        
        cleanup_file(file_path)
        
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Error analyzing floor plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reason-over-specs")
async def reason_over_specs(query: str):
    """Reason over construction specifications using RAG."""
    try:
        from src.agents.spec_reasoning_agent import SpecReasoningAgent
        
        spec_agent = SpecReasoningAgent()
        results = await spec_agent.reason_over_specs(query=query)
        
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Error in spec reasoning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def cleanup_file(file_path: Path):
    """Clean up uploaded file."""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Error cleaning up file {file_path}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
