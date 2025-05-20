import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
import plotly.graph_objects as go
from jinja2 import Template

from src.models.document import Document
from src.models.validation import ComplianceReport, ValidationIssue, ValidationResult

logger = logging.getLogger(__name__)

class EnhancedReportGenerator:
    def __init__(self, output_dir: Union[str, Path]):
        """Initialize the enhanced report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load HTML template
        self.html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Enhanced Compliance Report</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; }
                .card { margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .status-pass { color: #27ae60; }
                .status-fail { color: #c0392b; }
                .status-warning { color: #f39c12; }
                .status-error { color: #e74c3c; }
                .chart-container { margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="mb-4">Enhanced Compliance Report</h1>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h2>Document Information</h2>
                                {{ document_info | safe }}
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h2>Validation Summary</h2>
                                {{ validation_summary | safe }}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h2>Rule Compliance Distribution</h2>
                                <div id="ruleDistributionChart"></div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h2>Issue Severity Distribution</h2>
                                <div id="severityDistributionChart"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-body">
                                <h2>Detailed Validation Results</h2>
                                {{ validation_results | safe }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                {{ rule_distribution_script | safe }}
                {{ severity_distribution_script | safe }}
            </script>
        </body>
        </html>
        """)
    
    def generate_report(
        self,
        report: ComplianceReport,
        document: Document,
        related_documents: List[Document],
        format: str = "html"
    ) -> Path:
        """Generate an enhanced compliance report.
        
        Args:
            report: Compliance report
            document: Source document
            related_documents: Related documents
            format: Report format (html, json, markdown)
            
        Returns:
            Path to generated report
        """
        if format == "html":
            content = self._generate_enhanced_html_report(report, document, related_documents)
            extension = "html"
        elif format == "json":
            content = self._generate_json_report(report, document, related_documents)
            extension = "json"
        elif format == "markdown":
            content = self._generate_markdown_report(report, document, related_documents)
            extension = "md"
        else:
            raise ValueError(f"Unsupported report format: {format}")
        
        # Create report file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_compliance_report_{document.id}_{timestamp}.{extension}"
        report_path = self.output_dir / filename
        
        # Save report
        report_path.write_text(content)
        logger.info(f"Generated enhanced report: {report_path}")
        
        return report_path
    
    def _generate_enhanced_html_report(
        self,
        report: ComplianceReport,
        document: Document,
        related_documents: List[Document]
    ) -> str:
        """Generate an enhanced HTML report with interactive visualizations."""
        # Generate document information table
        document_info = self._generate_document_info_table(document)
        
        # Generate validation summary
        validation_summary = self._generate_validation_summary(report)
        
        # Generate validation results
        validation_results = self._generate_validation_results(report)
        
        # Generate charts
        rule_distribution_script = self._generate_rule_distribution_chart(report)
        severity_distribution_script = self._generate_severity_distribution_chart(report)
        
        # Render template
        return self.html_template.render(
            document_info=document_info,
            validation_summary=validation_summary,
            validation_results=validation_results,
            rule_distribution_script=rule_distribution_script,
            severity_distribution_script=severity_distribution_script
        )
    
    def _generate_document_info_table(self, document: Document) -> str:
        """Generate document information table."""
        info = [
            ("Document ID", document.id),
            ("Filename", document.filename),
            ("Type", document.document_type),
            ("Number", document.document_number or "N/A"),
            ("Vendor", document.vendor_name or "N/A"),
            ("Amount", f"{document.total_amount or 'N/A'} {document.currency}"),
            ("Date", document.date.isoformat() if document.date else "N/A")
        ]
        
        rows = "\n".join(
            f"<tr><th>{key}</th><td>{value}</td></tr>"
            for key, value in info
        )
        
        return f"""
        <table class="table table-striped">
            <tbody>
                {rows}
            </tbody>
        </table>
        """
    
    def _generate_validation_summary(self, report: ComplianceReport) -> str:
        """Generate validation summary."""
        summary_items = []
        for key, value in report.summary.items():
            status_class = ""
            if "pass" in key.lower():
                status_class = "status-pass"
            elif "fail" in key.lower():
                status_class = "status-fail"
            elif "warning" in key.lower():
                status_class = "status-warning"
            
            summary_items.append(
                f'<div class="d-flex justify-content-between">'
                f'<span>{key}</span>'
                f'<span class="{status_class}">{value}</span>'
                f'</div>'
            )
        
        return "\n".join(summary_items)
    
    def _generate_validation_results(self, report: ComplianceReport) -> str:
        """Generate detailed validation results."""
        results = []
        for result in report.validation_results:
            status_class = f"status-{result.status.lower()}"
            
            issues_html = ""
            if result.issues:
                issues_html = "<ul class='list-unstyled'>"
                for issue in result.issues:
                    severity_class = f"status-{issue.severity.lower()}"
                    issues_html += f"""
                    <li class="mb-2">
                        <span class="{severity_class}">[{issue.severity}]</span>
                        {issue.message}
                        {self._format_issue_details(issue.details)}
                    </li>
                    """
                issues_html += "</ul>"
            
            results.append(f"""
            <div class="card mb-3">
                <div class="card-body">
                    <h3 class="card-title">
                        Rule {result.document_id}
                        <span class="{status_class} float-end">{result.status}</span>
                    </h3>
                    <p class="card-text">
                        Execution Time: {result.execution_time:.2f}s
                    </p>
                    {issues_html}
                </div>
            </div>
            """)
        
        return "\n".join(results)
    
    def _generate_rule_distribution_chart(self, report: ComplianceReport) -> str:
        """Generate rule distribution chart."""
        # Count rule statuses
        status_counts = {}
        for result in report.validation_results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            hole=.3
        )])
        
        fig.update_layout(
            title="Rule Compliance Distribution",
            showlegend=True
        )
        
        return f"Plotly.newPlot('ruleDistributionChart', {fig.to_json()})"
    
    def _generate_severity_distribution_chart(self, report: ComplianceReport) -> str:
        """Generate severity distribution chart."""
        # Count issue severities
        severity_counts = {}
        for result in report.validation_results:
            for issue in result.issues:
                severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        # Create bar chart
        fig = go.Figure(data=[go.Bar(
            x=list(severity_counts.keys()),
            y=list(severity_counts.values())
        )])
        
        fig.update_layout(
            title="Issue Severity Distribution",
            xaxis_title="Severity",
            yaxis_title="Count"
        )
        
        return f"Plotly.newPlot('severityDistributionChart', {fig.to_json()})"
    
    def _format_issue_details(self, details: Dict) -> str:
        """Format issue details."""
        if not details:
            return ""
        
        details_html = "<div class='details'>"
        for key, value in details.items():
            details_html += f"<div><strong>{key}:</strong> {value}</div>"
        details_html += "</div>"
        
        return details_html 