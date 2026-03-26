"""
Simple JSON-based metadata storage for uploaded documents.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime

from core.config import METADATA_FILE

_lock = threading.Lock()


def _read_store() -> list:
    """Read the full document list from disk."""
    with _lock:
        if not os.path.exists(METADATA_FILE):
            return []
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []


def _write_store(data: list) -> None:
    """Write the full document list to disk."""
    # Note: _write_store is internal and usually called within a lock already,
    # but we can keep it simple as it is only called by add_document/delete_document.
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_document(doc_id: str, filename: str, file_path: str, summary: str = "") -> dict:
    """Append a new document record and return it."""
    record = {
        "id": doc_id,
        "filename": filename,
        "file_path": file_path,
        "summary": summary,
        "uploaded_at": datetime.now().isoformat(),
    }
    with _lock:
        # We call internal read/write here. 
        # Since _read_store has been updated to use _lock, we should avoid nested locks!
        # Re-implementing a simple non-locked internal reader/writer.
        
        if not os.path.exists(METADATA_FILE):
            store = []
        else:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                try: store = json.load(f)
                except: store = []
        
        from core.license import is_pro_active
        if len(store) >= 25 and not is_pro_active():
             raise ValueError("Free Tier limit reached. Upgrade to Pro for infinite docs!")
        
        store.append(record)
        
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, ensure_ascii=False)
            
    return record


def get_document(doc_id: str) -> dict | None:
    """Return a single record by ID, or None."""
    store = _read_store()
    for doc in store:
        if doc["id"] == doc_id:
            return doc
    return None


def get_all_documents() -> list:
    """Return every document record."""
    return _read_store()


def delete_document(doc_id: str) -> bool:
    """Remove a record by ID.  Returns True if found & removed."""
    with _lock:
        if not os.path.exists(METADATA_FILE):
            store = []
        else:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                try: store = json.load(f)
                except: store = []

        new_store = [d for d in store if d["id"] != doc_id]
        if len(new_store) == len(store):
            return False
        _write_store(new_store)
    return True
