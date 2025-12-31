"""Validators for agent outputs."""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class QuantityValidator:
    """Validates extracted quantities against rules and bounds."""
    
    def validate(self, quantities: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quantities."""
        issues = []
        
        for category, data in quantities.items():
            total = data.get("total_count", 0)
            
            # Check for negative values
            if total < 0:
                issues.append({
                    "category": category,
                    "issue": "negative_quantity",
                    "value": total
                })
            
            # Check for unreasonably high values
            max_bounds = {
                "doors": 1000,
                "windows": 2000,
                "rooms": 200,
                "hardware": 5000
            }
            
            max_bound = max_bounds.get(category, 10000)
            if total > max_bound:
                issues.append({
                    "category": category,
                    "issue": "exceeds_max_bound",
                    "value": total,
                    "max_bound": max_bound
                })
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }


class ConsistencyChecker:
    """Checks consistency between different agent outputs."""
    
    def check_consistency(
        self,
        text_results: Dict[str, Any],
        cv_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check consistency between text and CV results."""
        inconsistencies = []
        
        # Compare door counts
        text_doors = text_results.get("doors", {}).get("total_count", 0)
        cv_doors = len(
            cv_results.get("processed_objects", {}).get("doors", [])
        )
        
        if abs(text_doors - cv_doors) > max(2, text_doors * 0.1):
            inconsistencies.append({
                "type": "door_count_mismatch",
                "text_count": text_doors,
                "cv_count": cv_doors,
                "difference": abs(text_doors - cv_doors)
            })
        
        # Compare window counts
        text_windows = text_results.get("windows", {}).get("total_count", 0)
        cv_windows = len(
            cv_results.get("processed_objects", {}).get("windows", [])
        )
        
        if abs(text_windows - cv_windows) > max(2, text_windows * 0.1):
            inconsistencies.append({
                "type": "window_count_mismatch",
                "text_count": text_windows,
                "cv_count": cv_windows,
                "difference": abs(text_windows - cv_windows)
            })
        
        return {
            "is_consistent": len(inconsistencies) == 0,
            "inconsistencies": inconsistencies
        }


