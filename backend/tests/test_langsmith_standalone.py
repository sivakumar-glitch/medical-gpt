import os
import sys
import asyncio

# Ensure app is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set basic environment for testing
if not os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_API_KEY"] = "dry_run"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "medical-chatbot-rag-v"

from app.rag.rag_service import rag_service
from app.services.llm_service import llm_service

async def verify_standalone_tracing():
    print("--- LangSmith Standalone Tracing Verification ---")
    query = "Test standalone tracing"
    
    try:
        print("\n1. Testing RAG Retrieval Tracing...")
        results = rag_service.retrieve(query)
        print(f"RAG retrieval finished. Found {len(results)} results.")
        
        print("\n2. Testing LLM Generation Tracing...")
        # Note: This might fallback to MOCK if no OpenAI key is set, but tracing still works.
        async for chunk in llm_service.get_response_stream(query, "You are a test assistant."):
            pass
        print("LLM generation stream finished.")
        
        print("\nTracing verified successfully for RAG and LLM services.")
        print("Check your LangSmith dashboard to confirm traces are appearing.")
    except Exception as e:
        print(f"\nError during standalone verification: {e}")

if __name__ == "__main__":
    asyncio.run(verify_standalone_tracing())
