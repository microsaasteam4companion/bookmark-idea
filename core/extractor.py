"""
Text extraction from PDF and TXT files.
Includes OCR fallback for scanned/image-based PDFs using EasyOCR + PyMuPDF.
"""

import os
import traceback

from core.config import OCR_ENABLED, OCR_MIN_TEXT_LENGTH


def extract_text(file_path: str) -> str:
    """
    Extract text from a supported file.  Returns "" on any failure so the
    rest of the pipeline is never interrupted.
    """
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".pdf":
            return _extract_pdf(file_path)
        elif ext == ".txt":
            return _extract_txt(file_path)
        else:
            print(f"[extractor] Unsupported file type: {ext}")
            return ""
    except Exception:
        traceback.print_exc()
        return ""


def _extract_pdf(path: str) -> str:
    """Read all pages from a PDF using pypdf. Falls back to OCR if text is too short."""
    from pypdf import PdfReader

    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    result = "\n".join(pages)

    # ── OCR Fallback ─────────────────────────────────────────────
    # If pypdf got very little text (scanned/image PDF), try OCR
    if OCR_ENABLED and len(result.strip()) < OCR_MIN_TEXT_LENGTH:
        print(f"[extractor] pypdf returned only {len(result.strip())} chars — attempting OCR fallback...")
        ocr_text = _ocr_pdf(path)
        if ocr_text and len(ocr_text.strip()) > len(result.strip()):
            print(f"[extractor] OCR succeeded: {len(ocr_text.strip())} chars extracted.")
            return ocr_text

    return result


def _ocr_pdf(path: str) -> str:
    """
    OCR fallback: convert PDF pages to images using PyMuPDF (fitz),
    then run EasyOCR on each page image.
    Returns combined text from all pages.
    """
    try:
        import fitz  # PyMuPDF
        import easyocr
        import numpy as np
        from PIL import Image
        import io

        # Initialize EasyOCR reader (English only, no GPU for portability)
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)

        doc = fitz.open(path)
        all_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render page to image at 2x resolution for better OCR accuracy
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")

            # Convert to numpy array for EasyOCR
            img = Image.open(io.BytesIO(img_bytes))
            img_np = np.array(img)

            # Run OCR
            results = reader.readtext(img_np, detail=0, paragraph=True)
            page_text = "\n".join(results)

            if page_text.strip():
                all_text.append(page_text)

            print(f"[extractor] OCR page {page_num + 1}/{len(doc)}: {len(page_text)} chars")

        doc.close()
        return "\n\n".join(all_text)

    except ImportError as e:
        print(f"[extractor] OCR packages not installed ({e}). Skipping OCR fallback.")
        return ""
    except Exception as e:
        print(f"[extractor] OCR failed: {e}")
        traceback.print_exc()
        return ""


def _extract_txt(path: str) -> str:
    """Read a plain-text file."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
