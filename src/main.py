import argparse
import logging
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from src.core.document_matcher import DocumentMatcher
from src.core.document_processor import DocumentProcessor
from src.core.report_generator import ReportGenerator
from src.core.rule_engine import RuleEngine
from src.core.validation_engine import ValidationEngine
from src.models.document import Document
from src.models.rule import Rule, RuleSet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_environment():
    """Load environment variables."""
    load_dotenv()
    
    required_vars = [
        "OPENAI_API_KEY",
        "TESSERACT_CMD",  # Optional
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


def process_documents(
    document_paths: List[Path],
    rules: List[str],
    output_dir: Path,
    report_format: str = "markdown"
) -> None:
    """Process documents and generate compliance reports.
    
    Args:
        document_paths: List of document paths to process
        rules: List of natural language rules
        output_dir: Directory to save reports
        report_format: Report format (markdown, json, html)
    """
    # Initialize components
    document_processor = DocumentProcessor(
        tesseract_cmd=os.getenv("TESSERACT_CMD")
    )
    rule_engine = RuleEngine(
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    document_matcher = DocumentMatcher()
    validation_engine = ValidationEngine()
    report_generator = ReportGenerator(output_dir)
    
    # Process documents
    documents = []
    for path in document_paths:
        try:
            doc = document_processor.process_document(path)
            documents.append(doc)
            logger.info(f"Processed document: {path}")
        except Exception as e:
            logger.error(f"Error processing document {path}: {str(e)}")
    
    # Interpret rules
    rule_set = RuleSet(
        name="Compliance Rules",
        description="Rules for document compliance validation",
        rules=[]
    )
    
    for rule_text in rules:
        try:
            rule = rule_engine.interpret_rule(rule_text)
            rule_set.rules.append(rule)
            logger.info(f"Interpreted rule: {rule_text}")
        except Exception as e:
            logger.error(f"Error interpreting rule {rule_text}: {str(e)}")
    
    # Process each document
    for document in documents:
        try:
            # Find related documents
            related_docs = []
            for target_doc in documents:
                if target_doc.id != document.id:
                    matches = document_matcher.find_matches(
                        document,
                        [target_doc],
                        {
                            "source_type": document.document_type,
                            "target_type": target_doc.document_type,
                            "min_confidence": 0.7
                        }
                    )
                    if matches:
                        related_docs.append(target_doc)
            
            # Validate document
            report = validation_engine.validate_document(
                document,
                related_docs,
                rule_set.rules
            )
            
            # Generate report
            report_path = report_generator.generate_report(
                report,
                document,
                related_docs,
                format=report_format
            )
            
            logger.info(f"Generated report: {report_path}")
            
        except Exception as e:
            logger.error(f"Error processing document {document.filename}: {str(e)}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Document Compliance Checker")
    parser.add_argument(
        "--documents",
        nargs="+",
        required=True,
        help="Paths to documents to process"
    )
    parser.add_argument(
        "--rules",
        nargs="+",
        required=True,
        help="Natural language rules to validate against"
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory to save reports"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "html"],
        default="markdown",
        help="Report format"
    )
    
    args = parser.parse_args()
    
    try:
        # Load environment variables
        load_environment()
        
        # Process documents
        process_documents(
            [Path(p) for p in args.documents],
            args.rules,
            Path(args.output_dir),
            args.format
        )
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main() 