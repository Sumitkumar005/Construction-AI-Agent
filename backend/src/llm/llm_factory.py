"""Factory for creating LLM instances based on configuration."""

import logging
from typing import Optional
try:
    from langchain_core.language_models import BaseLanguageModel
except ImportError:
    # Fallback for older versions
    from langchain.schema import BaseLanguageModel

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except ImportError:
    ChatOpenAI = None
    OpenAIEmbeddings = None

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from src.core.config import settings

logger = logging.getLogger(__name__)


class SentenceTransformerEmbeddings:
    """Wrapper for sentence-transformers to work with LangChain."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
        logger.info(f"Loading sentence-transformers model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
    
    def embed_documents(self, texts: list) -> list:
        """Embed a list of documents."""
        return self.model.encode(texts, show_progress_bar=False).tolist()
    
    async def aembed_documents(self, texts: list) -> list:
        """Async embed documents."""
        import asyncio
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_documents, texts)
    
    def embed_query(self, text: str) -> list:
        """Embed a single query."""
        return self.model.encode([text], show_progress_bar=False)[0].tolist()
    
    async def aembed_query(self, text: str) -> list:
        """Async embed query."""
        import asyncio
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_query, text)


def get_llm(temperature: float = 0.1, model: Optional[str] = None) -> BaseLanguageModel:
    """
    Get LLM instance based on configuration.
    
    Args:
        temperature: Temperature for generation
        model: Override model name
        
    Returns:
        LangChain LLM instance
    """
    provider = settings.llm_provider.lower()
    model_name = model or settings.default_llm_model
    
    # Prevent using decommissioned models
    deprecated_models = ["llama-3.1-70b-versatile"]
    if model_name in deprecated_models:
        logger.warning(f"Model {model_name} is decommissioned! Using default: llama-3.1-8b-instant")
        model_name = "llama-3.1-8b-instant"
    
    if provider == "groq":
        if ChatGroq is None:
            raise ImportError("langchain-groq not installed. Run: pip install langchain-groq")
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not set in .env")
        
        logger.info(f"Using Groq with model: {model_name}")
        return ChatGroq(
            model=model_name,
            temperature=temperature,
            groq_api_key=settings.groq_api_key
        )
    
    elif provider == "openai":
        if ChatOpenAI is None:
            raise ImportError("langchain-openai not installed. Run: pip install langchain-openai")
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set in .env")
        
        logger.info(f"Using OpenAI with model: {model_name}")
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=settings.openai_api_key
        )
    
    elif provider == "anthropic":
        if ChatAnthropic is None:
            raise ImportError("langchain-anthropic not installed. Run: pip install langchain-anthropic")
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in .env")
        
        logger.info(f"Using Anthropic with model: {model_name}")
        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            api_key=settings.anthropic_api_key
        )
    
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def get_embeddings():
    """
    Get embeddings instance based on configuration.
    
    Returns:
        Embeddings instance
    """
    embedding_model = settings.default_embedding_model
    
    if embedding_model == "sentence-transformers":
        logger.info("Using sentence-transformers for embeddings (free, local)")
        return SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    
    elif embedding_model.startswith("text-embedding"):
        # OpenAI embeddings
        if OpenAIEmbeddings is None:
            raise ImportError("langchain-openai not installed. Run: pip install langchain-openai")
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY required for OpenAI embeddings")
        
        logger.info(f"Using OpenAI embeddings: {embedding_model}")
        return OpenAIEmbeddings(
            model=embedding_model,
            api_key=settings.openai_api_key
        )
    
    else:
        # Default to sentence-transformers
        logger.info("Using sentence-transformers (default)")
        return SentenceTransformerEmbeddings()

