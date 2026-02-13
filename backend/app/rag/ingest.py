import pandas as pd
import sys
import os

# Add parent dir to path to import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from backend.app.core.config import settings
from backend.app.rag.embeddings import get_embedding_service
from backend.app.rag.vector_store import VectorStore
from backend.app.rag.bm25_store import BM25Store, simple_tokenize

DATASET_PATH = "medDataset_processed.csv"
INDEX_PATH = settings.FAISS_INDEX_PATH
METADATA_PATH = settings.FAISS_METADATA_PATH
BM25_INDEX_PATH = settings.BM25_INDEX_PATH

def ingest_data():
    print("Loading dataset...")
    try:
        df = pd.read_csv(DATASET_PATH)
    except FileNotFoundError:
        print(f"Dataset not found at {DATASET_PATH}")
        return

    # Basic cleaning
    df.fillna("", inplace=True)
    
    documents = []
    metadatas = []
    
    print("Processing documents...")
    # Strategy: Embed "Question + Answer" for context, or just "Question" if retrieval is q-similarity dependent.
    # For RAG, embedding the 'content' we want to match against the user query is key.
    # Usually users ask questions, so matching Question is good. 
    # But sometimes the answer contains the relevant keywords.
    # Let's combine: "Type: {qtype}. Question: {Question}. Answer: {Answer}"
    
    batch_size = 64
    texts_batch = []
    meta_batch = []
    bm25_corpus_tokens = []
    bm25_metadata = []
    
    embedding_service = get_embedding_service()
    store = VectorStore(index_path=INDEX_PATH, metadata_path=METADATA_PATH)
    bm25_store = BM25Store(index_path=BM25_INDEX_PATH)
    store.create_index(384)

    total = len(df)
    
    for i, row in df.iterrows():
        # Text to embed
        text = f"Question: {row['Question']}\nAnswer: {row['Answer']}"
        
        # Metadata to store
        meta = {
            "qtype": row['qtype'],
            "question": row['Question'],
            "answer": row['Answer']
        }
        
        texts_batch.append(text)
        meta_batch.append(meta)
        bm25_corpus_tokens.append(simple_tokenize(text))
        bm25_metadata.append(meta)
        
        if len(texts_batch) >= batch_size:
            print(f"Embedding batch {i}/{total}...")
            embeddings = embedding_service.encode(texts_batch)
            store.add_documents(embeddings, meta_batch)
            texts_batch = []
            meta_batch = []

    # Final batch
    if texts_batch:
        print("Embedding final batch...")
        embeddings = embedding_service.encode(texts_batch)
        store.add_documents(embeddings, meta_batch)

    print("Saving index...")
    store.save()
    print("Saving BM25 index...")
    bm25_store.build(bm25_corpus_tokens, bm25_metadata)
    bm25_store.save()
    print("Ingestion complete!")

if __name__ == "__main__":
    ingest_data()
