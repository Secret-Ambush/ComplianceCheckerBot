import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from src.models.document import Document
from src.models.validation import ComplianceReport, ValidationIssue, ValidationResult

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self, output_dir: Union[str, Path]):
        """Initialize the report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(
        self,
        report: ComplianceReport,
        document: Document,
        related_documents: List[Document],
        format: str = "markdown"
    ) -> Path:
        """Generate a compliance report.
        
        Args:
            report: Compliance report
            document: Source document
            related_documents: Related documents
            format: Report format (markdown, json, html)
            
        Returns:
            Path to generated report
        """
        # Generate report content
        if format == "markdown":
            content = self._generate_markdown_report(report, document, related_documents)
            extension = "md"
        elif format == "json":
            content = self._generate_json_report(report, document, related_documents)
            extension = "json"
        elif format == "html":
            content = self._generate_html_report(report, document, related_documents)
            extension = "html"
        else:
            raise ValueError(f"Unsupported report format: {format}")
        
        # Create report file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_report_{document.id}_{timestamp}.{extension}"
        report_path = self.output_dir / filename
        
        # Save report
        report_path.write_text(content)
        logger.info(f"Generated report: {report_path}")
        
        return report_path
    
    def _generate_markdown_report(
        self, report: ComplianceReport, document: Document, related_documents: List[Document]
    ) -> str:
        """Generate a markdown report.
        
        Args:
            report: Compliance report
            document: Source document
            related_documents: Related documents
            
        Returns:
            Markdown report content
        """
        lines = [
            f"# Compliance Report for {document.filename}",
            f"\nGenerated at: {report.created_at.isoformat()}",
            f"\n## Document Information",
            f"\n- Document ID: {document.id}",
            f"- Document Type: {document.document_type}",
            f"- Document Number: {document.document_number or 'N/A'}",
            f"- Vendor: {document.vendor_name or 'N/A'}",
            f"- Total Amount: {document.total_amount or 'N/A'} {document.currency}",
        ]
        
        # Add related documents
        if related_documents:
            lines.append("\n## Related Documents")
            for doc in related_documents:
                lines.append(f"\n### {doc.filename}")
                lines.append(f"- Document ID: {doc.id}")
                lines.append(f"- Document Type: {doc.document_type}")
                lines.append(f"- Document Number: {doc.document_number or 'N/A'}")
        
        # Add validation summary
        lines.append("\n## Validation Summary")
        for key, value in report.summary.items():
            lines.append(f"- {key}: {value}")
        
        # Add validation results
        lines.append("\n## Validation Results")
        for result in report.validation_results:
            lines.append(f"\n### Rule {result.document_id}")
            lines.append(f"Status: {result.status}")
            lines.append(f"Execution Time: {result.execution_time:.2f}s")
            
            if result.issues:
                lines.append("\nIssues:")
                for issue in result.issues:
                    lines.append(f"- [{issue.severity}] {issue.message}")
                    if issue.details:
                        lines.append("  Details:")
                        for key, value in issue.details.items():
                            lines.append(f"  - {key}: {value}")
        
        return "\n".join(lines)
    
    def _generate_json_report(
        self, report: ComplianceReport, document: Document, related_documents: List[Document]
    ) -> str:
        """Generate a JSON report.
        
        Args:
            report: Compliance report
            document: Source document
            related_documents: Related documents
            
        Returns:
            JSON report content
        """
        # Create report data
        data = {
            "report": {
                "id": str(report.id),
                "job_id": str(report.job_id),
                "created_at": report.created_at.isoformat(),
                "overall_status": report.overall_status,
                "summary": report.summary
            },
            "document": {
                "id": str(document.id),
                "filename": document.filename,
                "type": document.document_type,
                "number": document.document_number,
                "vendor": document.vendor_name,
                "total_amount": document.total_amount,
                "currency": document.currency
            },
            "related_documents": [
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "type": doc.document_type,
                    "number": doc.document_number
                }
                for doc in related_documents
            ],
            "validation_results": [
                {
                    "id": str(result.id),
                    "status": result.status,
                    "execution_time": result.execution_time,
                    "issues": [
                        {
                            "id": str(issue.id),
                            "status": issue.status,
                            "severity": issue.severity,
                            "message": issue.message,
                            "details": issue.details
                        }
                        for issue in result.issues
                    ]
                }
                for result in report.validation_results
            ]
        }
        
        return json.dumps(data, indent=2)
    
    def _generate_html_report(
        self, report: ComplianceReport, document: Document, related_documents: List[Document]
    ) -> str:
        """Generate an HTML report.
        
        Args:
            report: Compliance report
            document: Source document
            related_documents: Related documents
            
        Returns:
            HTML report content
        """
        # Create HTML template
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Compliance Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #2c3e50; }
                h2 { color: #34495e; margin-top: 30px; }
                h3 { color: #7f8c8d; }
                .status-pass { color: #27ae60; }
                .status-fail { color: #c0392b; }
                .status-warning { color: #f39c12; }
                .status-error { color: #e74c3c; }
                .details { margin-left: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f5f5f5; }
            </style>
        </head>
        <body>
            <h1>Compliance Report for {filename}</h1>
            <p>Generated at: {timestamp}</p>
            
            <h2>Document Information</h2>
            <table>
                <tr><th>Field</th><th>Value</th></tr>
                <tr><td>Document ID</td><td>{doc_id}</td></tr>
                <tr><td>Document Type</td><td>{doc_type}</td></tr>
                <tr><td>Document Number</td><td>{doc_number}</td></tr>
                <tr><td>Vendor</td><td>{vendor}</td></tr>
                <tr><td>Total Amount</td><td>{amount} {currency}</td></tr>
            </table>
            
            <h2>Validation Summary</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                {summary_rows}
            </table>
            
            <h2>Validation Results</h2>
            {validation_results}
        </body>
        </html>
        """
        
        # Generate summary rows
        summary_rows = "\n".join(
            f"<tr><td>{key}</td><td>{value}</td></tr>"
            for key, value in report.summary.items()
        )
        
        # Generate validation results
        validation_results = []
        for result in report.validation_results:
            result_html = f"""
            <h3>Rule {result.document_id}</h3>
            <p>Status: <span class="status-{result.status.lower()}">{result.status}</span></p>
            <p>Execution Time: {result.execution_time:.2f}s</p>
            """
            
            if result.issues:
                result_html += "<h4>Issues:</h4><ul>"
                for issue in result.issues:
                    result_html += f"""
                    <li class="status-{issue.severity.lower()}">
                        {issue.message}
                        <div class="details">
                            {self._format_issue_details(issue.details)}
                        </div>
                    </li>
                    """
                result_html += "</ul>"
            
            validation_results.append(result_html)
        
        # Format template
        content = template.format(
            filename=document.filename,
            timestamp=report.created_at.isoformat(),
            doc_id=document.id,
            doc_type=document.document_type,
            doc_number=document.document_number or "N/A",
            vendor=document.vendor_name or "N/A",
            amount=document.total_amount or "N/A",
            currency=document.currency,
            summary_rows=summary_rows,
            validation_results="\n".join(validation_results)
        )
        
        return content
    
    def _format_issue_details(self, details: Dict) -> str:
        """Format issue details as HTML.
        
        Args:
            details: Issue details
            
        Returns:
            Formatted HTML
        """
        if not details:
            return ""
        
        html = "<ul>"
        for key, value in details.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        
        return html 