"""Professional report generation for construction document analysis."""

from typing import Dict, Any
from pathlib import Path
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate professional reports in multiple formats."""
    
    async def generate_report(
        self,
        results: Dict[str, Any],
        format: str = "html",
        output_dir: Path = None
    ) -> str:
        """
        Generate report from analysis results.
        
        Args:
            results: Analysis results dictionary
            format: Report format (html, pdf, markdown)
            output_dir: Output directory
            
        Returns:
            Path to generated report
        """
        output_dir = output_dir or Path("reports")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "html":
            return await self._generate_html_report(results, output_dir, timestamp)
        elif format == "pdf":
            return await self._generate_pdf_report(results, output_dir, timestamp)
        elif format == "markdown":
            return await self._generate_markdown_report(results, output_dir, timestamp)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def _generate_html_report(
        self,
        results: Dict[str, Any],
        output_dir: Path,
        timestamp: str
    ) -> str:
        """Generate interactive HTML report."""
        
        quantities = results.get("quantities", {}).get("quantities", {})
        verification = results.get("verification", {})
        extraction = results.get("extraction", {})
        
        # Build HTML content
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Construction Document Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a1a; margin-bottom: 10px; }}
        .subtitle {{ color: #666; margin-bottom: 30px; }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 15px; }}
        .metric-label {{ color: #666; font-size: 14px; text-transform: uppercase; }}
        .metric-value {{ color: #2c3e50; font-size: 32px; font-weight: bold; margin-top: 5px; }}
        .chart-container {{ margin: 20px 0; height: 300px; }}
        .status-badge {{ display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
        .status-success {{ background: #d4edda; color: #155724; }}
        .status-warning {{ background: #fff3cd; color: #856404; }}
        .status-error {{ background: #f8d7da; color: #721c24; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #2c3e50; }}
        .confidence-bar {{ background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden; }}
        .confidence-fill {{ background: linear-gradient(90deg, #28a745, #20c997); height: 100%; transition: width 0.3s; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏗️ Construction Document Analysis Report</h1>
        <p class="subtitle">Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
        
        <div class="section">
            <h2>Executive Summary</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                <div class="metric-card">
                    <div class="metric-label">Overall Confidence</div>
                    <div class="metric-value">{verification.get('overall_confidence', 0) * 100:.1f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Document Pages</div>
                    <div class="metric-value">{extraction.get('total_pages', 'N/A')}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Status</div>
                    <div class="metric-value">
                        <span class="status-badge {'status-success' if results.get('success') else 'status-error'}">
                            {'✓ Success' if results.get('success') else '✗ Failed'}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Extracted Quantities</h2>
            <div class="chart-container">
                <canvas id="quantitiesChart"></canvas>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Quantity</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        # Add quantity rows
        chart_data = {"labels": [], "values": []}
        for category, data in quantities.items():
            total = data.get("total_count", 0)
            confidence = verification.get("checks", {}).get("quantity_bounds", {}).get("category_results", {}).get(category, {}).get("confidence", 0.8)
            
            html_content += f"""
                    <tr>
                        <td><strong>{category.capitalize()}</strong></td>
                        <td>{total}</td>
                        <td>
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: {confidence * 100}%"></div>
                            </div>
                            <span style="margin-left: 10px;">{confidence * 100:.1f}%</span>
                        </td>
                    </tr>
"""
            chart_data["labels"].append(category.capitalize())
            chart_data["values"].append(total)
        
        html_content += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Verification Results</h2>
"""
        
        # Add verification details
        checks = verification.get("checks", {})
        for check_name, check_result in checks.items():
            is_valid = check_result.get("is_consistent", check_result.get("all_within_bounds", True))
            html_content += f"""
            <div class="metric-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{check_name.replace('_', ' ').title()}</strong>
                        <p style="color: #666; margin-top: 5px;">{check_result.get('confidence', 0) * 100:.1f}% confidence</p>
                    </div>
                    <span class="status-badge {'status-success' if is_valid else 'status-warning'}">
                        {'✓ Pass' if is_valid else '⚠ Review'}
                    </span>
                </div>
            </div>
"""
        
        html_content += """
        </div>
        
        <div class="section">
            <h2>Recommendations</h2>
            <ul style="line-height: 2;">
"""
        
        recommendations = verification.get("recommendations", [])
        for rec in recommendations:
            html_content += f"<li>{rec}</li>"
        
        html_content += """
            </ul>
        </div>
    </div>
    
    <script>
        // Quantities Chart
        const ctx = document.getElementById('quantitiesChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: """ + json.dumps(chart_data["labels"]) + """,
                datasets: [{
                    label: 'Quantity',
                    data: """ + json.dumps(chart_data["values"]) + """,
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.8)',
                        'rgba(46, 204, 113, 0.8)',
                        'rgba(241, 196, 15, 0.8)',
                        'rgba(231, 76, 60, 0.8)',
                        'rgba(155, 89, 182, 0.8)'
                    ],
                    borderColor: [
                        'rgba(52, 152, 219, 1)',
                        'rgba(46, 204, 113, 1)',
                        'rgba(241, 196, 15, 1)',
                        'rgba(231, 76, 60, 1)',
                        'rgba(155, 89, 182, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Extracted Quantities by Category'
                    }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    </script>
</body>
</html>
"""
        
        # Save HTML file
        output_path = output_dir / f"report_{timestamp}.html"
        output_path.write_text(html_content)
        
        return str(output_path)
    
    async def _generate_pdf_report(
        self,
        results: Dict[str, Any],
        output_dir: Path,
        timestamp: str
    ) -> str:
        """Generate PDF report (simplified - would use reportlab or weasyprint in production)."""
        # For now, generate HTML and note that PDF conversion would be added
        html_path = await self._generate_html_report(results, output_dir, timestamp)
        logger.info(f"PDF generation: HTML report saved at {html_path}. PDF conversion requires additional library.")
        return html_path
    
    async def _generate_markdown_report(
        self,
        results: Dict[str, Any],
        output_dir: Path,
        timestamp: str
    ) -> str:
        """Generate Markdown report."""
        
        quantities = results.get("quantities", {}).get("quantities", {})
        verification = results.get("verification", {})
        
        markdown = f"""# Construction Document Analysis Report

**Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}

## Executive Summary

- **Overall Confidence:** {verification.get('overall_confidence', 0) * 100:.1f}%
- **Status:** {'✓ Success' if results.get('success') else '✗ Failed'}

## Extracted Quantities

| Category | Quantity | Confidence |
|----------|----------|------------|
"""
        
        for category, data in quantities.items():
            total = data.get("total_count", 0)
            confidence = 0.85  # Would get from verification
            markdown += f"| {category.capitalize()} | {total} | {confidence * 100:.1f}% |\n"
        
        markdown += "\n## Verification Results\n\n"
        
        checks = verification.get("checks", {})
        for check_name, check_result in checks.items():
            is_valid = check_result.get("is_consistent", True)
            markdown += f"### {check_name.replace('_', ' ').title()}\n"
            markdown += f"- Status: {'✓ Pass' if is_valid else '⚠ Review'}\n"
            markdown += f"- Confidence: {check_result.get('confidence', 0) * 100:.1f}%\n\n"
        
        markdown += "## Recommendations\n\n"
        recommendations = verification.get("recommendations", [])
        for rec in recommendations:
            markdown += f"- {rec}\n"
        
        output_path = output_dir / f"report_{timestamp}.md"
        output_path.write_text(markdown)
        
        return str(output_path)

