"""Export takeoff results to various formats."""

from typing import Dict, List, Optional
import logging
from pathlib import Path
from datetime import datetime
import json

try:
    import pandas as pd
except ImportError:
    pd = None

logger = logging.getLogger(__name__)


class TakeoffExporter:
    """Export takeoff results to Excel, CSV, PDF."""
    
    async def export_to_excel(
        self,
        takeoff_result: Dict,
        output_path: Path
    ) -> Path:
        """Export takeoff to Excel format."""
        if pd is None:
            raise ImportError("pandas and openpyxl required for Excel export")
        
        try:
            # Create Excel writer
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    "Metric": [
                        "Project ID",
                        "Status",
                        "Total Trades",
                        "Overall Confidence",
                        "Created At",
                        "Completed At"
                    ],
                    "Value": [
                        takeoff_result.get("project_id", "N/A"),
                        takeoff_result.get("status", "N/A"),
                        len(takeoff_result.get("trades", [])),
                        f"{takeoff_result.get('confidence_scores', {}).get('overall', 0) * 100:.1f}%",
                        takeoff_result.get("created_at", "N/A"),
                        takeoff_result.get("completed_at", "N/A")
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
                
                # Quantities by trade
                quantities = takeoff_result.get("quantities", {})
                for trade in takeoff_result.get("trades", []):
                    trade_quantities = quantities.get(trade, {})
                    
                    if isinstance(trade_quantities, dict):
                        # Flatten quantities
                        rows = []
                        for item, value in trade_quantities.items():
                            if isinstance(value, (int, float)):
                                rows.append({
                                    "Item": item,
                                    "Quantity": value,
                                    "Unit": "count"  # Would get from metadata
                                })
                        
                        if rows:
                            df = pd.DataFrame(rows)
                            df.to_excel(writer, sheet_name=trade.capitalize(), index=False)
                
                # Verification results
                verification = takeoff_result.get("verification_results", {})
                if verification:
                    checks = verification.get("checks", {})
                    check_rows = []
                    for check_name, check_result in checks.items():
                        check_rows.append({
                            "Check": check_name.replace("_", " ").title(),
                            "Status": "PASS" if check_result.get("is_consistent", True) else "REVIEW",
                            "Confidence": f"{check_result.get('confidence', 0) * 100:.1f}%"
                        })
                    
                    if check_rows:
                        pd.DataFrame(check_rows).to_excel(
                            writer, sheet_name="Verification", index=False
                        )
            
            logger.info(f"Exported takeoff to Excel: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            raise
    
    async def export_to_csv(
        self,
        takeoff_result: Dict,
        output_path: Path
    ) -> Path:
        """Export takeoff to CSV format."""
        if pd is None:
            raise ImportError("pandas required for CSV export")
        
        try:
            # Combine all quantities into single CSV
            rows = []
            quantities = takeoff_result.get("quantities", {})
            
            for trade in takeoff_result.get("trades", []):
                trade_quantities = quantities.get(trade, {})
                if isinstance(trade_quantities, dict):
                    for item, value in trade_quantities.items():
                        if isinstance(value, (int, float)):
                            rows.append({
                                "Trade": trade,
                                "Item": item,
                                "Quantity": value,
                                "Unit": "count"
                            })
            
            if rows:
                df = pd.DataFrame(rows)
                df.to_csv(output_path, index=False)
            else:
                # Empty CSV with headers
                pd.DataFrame(columns=["Trade", "Item", "Quantity", "Unit"]).to_csv(
                    output_path, index=False
                )
            
            logger.info(f"Exported takeoff to CSV: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    async def export_to_pdf(
        self,
        takeoff_result: Dict,
        output_path: Path
    ) -> Path:
        """Export takeoff to PDF format."""
        # For now, generate HTML and note PDF conversion
        # In production, would use reportlab or weasyprint
        from src.reports.report_generator import ReportGenerator
        
        report_gen = ReportGenerator()
        html_path = await report_gen.generate_report(
            results={"quantities": takeoff_result},
            format="html",
            output_dir=output_path.parent
        )
        
        logger.info(f"PDF export: HTML report at {html_path}. PDF conversion requires additional library.")
        return Path(html_path)

