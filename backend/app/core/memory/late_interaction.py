import numpy as np
from typing import List, Dict, Any
import torch
from sentence_transformers import SentenceTransformer

class MaxSimReranker:
    """
    Implements a simplified MaxSim (ColBERT-style) reranking layer.
    Computes the maximum similarity of each query token to all document tokens.
    """
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self.device = "xpu" if hasattr(torch, "xpu") and torch.xpu.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[RERANKER] Loading MaxSim model on {self.device}...")
        # For true MaxSim we'd use a multi-vector model, 
        # but here we use a heavy Cross-Encoder/Reranker as a high-fidelity proxy.
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name, device=self.device)

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rerank a list of candidates based on deep interaction scores.
        """
        if not candidates:
            return []
            
        # Pairs for cross-encoding
        pairs = [[query, c['content']] for c in candidates]
        
        # Compute scores
        scores = self.model.predict(pairs)
        
        # Attach scores and sort
        for i, candidate in enumerate(candidates):
            candidate['rerank_score'] = float(scores[i])
            
        ranked_candidates = sorted(candidates, key=lambda x: x['rerank_score'], reverse=True)
        return ranked_candidates[:top_k]

# Lightweight mock for token-level MaxSim if heavy model is unavailable
def compute_maxsim(query_tokens: np.ndarray, doc_tokens: np.ndarray) -> float:
    """
    Manual MaxSim: \sum_{i} \max_{j} (q_i \cdot d_j)
    """
    # query_tokens: [Q_len, D_dim]
    # doc_tokens: [D_len, D_dim]
    sim_matrix = np.dot(query_tokens, doc_tokens.T) # [Q_len, D_len]
    max_sims = np.max(sim_matrix, axis=1) # [Q_len]
    return float(np.sum(max_sims))
