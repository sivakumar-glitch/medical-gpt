import faiss
import numpy as np
import pickle
import os

from ..core.config import settings

class VectorStore:
    def __init__(
        self, 
        index_path: str = settings.FAISS_INDEX_PATH, 
        metadata_path: str = settings.FAISS_METADATA_PATH
    ):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index = None
        self.metadata = [] # List of dicts corresponding to index IDs

    def create_index(self, dimension: int = 384):
        # Inner Product (dot product) works well with normalized embeddings (Cosine Similarity)
        self.index = faiss.IndexFlatIP(dimension) 
        self.metadata = []

    def add_documents(self, embeddings: list[list[float]], meta: list[dict]):
        if self.index is None:
            self.create_index(len(embeddings[0]))
        
        vectors = np.array(embeddings).astype('float32')
        self.index.add(vectors)
        self.metadata.extend(meta)

    def search(self, query_embedding: list[float], k: int = 5):
        if self.index is None:
            self.load()
        if self.index is None:
            return []
        
        query_vector = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(query_vector, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                results.append({
                    "score": float(distances[0][i]),
                    "metadata": self.metadata[idx]
                })
        return results

    def save(self):
        if self.index:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, "wb") as f:
                pickle.dump(self.metadata, f)

    def load(self):
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            print("Index files not found. Please run ingestion.")

vector_store = VectorStore(
    index_path=settings.FAISS_INDEX_PATH, 
    metadata_path=settings.FAISS_METADATA_PATH
)
