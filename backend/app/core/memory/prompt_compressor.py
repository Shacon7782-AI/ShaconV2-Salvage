import os
import gc
from typing import List, Optional
from llmlingua import PromptCompressor
import torch

class SovereignCompressor:
    """
    State-of-the-Art prompt compression for ShaconV2.
    Uses LLMLingua-2 to reduce prompt size by up to 80% while preserving semantics.
    """
    def __init__(self, model_name: str = "microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank"):
        self.model_name = model_name
        self.compressor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def _load_compressor(self):
        """Lazy-loads the compressor model to save RAM."""
        if self.compressor is None:
            print(f"[COMPRESSOR] Hot-loading LLMLingua model ({self.model_name}) on {self.device}...")
            self.compressor = PromptCompressor(
                model_name=self.model_name,
                use_llmlingua2=True,
                device_map=self.device
            )

    def compress(self, context: List[str], instruction: str = "", question: str = "", target_token: int = 1200) -> str:
        """
        Compresses a list of context strings into a highly dense prompt.
        """
        self._load_compressor()
        
        try:
            # Join context chunks
            context_text = "\n\n".join(context)
            
            # Simple compression call
            result = self.compressor.compress_prompt(
                context=[context_text],
                instruction=instruction,
                question=question,
                target_token=target_token,
                iterative_compression=False, # Faster for real-time
                force_tokens=["\n", "?", "!", ".", "```"], # Keep structural tokens
                use_sentence_level_filter=True
            )
            
            compressed_prompt = result.get("compressed_prompt", context_text)
            origin_tokens = result.get("origin_tokens", 0)
            compressed_tokens = result.get("compressed_tokens", 0)
            ratio = result.get("ratio", "100%")
            
            print(f"[COMPRESSOR] SUCCESS: {origin_tokens} -> {compressed_tokens} ({ratio} savings)")
            return compressed_prompt
        except Exception as e:
            print(f"[COMPRESSOR ERROR] Compression failed: {e}")
            return "\n\n".join(context) # Fallback to raw context
        finally:
            # We don't purge immediately as model loading is slow, 
            # but we can call gc periodically or implement a timeout.
            pass

    def purge(self):
        """Manually purge from VRAM/RAM."""
        if self.compressor:
            del self.compressor
            self.compressor = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            print("[COMPRESSOR] Purged from memory.")

# Global Singleton
compressor = SovereignCompressor()
