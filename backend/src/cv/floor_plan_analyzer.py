"""Floor plan analysis utilities."""

from typing import Dict, List, Tuple
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FloorPlanAnalyzer:
    """Utilities for analyzing floor plan images."""
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess floor plan image for analysis."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
        
        return denoised
    
    def detect_lines(self, image: np.ndarray) -> List[Dict]:
        """Detect lines in floor plan (walls, boundaries)."""
        # Edge detection
        edges = cv2.Canny(image, 50, 150)
        
        # Hough line transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=100,
            minLineLength=50,
            maxLineGap=10
        )
        
        detected_lines = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                detected_lines.append({
                    "start": [int(x1), int(y1)],
                    "end": [int(x2), int(y2)],
                    "length": np.sqrt((x2-x1)**2 + (y2-y1)**2)
                })
        
        return detected_lines
    
    def detect_rectangles(self, image: np.ndarray) -> List[Dict]:
        """Detect rectangular regions (rooms, spaces)."""
        # Threshold
        _, thresh = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        rectangles = []
        for contour in contours:
            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Check if it's roughly rectangular (4 corners)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                
                rectangles.append({
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "area": float(area),
                    "corners": approx.tolist()
                })
        
        return rectangles


