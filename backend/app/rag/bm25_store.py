import os
import pickle
import re

import numpy as np
from rank_bm25 import BM25Okapi

from ..core.config import settings

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def simple_tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


class BM25Store:
    def __init__(self, index_path: str = settings.BM25_INDEX_PATH):
        self.index_path = index_path
        self.corpus_tokens: list[list[str]] = []
        self.metadata: list[dict] = []
        self.bm25: BM25Okapi | None = None

    def build(self, corpus_tokens: list[list[str]], metadata: list[dict]):
        self.corpus_tokens = corpus_tokens
        self.metadata = metadata
        self.bm25 = BM25Okapi(corpus_tokens)

    def search(self, query_tokens: list[str], k: int = 5) -> list[dict]:
        if self.bm25 is None:
            self.load()
        if self.bm25 is None:
            return []

        scores = self.bm25.get_scores(query_tokens)
        top_indices = np.argsort(scores)[::-1][:k]

        results = []
        for idx in top_indices:
            if idx < len(self.metadata):
                results.append({
                    "score": float(scores[idx]),
                    "metadata": self.metadata[idx],
                })
        return results

    def save(self):
        payload = {
            "corpus_tokens": self.corpus_tokens,
            "metadata": self.metadata,
        }
        with open(self.index_path, "wb") as f:
            pickle.dump(payload, f)

    def load(self):
        if os.path.exists(self.index_path):
            with open(self.index_path, "rb") as f:
                payload = pickle.load(f)
            self.corpus_tokens = payload.get("corpus_tokens", [])
            self.metadata = payload.get("metadata", [])
            if self.corpus_tokens:
                self.bm25 = BM25Okapi(self.corpus_tokens)
        else:
            print("BM25 index file not found. Please run ingestion.")


bm25_store = BM25Store(index_path=settings.BM25_INDEX_PATH)
