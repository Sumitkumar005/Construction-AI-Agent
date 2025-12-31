"""Full multi-agent pipeline with RAG integration."""

from typing import Dict, List, Optional, Any, Callable
import logging
import asyncio
from datetime import datetime

from src.agents.extraction_agent import ExtractionAgent
from src.agents.spec_reasoning_agent import SpecReasoningAgent
from src.agents.verification_agent import VerificationAgent
from src.agents.cv_agent import ComputerVisionAgent
from src.services.trade_extractor import TradeExtractor
from src.services.moondream_service import MoondreamService
from src.tools.pdf_parser import PDFParser
from src.core.config import settings
from pathlib import Path

logger = logging.getLogger(__name__)


class FullAgentPipeline:
    """
    Complete multi-agent pipeline that integrates:
    - ExtractionAgent
    - MoondreamService (image-based dimension extraction)
    - TradeExtractor (trade-specific quantity extraction)
    - CVAgent (fallback computer vision)
    - SpecReasoningAgent (RAG-based spec compliance)
    - VerificationAgent (validation and confidence scoring)
    """
    
    def __init__(self):
        self.extraction_agent = ExtractionAgent()
        self.trade_extractor = TradeExtractor()
        self.spec_agent = SpecReasoningAgent()
        self.verification_agent = VerificationAgent()
        self.cv_agent = ComputerVisionAgent()
        self.moondream_service = None
        if settings.moondream_api_key:
            try:
                self.moondream_service = MoondreamService()
            except Exception as e:
                logger.warning(f"Moondream service not available: {e}")
    
    async def process_takeoff(
        self,
        pdf_path: str,
        selected_trades: List[str],
        project_id: str,
        project_file_name: Optional[str] = None,
        cancellation_check: Optional[Callable[[], bool]] = None
    ) -> Dict[str, Any]:
        """
        Process a takeoff through the full multi-agent pipeline.
        
        Args:
            pdf_path: Path to PDF document
            selected_trades: List of trades to extract (e.g., ["flooring", "painting"])
            project_id: Project identifier
            project_file_name: Optional filename for fallback extraction
            cancellation_check: Optional callable that returns True if processing should be cancelled
            
        Returns:
            Complete takeoff results with all agent outputs
        """
        pipeline_results = {
            "extraction": None,
            "moondream": None,
            "cv_analysis": None,
            "trade_quantities": {},
            "spec_reasoning": None,
            "verification": None,
            "metadata": {
                "start_time": datetime.now(),
                "project_id": project_id,
                "trades": selected_trades
            },
            "errors": []
        }
        
        try:
            # ============================================
            # STAGE 1: EXTRACTION
            # ============================================
            logger.info("🔍 Stage 1: Document Extraction")
            if cancellation_check and cancellation_check():
                raise asyncio.CancelledError("Processing cancelled")
            
            extraction_results = await self.extraction_agent.extract_document(pdf_path)
            pipeline_results["extraction"] = extraction_results
            
            # Combine text from all pages
            pages = extraction_results.get("pages", [])
            document_text = "\n\n".join([p.get("text", "") for p in pages])
            
            # Use OCR if text is minimal
            if len(document_text.strip()) < 500:
                logger.info("Text is minimal, attempting OCR...")
                extraction_results = await self.extraction_agent.extract_document(
                    pdf_path,
                    use_ocr=True
                )
                pages = extraction_results.get("pages", [])
                document_text = "\n\n".join([p.get("text", "") for p in pages])
                pipeline_results["extraction"] = extraction_results
            
            # ============================================
            # STAGE 2: IMAGE EXTRACTION
            # ============================================
            logger.info("🖼️ Stage 2: Image Extraction")
            image_paths = []
            try:
                temp_base = Path("temp_images")
                temp_base.mkdir(exist_ok=True, parents=True)
                
                pdf_parser = PDFParser()
                image_paths = await pdf_parser.extract_images(
                    pdf_path,
                    output_dir=str(temp_base / project_id)
                )
                logger.info(f"Extracted {len(image_paths)} images from PDF")
            except Exception as e:
                logger.warning(f"Failed to extract images: {e}")
                pipeline_results["errors"].append(f"Image extraction: {str(e)}")
            
            # ============================================
            # STAGE 3: MOONDREAM AI (Primary)
            # ============================================
            moondream_results = None
            if image_paths and self.moondream_service:
                try:
                    logger.info("🌙 Stage 3: Moondream AI Analysis")
                    moondream_results = await self.moondream_service.extract_dimensions_from_image(
                        image_paths[0]
                    )
                    if moondream_results.get("parsed_successfully"):
                        logger.info(f"✅ Moondream extracted {len(moondream_results.get('dimensions', {}))} room dimensions")
                    pipeline_results["moondream"] = moondream_results
                except Exception as e:
                    logger.warning(f"Moondream AI failed: {e}")
                    pipeline_results["errors"].append(f"Moondream: {str(e)}")
            
            # ============================================
            # STAGE 4: CV ANALYSIS (Fallback)
            # ============================================
            cv_results = None
            if not moondream_results and settings.enable_cv_analysis and image_paths:
                try:
                    logger.info("👁️ Stage 4: Computer Vision Analysis (Fallback)")
                    cv_results = await self.cv_agent.analyze_floor_plan(
                        image_paths[0],
                        analysis_type="full"
                    )
                    pipeline_results["cv_analysis"] = cv_results
                    logger.info(f"CV analysis complete: {len(cv_results.get('processed_objects', {}).get('rooms', []))} rooms detected")
                except Exception as e:
                    logger.warning(f"CV analysis failed: {e}")
                    pipeline_results["errors"].append(f"CV: {str(e)}")
            
            # ============================================
            # STAGE 5: TRADE QUANTITY EXTRACTION
            # ============================================
            logger.info("📊 Stage 5: Trade Quantity Extraction")
            trade_results = {}
            confidence_scores = {}
            
            for trade_str in selected_trades:
                # Check for cancellation before each trade
                if cancellation_check and cancellation_check():
                    raise asyncio.CancelledError("Processing cancelled")
                try:
                    from src.models.trade import TradeType
                    trade_type = TradeType(trade_str)
                    
                    result = await self.trade_extractor.extract_trade_quantities(
                        document_text=document_text,
                        trade_type=trade_type,
                        cv_results=cv_results,
                        project_file_name=project_file_name,
                        moondream_results=moondream_results
                    )
                    
                    trade_results[trade_str] = result.quantities
                    confidence_scores[trade_str] = result.confidence
                    
                    logger.info(f"✅ Extracted {trade_str}: {result.confidence:.2f} confidence")
                    
                except Exception as e:
                    logger.error(f"Error extracting {trade_str}: {e}", exc_info=True)
                    trade_results[trade_str] = {}
                    confidence_scores[trade_str] = 0.5
                    pipeline_results["errors"].append(f"Trade extraction ({trade_str}): {str(e)}")
            
            pipeline_results["trade_quantities"] = trade_results
            
            # ============================================
            # STAGE 6: SPEC REASONING (RAG)
            # ============================================
            spec_reasoning_results = None
            if trade_results:
                # Check for cancellation before RAG
                if cancellation_check and cancellation_check():
                    raise asyncio.CancelledError("Processing cancelled")
                
                try:
                    logger.info("📚 Stage 6: Specification Reasoning (RAG)")
                    
                    # Create query from extracted quantities
                    quantities_summary = self._summarize_quantities(trade_results)
                    query = f"Analyze these construction quantities for compliance: {quantities_summary}"
                    
                    # Reason over specs using RAG
                    spec_reasoning_results = await self.spec_agent.reason_over_specs(
                        query=query
                    )
                    
                    # Check compliance
                    compliance_results = await self.spec_agent.check_compliance(
                        extracted_quantities=trade_results,
                        spec_requirements={}
                    )
                    
                    spec_reasoning_results["compliance"] = compliance_results
                    pipeline_results["spec_reasoning"] = spec_reasoning_results
                    
                    logger.info(f"✅ Spec reasoning complete: {spec_reasoning_results.get('confidence', 0):.2f} confidence")
                    logger.info(f"✅ Compliance check: {compliance_results.get('overall_compliance', False)}")
                    
                except Exception as e:
                    logger.warning(f"Spec reasoning failed (RAG may not be initialized): {e}")
                    pipeline_results["errors"].append(f"Spec reasoning: {str(e)}")
                    # Continue without spec reasoning - not critical for basic extraction
            
            # ============================================
            # STAGE 7: VERIFICATION
            # ============================================
            logger.info("✅ Stage 7: Verification & Validation")
            
            # Check for cancellation before verification
            if cancellation_check and cancellation_check():
                raise asyncio.CancelledError("Processing cancelled")
            
            verification_results = await self.verification_agent.verify_extraction_results(
                extraction_results=extraction_results,
                quantities=trade_results,
                cv_results=cv_results
            )
            pipeline_results["verification"] = verification_results
            
            # Calculate overall confidence
            overall_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
            
            # ============================================
            # FINALIZE
            # ============================================
            pipeline_results["metadata"]["end_time"] = datetime.now()
            pipeline_results["metadata"]["processing_time"] = (
                pipeline_results["metadata"]["end_time"] - pipeline_results["metadata"]["start_time"]
            ).total_seconds()
            pipeline_results["metadata"]["overall_confidence"] = overall_confidence
            pipeline_results["metadata"]["success"] = len(pipeline_results["errors"]) == 0
            
            logger.info(f"🎉 Pipeline complete: {overall_confidence:.2f} confidence, {len(pipeline_results['errors'])} errors")
            
            return pipeline_results
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            pipeline_results["errors"].append(f"Pipeline: {str(e)}")
            pipeline_results["metadata"]["end_time"] = datetime.now()
            pipeline_results["metadata"]["success"] = False
            return pipeline_results
    
    def _summarize_quantities(self, trade_results: Dict) -> str:
        """Create a summary string of extracted quantities for RAG query."""
        summary_parts = []
        
        for trade, quantities in trade_results.items():
            if isinstance(quantities, dict):
                # Extract key metrics
                total = quantities.get("total_sqft") or quantities.get("total_count") or 0
                summary_parts.append(f"{trade}: {total}")
        
        return ", ".join(summary_parts)

