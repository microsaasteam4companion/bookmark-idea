import threading
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class DocumentSummarizer:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self._load_lock = threading.Lock()
        
        # Start loading model in background to not block app startup
        threading.Thread(target=self._load_model, daemon=True).start()

    def _load_model(self):
        with self._load_lock:
            if self.model is None:
                print("[summarizer] Loading local summarization AI model in background...")
                try:
                    # Falconsai/text_summarization is a tiny (240MB) model optimized for very fast, 
                    # offline summarization and requires minimal RAM.
                    model_name = "Falconsai/text_summarization"
                    self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                    print("[summarizer] Summarization model ready.")
                except Exception as e:
                    print(f"[summarizer] Failed to load model: {e}")
                
    def _wait_for_model(self):
        import time
        while self.model is None or self.tokenizer is None:
            time.sleep(0.5)

    def summarize(self, text: str, max_length: int = 60, min_length: int = 20) -> str:
        """Generate a short 1-3 sentence summary of the top of the document."""
        if not text or len(text.strip()) < 100:
            return "Document too short to summarize."
            
        self._wait_for_model()
        
        # The model context window limits how much we can feed it. 
        # For a general document summary, the first ~2500 chars (approx 500 words)
        # usually contains the title, abstract, and introduction, which is perfect.
        snippet_to_summarize = text[:2500]
        
        try:
            inputs = self.tokenizer(snippet_to_summarize, return_tensors="pt", max_length=512, truncation=True)
            outputs = self.model.generate(
                inputs["input_ids"], 
                max_length=max_length, 
                min_length=min_length, 
                do_sample=False
            )
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            print(f"[summarizer] Error generating summary: {e}")
            return "Summary unavailable."

# Singleton instance
summarizer = DocumentSummarizer()
