"""
STEP 2: PDF Prospectus Extractor
"""
import os
import json
import pypdf
from config import PDF_DIR, DOWNLOAD_DIR

OUTPUT_JSON = os.path.join(DOWNLOAD_DIR, "extracted_pdf.json")

def parse_all_pdfs():
    os.makedirs(PDF_DIR, exist_ok=True)
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    extracted_data = []
    for fname in pdf_files:
        fpath = os.path.join(PDF_DIR, fname)
        try:
            reader = pypdf.PdfReader(fpath)
            pages = []
            for i, p in enumerate(reader.pages, 1):
                text = p.extract_text() or ""
                if text.strip():
                    pages.append({"page_number": i, "text": text.strip()})
            extracted_data.append({
                "filename": fname,
                "filepath": fpath,
                "total_pages": len(reader.pages),
                "extracted_pages": pages
            })
        except Exception:
            pass

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=4, ensure_ascii=False)
    return extracted_data

if __name__ == "__main__":
    parse_all_pdfs()
