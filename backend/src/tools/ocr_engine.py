"""OCR engine for extracting text from scanned construction documents."""

from typing import Optional
import logging
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

try:
    import easyocr
except ImportError:
    easyocr = None

logger = logging.getLogger(__name__)


class OCREngine:
    """OCR engine for scanned construction documents."""
    
    def __init__(self, engine: str = "auto"):
        """
        Initialize OCR engine.
        
        Args:
            engine: OCR engine to use ('tesseract', 'easyocr', or 'auto')
                   'auto' will use EasyOCR if Tesseract is not available
        """
        # Auto-detect best available engine
        if engine == "auto":
            # Check if Tesseract is available
            try:
                if pytesseract is not None:
                    # Test if Tesseract binary is installed
                    import subprocess
                    result = subprocess.run(['tesseract', '--version'], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        engine = "tesseract"
                    else:
                        engine = "easyocr" if easyocr is not None else "tesseract"
                else:
                    engine = "easyocr" if easyocr is not None else "tesseract"
            except:
                # Tesseract not available, use EasyOCR
                engine = "easyocr" if easyocr is not None else "tesseract"
        
        self.engine = engine
        
        if engine == "easyocr" and easyocr is not None:
            try:
                logger.info("Initializing EasyOCR (this may take a moment on first run)...")
                self.reader = easyocr.Reader(['en'])
                logger.info("EasyOCR initialized successfully")
            except Exception as e:
                logger.warning(f"EasyOCR initialization failed: {e}, falling back to tesseract")
                self.engine = "tesseract"
                self.reader = None
        else:
            self.reader = None
    
    async def extract_text(self, image_path: Optional[str] = None, image=None) -> str:
        """
        Extract text from image using OCR.
        
        Args:
            image_path: Path to image file
            image: PIL Image object (alternative to image_path)
            
        Returns:
            Extracted text
        """
        try:
            if image_path:
                if Image is None:
                    raise ImportError("PIL not installed")
                img = Image.open(image_path)
            elif image:
                img = image
            else:
                raise ValueError("Either image_path or image must be provided")
            
            if self.engine == "easyocr" and self.reader is not None:
                return await self._extract_with_easyocr(img)
            else:
                return await self._extract_with_tesseract(img)
                
        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")
            return ""
    
    async def _extract_with_tesseract(self, image) -> str:
        """Extract text using Tesseract OCR."""
        if pytesseract is None:
            logger.warning("Tesseract not available")
            return ""
        
        try:
            # Configure Tesseract for construction documents
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(image, config=custom_config)
            return text.strip()
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return ""
    
    async def _extract_with_easyocr(self, image) -> str:
        """Extract text using EasyOCR."""
        if self.reader is None:
            return ""
        
        try:
            import numpy as np
            if hasattr(image, 'convert'):
                image_array = np.array(image.convert('RGB'))
            else:
                image_array = np.array(image)
            
            results = self.reader.readtext(image_array)
            text = "\n".join([result[1] for result in results])
            return text.strip()
        except Exception as e:
            logger.error(f"EasyOCR error: {e}")
            return ""


