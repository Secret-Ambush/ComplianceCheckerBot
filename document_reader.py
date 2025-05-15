
import re
import pytesseract
import pdfplumber
import cv2
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def extract_text_with_ocr(image_path):
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)[1]
    return pytesseract.image_to_string(thresh)

def classify_document(text, filename):
    name = filename.lower()
    text = text.lower()
    if "invoice" in name or re.search(r"invoice\s*number", text):
        return "invoice"
    if "po" in name or "purchase order" in text:
        return "purchase_order"
    if "grn" in name or "goods received" in text:
        return "grn"
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

    total_match = re.search(r"Total Amount \\(Including\\s+VAT\\)\s*:\s*([0-9]+\.[0-9]{2})", text)
    if not total_match:
        total_match = re.search(r"Total Amount \\(Including VAT\\)\s*:\s*([0-9]+\.[0-9]{2})", text)
    if not total_match:
        total_match = re.search(r"Total Amount.*VAT.*:\s*([0-9]+\.[0-9]{2})", text)
    if total_match:
        fields["total_amount"] = total_match.group(1)

    return fields


def process_document(file_path):
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext in [".png", ".jpg", ".jpeg"]:
        text = extract_text_with_ocr(file_path)
    elif ext == ".txt":
        text = Path(file_path).read_text()
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    doc_type = classify_document(text, file_path.name)
    vendor = detect_vendor(text, file_path.name)
    fields = extract_fields_regex(text)

    return {
        "filename": file_path.name,
        "doc_type": doc_type,
        "vendor": vendor,
        "fields": fields
    }

# Example usage:
result = process_document(Path("invoice (1).PDF"))
print(result)
