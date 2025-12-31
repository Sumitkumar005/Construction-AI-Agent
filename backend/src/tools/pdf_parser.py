"""PDF parsing utilities for construction documents."""

from typing import Dict, List, Any
import logging
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import pymupdf as fitz  # PyMuPDF
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from src.core.config import settings

logger = logging.getLogger(__name__)


class PDFParser:
    """Parser for construction PDF documents (handles large files 500MB-1GB+)."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse PDF document and extract text, images, and metadata.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with pages, text, images, and metadata
        """
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) not installed. Install with: pip install pymupdf")
        
        try:
            # Check file size
            file_size_mb = Path(pdf_path).stat().st_size / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                logger.warning(f"Large file detected: {file_size_mb:.2f}MB")
            
            # Parse PDF in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._parse_pdf_sync,
                pdf_path
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise
    
    def _parse_pdf_sync(self, pdf_path: str) -> Dict[str, Any]:
        """Synchronous PDF parsing."""
        doc = fitz.open(pdf_path)
        
        pages_data = []
        metadata = {
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "creator": doc.metadata.get("creator", ""),
            "producer": doc.metadata.get("producer", ""),
            "creation_date": doc.metadata.get("creationDate", ""),
            "modification_date": doc.metadata.get("modDate", ""),
            "page_count": len(doc),
            "file_size_mb": Path(pdf_path).stat().st_size / (1024 * 1024)
        }
        
        # Process pages
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text
            text = page.get_text()
            
            # Check for images
            image_list = page.get_images()
            has_images = len(image_list) > 0
            
            # Get page dimensions
            rect = page.rect
            dimensions = {
                "width": rect.width,
                "height": rect.height
            }
            
            pages_data.append({
                "page_number": page_num + 1,
                "text": text,
                "has_images": has_images,
                "image_count": len(image_list),
                "dimensions": dimensions
            })
        
        doc.close()
        
        return {
            "pages": pages_data,
            "metadata": metadata
        }
    
    async def extract_images(self, pdf_path: str, output_dir: str = "temp_images") -> List[str]:
        """Extract images from PDF pages. If no embedded images, render pages as images."""
        if fitz is None:
            raise ImportError("PyMuPDF not installed")
        
        try:
            # Create directory with parents if needed
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            doc = fitz.open(pdf_path)
            image_paths = []
            
            # First, try to extract embedded images
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_idx, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        image_path = Path(output_dir) / f"page_{page_num+1}_img_{img_idx}.{image_ext}"
                        image_path.write_bytes(image_bytes)
                        image_paths.append(str(image_path))
                    except Exception as e:
                        logger.warning(f"Failed to extract embedded image {img_idx} from page {page_num+1}: {e}")
            
            # If no embedded images found, render pages as PNG images (for floor plans)
            if not image_paths:
                logger.info("No embedded images found, rendering PDF pages as images...")
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    # Render page as image with high DPI for quality
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)
                    
                    image_path = Path(output_dir) / f"page_{page_num+1}.png"
                    pix.save(str(image_path))
                    image_paths.append(str(image_path))
                    logger.info(f"Rendered page {page_num+1} as image: {image_path}")
            
            doc.close()
            logger.info(f"Extracted {len(image_paths)} images from PDF")
            return image_paths
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}", exc_info=True)
            raise


