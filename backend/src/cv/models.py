"""Computer Vision models for floor plan analysis."""

from typing import Dict, List, Any
import logging
import numpy as np
import cv2
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    from transformers import ViTImageProcessor, ViTForImageClassification
    import torch
except ImportError:
    ViTImageProcessor = None
    ViTForImageClassification = None
    torch = None

from config.settings import settings

logger = logging.getLogger(__name__)


class YOLOModel:
    """YOLO model wrapper for object detection in floor plans."""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or settings.yolo_model_path
        
        if YOLO is None:
            logger.warning("YOLO not available - install ultralytics")
            self.model = None
        else:
            try:
                if Path(self.model_path).exists():
                    self.model = YOLO(self.model_path)
                else:
                    # Use pretrained model as fallback
                    logger.warning(f"Model not found at {self.model_path}, using pretrained")
                    self.model = YOLO("yolov8n.pt")
            except Exception as e:
                logger.error(f"Error loading YOLO model: {e}")
                self.model = None
    
    async def detect(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect objects in floor plan image.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Detection results with bounding boxes and classes
        """
        if self.model is None:
            # Return mock results if model not available
            return {
                "detections": [],
                "model_available": False
            }
        
        try:
            # Run inference
            results = self.model(image)
            
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.model.names[class_id]
                    
                    detections.append({
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "confidence": confidence,
                        "class": class_name,
                        "class_id": class_id
                    })
            
            return {
                "detections": detections,
                "model_available": True,
                "total_detections": len(detections)
            }
            
        except Exception as e:
            logger.error(f"Error in YOLO detection: {e}")
            return {
                "detections": [],
                "error": str(e),
                "model_available": True
            }


class VisionTransformer:
    """Vision Transformer for semantic understanding of floor plans."""
    
    def __init__(self):
        if ViTImageProcessor is None or ViTForImageClassification is None:
            logger.warning("Transformers not available - install transformers")
            self.processor = None
            self.model = None
        else:
            try:
                self.processor = ViTImageProcessor.from_pretrained(
                    "google/vit-base-patch16-224"
                )
                self.model = ViTForImageClassification.from_pretrained(
                    "google/vit-base-patch16-224"
                )
                if torch is not None:
                    self.model.eval()
            except Exception as e:
                logger.error(f"Error loading ViT model: {e}")
                self.processor = None
                self.model = None
    
    async def analyze_layout(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyze floor plan layout using Vision Transformer.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Layout analysis results
        """
        if self.processor is None or self.model is None:
            return {
                "layout_type": "unknown",
                "model_available": False,
                "analysis": "Model not available"
            }
        
        try:
            # Preprocess image
            if len(image.shape) == 2:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Resize to model input size
            image_rgb = cv2.resize(image_rgb, (224, 224))
            
            # Process with ViT
            inputs = self.processor(images=image_rgb, return_tensors="pt")
            
            if torch is not None:
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    logits = outputs.logits
                    probabilities = torch.nn.functional.softmax(logits, dim=-1)
                    top_probs, top_indices = torch.topk(probabilities, 5)
                    
                    predictions = []
                    for prob, idx in zip(top_probs[0], top_indices[0]):
                        label = self.model.config.id2label[idx.item()]
                        predictions.append({
                            "label": label,
                            "confidence": float(prob.item())
                        })
            else:
                predictions = []
            
            return {
                "layout_type": predictions[0]["label"] if predictions else "unknown",
                "predictions": predictions,
                "model_available": True,
                "analysis": "ViT-based layout analysis completed"
            }
            
        except Exception as e:
            logger.error(f"Error in ViT analysis: {e}")
            return {
                "layout_type": "unknown",
                "error": str(e),
                "model_available": True
            }


