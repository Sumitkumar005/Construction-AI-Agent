"""Verification Agent - Validates outputs, cross-checks, and confidence scoring."""

from typing import Dict, List, Optional, Any
from langchain_core.messages import HumanMessage, SystemMessage
import logging

from src.evaluation.validators import QuantityValidator, ConsistencyChecker
from src.llm.llm_factory import get_llm
from src.core.config import settings

logger = logging.getLogger(__name__)


class VerificationAgent:
    """
    Agent responsible for verifying and validating outputs from other agents.
    Performs cross-checks, sanity bounds, and confidence scoring.
    """
    
    def __init__(self):
        self.llm = get_llm(temperature=0.0)  # Deterministic for validation
        self.quantity_validator = QuantityValidator()
        self.consistency_checker = ConsistencyChecker()
        
    async def verify_extraction_results(
        self,
        extraction_results: Dict,
        quantities: Dict,
        cv_results: Optional[Dict] = None,
        selected_trades: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive verification of extraction and quantity results.
        
        Args:
            extraction_results: Results from extraction agent
            quantities: Results from quantity take-off agent
            cv_results: Optional CV analysis results for cross-validation
            
        Returns:
            Verification report with confidence scores and flags
        """
        try:
            logger.info("Starting verification process...")
            
            verification_report = {
                "overall_confidence": 0.0,
                "checks": {},
                "flags": [],
                "recommendations": []
            }
            
            # Check 1: Quantity sanity bounds
            quantity_check = await self._check_quantity_bounds(quantities)
            verification_report["checks"]["quantity_bounds"] = quantity_check
            
            # Check 2: Consistency between text and CV
            if cv_results:
                consistency_check = await self._check_cv_text_consistency(
                    quantities,
                    cv_results
                )
                verification_report["checks"]["cv_text_consistency"] = consistency_check
            
            # Check 3: Completeness check
            completeness_check = await self._check_completeness(
                extraction_results,
                quantities,
                selected_trades
            )
            verification_report["checks"]["completeness"] = completeness_check
            
            # Check 4: Logical consistency
            logic_check = await self._check_logical_consistency(quantities)
            verification_report["checks"]["logical_consistency"] = logic_check
            
            # Calculate overall confidence
            verification_report["overall_confidence"] = self._calculate_overall_confidence(
                verification_report["checks"]
            )
            
            # Generate flags and recommendations
            verification_report["flags"] = self._generate_flags(verification_report["checks"])
            verification_report["recommendations"] = await self._generate_recommendations(
                verification_report
            )
            
            return verification_report
            
        except Exception as e:
            logger.error(f"Error in verification: {e}")
            raise
    
    async def _check_quantity_bounds(self, quantities: Dict) -> Dict[str, Any]:
        """Check if quantities are within reasonable bounds."""
        
        bounds = {
            "doors": {"min": 0, "max": 500},
            "windows": {"min": 0, "max": 1000},
            "rooms": {"min": 1, "max": 100},
            "hardware": {"min": 0, "max": 2000},
            "flooring": {"min": 0, "max": 50000},  # sqft
            "painting": {"min": 0, "max": 50000},  # sqft
            "drywall": {"min": 0, "max": 10000},  # sheets
            "concrete": {"min": 0, "max": 10000},  # cubic yards
            "doors_windows": {"min": 0, "max": 1000}  # count
        }
        
        results = {}
        all_within_bounds = True
        
        for category, data in quantities.items():
            # Check both total_count and total_sqft
            total = data.get("total_count", 0) or data.get("total_sqft", 0)
            category_bounds = bounds.get(category, {"min": 0, "max": 10000})
            
            is_valid = (
                category_bounds["min"] <= total <= category_bounds["max"]
            )
            
            if not is_valid:
                all_within_bounds = False
            
            results[category] = {
                "total": total,
                "bounds": category_bounds,
                "is_valid": is_valid,
                "confidence": 0.9 if is_valid else 0.3
            }
        
        return {
            "all_within_bounds": all_within_bounds,
            "category_results": results,
            "confidence": 0.9 if all_within_bounds else 0.5
        }
    
    async def _check_cv_text_consistency(
        self,
        quantities: Dict,
        cv_results: Dict
    ) -> Dict[str, Any]:
        """Check consistency between CV detection and text extraction."""
        
        consistency_results = {}
        
        # Compare door counts
        text_doors = quantities.get("doors", {}).get("total_count", 0)
        cv_doors = len(
            cv_results.get("processed_objects", {}).get("doors", [])
        )
        
        door_diff = abs(text_doors - cv_doors)
        door_match = door_diff <= max(2, text_doors * 0.1)  # Allow 10% variance
        
        consistency_results["doors"] = {
            "text_count": text_doors,
            "cv_count": cv_doors,
            "difference": door_diff,
            "is_consistent": door_match,
            "confidence": 0.9 if door_match else 0.6
        }
        
        # Compare window counts
        text_windows = quantities.get("windows", {}).get("total_count", 0)
        cv_windows = len(
            cv_results.get("processed_objects", {}).get("windows", [])
        )
        
        window_diff = abs(text_windows - cv_windows)
        window_match = window_diff <= max(2, text_windows * 0.1)
        
        consistency_results["windows"] = {
            "text_count": text_windows,
            "cv_count": cv_windows,
            "difference": window_diff,
            "is_consistent": window_match,
            "confidence": 0.9 if window_match else 0.6
        }
        
        overall_consistent = door_match and window_match
        
        return {
            "is_consistent": overall_consistent,
            "category_results": consistency_results,
            "confidence": 0.85 if overall_consistent else 0.6
        }
    
    async def _check_completeness(
        self,
        extraction_results: Dict,
        quantities: Dict,
        selected_trades: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Check if extraction is complete (all expected categories present)."""
        
        # Use selected_trades if provided, otherwise use default expected categories
        if selected_trades:
            expected_categories = selected_trades
        else:
            # Default expected categories (for backward compatibility)
            expected_categories = ["doors", "windows", "hardware", "finishes"]
        
        found_categories = list(quantities.keys())
        
        missing_categories = [
            cat for cat in expected_categories 
            if cat not in found_categories
        ]
        
        # Calculate completeness based on selected trades
        if expected_categories:
            completeness_score = len(found_categories) / len(expected_categories)
        else:
            completeness_score = 1.0 if found_categories else 0.0
        
        return {
            "expected_categories": expected_categories,
            "found_categories": found_categories,
            "missing_categories": missing_categories,
            "completeness_score": completeness_score,
            "is_complete": len(missing_categories) == 0,
            "confidence": completeness_score if completeness_score > 0 else 0.25  # Minimum 25% if no matches
        }
    
    async def _check_logical_consistency(self, quantities: Dict) -> Dict[str, Any]:
        """Check for logical inconsistencies in extracted quantities."""
        
        issues = []
        
        # Check: More hardware items than doors (should be roughly 2-4x)
        doors_count = quantities.get("doors", {}).get("total_count", 0)
        hardware_count = quantities.get("hardware", {}).get("total_count", 0)
        
        if doors_count > 0:
            hardware_per_door = hardware_count / doors_count
            if hardware_per_door > 10:
                issues.append({
                    "type": "excessive_hardware",
                    "message": f"Hardware count ({hardware_count}) seems excessive for {doors_count} doors",
                    "severity": "medium"
                })
            elif hardware_per_door < 1:
                issues.append({
                    "type": "insufficient_hardware",
                    "message": f"Hardware count ({hardware_count}) seems low for {doors_count} doors",
                    "severity": "low"
                })
        
        # Check: Windows should be reasonable relative to rooms
        rooms_count = quantities.get("rooms", {}).get("total_count", 0)
        windows_count = quantities.get("windows", {}).get("total_count", 0)
        
        if rooms_count > 0:
            windows_per_room = windows_count / rooms_count
            if windows_per_room > 10:
                issues.append({
                    "type": "excessive_windows",
                    "message": f"Window count ({windows_count}) seems excessive for {rooms_count} rooms",
                    "severity": "medium"
                })
        
        return {
            "issues": issues,
            "is_consistent": len(issues) == 0,
            "confidence": 0.9 if len(issues) == 0 else 0.7 - len(issues) * 0.1
        }
    
    def _calculate_overall_confidence(self, checks: Dict) -> float:
        """Calculate overall confidence from individual checks."""
        
        confidences = [
            check.get("confidence", 0.5)
            for check in checks.values()
        ]
        
        if not confidences:
            return 0.5
        
        # Weighted average (could be more sophisticated)
        return sum(confidences) / len(confidences)
    
    def _generate_flags(self, checks: Dict) -> List[Dict]:
        """Generate flags for issues found during verification."""
        
        flags = []
        
        # Flag high-confidence issues
        for check_name, check_result in checks.items():
            if not check_result.get("is_consistent", True):
                flags.append({
                    "type": check_name,
                    "severity": "medium",
                    "message": f"Issue detected in {check_name}",
                    "details": check_result
                })
        
        return flags
    
    async def _generate_recommendations(
        self,
        verification_report: Dict
    ) -> List[str]:
        """Generate recommendations based on verification results."""
        
        recommendations = []
        checks = verification_report.get("checks", {})
        
        # Recommendation based on quantity bounds
        bounds_check = checks.get("quantity_bounds", {})
        if not bounds_check.get("all_within_bounds", True):
            recommendations.append(
                "Review quantity bounds - some values seem outside expected ranges"
            )
        
        # Recommendation based on consistency
        consistency_check = checks.get("cv_text_consistency", {})
        if not consistency_check.get("is_consistent", True):
            recommendations.append(
                "CV and text extraction show discrepancies - manual review recommended"
            )
        
        # Recommendation based on completeness
        completeness_check = checks.get("completeness", {})
        if not completeness_check.get("is_complete", True):
            missing = completeness_check.get("missing_categories", [])
            recommendations.append(
                f"Missing categories detected: {', '.join(missing)} - consider re-extraction"
            )
        
        if not recommendations:
            recommendations.append("All checks passed - results look good!")
        
        return recommendations
    
    async def create_review_queue(
        self,
        verification_report: Dict,
        threshold: float = None
    ) -> Dict[str, Any]:
        """
        Create human-in-the-loop review queue for low-confidence items.
        """
        threshold = threshold or settings.confidence_threshold
        
        review_items = []
        
        # Add items below confidence threshold
        if verification_report["overall_confidence"] < threshold:
            review_items.append({
                "type": "overall",
                "reason": "Overall confidence below threshold",
                "confidence": verification_report["overall_confidence"],
                "priority": "high"
            })
        
        # Add flagged items
        for flag in verification_report.get("flags", []):
            review_items.append({
                "type": flag["type"],
                "reason": flag["message"],
                "severity": flag.get("severity", "medium"),
                "priority": "medium" if flag["severity"] == "high" else "low"
            })
        
        return {
            "requires_review": len(review_items) > 0,
            "review_items": review_items,
            "total_items": len(review_items)
        }


