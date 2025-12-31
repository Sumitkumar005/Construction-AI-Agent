"""LangGraph orchestration for multi-agent construction document analysis."""

from typing import Dict, List, Optional, Any, TypedDict, Annotated
import logging
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from src.agents.extraction_agent import ExtractionAgent
from src.agents.quantity_agent import QuantityTakeoffAgent
from src.agents.spec_reasoning_agent import SpecReasoningAgent
from src.agents.cv_agent import ComputerVisionAgent
from src.agents.verification_agent import VerificationAgent

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State shared across all agents in the graph."""
    document_path: str
    extraction_results: Optional[Dict[str, Any]]
    quantity_results: Optional[Dict[str, Any]]
    cv_results: Optional[Dict[str, Any]]
    spec_reasoning_results: Optional[Dict[str, Any]]
    verification_results: Optional[Dict[str, Any]]
    final_output: Optional[Dict[str, Any]]
    errors: List[str]
    metadata: Dict[str, Any]


class ConstructionAgentSystem:
    """
    Multi-agent system for construction document analysis using LangGraph.
    Orchestrates extraction, quantity take-off, CV analysis, spec reasoning, and verification.
    """
    
    def __init__(self):
        # Initialize agents
        self.extraction_agent = ExtractionAgent()
        self.quantity_agent = QuantityTakeoffAgent()
        self.spec_agent = SpecReasoningAgent()
        self.cv_agent = ComputerVisionAgent()
        self.verification_agent = VerificationAgent()
        
        # Build graph
        self.graph = self._build_graph()
        
        # Compile with memory
        memory = MemorySaver()
        self.app = self.graph.compile(checkpointer=memory)
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph agent orchestration graph."""
        
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes (agents)
        workflow.add_node("extract", self._extract_node)
        workflow.add_node("quantity", self._quantity_node)
        workflow.add_node("cv_analysis", self._cv_node)
        workflow.add_node("spec_reasoning", self._spec_node)
        workflow.add_node("verify", self._verify_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Define edges (workflow)
        workflow.set_entry_point("extract")
        
        # After extraction, run quantity and CV in parallel
        workflow.add_edge("extract", "quantity")
        workflow.add_edge("extract", "cv_analysis")
        
        # After quantity and CV, do spec reasoning
        workflow.add_conditional_edges(
            "quantity",
            self._should_do_spec_reasoning,
            {
                "yes": "spec_reasoning",
                "no": "verify"
            }
        )
        
        workflow.add_edge("cv_analysis", "verify")
        workflow.add_edge("spec_reasoning", "verify")
        
        # After verification, finalize
        workflow.add_edge("verify", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow
    
    async def _extract_node(self, state: AgentState) -> AgentState:
        """Extraction agent node."""
        try:
            logger.info("Running extraction agent...")
            
            extraction_results = await self.extraction_agent.extract_document(
                pdf_path=state["document_path"]
            )
            
            state["extraction_results"] = extraction_results
            state["metadata"]["extraction_complete"] = True
            
            return state
            
        except Exception as e:
            logger.error(f"Error in extraction: {e}")
            state["errors"].append(f"Extraction error: {str(e)}")
            return state
    
    async def _quantity_node(self, state: AgentState) -> AgentState:
        """Quantity take-off agent node."""
        try:
            logger.info("Running quantity agent...")
            
            if not state.get("extraction_results"):
                state["errors"].append("No extraction results available")
                return state
            
            # Combine text from all pages
            pages = state["extraction_results"].get("pages", [])
            document_text = "\n\n".join([p.get("text", "") for p in pages])
            
            quantity_results = await self.quantity_agent.extract_quantities(
                document_text=document_text,
                document_type=state["extraction_results"].get("structured_data", {}).get("document_type", "floor_plan")
            )
            
            state["quantity_results"] = quantity_results
            state["metadata"]["quantity_complete"] = True
            
            return state
            
        except Exception as e:
            logger.error(f"Error in quantity extraction: {e}")
            state["errors"].append(f"Quantity extraction error: {str(e)}")
            return state
    
    async def _cv_node(self, state: AgentState) -> AgentState:
        """Computer Vision agent node."""
        try:
            logger.info("Running CV agent...")
            
            if not state.get("extraction_results"):
                state["errors"].append("No extraction results available")
                return state
            
            # Extract images from PDF if available
            from src.tools.pdf_parser import PDFParser
            pdf_parser = PDFParser()
            
            # For now, use first page image if available
            # In production, would extract all floor plan pages
            pages = state["extraction_results"].get("pages", [])
            
            cv_results = None
            for page in pages:
                if page.get("has_images"):
                    # In production, would extract and analyze images
                    # For now, return placeholder
                    cv_results = {
                        "analysis_complete": False,
                        "note": "CV analysis requires image extraction - implement in production"
                    }
                    break
            
            if not cv_results:
                cv_results = {
                    "analysis_complete": False,
                    "note": "No images found in document"
                }
            
            state["cv_results"] = cv_results
            state["metadata"]["cv_complete"] = True
            
            return state
            
        except Exception as e:
            logger.error(f"Error in CV analysis: {e}")
            state["errors"].append(f"CV analysis error: {str(e)}")
            state["cv_results"] = {"error": str(e)}
            return state
    
    async def _spec_node(self, state: AgentState) -> AgentState:
        """Specification reasoning agent node."""
        try:
            logger.info("Running spec reasoning agent...")
            
            if not state.get("quantity_results"):
                state["errors"].append("No quantity results available")
                return state
            
            # Create query from extracted quantities
            quantities = state["quantity_results"].get("quantities", {})
            query = f"Analyze these construction quantities: {quantities}"
            
            spec_results = await self.spec_agent.reason_over_specs(query=query)
            
            # Check compliance
            compliance = await self.spec_agent.check_compliance(
                extracted_quantities=quantities,
                spec_requirements={}
            )
            
            spec_results["compliance"] = compliance
            
            state["spec_reasoning_results"] = spec_results
            state["metadata"]["spec_reasoning_complete"] = True
            
            return state
            
        except Exception as e:
            logger.error(f"Error in spec reasoning: {e}")
            state["errors"].append(f"Spec reasoning error: {str(e)}")
            return state
    
    async def _verify_node(self, state: AgentState) -> AgentState:
        """Verification agent node."""
        try:
            logger.info("Running verification agent...")
            
            verification_results = await self.verification_agent.verify_extraction_results(
                extraction_results=state.get("extraction_results", {}),
                quantities=state.get("quantity_results", {}).get("quantities", {}),
                cv_results=state.get("cv_results")
            )
            
            # Create review queue if needed
            review_queue = await self.verification_agent.create_review_queue(
                verification_results
            )
            verification_results["review_queue"] = review_queue
            
            state["verification_results"] = verification_results
            state["metadata"]["verification_complete"] = True
            
            return state
            
        except Exception as e:
            logger.error(f"Error in verification: {e}")
            state["errors"].append(f"Verification error: {str(e)}")
            return state
    
    async def _finalize_node(self, state: AgentState) -> AgentState:
        """Finalize and compile results."""
        try:
            logger.info("Finalizing results...")
            
            final_output = {
                "document_path": state["document_path"],
                "extraction": state.get("extraction_results"),
                "quantities": state.get("quantity_results"),
                "cv_analysis": state.get("cv_results"),
                "spec_reasoning": state.get("spec_reasoning_results"),
                "verification": state.get("verification_results"),
                "metadata": state.get("metadata", {}),
                "errors": state.get("errors", []),
                "success": len(state.get("errors", [])) == 0
            }
            
            state["final_output"] = final_output
            state["metadata"]["finalized"] = True
            
            return state
            
        except Exception as e:
            logger.error(f"Error in finalization: {e}")
            state["errors"].append(f"Finalization error: {str(e)}")
            return state
    
    def _should_do_spec_reasoning(self, state: AgentState) -> str:
        """Conditional edge: decide if spec reasoning is needed."""
        # Check if spec documents are available or if quantities were extracted
        if state.get("quantity_results") and state["quantity_results"].get("quantities"):
            return "yes"
        return "no"
    
    async def process_document(
        self,
        pdf_path: str,
        spec_docs: Optional[List[str]] = None,
        config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a construction document through the full agent pipeline.
        
        Args:
            pdf_path: Path to PDF document
            spec_docs: Optional list of specification document paths
            config: Optional configuration dictionary
            
        Returns:
            Final output with all analysis results
        """
        try:
            # Initialize state
            initial_state: AgentState = {
                "document_path": pdf_path,
                "extraction_results": None,
                "quantity_results": None,
                "cv_results": None,
                "spec_reasoning_results": None,
                "verification_results": None,
                "final_output": None,
                "errors": [],
                "metadata": {
                    "spec_docs": spec_docs or [],
                    "config": config or {}
                }
            }
            
            # Run graph
            config_dict = {"configurable": {"thread_id": "1"}}
            final_state = await self.app.ainvoke(initial_state, config_dict)
            
            return final_state.get("final_output", {})
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_path": pdf_path
            }


