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

    def compress_rag(self, context: List[str], question: str, target_token: int = 1500) -> str:
        """
        Advanced RAG compression using LongLLMLingua (Question-Aware).
        Implements CPMI (Conditional Prompt Mutual Information) to prioritize relevance to the question.
        """
        self._load_compressor()
        
        try:
            print(f"[COMPRESSOR] Executing Question-Aware CPMI Compression for RAG...")
            result = self.compressor.compress_prompt(
                context=context,
                question=question,
                target_token=target_token,
                condition_in_question="after_condition",
                reorder_context="sort", # LongLLMLingua optimization
                dynamic_context_compression_ratio=0.4,
                condition_compare=True
            )
            
            return result.get("compressed_prompt", "\n\n".join(context))
        except Exception as e:
            print(f"[COMPRESSOR ERROR] RAG Compression failed: {e}")
            return "\n\n".join(context)

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
