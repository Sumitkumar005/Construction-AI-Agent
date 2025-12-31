"""Evaluation metrics for agent performance."""

from typing import Dict, List, Any
import logging
import numpy as np

logger = logging.getLogger(__name__)


class EvaluationMetrics:
    """Calculate evaluation metrics for agent outputs."""
    
    @staticmethod
    def calculate_accuracy(
        predicted: Dict[str, Any],
        ground_truth: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate accuracy metrics for quantity extraction.
        
        Args:
            predicted: Predicted quantities from agents
            ground_truth: Ground truth quantities
            
        Returns:
            Dictionary with accuracy metrics
        """
        metrics = {}
        
        for category in ["doors", "windows", "hardware", "finishes"]:
            pred_count = predicted.get(category, {}).get("total_count", 0)
            true_count = ground_truth.get(category, {}).get("total_count", 0)
            
            if true_count > 0:
                accuracy = 1 - abs(pred_count - true_count) / true_count
                accuracy = max(0, min(1, accuracy))  # Clamp to [0, 1]
            else:
                accuracy = 1.0 if pred_count == 0 else 0.0
            
            metrics[f"{category}_accuracy"] = accuracy
        
        # Overall accuracy
        metrics["overall_accuracy"] = np.mean(list(metrics.values()))
        
        return metrics
    
    @staticmethod
    def calculate_precision_recall(
        predicted: Dict[str, Any],
        ground_truth: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate precision and recall for detected elements."""
        # Simplified implementation
        # In production, would compare individual elements
        
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        
        for category in ["doors", "windows"]:
            pred_elements = predicted.get(category, {}).get("elements", [])
            true_elements = ground_truth.get(category, {}).get("elements", [])
            
            pred_count = len(pred_elements)
            true_count = len(true_elements)
            
            tp = min(pred_count, true_count)
            fp = max(0, pred_count - true_count)
            fn = max(0, true_count - pred_count)
            
            true_positives += tp
            false_positives += fp
            false_negatives += fn
        
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0 else 0.0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0 else 0.0
        )
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0 else 0.0
        )
        
        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }
    
    @staticmethod
    def calculate_confidence_metrics(
        results: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate confidence-related metrics."""
        confidence_scores = results.get("confidence_scores", {})
        
        if not confidence_scores:
            return {
                "mean_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0
            }
        
        confidences = list(confidence_scores.values())
        
        return {
            "mean_confidence": float(np.mean(confidences)),
            "min_confidence": float(np.min(confidences)),
            "max_confidence": float(np.max(confidences)),
            "std_confidence": float(np.std(confidences))
        }


