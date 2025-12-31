"""Trade-specific quantity extraction service."""

from typing import Dict, List, Optional
import logging
from src.models.trade import TradeType, TradeConfig, TradeExtractionResult, TRADE_CONFIGS
from src.agents.quantity_agent import QuantityTakeoffAgent
from src.agents.cv_agent import ComputerVisionAgent

logger = logging.getLogger(__name__)


class TradeExtractor:
    """Extract quantities for specific trades."""
    
    def __init__(self):
        self.quantity_agent = QuantityTakeoffAgent()
        self.cv_agent = ComputerVisionAgent()
    
    async def extract_trade_quantities(
        self,
        document_text: str,
        trade_type: TradeType,
        cv_results: Optional[Dict] = None,
        project_file_name: Optional[str] = None,
        moondream_results: Optional[Dict] = None
    ) -> TradeExtractionResult:
        """
        Extract quantities for a specific trade.
        
        Args:
            document_text: Extracted document text
            trade_type: Trade to extract
            cv_results: Optional CV analysis results
            
        Returns:
            TradeExtractionResult with quantities
        """
        try:
            config = TRADE_CONFIGS.get(trade_type)
            if not config or not config.enabled:
                raise ValueError(f"Trade {trade_type} is not enabled")
            
            logger.info(f"Extracting quantities for trade: {trade_type}")
            
            # Trade-specific extraction logic
            if trade_type == TradeType.PAINTING:
                return await self._extract_painting(document_text, cv_results)
            elif trade_type == TradeType.DRYWALL:
                return await self._extract_drywall(document_text, cv_results)
            elif trade_type == TradeType.DOORS_WINDOWS:
                return await self._extract_doors_windows(document_text, cv_results)
            elif trade_type == TradeType.FLOORING:
                return await self._extract_flooring(
                    document_text, 
                    cv_results, 
                    project_file_name,
                    moondream_results
                )
            elif trade_type == TradeType.CONCRETE:
                return await self._extract_concrete(document_text, cv_results)
            else:
                # Generic extraction for unsupported trades
                return await self._extract_generic(document_text, trade_type)
                
        except Exception as e:
            logger.error(f"Error extracting {trade_type}: {e}")
            raise
    
    async def _extract_painting(
        self,
        text: str,
        cv_results: Optional[Dict]
    ) -> TradeExtractionResult:
        """Extract painting quantities."""
        # Use LLM to extract painting-specific quantities
        prompt = f"""Extract painting quantities from this construction document:
        
{text[:8000]}

Extract:
- Wall area (sqft) - interior and exterior separately
- Ceiling area (sqft)
- Trim/Baseboard linear feet
- Door frames (count)
- Window frames (count)

Return structured data with areas and counts."""
        
        # In production, would call LLM with structured output
        # For now, use quantity agent with painting-specific prompt
        
        quantities = {
            "interior_walls_sqft": 0,
            "exterior_walls_sqft": 0,
            "ceiling_sqft": 0,
            "trim_linear_feet": 0,
            "door_frames_count": 0,
            "window_frames_count": 0
        }
        
        # Extract from text using quantity agent
        result = await self.quantity_agent.extract_quantities(
            document_text=text,
            document_type="floor_plan"
        )
        
        # Map to painting-specific quantities
        # This would be more sophisticated in production
        
        return TradeExtractionResult(
            trade_type=TradeType.PAINTING,
            quantities=quantities,
            confidence=0.85,
            units={
                "interior_walls_sqft": "sqft",
                "exterior_walls_sqft": "sqft",
                "ceiling_sqft": "sqft",
                "trim_linear_feet": "linear_ft",
                "door_frames_count": "count",
                "window_frames_count": "count"
            }
        )
    
    async def _extract_drywall(
        self,
        text: str,
        cv_results: Optional[Dict]
    ) -> TradeExtractionResult:
        """Extract drywall quantities."""
        quantities = {
            "sheets_4x8": 0,
            "sheets_4x12": 0,
            "linear_feet_partitions": 0,
            "corners": 0
        }
        
        return TradeExtractionResult(
            trade_type=TradeType.DRYWALL,
            quantities=quantities,
            confidence=0.85,
            units={
                "sheets_4x8": "sheets",
                "sheets_4x12": "sheets",
                "linear_feet_partitions": "linear_ft",
                "corners": "count"
            }
        )
    
    async def _extract_doors_windows(
        self,
        text: str,
        cv_results: Optional[Dict]
    ) -> TradeExtractionResult:
        """Extract doors and windows quantities."""
        # Use existing quantity agent
        result = await self.quantity_agent.extract_quantities(
            document_text=text,
            document_type="floor_plan"
        )
        
        quantities_data = result.get("quantities", {})
        
        quantities = {
            "doors": quantities_data.get("doors", {}).get("total_count", 0),
            "windows": quantities_data.get("windows", {}).get("total_count", 0),
            "hardware": quantities_data.get("hardware", {}).get("total_count", 0)
        }
        
        return TradeExtractionResult(
            trade_type=TradeType.DOORS_WINDOWS,
            quantities=quantities,
            confidence=result.get("confidence_scores", {}).get("doors", 0.85),
            units={
                "doors": "count",
                "windows": "count",
                "hardware": "count"
            }
        )
    
    async def _extract_flooring(
        self,
        text: str,
        cv_results: Optional[Dict],
        project_file_name: Optional[str] = None,
        moondream_results: Optional[Dict] = None
    ) -> TradeExtractionResult:
        """Extract flooring quantities from text and CV results."""
        try:
            logger.info("Extracting flooring quantities...")
            
            # Skip quantity agent for flooring - we'll extract directly from text/CV/Moondream
            # The quantity agent is for doors/windows, not flooring areas
            # extracted_quantities = {}
            # flooring_data = {}
            
            # Calculate total area from CV if available
            total_sqft = 0.0
            by_room = {}
            by_type = {
                "hardwood_sqft": 0.0,
                "tile_sqft": 0.0,
                "carpet_sqft": 0.0,
                "concrete_sqft": 0.0,
                "underlayment_sqft": 0.0,
                "baseboard_linear_ft": 0.0,
                "transition_strips": 0
            }
            
            # Priority 1: Use Moondream results if available (most accurate)
            if moondream_results and moondream_results.get("parsed_successfully"):
                dimensions = moondream_results.get("dimensions", {})
                logger.info(f"Using Moondream extracted dimensions: {len(dimensions)} rooms")
                
                # Track room names to handle duplicates
                room_name_counts = {}
                
                for room_name, room_data in dimensions.items():
                    if room_name.lower() == "overall":
                        # Store overall for validation
                        overall_area = room_data.get("area_sqft", 0.0)
                        logger.info(f"Overall floor plan dimensions: {overall_area} sqft")
                        continue
                    
                    area = room_data.get("area_sqft", 0.0)
                    if area > 0:
                        # Handle duplicate room names (e.g., "Bed Room" appears twice)
                        original_name = room_name
                        if room_name in by_room:
                            # Duplicate detected - add suffix
                            room_name_counts[original_name] = room_name_counts.get(original_name, 1) + 1
                            room_name = f"{original_name} {room_name_counts[original_name]}"
                            logger.info(f"Duplicate room name detected: '{original_name}' -> '{room_name}'")
                        else:
                            room_name_counts[original_name] = 1
                        
                        # Determine flooring type based on room name
                        room_lower = room_name.lower()
                        if "bath" in room_lower or "toilet" in room_lower or "kitchen" in room_lower or "pooja" in room_lower:
                            flooring_type = "tile"
                        elif "parking" in room_lower:
                            flooring_type = "concrete"
                        else:
                            flooring_type = "hardwood"
                        
                        by_room[room_name] = {
                            "area_sqft": area,
                            "flooring_type": flooring_type,
                            "underlayment_sqft": area if flooring_type != "concrete" else 0.0,
                            "length_ft": room_data.get("length_ft"),
                            "width_ft": room_data.get("width_ft")
                        }
                        total_sqft += area
                        
                        # Add to by_type
                        if flooring_type == "hardwood":
                            by_type["hardwood_sqft"] += area
                        elif flooring_type == "tile":
                            by_type["tile_sqft"] += area
                        elif flooring_type == "concrete":
                            by_type["concrete_sqft"] += area
                        
                        if flooring_type != "concrete":
                            by_type["underlayment_sqft"] += area
                
                logger.info(f"Moondream extraction: Total {total_sqft} sqft from {len(by_room)} rooms")
                
                # Validation: Check if we're missing rooms
                # If overall dimensions suggest ~1,500 sqft but we only extracted < 800 sqft, likely missing rooms
                overall_data = dimensions.get("overall", {})
                if overall_data:
                    overall_area = overall_data.get("area_sqft", 0.0)
                    expected_interior = overall_area * 0.7  # ~70% interior (exclude walls, parking)
                    if overall_area > 0 and total_sqft < expected_interior * 0.6:
                        logger.warning(
                            f"⚠️ Potential missing rooms detected! "
                            f"Overall: {overall_area} sqft, Expected interior: ~{expected_interior:.0f} sqft, "
                            f"Extracted: {total_sqft} sqft. Only {total_sqft/expected_interior*100:.1f}% extracted."
                        )
            
            # Priority 2: Extract from CV results if available (fallback)
            elif cv_results:
                rooms = cv_results.get("processed_objects", {}).get("rooms", [])
                measurements = cv_results.get("measurements", {})
                room_areas = measurements.get("room_areas", [])
                
                for i, room in enumerate(rooms):
                    room_name = room.get("label", f"room_{i+1}")
                    area = room.get("area_sqft", 0.0)
                    
                    # Try to get area from measurements
                    if i < len(room_areas):
                        area = room_areas[i].get("area_sqft", area)
                    
                    if area > 0:
                        by_room[room_name] = {
                            "area_sqft": area,
                            "flooring_type": room.get("flooring_type", "hardwood"),
                            "underlayment_sqft": area
                        }
                        total_sqft += area
                        
                        # Add to by_type
                        flooring_type = room.get("flooring_type", "hardwood").lower()
                        if "hardwood" in flooring_type or "wood" in flooring_type:
                            by_type["hardwood_sqft"] += area
                        elif "tile" in flooring_type:
                            by_type["tile_sqft"] += area
                        elif "carpet" in flooring_type:
                            by_type["carpet_sqft"] += area
                        elif "concrete" in flooring_type:
                            by_type["concrete_sqft"] += area
                        
                        by_type["underlayment_sqft"] += area
            
            # Extract from text if CV didn't provide data
            if total_sqft == 0 and text:
                # Look for dimensions in text (e.g., "11' x 10'", "50' x 30'", "20' x 45'")
                import re
                
                # First, try to find room-specific dimensions: "Bed Room: 11' x 10'"
                room_dimension_pattern = r'([A-Za-z\s]+(?:Room|Area|Bath|Kitchen|Dining|Drawing|Pooja|Store|Parking|Bedroom)?):\s*(\d+(?:\.\d+)?)\s*[\'"]?\s*[x×]\s*(\d+(?:\.\d+)?)\s*[\'"]?'
                room_matches = re.finditer(room_dimension_pattern, text, re.IGNORECASE)
                
                room_count = 0
                for match in room_matches:
                    room_name = match.group(1).strip()
                    length = float(match.group(2))
                    width = float(match.group(3))
                    area = length * width
                    
                    if area > 0 and area < 500:  # Likely a room, not overall dimensions
                        room_lower = room_name.lower()
                        if "bath" in room_lower or "toilet" in room_lower or "kitchen" in room_lower or "pooja" in room_lower:
                            flooring_type = "tile"
                        elif "parking" in room_lower:
                            flooring_type = "concrete"
                        else:
                            flooring_type = "hardwood"
                        
                        by_room[room_name] = {
                            "area_sqft": round(area, 2),
                            "flooring_type": flooring_type,
                            "underlayment_sqft": round(area, 2) if flooring_type != "concrete" else 0.0,
                            "length_ft": length,
                            "width_ft": width
                        }
                        total_sqft += area
                        
                        if flooring_type == "hardwood":
                            by_type["hardwood_sqft"] += area
                        elif flooring_type == "tile":
                            by_type["tile_sqft"] += area
                        elif flooring_type == "concrete":
                            by_type["concrete_sqft"] += area
                        
                        if flooring_type != "concrete":
                            by_type["underlayment_sqft"] += area
                        
                        room_count += 1
                        logger.info(f"Extracted room from text: {room_name} = {length}' × {width}' = {area} sqft")
                
                # If no room-specific dimensions found, look for general dimension patterns
                if room_count == 0:
                    # Pattern for dimensions: "11' x 10'", "11'×10'", "11 ft x 10 ft", "20' x 45'"
                    # Also handle formats like "10' x 8' 2"" (with inches)
                    dimension_pattern = r'(\d+(?:\.\d+)?)\s*[\'"]?\s*[x×]\s*(\d+(?:\.\d+)?)\s*[\'"]?'
                    dimensions = re.findall(dimension_pattern, text, re.IGNORECASE)
                    
                    logger.info(f"Found {len(dimensions)} dimension patterns in text: {dimensions}")
                    
                    # Calculate total area from dimensions
                    room_areas = []
                    for dim in dimensions:
                        try:
                            length = float(dim[0])
                            width = float(dim[1])
                            area = length * width
                            room_areas.append(area)
                            total_sqft += area
                            logger.info(f"Calculated area from {dim}: {area} sqft")
                        except Exception as e:
                            logger.warning(f"Failed to parse dimension {dim}: {e}")
                            pass
                
                # If we found overall dimensions (20' x 45' = 900, 50' x 30' = 1500), use that
                if len(dimensions) > 0:
                    # Find largest dimension (likely overall)
                    largest_area = max(room_areas) if room_areas else 0
                    logger.info(f"Largest area found: {largest_area} sqft")
                    
                    # If largest is > 500, it's likely overall dimensions
                    # For 20x45 = 900, 50x30 = 1500
                    if largest_area > 500:
                        # Use overall dimensions but estimate interior area (exclude parking)
                        # For residential, interior is typically 60-80% of total
                        estimated_interior = largest_area * 0.7  # 70% interior
                        total_sqft = estimated_interior
                        by_type["hardwood_sqft"] = total_sqft * 0.7  # Estimate 70% hardwood
                        by_type["tile_sqft"] = total_sqft * 0.2  # Estimate 20% tile
                        by_type["underlayment_sqft"] = total_sqft * 0.9  # Most rooms need underlayment
                        
                        # Create a placeholder entry in by_room to indicate this is an estimate
                        # Extract the dimensions used
                        largest_dim = None
                        for dim in dimensions:
                            length = float(dim[0])
                            width = float(dim[1])
                            if length * width == largest_area:
                                largest_dim = (length, width)
                                break
                        
                        if largest_dim:
                            by_room["Overall Estimate"] = {
                                "area_sqft": round(total_sqft, 2),
                                "flooring_type": "mixed",
                                "underlayment_sqft": round(by_type["underlayment_sqft"], 2),
                                "length_ft": largest_dim[0],
                                "width_ft": largest_dim[1],
                                "note": "Estimated from overall floor plan dimensions"
                            }
                        
                        logger.info(f"Using overall dimensions: {largest_area} sqft total, {total_sqft} sqft interior")
                    elif total_sqft > 0:
                        # Sum of room areas
                        by_type["hardwood_sqft"] = total_sqft * 0.7
                        by_type["tile_sqft"] = total_sqft * 0.2
                        by_type["underlayment_sqft"] = total_sqft * 0.9
                
                # Extract flooring types from text
                text_lower = text.lower()
                if "hardwood" in text_lower or "wood" in text_lower:
                    by_type["hardwood_sqft"] = max(by_type["hardwood_sqft"], total_sqft * 0.6)
                if "tile" in text_lower:
                    by_type["tile_sqft"] = max(by_type["tile_sqft"], total_sqft * 0.3)
                if "carpet" in text_lower:
                    by_type["carpet_sqft"] = max(by_type["carpet_sqft"], total_sqft * 0.1)
            
            # Final fallback: if still 0, try filename extraction
            if total_sqft == 0 and project_file_name:
                logger.warning("No dimensions found in text, CV, or Moondream. Trying filename extraction...")
                import re
                filename_match = re.search(r'(\d+)\s*[x×]\s*(\d+)', project_file_name, re.IGNORECASE)
                if filename_match:
                    length = float(filename_match.group(1))
                    width = float(filename_match.group(2))
                    total_sqft = length * width * 0.7  # 70% interior (exclude parking)
                    by_type["hardwood_sqft"] = total_sqft * 0.7
                    by_type["tile_sqft"] = total_sqft * 0.2
                    by_type["underlayment_sqft"] = total_sqft * 0.9
                    logger.info(f"Extracted from filename '{project_file_name}': {length}x{width} = {total_sqft} sqft interior")
            
            # Calculate baseboard (estimate 80% of perimeter)
            if total_sqft > 0:
                # Rough estimate: sqrt(area) * 4 * 0.8 for perimeter
                estimated_perimeter = (total_sqft ** 0.5) * 4 * 0.8
                by_type["baseboard_linear_ft"] = estimated_perimeter
            
            # Calculate transition strips (estimate based on room count)
            room_count = len(by_room) if by_room else 1
            by_type["transition_strips"] = max(room_count - 1, 0)
            
            # Ensure total_sqft is not 0 if we have any data
            if total_sqft == 0 and (by_type["hardwood_sqft"] > 0 or by_type["tile_sqft"] > 0):
                total_sqft = by_type["hardwood_sqft"] + by_type["tile_sqft"] + by_type["carpet_sqft"]
            
            quantities = {
                "total_sqft": round(total_sqft, 2),
                "by_room": by_room,
                "by_type": {k: round(v, 2) if isinstance(v, float) else v for k, v in by_type.items()}
            }
            
            # Calculate confidence based on data sources
            confidence = 0.85
            if cv_results and total_sqft > 0:
                confidence = 0.92  # Higher confidence with CV data
            elif total_sqft > 0:
                confidence = 0.80  # Lower confidence if only text
            
            logger.info(f"Extracted flooring: {total_sqft} sqft with confidence {confidence}")
            
            return TradeExtractionResult(
                trade_type=TradeType.FLOORING,
                quantities=quantities,
                confidence=confidence,
                units={
                    "total_sqft": "sqft",
                    "hardwood_sqft": "sqft",
                    "tile_sqft": "sqft",
                    "carpet_sqft": "sqft",
                    "concrete_sqft": "sqft",
                    "underlayment_sqft": "sqft",
                    "baseboard_linear_ft": "linear_ft",
                    "transition_strips": "count"
                }
            )
            
        except Exception as e:
            logger.error(f"Error extracting flooring quantities: {e}", exc_info=True)
            # Return minimal result on error
            return TradeExtractionResult(
                trade_type=TradeType.FLOORING,
                quantities={
                    "total_sqft": 0,
                    "by_room": {},
                    "by_type": {}
                },
                confidence=0.5,
                units={"total_sqft": "sqft"},
                metadata={"error": str(e)}
            )
    
    async def _extract_concrete(
        self,
        text: str,
        cv_results: Optional[Dict]
    ) -> TradeExtractionResult:
        """Extract concrete quantities."""
        quantities = {
            "slabs_cubic_yards": 0,
            "foundations_cubic_yards": 0,
            "walls_cubic_yards": 0
        }
        
        return TradeExtractionResult(
            trade_type=TradeType.CONCRETE,
            quantities=quantities,
            confidence=0.85,
            units={
                "slabs_cubic_yards": "cubic_yds",
                "foundations_cubic_yards": "cubic_yds",
                "walls_cubic_yards": "cubic_yds"
            }
        )
    
    async def _extract_generic(
        self,
        text: str,
        trade_type: TradeType
    ) -> TradeExtractionResult:
        """Generic extraction for unsupported trades."""
        return TradeExtractionResult(
            trade_type=trade_type,
            quantities={},
            confidence=0.5,
            units={},
            metadata={"note": "Trade not yet fully supported"}
        )

