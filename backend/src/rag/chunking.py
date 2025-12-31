"""Document chunking strategies for RAG."""

from typing import List, Dict, Any
import logging
import uuid

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain_community.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Handles chunking of construction specification documents."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        if separators is None:
            separators = [
                "\n\n## ",  # Markdown headers
                "\n\nSection ",
                "\n\n",
                "\n",
                ". ",
                " "
            ]
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len
        )
    
    def chunk_document(
        self,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk a document into smaller pieces for RAG.
        
        Args:
            content: Document content text
            metadata: Document metadata
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(content)
            
            # Create chunk documents with metadata
            chunk_docs = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    **(metadata or {}),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk)
                }
                
                # Generate UUID for Qdrant (requires UUID or integer, not string)
                chunk_id = str(uuid.uuid4())
                
                chunk_docs.append({
                    "content": chunk,
                    "metadata": chunk_metadata,
                    "id": chunk_id  # Use UUID instead of string
                })
            
            logger.info(f"Chunked document into {len(chunk_docs)} chunks")
            return chunk_docs
            
        except Exception as e:
            logger.error(f"Error chunking document: {e}")
            raise
    
    def chunk_specification_document(
        self,
        content: str,
        doc_id: str,
        division: str = None
    ) -> List[Dict[str, Any]]:
        """
        Specialized chunking for construction specification documents.
        Preserves section structure.
        """
        metadata = {
            "doc_id": doc_id,
            "document_type": "specification",
            "division": division
        }
        
        # Try to preserve section boundaries
        sections = self._extract_sections(content)
        
        all_chunks = []
        for section_name, section_content in sections:
            section_metadata = {
                **metadata,
                "section": section_name
            }
            
            # Chunk each section
            section_chunks = self.chunk_document(
                section_content,
                section_metadata
            )
            all_chunks.extend(section_chunks)
        
        return all_chunks
    
    def _extract_sections(self, content: str) -> List[tuple]:
        """Extract sections from specification document."""
        sections = []
        
        # Look for section markers (Division 8, Section 08, etc.)
        lines = content.split('\n')
        current_section = "Introduction"
        current_content = []
        
        for line in lines:
            # Detect section headers
            if any(marker in line.upper() for marker in [
                "DIVISION", "SECTION", "PART", "CHAPTER"
            ]):
                if current_content:
                    sections.append((current_section, '\n'.join(current_content)))
                current_section = line.strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add final section
        if current_content:
            sections.append((current_section, '\n'.join(current_content)))
        
        return sections if sections else [("Full Document", content)]


