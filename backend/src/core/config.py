"""Configuration management with validation."""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Construction Document Intelligence API"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # LLM API Keys - Using Groq (faster & cheaper)
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None  # Optional, only for embeddings if needed
    anthropic_api_key: Optional[str] = None
    
    # Moondream AI - Vision-language model for floor plan analysis
    moondream_api_key: Optional[str] = None
    
    # LLM Model Settings
    llm_provider: str = "groq"  # groq, openai, anthropic
    default_llm_model: str = "llama-3.1-8b-instant"  # Groq instant model (fast & available, NOT decommissioned)
    # Alternative models: "llama-3.3-70b-versatile", "mixtral-8x7b-32768", "llama-3.2-90b-text-preview"
    # NOTE: "llama-3.1-70b-versatile" is DEPRECATED - do not use!
    default_embedding_model: str = "sentence-transformers"  # Free local embeddings
    # Alternative: "text-embedding-3-small" if using OpenAI for embeddings
    
    # Vector Database
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection: str = "construction_specs"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # File Handling
    max_file_size_mb: int = 1024
    upload_dir: Path = Path("uploads")
    reports_dir: Path = Path("reports")
    exports_dir: Path = Path("exports")
    
    # Processing
    enable_cv_analysis: bool = True
    confidence_threshold: float = 0.7
    max_retries: int = 3
    timeout_seconds: int = 300
    
    # Model Settings
    yolo_model_path: str = "models/yolov8_floorplan.pt"
    
    # CORS
    cors_origins: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173"
    ]
    
    class Config:
        # Look for .env in backend directory
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = False
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories
        self.upload_dir.mkdir(exist_ok=True, parents=True)
        self.reports_dir.mkdir(exist_ok=True, parents=True)
        self.exports_dir.mkdir(exist_ok=True, parents=True)


# Global settings instance
settings = Settings()
