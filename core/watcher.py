import os
import time
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.config import WATCHED_DIR
from core.extractor import extract_text
from core import metadata

class DocumentHandler(FileSystemEventHandler):
    def __init__(self, vector_store):
        super().__init__()
        self.vector_store = vector_store

    def _process_event(self, event):
        if event.is_directory:
            return
        
        filepath = event.src_path if hasattr(event, 'src_path') else event.dest_path
        filename = os.path.basename(filepath)
        
        # Only process txt and pdf
        if not filename.lower().endswith(('.pdf', '.txt')):
            return

        # Check limits for Free Tier
        from core.license import is_pro_active
        docs = metadata.get_all_documents()
        if len(docs) >= 25 and not is_pro_active():
             print(f"[WATCHER] Limit reached (25 docs). Skipping {filename}. Upgrade to Pro!")
             return
            
        print(f"[WATCHER] Resource activity detected: {filename}")
        time.sleep(1.5) # slightly longer wait for file system lock release
        
        try:
            # Check if file still exists and is not empty
            if not os.path.exists(filepath):
                 return
            
            # Extract text
            text = extract_text(filepath)
            if not text.strip():
                print(f"[WATCHER] Could not extract text from {filename} (empty?)")
                return
                
            # Document ID
            import uuid
            doc_id = uuid.uuid4().hex
            
            # Embed
            self.vector_store.add_document(
                doc_id=doc_id,
                text=text,
                metadata={"filename": filename},
            )
            
            # Summarize
            doc_summary = "Summary unavailable."
            try:
                from core.summarizer import summarizer
                doc_summary = summarizer.summarize(text)
            except Exception as e:
                pass
                
            # Save metadata
            metadata.add_document(doc_id, filename, filepath, summary=doc_summary)
            print(f"[WATCHER] Successfully indexed: {filename}")
            
        except Exception as e:
            print(f"[WATCHER] Error indexing {filename}: {e}")

    def on_created(self, event):
        self._process_event(event)

    def on_moved(self, event):
        self._process_event(event)

    def on_modified(self, event):
        # We handle modified specifically to avoid double-processing, 
        # but sometimes 'created' is missed on some systems.
        pass

    def on_deleted(self, event):
        if event.is_directory:
            return
            
        filepath = event.src_path
        print(f"[WATCHER] File deleted: {filepath}")
        
        # Find which doc_id point to this filepath
        docs = metadata.get_all_documents()
        for doc in docs:
            if doc.get("file_path") == filepath:
                doc_id = doc.get("id")
                if doc_id:
                    self.vector_store.delete_document(doc_id)
                    metadata.delete_document(doc_id)
                    print(f"[WATCHER] Automatically removed from index: {doc.get('filename')}")
                break

_observer = None
_event_handler = None

def update_watched_dir(new_path):
    """Dynamic update to start looking at a new directory on the fly."""
    global _observer, _event_handler
    if _observer and _event_handler:
        if not os.path.exists(new_path):
            os.makedirs(new_path, exist_ok=True)
        print(f"[WATCHER] Switching monitored folder to: {new_path}")
        _observer.unschedule_all()
        _observer.schedule(_event_handler, path=new_path, recursive=True)

def start_watcher(vector_store):
    """Start watching the configured directory in a background thread."""
    global _observer, _event_handler
    if not os.path.exists(WATCHED_DIR):
        try:
            os.makedirs(WATCHED_DIR, exist_ok=True)
        except Exception:
            pass

    def run():
        global _observer, _event_handler
        print(f"[WATCHER] Monitoring folder: {WATCHED_DIR}")
        _event_handler = DocumentHandler(vector_store)
        _observer = Observer()
        _observer.schedule(_event_handler, path=WATCHED_DIR, recursive=True)
        _observer.start()
        
        try:
            while True:
                time.sleep(2) # reduced loop poll slightly
        except KeyboardInterrupt:
            _observer.stop()
        _observer.join()
        
    t = Thread(target=run, daemon=True)
    t.start()
    return t
