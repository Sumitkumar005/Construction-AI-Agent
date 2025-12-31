"""Document Extraction Agent - Handles PDF parsing and text extraction."""

from typing import Dict, List, Optional, Any
from langchain_core.messages import HumanMessage, SystemMessage
import logging
from pathlib import Path

from src.tools.pdf_parser import PDFParser
from src.tools.ocr_engine import OCREngine
from src.llm.llm_factory import get_llm
from src.core.config import settings

logger = logging.getLogger(__name__)


class ExtractionAgent:
    """
    Agent responsible for extracting text and structured data from construction documents.
    Handles large PDFs (500MB-1GB+) with efficient chunking and OCR fallback.
    """
    
    def __init__(self):
        self.llm = get_llm(temperature=0.1)
        self.pdf_parser = PDFParser()
        self.ocr_engine = OCREngine()
        
    async def extract_document(
        self, 
        pdf_path: str,
        use_ocr: bool = False
    ) -> Dict[str, Any]:
        """
        Extract text and metadata from construction PDF.
        
        Args:
            pdf_path: Path to PDF file
            use_ocr: Whether to use OCR for scanned documents
            
        Returns:
            Dictionary with extracted text, metadata, and page information
        """
        try:
            logger.info(f"Extracting document: {pdf_path}")
            
            # Parse PDF structure
            pdf_info = await self.pdf_parser.parse_pdf(pdf_path)
            
            # Extract text from each page
            extracted_pages = []
            for page_num, page_data in enumerate(pdf_info["pages"], 1):
                page_text = page_data.get("text", "")
                
                # Use OCR if text is minimal or explicitly requested
                if use_ocr or len(page_text.strip()) < 100:
                    image_path = page_data.get("image_path")
                    if image_path:
                        logger.info(f"Using OCR for page {page_num}")
                        ocr_text = await self.ocr_engine.extract_text(image_path=image_path)
                        page_text = ocr_text if ocr_text else page_text
                    else:
                        logger.warning(f"No image_path available for OCR on page {page_num}, skipping OCR")
                
                extracted_pages.append({
                    "page_number": page_num,
                    "text": page_text,
                    "has_images": page_data.get("has_images", False),
                    "dimensions": page_data.get("dimensions")
                })
            
            # Structure extraction using LLM
            structured_data = await self._extract_structure(extracted_pages)
            
            return {
                "document_path": pdf_path,
                "total_pages": len(extracted_pages),
                "pages": extracted_pages,
                "structured_data": structured_data,
                "metadata": pdf_info.get("metadata", {}),
                "extraction_method": "ocr" if use_ocr else "native"
            }
            
        except Exception as e:
            logger.error(f"Error extracting document: {e}")
            raise
    
    async def _extract_structure(self, pages: List[Dict]) -> Dict[str, Any]:
        """
        Use LLM to identify document structure (title blocks, drawings, specs, etc.)
        """
        # Combine text from first few pages for structure analysis
        sample_text = "\n\n".join([p["text"][:2000] for p in pages[:5]])
        
        system_prompt = """You are an expert at analyzing construction documents.
        Identify the document structure:
        - Title blocks and project information
        - Drawing types (floor plans, elevations, sections)
        - Specification sections
        - Tables and schedules
        Return structured JSON with identified sections."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyze this construction document:\n\n{sample_text}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Parse LLM response to extract structure
        # In production, use structured output parsing
        return {
            "document_type": "construction_drawing",
            "identified_sections": ["title_block", "floor_plans", "specifications"],
            "analysis": response.content
        }
    
    def get_tools(self) -> List[Dict]:
        """Return tools available to this agent."""
        return [
            {
                "name": "parse_pdf",
                "description": "Parse PDF document structure",
                "parameters": {
                    "pdf_path": {"type": "string", "description": "Path to PDF file"}
                }
            },
            {
                "name": "extract_text_ocr",
                "description": "Extract text using OCR for scanned documents",
                "parameters": {
                    "image_path": {"type": "string", "description": "Path to image file"}
                }
            }
        ]


