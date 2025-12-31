"""Moondream AI service for visual question answering on floor plans."""

from typing import Dict, Optional, List
import logging
from pathlib import Path
import base64
from io import BytesIO

try:
    import moondream as md
    from PIL import Image
except ImportError:
    md = None
    Image = None

from src.core.config import settings

logger = logging.getLogger(__name__)


class MoondreamService:
    """Service for using Moondream AI to extract information from floor plan images."""
    
    def __init__(self):
        if md is None:
            raise ImportError("moondream not installed. Install with: pip install moondream")
        if Image is None:
            raise ImportError("PIL not installed. Install with: pip install pillow")
        
        if not settings.moondream_api_key:
            raise ValueError("MOONDREAM_API_KEY not set in .env")
        
        logger.info("Initializing Moondream AI service...")
        self.model = md.vl(api_key=settings.moondream_api_key)
        logger.info("Moondream AI service initialized")
    
    async def extract_dimensions_from_image(
        self,
        image_path: str,
        question: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Extract room dimensions from a floor plan image using Moondream AI.
        
        Args:
            image_path: Path to floor plan image
            question: Optional custom question (defaults to dimension extraction)
            
        Returns:
            Dictionary with extracted dimensions and metadata
        """
        try:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            logger.info(f"Loading image for Moondream analysis: {image_path}")
            image = Image.open(image_path)
            
            # Default question for dimension extraction - explicitly ask for ALL rooms
            if question is None:
                question = (
                    "List EVERY SINGLE room in this floor plan with their exact dimensions. "
                    "Include ALL rooms such as: Bed Room (there may be multiple - list each one separately), "
                    "Drawing Room, Dining Room, Kitchen, Bath/Toilet, Pooja, Store, Parking, and any other rooms. "
                    "For each room, provide: Room Name: Length × Width (include inches if present, e.g., '9' 3\" × 10' 3\"'). "
                    "If there are multiple rooms with the same name, distinguish them (e.g., 'Top Bed Room', 'Bottom Bed Room'). "
                    "Also provide the overall dimensions of the entire floor plan if visible."
                )
            
            logger.info(f"Asking Moondream: {question}")
            result = self.model.query(image, question)
            
            answer = result.get("answer", "")
            request_id = result.get("request_id", "")
            
            logger.info(f"Moondream response (ID: {request_id}): {answer[:200]}...")
            
            # Parse the answer to extract dimensions
            parsed_dimensions = self._parse_dimensions_from_answer(answer)
            
            return {
                "raw_answer": answer,
                "request_id": request_id,
                "dimensions": parsed_dimensions,
                "parsed_successfully": len(parsed_dimensions) > 0
            }
            
        except Exception as e:
            logger.error(f"Error extracting dimensions with Moondream: {e}", exc_info=True)
            return {
                "raw_answer": "",
                "request_id": "",
                "dimensions": {},
                "parsed_successfully": False,
                "error": str(e)
            }
    
    def _parse_dimensions_from_answer(self, answer: str) -> Dict[str, Dict]:
        """
        Parse room dimensions from Moondream's answer.
        
        Handles both JSON format: {"Bed Rooms": [{"name": "...", "dimensions": "..."}]}
        and plain text format: "Bedroom: 11' x 10'"
        
        Returns:
            Dictionary mapping room names to their dimensions
        """
        import re
        import json
        
        dimensions = {}
        
        # Try to parse as JSON first (Moondream sometimes returns JSON)
        try:
            # Clean up the answer - might have extra text before/after JSON
            answer_clean = answer.strip()
            
            # Try to find JSON object in the response
            json_start = answer_clean.find('{')
            json_end = answer_clean.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = answer_clean[json_start:json_end]
                json_data = json.loads(json_str)
                
                logger.info(f"Parsing Moondream response as JSON: {list(json_data.keys())}")
                
                # Handle different JSON structures
                for key, value in json_data.items():
                    # Skip "Overall Dimensions" - we'll handle it separately
                    if "overall" in key.lower() or "total" in key.lower() or "entire" in key.lower():
                        if isinstance(value, (str, dict)):
                            # Will be handled in overall dimensions section
                            continue
                    
                    if isinstance(value, list):
                        # Format: {"Bed Rooms": [{"name": "...", "dimensions": "..."}]}
                        # OR: {"Bed Rooms": [{"Name": "...", "Dimensions": "..."}]}
                        # OR: {"Bed Rooms": [{"Room Name": "...", "Length": "...", "Width": "..."}]}
                        logger.debug(f"Processing list for key '{key}' with {len(value)} items")
                        for idx, item in enumerate(value):
                            if isinstance(item, dict):
                                logger.debug(f"Item {idx}: {item}")
                                # Try different key variations (case-insensitive)
                                room_name = (
                                    item.get("name") or 
                                    item.get("Name") or 
                                    item.get("room_name") or 
                                    item.get("Room Name") or
                                    item.get("room") or
                                    f"{key} {idx + 1}"  # Fallback: "Bed Rooms 1", "Bed Rooms 2"
                                )
                                
                                # Try to get dimensions - handle different formats
                                dim_str = (
                                    item.get("dimensions") or 
                                    item.get("Dimensions") or
                                    item.get("dimension") or
                                    ""
                                )
                                
                                # If no dimensions string, try Length x Width format
                                if not dim_str:
                                    length = item.get("Length") or item.get("length") or ""
                                    width = item.get("Width") or item.get("width") or ""
                                    if length and width:
                                        dim_str = f"{length} x {width}"
                                
                                logger.debug(f"Extracted: room_name='{room_name}', dim_str='{dim_str}'")
                                
                                if room_name and dim_str:
                                    parsed = self._parse_dimension_string(room_name, dim_str)
                                    if parsed:
                                        dimensions[room_name] = parsed
                                        logger.info(f"✅ Extracted room from JSON: {room_name} = {dim_str} → {parsed['area_sqft']} sqft")
                                    else:
                                        logger.warning(f"❌ Failed to parse dimension for {room_name}: {dim_str}")
                                else:
                                    logger.warning(f"⚠️ Missing room_name or dim_str: room_name='{room_name}', dim_str='{dim_str}', item keys={list(item.keys())}")
                    elif isinstance(value, dict):
                        # Format: {"Bed Room": {"dimensions": "11' x 10'"}}
                        # OR: {"Bed Room": {"Dimensions": "11' x 10'"}}
                        dim_str = value.get("dimensions") or value.get("Dimensions") or value.get("dimension") or ""
                        if not dim_str:
                            # Try Length x Width
                            length = value.get("Length") or value.get("length") or ""
                            width = value.get("Width") or value.get("width") or ""
                            if length and width:
                                dim_str = f"{length} x {width}"
                        
                        if dim_str:
                            parsed = self._parse_dimension_string(key, dim_str)
                            if parsed:
                                dimensions[key] = parsed
                    elif isinstance(value, str):
                        # Format: {"Bed Room": "11' x 10'"}
                        parsed = self._parse_dimension_string(key, value)
                        if parsed:
                            dimensions[key] = parsed
                
                if dimensions:
                    logger.info(f"Successfully parsed {len(dimensions)} rooms from JSON")
                    return dimensions
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.debug(f"Failed to parse as JSON, trying text format: {e}")
            # Fall through to text parsing
        
        # Fallback: Parse as plain text
        # Pattern to match: "Room Name: 11' x 10'" or "Room Name: 9' 3\" x 10' 3\""
        pattern = r'([A-Za-z\s]+(?:Room|Area|Space|Bath|Toilet|Kitchen|Dining|Drawing|Pooja|Store|Parking|Bedroom|Bed\s+Room)?):?\s*(\d+(?:\s*\d+)?(?:\s*[\'"])?)\s*[\'"]?\s*[x×]\s*(\d+(?:\s*\d+)?(?:\s*[\'"])?)\s*[\'"]?'
        
        matches = re.finditer(pattern, answer, re.IGNORECASE)
        
        for match in matches:
            room_name = match.group(1).strip()
            length_str = match.group(2).strip()
            width_str = match.group(3).strip()
            
            parsed = self._parse_dimension_string(room_name, f"{length_str} x {width_str}")
            if parsed:
                dimensions[room_name] = parsed
        
        # Also look for overall dimensions (only if not already found in JSON)
        if "overall" not in dimensions:
            overall_pattern = r'(?:overall|total|entire|whole).*?(\d+(?:\s*\d+)?)\s*[\'"]?\s*[x×]\s*(\d+(?:\s*\d+)?)\s*[\'"]?'
            overall_match = re.search(overall_pattern, answer, re.IGNORECASE)
            if overall_match:
                try:
                    length_str = overall_match.group(1).strip()
                    width_str = overall_match.group(2).strip()
                    
                    length_parts = length_str.split()
                    length_ft = float(length_parts[0]) + (float(length_parts[1]) / 12.0 if len(length_parts) == 2 else 0)
                    
                    width_parts = width_str.split()
                    width_ft = float(width_parts[0]) + (float(width_parts[1]) / 12.0 if len(width_parts) == 2 else 0)
                    
                    dimensions["overall"] = {
                        "length_ft": round(length_ft, 2),
                        "width_ft": round(width_ft, 2),
                        "area_sqft": round(length_ft * width_ft, 2),
                        "raw_text": f"{length_str} x {width_str}"
                    }
                    logger.info(f"Found overall dimensions: {length_ft}' x {width_ft}'")
                except:
                    pass
        
        return dimensions
    
    def _parse_dimension_string(self, room_name: str, dim_str: str) -> Optional[Dict]:
        """
        Parse a dimension string like "11' x 10'" or "11' 10\" x 10'" into a dimension dict.
        
        Args:
            room_name: Name of the room
            dim_str: Dimension string (e.g., "11' x 10'", "11' 10\" x 10'")
            
        Returns:
            Dictionary with length_ft, width_ft, area_sqft, or None if parsing fails
        """
        import re
        
        if not dim_str:
            return None
        
        # Pattern to extract two dimensions: "11' x 10'" or "11' 10\" x 10'"
        pattern = r'(\d+(?:\s*\d+)?)\s*[\'"]?\s*[x×]\s*(\d+(?:\s*\d+)?)\s*[\'"]?'
        match = re.search(pattern, dim_str, re.IGNORECASE)
        
        if not match:
            logger.warning(f"Could not parse dimension string for {room_name}: {dim_str}")
            return None
        
        length_str = match.group(1).strip()
        width_str = match.group(2).strip()
        
        try:
            # Parse length (e.g., "11", "9 3" -> 9.25 feet, "9' 3\"" -> 9.25 feet)
            # Remove quotes and apostrophes, then split
            length_clean = length_str.replace("'", " ").replace('"', " ").replace("ft", " ").strip()
            length_parts = length_clean.split()
            if len(length_parts) >= 2:
                feet = float(length_parts[0])
                inches = float(length_parts[1])
                length_ft = feet + (inches / 12.0)
            else:
                length_ft = float(length_parts[0])
            
            # Parse width (same logic)
            width_clean = width_str.replace("'", " ").replace('"', " ").replace("ft", " ").strip()
            width_parts = width_clean.split()
            if len(width_parts) >= 2:
                feet = float(width_parts[0])
                inches = float(width_parts[1])
                width_ft = feet + (inches / 12.0)
            else:
                width_ft = float(width_parts[0])
            
            area_sqft = length_ft * width_ft
            
            result = {
                "length_ft": round(length_ft, 2),
                "width_ft": round(width_ft, 2),
                "area_sqft": round(area_sqft, 2),
                "raw_text": dim_str
            }
            
            logger.info(f"Parsed dimension: {room_name} = {length_ft}' x {width_ft}' = {area_sqft} sqft")
            return result
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse dimension for {room_name} ({dim_str}): {e}")
            return None
    
    async def ask_question(
        self,
        image_path: str,
        question: str
    ) -> str:
        """
        Ask a custom question about the floor plan image.
        
        Args:
            image_path: Path to floor plan image
            question: Question to ask
            
        Returns:
            Answer from Moondream
        """
        try:
            image = Image.open(image_path)
            result = self.model.query(image, question)
            return result.get("answer", "")
        except Exception as e:
            logger.error(f"Error asking question with Moondream: {e}")
            return f"Error: {str(e)}"

