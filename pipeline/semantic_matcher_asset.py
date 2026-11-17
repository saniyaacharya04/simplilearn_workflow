import json
import re
import numpy as np
from sentence_transformers import SentenceTransformer
import os

try:
    from nltk.tokenize import sent_tokenize
    import nltk
    nltk.download("punkt", quiet=True)
except Exception:
    sent_tokenize = None

# ----------------------------
# CONFIG
# ----------------------------
MODEL_NAME = "BAAI/bge-small-en-v1.5"
#MODEL_NAME = "Octen/Octen-Embedding-0.6B"
TOP_K = 3
SIM_THRESHOLD = 0.55  # conservative default

# ----------------------------
# LOAD MODEL
# ----------------------------
_model = SentenceTransformer(MODEL_NAME)

def _embed(texts):
    return _model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

# ----------------------------
# LOAD SNIPPET INDEX
# ----------------------------
_WORKFLOW_DIR = os.path.dirname(os.path.abspath(__file__))
_INDEX_PATH = os.path.join(_WORKFLOW_DIR, "Creative_Assets", "asset_rag_index.json")
if not os.path.exists(_INDEX_PATH):
    _INDEX_PATH = os.path.abspath("./Creative_Assets/asset_rag_index.json")

with open(_INDEX_PATH, "r", encoding="utf-8") as f:
    _RAW_MAP = json.load(f)

_SCRIPT_MAP = {}
for k, v in _RAW_MAP.items():
    if not os.path.isabs(v):
        candidate_rel = os.path.join(_WORKFLOW_DIR, v.lstrip("./"))
        if os.path.exists(candidate_rel):
            _SCRIPT_MAP[k] = candidate_rel
        else:
            _SCRIPT_MAP[k] = os.path.abspath(v)
    else:
        _SCRIPT_MAP[k] = v

_SNIPPET_TEXTS = list(_SCRIPT_MAP.keys())
_SNIPPET_PATHS = list(_SCRIPT_MAP.values())
_SNIPPET_EMBS = _embed(_SNIPPET_TEXTS)  # embed once

# ----------------------------
# DROP-IN MATCHER
# ----------------------------
def match_manim_snippets(
    guideline_text: str,
    top_k: int = TOP_K,
    threshold: float = SIM_THRESHOLD,
):
    """
    Drop-in semantic matcher for Manim RAG snippets.

    Returns:
        [
            {
                "matched_sentence": "...",
                "description": "...",
                "path": "...",
                "score": 0.78
            },
            ...
        ]
    """

    # 1. Split guideline into sentences
    sentences = []
    if sent_tokenize is not None:
        try:
            sentences = sent_tokenize(guideline_text)
        except Exception:
            sentences = []
    if not sentences:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', guideline_text) if s.strip()]

    if not sentences:
        return []

    sent_embs = _embed(sentences)

    matches = []

    # 2. Compare each sentence to all snippet descriptions
    for sent, sent_emb in zip(sentences, sent_embs):
        sims = np.dot(_SNIPPET_EMBS, sent_emb)
        sims = np.nan_to_num(sims, nan=0.0, posinf=1.0, neginf=-1.0)
        best_idxs = np.argsort(sims)[::-1][:top_k]

        for idx in best_idxs:
            score = float(sims[idx])
            if score >= threshold:
                matches.append({
                    "matched_sentence": sent,
                    "description": _SNIPPET_TEXTS[idx],
                    "path": _SNIPPET_PATHS[idx],
                    "score": score
                })

    # 3. Deduplicate by path (keep highest score)
    dedup = {}
    for m in matches:
        p = m["path"]
        if p not in dedup or m["score"] > dedup[p]["score"]:
            dedup[p] = m

    # 4. Sort by score
    return sorted(dedup.values(), key=lambda x: -x["score"])