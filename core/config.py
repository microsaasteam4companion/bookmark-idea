"""
Configuration — single source of truth for all paths and settings.
"""

import os

# ── Paths ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_data_v2")
METADATA_FILE = os.path.join(BASE_DIR, "metadata_v2.json")
WATCHED_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Ai Assistant Input")
WATCHED_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Ai Assistant Input")

# ── AI Model ─────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-mpnet-base-v2" # Gold standard for high-accuracy local semantic search

# ── OCR ──────────────────────────────────────────────────────────
OCR_ENABLED = True                    # Enable OCR fallback for scanned/image-based PDFs
OCR_MIN_TEXT_LENGTH = 50              # If pypdf extracts fewer chars than this, trigger OCR

# ── Limits ───────────────────────────────────────────────────────────
MAX_TEXT_LENGTH = 10_000  # characters sent to the embedding model

# ── Auto-create required directories ─────────────────────────────────
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_PATH, exist_ok=True)
