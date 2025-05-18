import re
import pytesseract
import pdfplumber
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(temperature=0, model="gpt-4", openai_api_key=os.getenv("OPENAI_API_KEY"))

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

# --- Main interface function
def process_document(file_path):
    ext = file_path.suffix.lower()
    text = ""
    tables = []

    if ext == ".pdf":
        text = extract_text_from_pdf_with_ocr_fallback(file_path)
        tables = []  # No direct table extraction yet for PDF pages
    elif ext in [".png", ".jpg", ".jpeg"]:
        text = extract_text_with_ocr(file_path)
        try:
            tables = extract_tables_from_scanned_image(file_path)
        except Exception:
            tables = []
    elif ext == ".txt":
        text = Path(file_path).read_text()
        tables = []
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    structured_table = []
    for table_text in tables:
        structured_table.extend(parse_ocr_table(table_text))

    doc_type = classify_document(text, file_path.name)
    vendor = detect_vendor(text, file_path.name)
    fields = extract_fields_regex(text)

    return {
        "filename": file_path.name,
        "doc_type": doc_type,
        "vendor": vendor,
        "fields": fields,
        "tables_raw": tables,
        "tables_structured": structured_table
    }
