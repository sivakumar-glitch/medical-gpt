import os
import sys
import asyncio

# Ensure app is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set dummy key if not present for basic validation of decorators
if not os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_API_KEY"] = "dry_run"

from app.api.v1.endpoints.chat import chat_stream, ChatRequest

async def verify_tracing():
    print("--- LangSmith Tracing Verification ---")
    print(f"Project: {os.environ.get('LANGCHAIN_PROJECT', 'Not Set')}")
    print(f"Endpoint: {os.environ.get('LANGCHAIN_ENDPOINT', 'Not Set')}")
    
    request = ChatRequest(query="Verify LangSmith tracing is working.", history=[])
    
    print("\nStarting traced execution...")
    try:
        # This will invoke the decorators in chat.py, rag_service.py, and llm_service.py
        result = await chat_stream(request)
        print("Successfully initiated chat stream.")
        
        # Consuming the generator to ensure the LLM service trace completes
        async for chunk in result.body_iterator:
            # print(chunk, end="", flush=True)
            pass
            
        print("\n\nExecution finished successfully.")
        print("If your LANGCHAIN_API_KEY is valid, check smith.langchain.com.")
    except Exception as e:
        print(f"\nError during verification: {e}")

if __name__ == "__main__":
    asyncio.run(verify_tracing())
