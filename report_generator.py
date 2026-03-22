import json
import csv
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
import logging
from pathlib import Path
import tempfile
from dataclasses import dataclass
from enum import Enum

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Supported report formats."""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    TEXT = "text"
    PDF = "pdf"


@dataclass
class ReportMetadata:
    """Metadata for generated reports."""
    title: str
    description: str
    generated_at: datetime
    format: ReportFormat
    data_sources: List[str]
    filters_applied: Dict[str, Any]
    total_records: int


class ReportGenerator:
    """A comprehensive report generator for analyzed data."""
    
    def __init__(self, output_dir: str = "reports", template_dir: Optional[str] = None):
        """
        Initialize the report generator.
        
        Args:
            output_dir: Directory to save generated reports
            template_dir: Directory containing report templates
        """
        self.output_dir = Path(output_dir)
        self.template_dir = Path(template_dir) if template_dir else None
        self.output_dir.mkdir(exist_ok=True)
        
        # Default report configuration
        self.default_config = {
            "include_metadata": True,
            "include_summary": True,
            "include_charts": True,
            "page_size": 100,
            "date_format": "%Y-%m-%d %H:%M:%S",
            "number_format": "{:.2f}"
        }
    
    def generate_report(
        self,
        data: Union[Dict, List, pd.DataFrame],
        title: str,
        format: ReportFormat = ReportFormat.JSON,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a formatted report from analyzed data.
        
        Args:
            data: The data to include in the report
            title: Report title
            format: Output format for the report
            filename: Custom filename (optional)
            metadata: Additional metadata to include
            config: Report configuration options
            
        Returns:
            Dict containing report information and file path
        """
        try:
            # Merge configuration
            report_config = {**self.default_config, **(config or {})}
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{title.lower().replace(' ', '_')}_{timestamp}.{format.value}"
            
            # Create report metadata
            report_metadata = ReportMetadata(
                title=title,
                description=metadata.get("description", "") if metadata else "",
                generated_at=datetime.now(timezone.utc),
                format=format,
                data_sources=metadata.get("data_sources", []) if metadata else [],
                filters_applied=metadata.get("filters", {}) if metadata else {},
                total_records=self._count_records(data)
            )
            
            # Generate report based on format
            file_path = self.output_dir / filename
            
            if format == ReportFormat.JSON:
                self._generate_json_report(data, report_metadata, file_path, report_config)
            elif format == ReportFormat.CSV:
                self._generate_csv_report(data, report_metadata, file_path, report_config)
            elif format == ReportFormat.HTML:
                self._generate_html_report(data, report_metadata, file_path, report_config)
            elif format == ReportFormat.TEXT:
                self._generate_text_report(data, report_metadata, file_path, report_config)
            elif format == ReportFormat.PDF:
                self._generate_pdf_report(data, report_metadata, file_path, report_config)
            else:
                raise ValueError(f"Unsupported report format: {format}")
            
            logger.info(f"Report generated successfully: {file_path}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "format": format.value,
                "title": title,
                "metadata": {
                    "generated_at": report_metadata.generated_at.isoformat(),
                    "total_records": report_metadata.total_records,
                    "file_size": file_path.stat().st_size if file_path.exists() else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "title": title,
                "format": format.value
            }
    
    def _count_records(self, data: Union[Dict, List, pd.DataFrame]) -> int:
        """Count the number of records in the data."""
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            return len(data)
        elif isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            # Try to find the main data collection
            for key, value in data.items():
                if isinstance(value, (list, dict)) and key in ['data', 'results', 'records']:
                    return len(value) if isinstance(value, list) else 1
            return 1
        return 0
    
    def _generate_json_report(
        self, 
        data: Any, 
        metadata: ReportMetadata, 
        file_path: Path, 
        config: Dict[str, Any]
    ):
        """Generate a JSON format report."""
        report_data = {
            "metadata": {
                "title": metadata.title,
                "description": metadata.description,
                "generated_at": metadata.generated_at.isoformat(),
                "format": metadata.format.value,
                "data_sources": metadata.data_sources,
                "filters_applied": metadata.filters_applied,
                "total_records": metadata.total_records
            } if config["include_metadata"] else {},
            "summary": self._generate_summary(data) if config["include_summary"] else {},
            "data": self._serialize_data(data)
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
    
    def _generate_csv_report(
        self, 
        data: Any, 
        metadata: ReportMetadata, 
        file_path: Path, 
        config: Dict[str, Any]
    ):
        """Generate a CSV format report."""
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            # Add metadata as header comments if requested
            if config["include_metadata"]:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    f.write(f"# Report: {metadata.title}\n")
                    f.write(f"# Generated: {metadata.generated_at.isoformat()}\n")
                    f.write(f"# Total Records: {metadata.total_records}\n")
                    f.write("#\n")
                
                # Append DataFrame
                data.to_csv(file_path, mode='a', index=False)
            else:
                data.to_csv(file_path, index=False)
        else:
            # Convert other data types to CSV
            csv_data = self._convert_to_csv_format(data)
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if config["include_metadata"]:
                    f.write(f"# Report: {metadata.title}\n")
                    f.write(f"# Generated: {metadata.generated_at.isoformat()}\n")
                    f.write(f"# Total Records: {metadata.total_records}\n")
                    f.write("#\n")
                
                if csv_data:
                    writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                    writer.writeheader()
                    writer.writerows(csv_data)
    
    def _generate_html_report(
        self, 
        data: Any, 
        metadata: ReportMetadata, 
        file_path: Path, 
        config: Dict[str, Any]
    ):
        """Generate an HTML format report."""
        html_content = self._build_html_report(data, metadata, config)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_text_report(
        self, 
        data: Any, 
        metadata: ReportMetadata, 
        file_path: Path, 
        config: Dict[str, Any]
    ):
        """Generate a plain text format report."""
        with open(file_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write(f"REPORT: {metadata.title.upper()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Metadata
            if config["include_metadata"]:
                f.write("METADATA:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Generated: {metadata.generated_at.strftime(config['date_format'])}\n")
                f.write(f"Total Records: {metadata.total_records}\n")
                f.write(f"Format: {metadata.format.value.upper()}\n")
                if metadata.description:
                    f.write(f"Description: {metadata.description}\n")
                if metadata.data_sources:
                    f.write(f"Data Sources: {', '.join(metadata.data_sources)}\n")
                f.write("\n")
            
            # Summary
            if config["include_summary"]:
                summary = self._generate_summary(data)
                if summary:
                    f.write("SUMMARY:\n")
                    f.write("-" * 40 + "\n")
                    for key, value in summary.items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n")
            
            # Data
            f.write("DATA:\n")
            f.write("-" * 40 + "\n")
            f.write(self._format_data_as_text(data, config))
    
    def _generate_pdf_report(
        self, 
        data: Any, 
        metadata: ReportMetadata, 
        file_path: Path, 
        config: Dict[str, Any]
    ):
        """Generate a PDF format report."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")
        
        doc = SimpleDocTemplate(str(file_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph(metadata.title, title_style))
        story.append(Spacer(1, 12))
        
        # Metadata
        if config["include_metadata"]:
            story.append(Paragraph("Report Metadata", styles['Heading2']))
            metadata_data = [
                ["Generated", metadata.generated_at.strftime(config['date_format'])],
                ["Total Records", str(metadata.total_records)],
                ["Format", metadata.format.value.upper()]
            ]
            if metadata.description:
                metadata_data.append(["Description", metadata.description])
            
            metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
            metadata_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(metadata_table)
            story.append(Spacer(1, 12))
        
        # Summary
        if config["include_summary"]:
            summary = self._generate_summary(data)
            if summary:
                story.append(Paragraph("Summary", styles['Heading2']))
                summary_text = "\n".join([f"{k}: {v}" for k, v in summary.items()])
                story.append(Paragraph(summary_text, styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Data (truncated for PDF)
        story.append(Paragraph("Data Sample", styles['Heading2']))
        pdf_data = self._prepare_data_for_pdf(data, max_rows=50)
        if pdf_data:
            data_table = Table(pdf_data)
            data_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 6)
            ]))
            story.append(data_table)
        
        doc.build(story)
    
    def _serialize_data(self, data: Any) -> Any:
        """Serialize data for JSON output."""
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            return data.to_dict('records')
        elif isinstance(data, (dict, list)):
            return data
        else:
            return str(data)
    
    def _generate_summary(self, data: Any) -> Dict[str, Any]:
        """Generate a summary of the data."""
        summary = {}
        
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            summary["total_rows"] = len(data)
            summary["total_columns"] = len(data.columns)
            summary["columns"] = list(data.columns)
            
            # Numeric summary
            numeric_cols = data.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                summary["numeric_summary"] = data[numeric_cols].describe().to_dict()
        
        elif isinstance(data, list):
            summary["total_items"] = len(data)
            if data and isinstance(data[0], dict):
                summary["keys"] = list(data[0].keys())
        
        elif isinstance(data, dict):
            summary["total_keys"] = len(data)
            summary["keys"] = list(data.keys())
        
        return summary
    
    def _convert_to_csv_format(self, data: Any) -> List[Dict[str, Any]]:
        """Convert data to CSV-compatible format."""
        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                return data
            else:
                return [{"value": item} for item in data]
        elif isinstance(data, dict):
            # Flatten dictionary
            return [{"key": k, "value": v} for k, v in data.items()]
        else:
            return [{"data": str(data)}]
    
    def _build_html_report(
        self, 
        data: Any, 
        metadata: ReportMetadata, 
        config: Dict[str, Any]
    ) -> str:
        """Build HTML report content."""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{metadata.title}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            ".metadata { background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }",
            ".summary { background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{metadata.title}</h1>"
        ]
        
        # Metadata section
        if config["include_metadata"]:
            html_parts.extend([
                '<div class="metadata">',
                "<h2>Metadata</h2>",
                f"<p><strong>Generated:</strong> {metadata.generated_at.strftime(config['date_format'])}</p>",
                f"<p><strong>Total Records:</strong> {metadata.total_records}</p>",
                f"<p><strong>Format:</strong> {metadata.format.value.upper()}</p>"
            ])
            
            if metadata.description:
                html_parts.append(f"<p><strong>Description:</strong> {metadata.description}</p>")
            
            html_parts.append("</div>")
        
        # Summary section
        if config["include_summary"]:
            summary = self._generate_summary(data)
            if summary:
                html_parts.extend([
                    '<div class="summary">',
                    "<h2>Summary</h2>"
                ])
                
                for key, value in summary.items():
                    html_parts.append(f"<p><strong>{key}:</strong> {value}</p>")
                
                html_parts.append("</div>")
        
        # Data section
        html_parts.append("<h2>Data</h2>")
        html_parts.append(self._format_data_as_html_table(data))
        
        html_parts.extend([
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_parts)
    
    def _format_data_as_html_table(self, data: Any) -> str:
        """Format data as HTML table."""
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            return data.to_html(classes='data-table', escape=False)
        
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            # List of dictionaries
            headers = list(data[0].keys())
            html_parts = ["<table>", "<tr>"]
            
            for header in headers:
                html_parts.append(f"<th>{header}</th>")
            html_parts.append("</tr>")
            
            for row in data:
                html_parts.append("<tr>")
                for header in headers:
                    value = row.get(header, "")
                    html_parts.append(f"<td>{value}</td>")
                html_parts.append("</tr>")
            
            html_parts.append("</table>")
            return "".join(html_parts)
        
        else:
            return f"<pre>{str(data)}</pre>"
    
    def _format_data_as_text(self, data: Any, config: Dict[str, Any]) -> str:
        """Format data as plain text."""
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            return data.to_string()
        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                # Format as table-like structure
                if not data:
                    return "No data available"
                
                headers = list(data[0].keys())
                lines = [" | ".join(headers)]
                lines.append("-" * len(lines[0]))
                
                for row in data:
                    values = [str(row.get(h, "")) for h in headers]
                    lines.append(" | ".join(values))
                
                return "\n".join(lines)
            else:
                return "\n".join([str(item) for item in data])
        else:
            return str(data)
    
    def _prepare_data_for_pdf(self, data: Any, max_rows: int = 50) -> Optional[List[List[str]]]:
        """Prepare data for PDF table format."""
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            # Convert DataFrame to list of lists
            result = [list(data.columns)]
            for _, row in data.head(max_rows).iterrows():
                result.append([str(val) for val in row.values])
            return result
        
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            headers = list(data[0].keys())
            result = [headers]
            
            for row in data[:max_rows]:
                result.append([str(row.get(h, "")) for h in headers])
            
            return result
        
        return None
    
    def create_dashboard_report(
        self,
        datasets: Dict[str, Any],
        title: str = "Dashboard Report",
        format: ReportFormat = ReportFormat.HTML,
        include_charts: bool = True
    ) -> Dict[str, Any]:
        """
        Create a comprehensive dashboard-style report from multiple datasets.
        
        Args:
            datasets: Dictionary of dataset name to data mappings
            title: Dashboard title
            format: Output format
            include_charts: Whether to include charts (requires matplotlib)
            
        Returns:
            Report generation result
        """
        try:
            # Aggregate all datasets
            combined_data = {
                "datasets": datasets,
                "summary": {
                    name: self._generate_summary(data) 
                    for name, data in datasets.items()
                },
                "total_datasets": len(datasets),
                "combined_records": sum(self._count_records(data) for data in datasets.values())
            }
            
            # Generate charts if requested and matplotlib is available
            if include_charts and MATPLOTLIB_AVAILABLE:
                chart_paths = self._generate_charts(datasets)
                combined_data["charts"] = chart_paths
            
            metadata = {
                "description": f"Dashboard report combining {len(datasets)} datasets",
                "data_sources": list(datasets.keys())
            }
            
            return self.generate_report(
                data=combined_data,
                title=title,
                format=format,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error creating dashboard report: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _generate_charts(self, datasets: Dict[str, Any]) -> List[str]:
        """Generate charts for dashboard datasets."""
        chart_paths = []
        
        for name, data in datasets.items():
            try:
                if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                    # Generate simple plots for numeric columns
                    numeric_cols = data.select_dtypes(include=['number']).columns
                    
                    if len(numeric_cols) > 0:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        if len(numeric_cols) == 1:
                            data[numeric_cols[0]].hist(ax=ax, bins=20)
                            ax.set_title(f'Distribution of {numeric_cols[0]} ({name})')
                        else:
                            # Plot first few numeric columns
                            for col in numeric_cols[:3]:
                                ax.plot(data.index, data[col], label=col, alpha=0.7)
                            ax.legend()
                            ax.set_title(f'Trends in {name}')
                        
                        chart_path = self.output_dir / f"chart_{name.lower().replace(' ', '_')}.png"
                        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
                        plt.close()
                        
                        chart_paths.append(str(chart_path))
                        
            except Exception as e:
                logger.warning(f"Could not generate chart for {name}: {str(e)}")
                continue
        
        return chart_paths
    
    def cleanup_old_reports(self, days_old: int = 30) -> Dict[str, Any]:
        """
        Clean up old report files.
        
        Args:
            days_old: Remove reports older than this many days
            
        Returns:
            Cleanup summary
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
            removed_files = []
            total_size_freed = 0
            
            for file_path in self.output_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    removed_files.append(str(file_path))
                    total_size_freed += size
            
            return {
                "success": True,
                "removed_files": len(removed_files),
                "files_list": removed_files,
                "size_freed_bytes": total_size_freed,
                "size_freed_mb": round(total_size_freed / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old reports: {str(e)}")
            return {"success": False, "error": str(e)}


# Convenience functions
def generate_report(
    data: Union[Dict, List, pd.DataFrame],
    title: str,
    format: ReportFormat = ReportFormat.JSON,
    output_dir: str = "reports",
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to generate a report.
    
    Args:
        data: Data to include in the report
        title: Report title
        format: Output format
        output_dir: Output directory
        **kwargs: Additional arguments for ReportGenerator
        
    Returns:
        Report generation result
    """
    generator = ReportGenerator(output_dir=output_dir)
    return generator.generate_report(data=data, title=title, format=format, **kwargs)


def create_summary_report(data: Union[Dict, List, pd.DataFrame]) -> Dict[str, Any]:
    """
    Create a quick summary report of the data.
    
    Args:
        data: Data to summarize
        
    Returns:
        Summary information
    """
    generator = ReportGenerator()
    return generator._generate_summary(data)


if __name__ == "__main__":
    # Example usage
    sample_data = [
        {"name": "John", "age": 30, "city": "New York"},
        {"name": "Jane", "age": 25, "city": "Los Angeles"},
        {"name": "Bob", "age": 35, "city": "Chicago"}
    ]
    
    generator = ReportGenerator()
    
    # Generate different format reports
    for fmt in [ReportFormat.JSON, ReportFormat.CSV, ReportFormat.HTML, ReportFormat.TEXT]:
        result = generator.generate_report(
            data=sample_data,
            title="Sample Data Report",
            format=fmt,
            metadata={
                "description": "A sample report demonstrating the report generator",
                "data_sources": ["sample_dataset"]
            }
        )
        print(f"{fmt.value.upper()} Report: {result}")