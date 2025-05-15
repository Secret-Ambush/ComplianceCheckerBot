# Compliance Checker

🔹 1. Document Reader & Field Extractor
📁 Input Folder (PDF/TXT/Images)
   └── 🔍 Document Reader
           ├── Type Classifier (filename + content)
           ├── Vendor Detector
           ├── Text Extractor (PDF/TXT/OCR)
           ├── Field Extractor (Template | Regex | LLM)
           └── ➡️ Normalised JSON Output

🔹 2. Text Extraction Module
💡 Strategy:
PDF (text) → pdfplumber or PyMuPDF to extract text and coordinates.
Scanned PDF/Image → Preprocess with OpenCV → OCR with Tesseract.

