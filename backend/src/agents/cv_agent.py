"""Computer Vision Agent - Analyzes floor plans using YOLO and Vision Transformers."""

from typing import Dict, List, Optional, Any, Tuple
import logging
import numpy as np
from pathlib import Path
import cv2

from src.cv.floor_plan_analyzer import FloorPlanAnalyzer
from src.cv.models import YOLOModel, VisionTransformer
from config.settings import settings

logger = logging.getLogger(__name__)


class ComputerVisionAgent:
    """
    Agent that analyzes construction floor plans using Computer Vision.
    Combines YOLO for object detection and ViT for semantic understanding.
    """
    
    def __init__(self):
        self.floor_plan_analyzer = FloorPlanAnalyzer()
        self.yolo_model = YOLOModel(model_path=settings.yolo_model_path)
        self.vit_model = VisionTransformer()
        
    async def analyze_floor_plan(
        self,
        image_path: str,
        analysis_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Analyze floor plan image to extract spatial information.
        
        Args:
            image_path: Path to floor plan image
            analysis_type: Type of analysis (full, objects_only, layout_only)
            
        Returns:
            Analysis results with detected objects, layout, and measurements
        """
        try:
            logger.info(f"Analyzing floor plan: {image_path}")
            
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            results = {
                "image_path": image_path,
                "image_dimensions": image.shape[:2]
            }
            
            # Object detection using YOLO
            if analysis_type in ["full", "objects_only"]:
                logger.info("Running YOLO object detection...")
                yolo_results = await self.yolo_model.detect(image)
                results["detected_objects"] = yolo_results
                
                # Post-process detections
                processed_objects = self._process_detections(yolo_results)
                results["processed_objects"] = processed_objects
            
            # Layout analysis using ViT
            if analysis_type in ["full", "layout_only"]:
                logger.info("Running layout analysis with ViT...")
                layout_results = await self.vit_model.analyze_layout(image)
                results["layout_analysis"] = layout_results
            
            # Spatial reasoning
            if analysis_type == "full":
                logger.info("Performing spatial reasoning...")
                spatial_info = await self._spatial_reasoning(
                    results.get("processed_objects", {}),
                    results.get("layout_analysis", {})
                )
                results["spatial_analysis"] = spatial_info
            
            # Extract measurements if scale is available
            measurements = await self._extract_measurements(image, results)
            results["measurements"] = measurements
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing floor plan: {e}")
            raise
    
    def _process_detections(self, yolo_results: Dict) -> Dict[str, List]:
        """Process YOLO detections into structured format."""
        processed = {
            "doors": [],
            "windows": [],
            "rooms": [],
            "walls": [],
            "furniture": [],
            "other": []
        }
        
        for detection in yolo_results.get("detections", []):
            obj_class = detection.get("class", "").lower()
            bbox = detection.get("bbox", [])
            confidence = detection.get("confidence", 0.0)
            
            obj_data = {
                "bbox": bbox,
                "confidence": confidence,
                "center": [
                    (bbox[0] + bbox[2]) / 2,
                    (bbox[1] + bbox[3]) / 2
                ],
                "area": (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            }
            
            # Categorize objects
            if "door" in obj_class:
                processed["doors"].append(obj_data)
            elif "window" in obj_class:
                processed["windows"].append(obj_data)
            elif "room" in obj_class or "space" in obj_class:
                processed["rooms"].append(obj_data)
            elif "wall" in obj_class:
                processed["walls"].append(obj_data)
            elif any(f in obj_class for f in ["table", "chair", "bed", "sofa"]):
                processed["furniture"].append(obj_data)
            else:
                processed["other"].append(obj_data)
        
        return processed
    
    async def _spatial_reasoning(
        self,
        objects: Dict,
        layout: Dict
    ) -> Dict[str, Any]:
        """Perform spatial reasoning on detected objects and layout."""
        
        spatial_info = {
            "room_connections": [],
            "adjacency_matrix": {},
            "circulation_paths": [],
            "spatial_hierarchy": {}
        }
        
        # Analyze room adjacencies
        rooms = objects.get("rooms", [])
        doors = objects.get("doors", [])
        
        # Simple adjacency detection based on proximity
        for i, room1 in enumerate(rooms):
            for j, room2 in enumerate(rooms[i+1:], i+1):
                # Check if rooms share a door
                shared_door = self._check_shared_door(room1, room2, doors)
                if shared_door:
                    spatial_info["room_connections"].append({
                        "room1": i,
                        "room2": j,
                        "connection_type": "door",
                        "door_id": shared_door
                    })
        
        # Identify circulation paths
        spatial_info["circulation_paths"] = self._identify_circulation_paths(
            rooms, doors
        )
        
        return spatial_info
    
    def _check_shared_door(
        self,
        room1: Dict,
        room2: Dict,
        doors: List[Dict]
    ) -> Optional[int]:
        """Check if two rooms share a door."""
        room1_center = room1["center"]
        room2_center = room2["center"]
        
        for door_idx, door in enumerate(doors):
            door_center = door["center"]
            # Check if door is between rooms (simplified logic)
            if self._point_between_rooms(door_center, room1_center, room2_center):
                return door_idx
        
        return None
    
    def _point_between_rooms(
        self,
        point: List[float],
        room1_center: List[float],
        room2_center: List[float]
    ) -> bool:
        """Check if a point is between two room centers."""
        # Simplified geometric check
        dist1 = np.sqrt(
            (point[0] - room1_center[0])**2 + 
            (point[1] - room1_center[1])**2
        )
        dist2 = np.sqrt(
            (point[0] - room2_center[0])**2 + 
            (point[1] - room2_center[1])**2
        )
        
        # Check if point is roughly equidistant (within threshold)
        return abs(dist1 - dist2) < min(dist1, dist2) * 0.3
    
    def _identify_circulation_paths(
        self,
        rooms: List[Dict],
        doors: List[Dict]
    ) -> List[Dict]:
        """Identify main circulation paths through the floor plan."""
        # Simplified path identification
        paths = []
        
        # Find rooms with multiple doors (likely circulation spaces)
        for room_idx, room in enumerate(rooms):
            connected_doors = [
                door_idx for door_idx, door in enumerate(doors)
                if self._door_in_room(door, room)
            ]
            
            if len(connected_doors) >= 2:
                paths.append({
                    "room_id": room_idx,
                    "type": "circulation_space",
                    "connected_doors": connected_doors
                })
        
        return paths
    
    def _door_in_room(self, door: Dict, room: Dict) -> bool:
        """Check if a door is within a room's bounding box."""
        door_center = door["center"]
        room_bbox = room.get("bbox", [])
        
        if len(room_bbox) == 4:
            return (
                room_bbox[0] <= door_center[0] <= room_bbox[2] and
                room_bbox[1] <= door_center[1] <= room_bbox[3]
            )
        return False
    
    async def _extract_measurements(
        self,
        image: np.ndarray,
        analysis_results: Dict
    ) -> Dict[str, Any]:
        """Extract measurements from floor plan if scale is available."""
        # Look for scale indicators in the image
        # This is a simplified version - production would use OCR + CV
        
        measurements = {
            "scale_detected": False,
            "scale_factor": None,
            "room_areas": [],
            "wall_lengths": []
        }
        
        # In production, would:
        # 1. Detect scale bar using CV
        # 2. OCR the scale text
        # 3. Calculate pixel-to-foot/meter ratio
        # 4. Apply to detected objects
        
        return measurements
    
    async def cross_validate_with_text(
        self,
        cv_results: Dict,
        text_extraction: Dict
    ) -> Dict[str, Any]:
        """
        Cross-validate CV results with text-extracted quantities.
        """
        logger.info("Cross-validating CV and text extraction results...")
        
        # Compare door counts
        cv_doors = len(cv_results.get("processed_objects", {}).get("doors", []))
        text_doors = self._extract_count_from_text(text_extraction, "door")
        
        # Compare window counts
        cv_windows = len(cv_results.get("processed_objects", {}).get("windows", []))
        text_windows = self._extract_count_from_text(text_extraction, "window")
        
        validation = {
            "doors": {
                "cv_count": cv_doors,
                "text_count": text_doors,
                "match": abs(cv_doors - text_windows) <= 2,
                "discrepancy": abs(cv_doors - text_doors)
            },
            "windows": {
                "cv_count": cv_windows,
                "text_count": text_windows,
                "match": abs(cv_windows - text_windows) <= 2,
                "discrepancy": abs(cv_windows - text_windows)
            }
        }
        
        return validation
    
    def _extract_count_from_text(self, text_data: Dict, keyword: str) -> int:
        """Extract count of keyword from text extraction results."""
        # Simplified - would use more sophisticated NLP
        text = str(text_data.get("text", "")).lower()
        count = text.count(keyword)
        return count


