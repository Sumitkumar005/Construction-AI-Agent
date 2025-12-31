"""Vector store implementation using Qdrant."""

from typing import List, Dict, Optional, Any
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from src.core.config import settings
from src.llm.llm_factory import get_embeddings

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector database for storing and retrieving construction specification embeddings."""
    
    def __init__(self, collection_name: str = "construction_specs"):
        self.collection_name = collection_name
        
        # Handle Qdrant Cloud URLs (add port if not present)
        qdrant_url = settings.qdrant_url
        if qdrant_url.startswith('https://') and ':6333' not in qdrant_url:
            qdrant_url = f"{qdrant_url}:6333"
        
        self.client = QdrantClient(
            url=qdrant_url,
            api_key=settings.qdrant_api_key
        )
        self.embeddings = get_embeddings()  # Uses Groq or sentence-transformers
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist, or recreate if dimension mismatch."""
        try:
            # Get actual vector size from embedding model
            try:
                test_embedding = self.embeddings.embed_query("test")
                actual_vector_size = len(test_embedding)
                logger.info(f"Detected vector size: {actual_vector_size} from embedding model")
            except:
                # Default sizes
                if hasattr(self.embeddings, 'model_name') and 'MiniLM' in str(self.embeddings.model_name):
                    actual_vector_size = 384  # sentence-transformers all-MiniLM-L6-v2
                else:
                    actual_vector_size = 1536  # OpenAI or default
                logger.info(f"Using default vector size: {actual_vector_size}")
            
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name} with dimension {actual_vector_size}")
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=actual_vector_size,
                        distance=Distance.COSINE
                    )
                )
            else:
                # Collection exists - check if dimension matches
                try:
                    collection_info = self.client.get_collection(self.collection_name)
                    existing_dim = collection_info.config.params.vectors.size
                    
                    if existing_dim != actual_vector_size:
                        logger.warning(
                            f"⚠️ Collection dimension mismatch! "
                            f"Existing: {existing_dim}, Current model: {actual_vector_size}. "
                            f"Deleting and recreating collection..."
                        )
                        # Delete and recreate with correct dimension
                        self.client.delete_collection(self.collection_name)
                        self.client.create_collection(
                            collection_name=self.collection_name,
                            vectors_config=VectorParams(
                                size=actual_vector_size,
                                distance=Distance.COSINE
                            )
                        )
                        logger.info(f"✅ Recreated collection with correct dimension: {actual_vector_size}")
                    else:
                        logger.info(f"✅ Collection exists with correct dimension: {existing_dim}")
                except Exception as check_error:
                    logger.warning(f"Could not check collection dimension: {check_error}. Assuming correct.")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ):
        """
        Add documents to vector store.
        
        Args:
            documents: List of dicts with 'content', 'metadata', 'id'
            batch_size: Number of documents to process per batch
        """
        try:
            logger.info(f"Adding {len(documents)} documents to vector store...")
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # Generate embeddings
                texts = [doc["content"] for doc in batch]
                embeddings = await self.embeddings.aembed_documents(texts)
                
                # Create points
                points = []
                for doc, embedding in zip(batch, embeddings):
                    # Ensure ID is UUID or integer (Qdrant requirement)
                    doc_id = doc.get("id")
                    if doc_id is None:
                        # Generate UUID if no ID provided
                        import uuid
                        doc_id = str(uuid.uuid4())
                    elif isinstance(doc_id, str):
                        # If string ID, check if it's already a valid UUID
                        try:
                            # Try to parse as UUID
                            uuid.UUID(doc_id)
                            # Already valid UUID, keep as is
                        except ValueError:
                            # Not a valid UUID, convert to UUID5 (deterministic)
                            import uuid
                            doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))
                    elif isinstance(doc_id, int):
                        # Integer is fine, but ensure it's positive
                        if doc_id < 0:
                            doc_id = abs(doc_id)
                    
                    point = PointStruct(
                        id=doc_id,
                        vector=embedding,
                        payload={
                            "content": doc["content"],
                            "metadata": doc.get("metadata", {})
                        }
                    )
                    points.append(point)
                
                # Upload to Qdrant
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
                logger.info(f"Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            logger.info("All documents added successfully")
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of similar documents with scores
        """
        try:
            # Generate query embedding
            query_embedding = await self.embeddings.aembed_query(query)
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=None  # Could add metadata filtering here
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "content": result.payload.get("content", ""),
                    "metadata": result.payload.get("metadata", {}),
                    "score": result.score,
                    "id": result.id
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise
    
    def delete_collection(self):
        """Delete the collection (use with caution)."""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise


