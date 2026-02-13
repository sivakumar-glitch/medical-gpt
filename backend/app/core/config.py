from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union, Any
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Medical Chatbot RAG"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return [v] if v else []

    # Database (Supabase or Postgres)
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/db" # Default fallback
    
    # JWT
    SECRET_KEY: str = "u6f8S_7v6N-b5_G3-k-8S_7v6N-b-G3-k"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # RAG / OpenAI
    OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview" # Updated for GTP-4o/latest
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4.1" 

    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "app/rag/faiss_index.bin"
    FAISS_METADATA_PATH: str = "app/rag/metadata.pkl"
    BM25_INDEX_PATH: str = "app/rag/bm25_index.pkl"

    # Hybrid retrieval
    HYBRID_DENSE_K: int = 12
    HYBRID_BM25_K: int = 12
    HYBRID_RRF_K: int = 60

    # LangSmith
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_PROJECT: str = "medical-chatbot-rag"
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../../../.env"), 
        env_file_encoding="utf-8", 
        extra="ignore",
        case_sensitive=False
    )

settings = Settings()
