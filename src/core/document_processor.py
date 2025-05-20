import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import cv2
import layoutparser as lp
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfReader

from src.models.document import Document, DocumentStatus, DocumentType, LineItem

logger = logging.getLogger(__name__)


class DocumentProcessor:
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """Initialize the document processor.
        
        Args:
            tesseract_cmd: Path to tesseract executable if not in PATH
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Initialize layout parser model
        self.layout_model = lp.AutoLayoutModel("lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x")
    
    def process_document(self, file_path: Union[str, Path]) -> Document:
        """Process a document and extract its content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Document object with extracted information
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Create base document
        doc = Document(
            filename=file_path.name,
            document_type=self._detect_document_type(file_path),
            status=DocumentStatus.PROCESSING
        )
        
        try:
            # Extract text and layout
            if file_path.suffix.lower() == '.pdf':
                text, layout = self._process_pdf(file_path)
            else:
                text, layout = self._process_image(file_path)
            
            doc.raw_text = text
            
            # Extract structured data
            extracted_data = self._extract_structured_data(text, layout)
            doc.extracted_data = extracted_data
            
            # Update document with extracted information
            self._update_document_fields(doc, extracted_data)
            
            doc.status = DocumentStatus.PROCESSED
            doc.processed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            doc.status = DocumentStatus.FAILED
            raise
        
        return doc
    
    def _detect_document_type(self, file_path: Path) -> DocumentType:
        """Detect the type of document based on filename and content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Detected document type
        """
        filename = file_path.name.lower()
        
        # Simple rule-based detection
        if 'invoice' in filename:
            return DocumentType.INVOICE
        elif 'po' in filename or 'purchase_order' in filename:
            return DocumentType.PURCHASE_ORDER
        elif 'grn' in filename or 'goods_receipt' in filename:
            return DocumentType.GOODS_RECEIPT
        elif 'vendor' in filename and 'policy' in filename:
            return DocumentType.VENDOR_POLICY
        
        return DocumentType.UNKNOWN
    
    def _process_pdf(self, file_path: Path) -> tuple[str, List[Dict]]:
        """Process a PDF document.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple of (extracted text, layout information)
        """
        # Convert PDF to images
        images = convert_from_path(file_path)
        
        all_text = []
        all_layouts = []
        
        for i, image in enumerate(images):
            # Convert PIL image to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Extract text
            text = pytesseract.image_to_string(cv_image)
            all_text.append(text)
            
            # Extract layout
            layout = self.layout_model.detect(cv_image)
            all_layouts.extend(layout.to_dict())
        
        return "\n".join(all_text), all_layouts
    
    def _process_image(self, file_path: Path) -> tuple[str, List[Dict]]:
        """Process an image document.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Tuple of (extracted text, layout information)
        """
        # Read image
        image = cv2.imread(str(file_path))
        if image is None:
            raise ValueError(f"Could not read image: {file_path}")
        
        # Extract text
        text = pytesseract.image_to_string(image)
        
        # Extract layout
        layout = self.layout_model.detect(image)
        
        return text, layout.to_dict()
    
    def _extract_structured_data(self, text: str, layout: List[Dict]) -> Dict:
        """Extract structured data from text and layout.
        
        Args:
            text: Extracted text from document
            layout: Layout information from document
            
        Returns:
            Dictionary of extracted structured data
        """
        # TODO: Implement more sophisticated extraction logic
        # This is a basic implementation that can be enhanced with ML models
        
        data = {
            'document_number': self._extract_document_number(text),
            'vendor_name': self._extract_vendor_name(text),
            'vendor_id': self._extract_vendor_id(text),
            'issue_date': self._extract_date(text, 'issue'),
            'due_date': self._extract_date(text, 'due'),
            'total_amount': self._extract_total_amount(text),
            'line_items': self._extract_line_items(text, layout)
        }
        
        return data
    
    def _update_document_fields(self, doc: Document, data: Dict):
        """Update document fields with extracted data.
        
        Args:
            doc: Document to update
            data: Extracted data
        """
        doc.document_number = data.get('document_number')
        doc.vendor_name = data.get('vendor_name')
        doc.vendor_id = data.get('vendor_id')
        doc.issue_date = data.get('issue_date')
        doc.due_date = data.get('due_date')
        doc.total_amount = data.get('total_amount')
        
        # Convert line items
        if 'line_items' in data:
            doc.line_items = [
                LineItem(**item) for item in data['line_items']
            ]
    
    def _extract_document_number(self, text: str) -> Optional[str]:
        """Extract document number from text."""
        # TODO: Implement document number extraction
        return None
    
    def _extract_vendor_name(self, text: str) -> Optional[str]:
        """Extract vendor name from text."""
        # TODO: Implement vendor name extraction
        return None
    
    def _extract_vendor_id(self, text: str) -> Optional[str]:
        """Extract vendor ID from text."""
        # TODO: Implement vendor ID extraction
        return None
    
    def _extract_date(self, text: str, date_type: str) -> Optional[datetime]:
        """Extract date from text."""
        # TODO: Implement date extraction
        return None
    
    def _extract_total_amount(self, text: str) -> Optional[float]:
        """Extract total amount from text."""
        # TODO: Implement total amount extraction
        return None
    
    def _extract_line_items(self, text: str, layout: List[Dict]) -> List[Dict]:
        """Extract line items from text and layout."""
        # TODO: Implement line item extraction
        return [] 