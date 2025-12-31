"""Quantity Take-off Agent - Extracts quantities of doors, windows, hardware, finishes."""

from typing import Dict, List, Optional, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import Tool
import logging
import json

from src.llm.llm_factory import get_llm
from src.core.config import settings

logger = logging.getLogger(__name__)


class QuantityTakeoffAgent:
    """
    Agent specialized in extracting quantities from construction documents.
    Identifies doors, windows, hardware, finishes, and other materials with counts.
    """
    
    def __init__(self):
        self.llm = get_llm(temperature=0.0)  # Deterministic for quantity extraction
        
    async def extract_quantities(
        self,
        document_text: str,
        document_type: str = "floor_plan"
    ) -> Dict[str, Any]:
        """
        Extract quantities of construction elements from document text.
        
        Args:
            document_text: Extracted text from construction document
            document_type: Type of document (floor_plan, elevation, schedule, etc.)
            
        Returns:
            Dictionary with extracted quantities organized by category
        """
        try:
            logger.info(f"Extracting quantities from {document_type}")
            
            # Task decomposition: break into smaller extraction tasks
            tasks = self._decompose_extraction_tasks(document_type)
            
            extracted_quantities = {}
            
            for task in tasks:
                category = task["category"]
                logger.info(f"Extracting {category} quantities...")
                
                quantities = await self._extract_category_quantities(
                    document_text,
                    category,
                    task["elements"]
                )
                
                extracted_quantities[category] = quantities
            
            # Validate and cross-check quantities
            validated_quantities = await self._validate_quantities(extracted_quantities)
            
            return {
                "quantities": validated_quantities,
                "confidence_scores": self._calculate_confidence(validated_quantities),
                "source_document_type": document_type,
                "extraction_method": "llm_reasoning"
            }
            
        except Exception as e:
            logger.error(f"Error extracting quantities: {e}")
            raise
    
    def _decompose_extraction_tasks(self, doc_type: str) -> List[Dict]:
        """Decompose quantity extraction into category-specific tasks."""
        base_tasks = [
            {
                "category": "doors",
                "elements": ["interior_doors", "exterior_doors", "fire_doors", "sliding_doors"]
            },
            {
                "category": "windows",
                "elements": ["standard_windows", "bay_windows", "skylights", "glass_doors"]
            },
            {
                "category": "hardware",
                "elements": ["door_handles", "locks", "hinges", "closers", "strikes"]
            },
            {
                "category": "finishes",
                "elements": ["paint", "flooring", "wall_coverings", "ceiling_treatments"]
            }
        ]
        
        # Add document-specific tasks
        if doc_type == "floor_plan":
            base_tasks.append({
                "category": "rooms",
                "elements": ["bedrooms", "bathrooms", "kitchens", "living_areas"]
            })
        
        return base_tasks
    
    async def _extract_category_quantities(
        self,
        text: str,
        category: str,
        elements: List[str]
    ) -> Dict[str, Any]:
        """Extract quantities for a specific category using LLM reasoning."""
        
        system_prompt = f"""You are an expert quantity surveyor analyzing construction documents.
        Extract quantities for {category} category, specifically looking for: {', '.join(elements)}
        
        For each element found, provide:
        - Element type/description
        - Quantity (count)
        - Unit of measurement
        - Location/room reference if available
        - Specifications (size, material, etc.)
        
        Be precise and only extract information explicitly stated or clearly inferable.
        Return results as structured JSON."""
        
        user_prompt = f"""Extract {category} quantities from this construction document text:
        
        {text[:8000]}  # Limit text to avoid token limits
        
        Return JSON with this structure:
        {{
            "elements": [
                {{
                    "type": "element_type",
                    "quantity": number,
                    "unit": "unit",
                    "location": "location_ref",
                    "specifications": {{}}
                }}
            ]
        }}"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Parse JSON response
        try:
            # In production, use structured output parsing
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            logger.warning("Failed to parse JSON from LLM response")
        
        return {"elements": [], "raw_response": response.content}
    
    async def _validate_quantities(self, quantities: Dict) -> Dict:
        """Apply validation rules and sanity checks."""
        validated = {}
        
        for category, data in quantities.items():
            elements = data.get("elements", [])
            
            # Sanity checks
            validated_elements = []
            for elem in elements:
                qty = elem.get("quantity", 0)
                
                # Apply bounds checking
                if category == "doors" and qty > 1000:
                    logger.warning(f"Suspicious door quantity: {qty}")
                    elem["confidence"] = 0.5
                    elem["validation_flag"] = "high_quantity"
                elif qty < 0:
                    logger.warning(f"Negative quantity detected: {qty}")
                    elem["confidence"] = 0.0
                    elem["validation_flag"] = "invalid"
                else:
                    elem["confidence"] = 0.9
                    elem["validation_flag"] = "valid"
                
                validated_elements.append(elem)
            
            validated[category] = {
                "elements": validated_elements,
                "total_count": sum(e.get("quantity", 0) for e in validated_elements)
            }
        
        return validated
    
    def _calculate_confidence(self, quantities: Dict) -> Dict[str, float]:
        """Calculate confidence scores for extracted quantities."""
        confidence_scores = {}
        
        for category, data in quantities.items():
            elements = data.get("elements", [])
            if elements:
                avg_confidence = sum(
                    e.get("confidence", 0.5) for e in elements
                ) / len(elements)
                confidence_scores[category] = avg_confidence
            else:
                confidence_scores[category] = 0.0
        
        return confidence_scores
    
    def get_tools(self) -> List[Tool]:
        """Return tools available to this agent."""
        return [
            Tool(
                name="extract_quantities",
                func=lambda x: self.extract_quantities(x),
                description="Extract quantities of construction elements from document text"
            )
        ]


