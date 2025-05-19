import re
import pytesseract
import pdfplumber
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
import pdf2image
from typing import Dict, Any, List, Optional, Tuple
import logging
from pdf2image.exceptions import PDFInfoNotInstalledError

load_dotenv()
llm = ChatOpenAI(temperature=0, model="gpt-4", openai_api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # Configure Tesseract with more options
        self.psm_modes = [3, 4, 6, 11, 12]  # Added more PSM modes
        self.ocr_settings = {
            'lang': 'eng',
            'config': '--oem 3'  # Use LSTM OCR Engine Mode
        }
        
        # LLM prompts
        self.llm_prompts = {
            'enhance_text': """You are an expert at understanding and correcting OCR text from business documents.
            Given the raw OCR text, your task is to:
            1. Correct any obvious OCR mistakes
            2. Fix formatting issues
            3. Maintain the original structure
            4. Preserve numbers and special characters
            5. Keep the original line breaks where they make sense
            
            Return the enhanced text exactly as it should appear in the document.
            Do not add explanations or notes.""",
            
            'extract_fields': """You are an expert at extracting structured information from business documents.
            Given the text, extract the following fields if present:
            - Invoice Number
            - PO Number
            - Date
            - Vendor Name
            - Total Amount
            - Currency
            - Line Items (as a list of dictionaries with item, quantity, unit price, and total)
            
            Return the information in a structured format.""",
            
            'validate_table': """You are an expert at understanding and validating table structures in business documents.
            Given the raw table text, your task is to:
            1. Identify the table structure
            2. Correct any misaligned columns
            3. Fix any OCR mistakes in the data
            4. Ensure numbers are properly formatted
            5. Maintain the original table layout
            
            Return the corrected table text."""
        }

    def preprocess_image(self, image: np.ndarray) -> List[np.ndarray]:
        """Apply various preprocessing techniques to improve OCR accuracy."""
        processed_images = []
        
        # Original image
        processed_images.append(image)
        
        # Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        processed_images.append(gray)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        processed_images.append(thresh)
        
        # Denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        processed_images.append(denoised)
        
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        processed_images.append(enhanced)
        
        # Inverted
        inverted = cv2.bitwise_not(gray)
        processed_images.append(inverted)
        
        return processed_images

    def enhance_text_with_llm(self, text: str) -> str:
        """Use LLM to enhance and correct OCR text."""
        try:
            messages = [
                SystemMessage(content=self.llm_prompts['enhance_text']),
                HumanMessage(content=f"Here is the raw OCR text:\n\n{text}")
            ]
            response = llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            logger.warning(f"LLM text enhancement failed: {str(e)}")
            return text

    def extract_structured_fields(self, text: str) -> Dict[str, Any]:
        """Use LLM to extract structured fields from text."""
        try:
            messages = [
                SystemMessage(content=self.llm_prompts['extract_fields']),
                HumanMessage(content=f"Here is the document text:\n\n{text}")
            ]
            response = llm.invoke(messages)
            # Parse the response as JSON
            import json
            return json.loads(response.content)
        except Exception as e:
            logger.warning(f"LLM field extraction failed: {str(e)}")
            return {}

    def validate_table_with_llm(self, table_text: str) -> str:
        """Use LLM to validate and correct table structure."""
        try:
            messages = [
                SystemMessage(content=self.llm_prompts['validate_table']),
                HumanMessage(content=f"Here is the raw table text:\n\n{table_text}")
            ]
            response = llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            logger.warning(f"LLM table validation failed: {str(e)}")
            return table_text

    def extract_text_from_image(self, image: np.ndarray) -> Tuple[str, Dict[str, Any]]:
        """Extract text from an image using OCR and enhance with LLM."""
        logger.info("Starting OCR extraction...")
        
        # Get initial OCR text
        texts = []
        processed_images = self.preprocess_image(image)
        
        for img in processed_images:
            for psm in self.psm_modes:
                try:
                    config = f'--oem 3 --psm {psm}'
                    logger.info(f"Trying OCR with PSM mode {psm}")
                    
                    text = pytesseract.image_to_string(
                        img, 
                        lang=self.ocr_settings['lang'],
                        config=config
                    )
                    
                    if text.strip():
                        logger.info(f"Found text with PSM {psm}, length: {len(text)}")
                        texts.append(text)
                except Exception as e:
                    logger.warning(f"OCR attempt failed with PSM {psm}: {str(e)}")
                    continue
        
        if not texts:
            logger.warning("No text extracted from image")
            return "", {}
        
        # Get the best OCR result
        best_text = max(texts, key=len)
        logger.info(f"Best OCR result length: {len(best_text)}")
        
        # Enhance text with LLM
        try:
            enhanced_text = self.enhance_text_with_llm(best_text)
            logger.info("Text enhanced with LLM")
        except Exception as e:
            logger.warning(f"LLM enhancement failed: {str(e)}")
            enhanced_text = best_text
        
        # Extract structured fields
        try:
            structured_fields = self.extract_structured_fields(enhanced_text)
            logger.info(f"Extracted {len(structured_fields)} structured fields")
        except Exception as e:
            logger.warning(f"Field extraction failed: {str(e)}")
            structured_fields = {}
        
        return enhanced_text, structured_fields

    def process_pdf(self, pdf_path: str) -> List[np.ndarray]:
        """Convert PDF to images with better error handling."""
        try:
            logger.info(f"Converting PDF: {pdf_path}")
            images = pdf2image.convert_from_path(
                pdf_path,
                dpi=300,  # Higher DPI for better quality
                thread_count=4  # Use multiple threads
            )
            logger.info(f"Converted PDF to {len(images)} images")
            return images
        except PDFInfoNotInstalledError:
            logger.error("pdf2image requires poppler to be installed")
            raise
        except Exception as e:
            logger.error(f"Error converting PDF: {str(e)}")
            raise

    def extract_tables(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Extract tables from the image."""
        # Convert image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        tables = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 100 and h > 100:  # Filter small contours
                roi = image[y:y+h, x:x+w]
                table_text = self.extract_text_from_image(roi)[0]
                if table_text.strip():
                    tables.append({
                        'text': table_text,
                        'position': {'x': x, 'y': y, 'width': w, 'height': h}
                    })
        
        return tables

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a document and extract text, tables, and structured fields."""
        file_path = Path(file_path)
        logger.info(f"Processing document: {file_path}")
        
        result = {
            'text': '',
            'tables': [],
            'structured_fields': {},
            'metadata': {
                'filename': file_path.name,
                'file_type': file_path.suffix.lower()
            }
        }
        
        try:
            if file_path.suffix.lower() == '.pdf':
                # Try pdfplumber first
                try:
                    with pdfplumber.open(file_path) as pdf:
                        text_all = []
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text and text.strip():
                                text_all.append(text)
                        if text_all:
                            result['text'] = "\n".join(text_all)
                            logger.info("Successfully extracted text using pdfplumber")
                except Exception as e:
                    logger.warning(f"pdfplumber extraction failed: {str(e)}")
                
                # If pdfplumber failed, try OCR
                if not result['text']:
                    logger.info("Falling back to OCR processing")
                    images = self.process_pdf(str(file_path))
                    for i, image in enumerate(images):
                        logger.info(f"Processing page {i+1}")
                        # Convert PIL Image to numpy array
                        img_array = np.array(image)
                        # Convert RGB to BGR (OpenCV format)
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                        
                        # Extract text and structured fields
                        page_text, page_fields = self.extract_text_from_image(img_array)
                        if page_text:
                            result['text'] += f"\n--- Page {i+1} ---\n{page_text}"
                            result['structured_fields'].update(page_fields)
                        
                        # Extract and validate tables
                        tables = self.extract_tables(img_array)
                        for table in tables:
                            validated_table = self.validate_table_with_llm(table['text'])
                            table['text'] = validated_table
                        result['tables'].extend(tables)
            
            else:
                # Process image
                image = cv2.imread(str(file_path))
                if image is None:
                    raise ValueError(f"Could not read image: {file_path}")
                
                # Extract text and structured fields
                result['text'], result['structured_fields'] = self.extract_text_from_image(image)
                
                # Extract and validate tables
                tables = self.extract_tables(image)
                for table in tables:
                    validated_table = self.validate_table_with_llm(table['text'])
                    table['text'] = validated_table
                result['tables'] = tables
            
            # If still no text, try direct OCR
            if not result['text']:
                logger.warning("No text extracted, trying direct OCR")
                if file_path.suffix.lower() == '.pdf':
                    result['text'] = extract_text_from_pdf_with_ocr_fallback(str(file_path))
                else:
                    result['text'] = extract_text_with_ocr(str(file_path))
            
            logger.info(f"Document processing complete. Text length: {len(result['text'])}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            raise

def process_document(file_path: str) -> Dict[str, Any]:
    """Main function to process a document."""
    processor = DocumentProcessor()
    result = processor.process_document(file_path)
    
    # Ensure we have the basic structure
    if not isinstance(result, dict):
        result = {}
    
    # Add required fields if missing
    result.setdefault('filename', Path(file_path).name)
    result.setdefault('doc_type', 'unknown')
    result.setdefault('vendor', 'generic')
    result.setdefault('fields', {})
    result.setdefault('tables_raw', [])
    result.setdefault('tables_structured', [])
    
    # If we have structured fields from LLM, merge them into fields
    if 'structured_fields' in result:
        result['fields'].update(result['structured_fields'])
        del result['structured_fields']
    
    # If we have text but no fields, try to extract fields using regex
    if result['text'] and not result['fields']:
        result['fields'] = extract_fields_regex(result['text'])
    
    # If we have text but no doc_type, try to classify
    if result['text'] and result['doc_type'] == 'unknown':
        result['doc_type'] = classify_document(result['text'], result['filename'])
    
    # If we have text but no vendor, try to detect
    if result['text'] and result['vendor'] == 'generic':
        result['vendor'] = detect_vendor(result['text'], result['filename'])
    
    # Process tables if we have them
    if result['tables_raw']:
        for table in result['tables_raw']:
            if isinstance(table, dict) and 'text' in table:
                structured_table = parse_ocr_table(table['text'])
                if structured_table:
                    result['tables_structured'].extend(structured_table)
    
    return result

# --- OCR Functions
def extract_text_from_pdf_with_ocr_fallback(pdf_path):
    text_all = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text and text.strip():
                text_all.append(text)
            else:
                pil_image = page.to_image(resolution=300).original.convert("L")
                np_img = np.array(pil_image)
                blur = cv2.GaussianBlur(np_img, (5, 5), 0)
                thresh = cv2.adaptiveThreshold(
                    blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )
                coords = np.column_stack(np.where(thresh > 0))
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle
                (h, w) = thresh.shape[:2]
                M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
                deskewed = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                text_all.append(pytesseract.image_to_string(deskewed, config='--psm 6'))
    return "\n".join(text_all)

def extract_text_with_ocr(image_path):
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = thresh.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    deskewed = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return pytesseract.image_to_string(deskewed, config='--psm 6')

# --- Table Extraction
def extract_tables_from_scanned_image(image_path):
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
    vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel)
    table_mask = cv2.add(horizontal_lines, vertical_lines)

    contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    tables = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 50 and h > 50:
            table_roi = img[y:y+h, x:x+w]
            text = pytesseract.image_to_string(table_roi, config='--psm 6')
            tables.append(text)
    return tables

def parse_ocr_table(ocr_text):
    lines = ocr_text.strip().split("\n")
    rows = []

    # Try to identify header line (assume first line)
    header = re.split(r"\s{2,}|\t+", lines[0].strip())
    header = [h.lower().strip().replace(" ", "_") for h in header]

    for line in lines[1:]:
        if not line.strip():
            continue
        columns = re.split(r"\s{2,}|\t+", line.strip())
        if len(columns) != len(header):
            continue  # skip badly formed lines

        row = dict(zip(header, columns))
        
        # Convert known numeric fields
        for key in row:
            if key in ["qty", "quantity"]:
                try: row[key] = int(row[key])
                except: pass
            if key in ["unit_price", "total", "amount"]:
                try: row[key] = float(row[key].replace(",", ""))
                except: pass

        rows.append(row)
    return rows

# --- Classification + Field Extraction
def classify_document(text, filename):
    name = filename.lower()
    text = text.lower()
    if "invoice" in name or re.search(r"invoice\s*number", text):
        return "invoice"
    if "purchase order" in text:
        return "purchase_order"
    if "grn" in name or "goods received" in text:
        return "grn"

    prompt = f"""
    The following is raw OCR or extracted text from a scanned business document.

    Classify the document type as one of the following:
    - invoice
    - purchase_order
    - grn
    - unknown

    Do not explain, just respond with one word from the list above.

    ---
    {text[:3000]}
    ---
    """
    try:
        response = llm([HumanMessage(content=prompt)])
        result = response.content.strip().lower()
        return result if result in ["invoice", "purchase_order", "grn"] else "unknown"
    except Exception:
        return "unknown"

def detect_vendor(text, filename):
    if "abc corp" in text.lower():
        return "abc_corp"
    elif "xyz ltd" in text.lower():
        return "xyz_ltd"
    else:
        return "generic"

def extract_fields_regex(text):
    fields = {}

    po_match = re.search(r"PO\s*No\s*:\s*([A-Z0-9\-]+)", text)
    if po_match:
        fields["po_number"] = po_match.group(1)

    invoice_match = re.search(r"Invoice\s*No\s*:\s*([A-Z0-9\-]+)", text)
    if invoice_match:
        fields["invoice_number"] = invoice_match.group(1)

    date_match = re.search(r"Invoice\s*Date\s*:\s*([0-9]{2}-[A-Za-z]{3}-[0-9]{4})", text)
    if date_match:
        fields["invoice_date"] = date_match.group(1)

    currency_match = re.search(r"Currency\s*:\s*([A-Z]{3})", text)
    if currency_match:
        fields["currency"] = currency_match.group(1)
        
    quantity_match = re.search(r"Quantity\s*:\s*([0-9]+)", text, re.IGNORECASE)
    if quantity_match:
        fields["quantity"] = quantity_match.group(1)

    price_match = re.search(r"Unit\s*Price\s*:\s*([0-9]+\.[0-9]{2})", text, re.IGNORECASE)
    if price_match:
        fields["unit_price"] = price_match.group(1)

    total_match = re.search(r"Total Amount \\(Including\\s+VAT\\)\s*:\s*([0-9]+\.[0-9]{2})", text)
    if not total_match:
        total_match = re.search(r"Total Amount \\(Including VAT\\)\s*:\s*([0-9]+\.[0-9]{2})", text)
    if not total_match:
        total_match = re.search(r"Total Amount.*VAT.*:\s*([0-9]+\.[0-9]{2})", text)
    if total_match:
        fields["total_amount"] = total_match.group(1)

    return fields
