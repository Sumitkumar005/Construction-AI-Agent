"""RAG retrieval system for construction specifications."""

from typing import List, Dict, Optional, Any
import logging

from src.rag.vector_store import VectorStore
from src.core.config import settings

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieval component for RAG pipeline."""
    
    def __init__(self, collection_name: str = "construction_specs"):
        self.vector_store = VectorStore(collection_name=collection_name)
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant specification sections for a query.
        
        Args:
            query: Query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of relevant specification sections with scores
        """
        try:
            logger.info(f"Retrieving specs for query: {query[:100]}...")
            
            # Search vector store
            results = await self.vector_store.search(
                query=query,
                top_k=top_k,
                filter_metadata=filter_metadata
            )
            
            # Format results with additional context
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result["content"],
                    "score": result["score"],
                    "section": result["metadata"].get("section", "Unknown"),
                    "division": result["metadata"].get("division"),
                    "source": result["metadata"].get("doc_id", "Unknown"),
                    "metadata": result["metadata"]
                })
            
            logger.info(f"Retrieved {len(formatted_results)} relevant sections")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error retrieving specs: {e}")
            raise
    
    async def retrieve_by_division(
        self,
        division: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve specs filtered by division (e.g., Division 8, Division 9)."""
        filter_metadata = {"division": division}
        return await self.retrieve(query, top_k, filter_metadata)
    
    async def add_specification_document(
        self,
        content: str,
        doc_id: str,
        division: str = None,
        metadata: Dict = None
    ):
        """
        Add a specification document to the vector store.
        
        Args:
            content: Document content
            doc_id: Document identifier
            division: Division number (8, 9, etc.)
            metadata: Additional metadata
        """
        try:
            from src.rag.chunking import DocumentChunker
            
            chunker = DocumentChunker()
            chunks = chunker.chunk_specification_document(
                content=content,
                doc_id=doc_id,
                division=division
            )
            
            # Add metadata to chunks
            if metadata:
                for chunk in chunks:
                    chunk["metadata"].update(metadata)
            
            # Add to vector store
            await self.vector_store.add_documents(chunks)
            
            logger.info(f"Added specification document: {doc_id}")
            
        except Exception as e:
            logger.error(f"Error adding specification document: {e}")
            raise


