"""Specification Reasoning Agent - Reasons over Division 8/9 specs using RAG."""

from typing import Dict, List, Optional, Any
from langchain_core.messages import HumanMessage, SystemMessage
import logging

from src.rag.retrieval import RAGRetriever
from src.llm.llm_factory import get_llm, get_embeddings
from src.core.config import settings

logger = logging.getLogger(__name__)


class SpecReasoningAgent:
    """
    Agent that reasons over construction specifications (Division 8/9) using RAG.
    Retrieves relevant spec sections and applies reasoning to answer questions.
    """
    
    def __init__(self):
        self.llm = get_llm(temperature=0.2)  # Slightly creative for reasoning
        self.embeddings = get_embeddings()
        self.rag_retriever = RAGRetriever()
        
    async def reason_over_specs(
        self,
        query: str,
        context_documents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Reason over construction specifications to answer queries.
        
        Args:
            query: Question or requirement to reason about
            context_documents: Additional document context
            
        Returns:
            Reasoning result with citations and confidence
        """
        try:
            logger.info(f"Reasoning over specs for query: {query[:100]}...")
            
            # Retrieve relevant spec sections using RAG
            relevant_specs = await self.rag_retriever.retrieve(
                query=query,
                top_k=5
            )
            
            # Build context from retrieved specs
            spec_context = self._build_spec_context(relevant_specs)
            
            # Multi-step reasoning
            reasoning_result = await self._perform_reasoning(query, spec_context)
            
            # Validate reasoning against spec rules
            validation = await self._validate_reasoning(reasoning_result, relevant_specs)
            
            return {
                "query": query,
                "answer": reasoning_result["answer"],
                "reasoning_steps": reasoning_result["steps"],
                "citations": relevant_specs,
                "confidence": reasoning_result["confidence"],
                "validation": validation,
                "spec_sections_used": [s["section"] for s in relevant_specs]
            }
            
        except Exception as e:
            logger.error(f"Error in spec reasoning: {e}")
            raise
    
    def _build_spec_context(self, retrieved_specs: List[Dict]) -> str:
        """Build context string from retrieved specification sections."""
        context_parts = []
        
        for i, spec in enumerate(retrieved_specs, 1):
            context_parts.append(
                f"Spec Section {i} (Relevance: {spec.get('score', 0):.2f}):\n"
                f"{spec.get('content', '')}\n"
                f"Source: {spec.get('source', 'unknown')}\n"
            )
        
        return "\n\n".join(context_parts)
    
    async def _perform_reasoning(
        self,
        query: str,
        spec_context: str
    ) -> Dict[str, Any]:
        """Perform multi-step reasoning over specifications."""
        
        system_prompt = """You are an expert construction specification analyst.
        Your task is to reason over construction specifications (Division 8/9) to answer questions.
        
        Process:
        1. Understand the query and identify relevant spec sections
        2. Extract key requirements and constraints
        3. Apply logical reasoning to connect requirements
        4. Provide a clear answer with justification
        
        Be precise and cite specific spec sections in your reasoning."""
        
        reasoning_prompt = f"""Query: {query}

Relevant Specification Sections:
{spec_context}

Reason through this step-by-step:
1. What is the query asking?
2. Which spec sections are most relevant?
3. What are the key requirements?
4. How do they apply to the query?
5. What is the final answer?

Provide your reasoning and answer."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=reasoning_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Parse reasoning steps (in production, use structured output)
        reasoning_steps = self._extract_reasoning_steps(response.content)
        
        return {
            "answer": response.content,
            "steps": reasoning_steps,
            "confidence": 0.85  # Would calculate based on spec match quality
        }
    
    def _extract_reasoning_steps(self, reasoning_text: str) -> List[str]:
        """Extract structured reasoning steps from LLM response."""
        # Simple extraction - in production, use structured parsing
        steps = []
        lines = reasoning_text.split('\n')
        
        for line in lines:
            if line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                steps.append(line.strip())
        
        return steps if steps else [reasoning_text]
    
    async def _validate_reasoning(
        self,
        reasoning_result: Dict,
        specs: List[Dict]
    ) -> Dict[str, Any]:
        """Validate reasoning against specification rules."""
        
        validation_prompt = f"""Validate this reasoning against the specifications:

Reasoning: {reasoning_result['answer']}

Specifications:
{self._build_spec_context(specs)}

Check:
1. Is the reasoning consistent with the specs?
2. Are there any contradictions?
3. Are all requirements addressed?
4. Is the confidence level appropriate?

Return validation result."""
        
        messages = [
            SystemMessage(content="You are a validation expert for construction specifications."),
            HumanMessage(content=validation_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        return {
            "is_valid": "consistent" in response.content.lower(),
            "issues": [],
            "validation_notes": response.content
        }
    
    async def check_compliance(
        self,
        extracted_quantities: Dict,
        spec_requirements: Dict
    ) -> Dict[str, Any]:
        """
        Check if extracted quantities comply with specification requirements.
        """
        logger.info("Checking compliance with specifications...")
        
        compliance_results = {}
        
        for category, quantities in extracted_quantities.items():
            # Retrieve relevant specs for this category
            spec_query = f"{category} requirements and specifications"
            relevant_specs = await self.rag_retriever.retrieve(
                query=spec_query,
                top_k=3
            )
            
            # Check compliance
            compliance_check = await self._check_category_compliance(
                category,
                quantities,
                relevant_specs
            )
            
            compliance_results[category] = compliance_check
        
        return {
            "overall_compliance": all(
                r.get("is_compliant", False) 
                for r in compliance_results.values()
            ),
            "category_results": compliance_results
        }
    
    async def _check_category_compliance(
        self,
        category: str,
        quantities: Dict,
        specs: List[Dict]
    ) -> Dict[str, Any]:
        """Check compliance for a specific category."""
        
        check_prompt = f"""Check if these {category} quantities comply with specifications:

Quantities: {quantities}

Specifications:
{self._build_spec_context(specs)}

Determine compliance status."""
        
        messages = [
            SystemMessage(content="You are a compliance checker for construction specifications."),
            HumanMessage(content=check_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        return {
            "is_compliant": "compliant" in response.content.lower(),
            "issues": [],
            "notes": response.content
        }


