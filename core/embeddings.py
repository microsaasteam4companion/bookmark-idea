"""
AI embedding model + ChromaDB vector store.
"""

from __future__ import annotations

import chromadb
from sentence_transformers import SentenceTransformer

from core.config import CHROMA_PATH, EMBEDDING_MODEL, MAX_TEXT_LENGTH


class VectorStore:
    """Wraps the sentence-transformer model and a persistent ChromaDB collection."""

    def __init__(self):
        print("[embeddings] Vector store init started...")
        self.model = None
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )
        
        # Load the heavy model in a background thread so UI can start instantly
        import threading
        def _load_model():
            print("[embeddings] Loading AI model in background...")
            self.model = SentenceTransformer(EMBEDDING_MODEL)
            print("[embeddings] AI model ready.")
            
        threading.Thread(target=_load_model, daemon=True).start()

    def _wait_for_model(self):
        import time
        while self.model is None:
            time.sleep(0.5)

    # ── helpers ──────────────────────────────────────────────────────
    def _chunk_text(self, text: str, max_chunk_length: int = 600, overlap: int = 100) -> list[str]:
        """Split text semantically into chunks (paragraphs) ensuring context overlap."""
        import re
        
        # Split by double newline (paragraphs) first
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            if len(current_chunk) + len(p) < max_chunk_length:
                current_chunk += p + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                
                # Carry over overlap context
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                clean_break = max(overlap_text.rfind('. '), overlap_text.rfind('\n'))
                if clean_break != -1:
                    overlap_text = overlap_text[clean_break+1:].strip()
                    
                current_chunk = overlap_text + "\n\n" + p + "\n\n"
                
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks if chunks else [text.strip()[:max_chunk_length]] if text.strip() else []

    def _embed(self, text: str) -> list[float]:
        """Convert text → vector."""
        self._wait_for_model()
        return self.model.encode(text).tolist()

    # ── public API ───────────────────────────────────────────────────

    def add_document(self, doc_id: str, text: str, metadata: dict | None = None):
        """Chunk *text*, embed each chunk, and store the vectors linked to *doc_id*."""
        chunks = self._chunk_text(text)
        if not chunks:
            return
            
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        filename = metadata.get("filename", "Unknown Document") if metadata else "Unknown Document"
        
        for i, chunk in enumerate(chunks):
            # Prepend filename context so the embedding model knows WHAT it is reading
            context_chunk = f"Document: {filename}\n\n{chunk}"
            
            vector = self._embed(context_chunk)
            ids.append(f"{doc_id}_chunk_{i}")
            embeddings.append(vector)
            documents.append(chunk)
            
            # Store the parent doc_id in metadata so we can group results
            meta = metadata.copy() if metadata else {}
            meta["doc_id"] = doc_id
            metadatas.append(meta)
            
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Return the most similar documents.
        Searches all chunks, then groups by doc_id to return unique documents with the best matching snippet.
        """
        vector = self._embed(query)
        # Query more chunks than top_k because multiple chunks might belong to the same document
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=top_k * 5,
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        seen_docs = set()
        
        if results and results["ids"]:
            for i, chunk_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                doc_id = meta.get("doc_id", chunk_id)  # Fallback for old unchunked data
                
                if doc_id in seen_docs:
                    continue
                seen_docs.add(doc_id)
                
                hits.append(
                    {
                        "id": doc_id,
                        "distance": results["distances"][0][i],
                        "text": (results["documents"][0][i] or "")[:500],
                        "metadata": meta,
                    }
                )
                
                if len(hits) >= top_k:
                    break
                    
        return hits

    def delete_document(self, doc_id: str):
        """Remove all chunks belonging to a doc_id."""
        try:
            # First try to delete by metadata (chunked documents)
            results = self.collection.get(where={"doc_id": doc_id})
            if results and results["ids"]:
                self.collection.delete(ids=results["ids"])
            else:
                # Cleanup fallback for any old unchunked insertions
                self.collection.delete(ids=[doc_id])
        except Exception:
            pass
